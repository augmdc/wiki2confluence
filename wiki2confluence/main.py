import yaml
import os
import sys
import logging
import argparse
from directory_mapper.wiki_page_collector import WikiPageCollector
from wiki_api import WikiAPI
from wiki_converter import WikiConverter
from confluence_api import ConfluenceAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'config.yaml')
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

def process_page(wiki_api, confluence_api, page_title, config, parent_id, dry_run=False):
    try:
        normalized_title = wiki_api.normalize_title(page_title)
        
        wiki_content = wiki_api.get_wiki_content(normalized_title)
        if wiki_content == "":
            logger.info(f"Page '{normalized_title}' is empty or not found. Would create new page with placeholder content.")
            wiki_content = f"# {page_title}\n\nThis page is currently empty or was not found in the original wiki."

        html_content = wiki_api.convert_to_html(wiki_content)
        if not html_content:
            logger.error(f"Failed to convert content to HTML for page: {normalized_title}")
            return False

        markdown_content = WikiConverter.wiki_to_markdown(html_content)
        if not markdown_content:
            logger.error(f"Failed to convert content to Markdown for page: {normalized_title}")
            return False

        confluence_title = normalized_title.replace('_', ' ')

        if dry_run:
            logger.info(f"[DRY RUN] Would create/update page: {confluence_title}")
            logger.info(f"[DRY RUN] Content preview (first 100 characters): {markdown_content[:100]}...")
        else:
            page_id = confluence_api.create_or_update_page(
                space=config['confluence']['space_key'],
                title=confluence_title,
                body=markdown_content,
                parent_id=parent_id
            )
            
            if not page_id:
                logger.error(f"Failed to upload page to Confluence: {confluence_title}")
                return False

        logger.info(f"Successfully processed page: {confluence_title}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error processing page {normalized_title}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Wiki to Confluence Migration Tool")
    parser.add_argument("--single-page", help="Process a single page by title", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without creating Confluence pages")
    args = parser.parse_args()

    try:
        config = load_config()
        
        verify_ssl = config.get('mediawiki', {}).get('verify_ssl', True)
        
        wiki_api = WikiAPI(
            api_url=config['mediawiki']['api_url'],
            wiki_url=config['mediawiki']['wiki_url'],
            verify_ssl=verify_ssl
        )
        page_collector = WikiPageCollector(
            api_url=config['mediawiki']['api_url'],
            wiki_url=config['mediawiki']['wiki_url'],
            verify_ssl=verify_ssl
        )
        
        confluence_api = ConfluenceAPI(
            url=config['confluence']['url'],
            username=config['confluence']['username'],
            api_token=config['confluence']['api_token'],
            rate_limit=100
        )
        
        wiki_page_id = config['confluence']['parent_page_id']

        if not args.dry_run:
            # Verify the existence of the parent Wiki folder
            if not confluence_api.verify_page_exists(wiki_page_id):
                logger.error(f"Parent Wiki folder with ID {wiki_page_id} not found in Confluence. Please check your configuration.")
                sys.exit(1)

        if args.dry_run:
            logger.info("Running in DRY RUN mode. No pages will be created or updated in Confluence.")

        if args.single_page:
            # Process a single page
            success = process_page(wiki_api, confluence_api, args.single_page, config, wiki_page_id, args.dry_run)
            if success:
                logger.info(f"Successfully processed page: {args.single_page}")
            else:
                logger.error(f"Failed to process page: {args.single_page}")
        else:
            # Process all pages
            all_pages = page_collector.collect_all_pages()
            logger.info(f"Total number of pages to process: {len(all_pages)}")
            
            for page_title in all_pages:
                success = process_page(wiki_api, confluence_api, page_title, config, wiki_page_id, args.dry_run)
                if not success:
                    page_collector.add_unprocessed_page(page_title)

            # Save the list of pages to a text file, including unprocessed pages
            page_collector.save_pages_to_file(all_pages, "wiki_pages.txt")

            logger.info(f"Wiki migration {'simulation' if args.dry_run else 'process'} completed.")
            logger.info(f"Total pages processed: {len(all_pages) - len(page_collector.unprocessed_pages)}")
            if page_collector.unprocessed_pages:
                logger.info(f"Number of unprocessed pages: {len(page_collector.unprocessed_pages)}")

    except Exception as e:
        logger.error(f"An error occurred during migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()