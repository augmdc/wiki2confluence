import yaml
import os
import sys
import logging
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

def process_page(wiki_api, confluence_api, page_title, config, parent_id):
    try:
        # Use the same normalization method for consistency
        normalized_title = wiki_api.normalize_title(page_title)
        
        wiki_content = wiki_api.get_wiki_content(normalized_title)
        if not wiki_content:
            logger.error(f"Failed to fetch wiki content for page: {normalized_title}")
            return False

        html_content = wiki_api.convert_to_html(wiki_content)
        if not html_content:
            logger.error(f"Failed to convert content to HTML for page: {normalized_title}")
            return False

        markdown_content = WikiConverter.wiki_to_markdown(html_content)
        if not markdown_content:
            logger.error(f"Failed to convert content to Markdown for page: {normalized_title}")
            return False

        # Convert underscores back to spaces for the Confluence title
        confluence_title = normalized_title.replace('_', ' ')

        page_id = confluence_api.create_or_update_page(
            space=config['confluence']['space_key'],
            title=confluence_title,
            body=markdown_content,
            parent_id=parent_id
        )
        
        if not page_id:
            logger.error(f"Failed to upload page to Confluence: {confluence_title}")
            return False

        return True
    except Exception as e:
        logger.error(f"Unexpected error processing page {normalized_title}: {str(e)}")
        return False

def main():
    try:
        config = load_config()
        
        verify_ssl = config.get('mediawiki', {}).get('verify_ssl', True)
        
        wiki_api = WikiAPI(config['mediawiki']['api_url'], verify_ssl=verify_ssl)
        page_collector = WikiPageCollector(config['mediawiki']['api_url'], verify_ssl=verify_ssl)
        
        confluence_api = ConfluenceAPI(
            url=config['confluence']['url'],
            username=config['confluence']['username'],
            api_token=config['confluence']['api_token'],
            rate_limit=100
        )
        
        wiki_page_id = config['confluence']['parent_page_id']

        # Verify the existence of the parent Wiki folder
        if not confluence_api.verify_page_exists(wiki_page_id):
            logger.error(f"Parent Wiki folder with ID {wiki_page_id} not found in Confluence. Please check your configuration.")
            sys.exit(1)

        # Collect non-empty pages
        non_empty_pages = page_collector.collect_non_empty_pages()
        
        # Save the list of pages to a text file
        page_collector.save_pages_to_file(non_empty_pages, "wiki_pages.txt")
        
        # Process all non-empty pages
        for page_title in non_empty_pages:
            process_page(wiki_api, confluence_api, page_title, config, wiki_page_id)

        logger.info("Wiki migration completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()