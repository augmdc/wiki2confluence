import yaml
import os
import json
import concurrent.futures
import time
import logging
from directory_mapper.mapper import DirectoryMapper
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

def generate_wiki_structure_json(structure):
    def page_to_dict(page):
        return {
            'title': page.title,
            'children': [page_to_dict(child) for child in page.children]
        }

    return [page_to_dict(page) for page in structure.pages]

def save_wiki_structure_json(structure):
    json_structure = generate_wiki_structure_json(structure)
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    json_file_path = os.path.join(desktop_path, 'wiki_structure.json')
    
    with open(json_file_path, 'w') as f:
        json.dump(json_structure, f, indent=2)
    
    logger.info(f"Wiki structure JSON saved to: {json_file_path}")

def process_page(wiki_api, page):
    try:
        wiki_content = wiki_api.get_wiki_content(page.title)
        if not wiki_content:
            return False, f"Failed to fetch wiki content"

        html_content = wiki_api.convert_to_html(wiki_content)
        if not html_content:
            return False, f"Failed to convert content to HTML"

        markdown_content = WikiConverter.wiki_to_markdown(html_content)
        if not markdown_content:
            return False, f"Failed to convert content to Markdown"

        page.content = markdown_content
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    try:
        logger.info("Starting wiki migration process")
        config = load_config()
        
        verify_ssl = config.get('mediawiki', {}).get('verify_ssl', True)
        max_workers = config.get('general', {}).get('max_workers', 10)
        
        wiki_api = WikiAPI(config['mediawiki']['api_url'], verify_ssl=verify_ssl)
        directory_mapper = DirectoryMapper(config['mediawiki']['api_url'], verify_ssl=verify_ssl)
        
        logger.info("Mapping wiki structure")
        wiki_structure = directory_mapper.map_wiki_structure()
        logger.info(f"Wiki structure mapped. Total pages: {len(wiki_structure.get_all_pages())}")
        
        save_wiki_structure_json(wiki_structure)
        
        confluence_api = ConfluenceAPI(
            url=config['confluence']['url'],
            username=config['confluence']['username'],
            api_token=config['confluence']['api_token'],
            rate_limit=2  # 2 requests per second
        )
        
        logger.info("Converting wiki content to Markdown")
        all_pages = wiki_structure.get_all_pages()
        total_pages = len(all_pages)
        processed_pages = 0
        failed_pages = []

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {executor.submit(process_page, wiki_api, page): page for page in all_pages}
            for future in concurrent.futures.as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    success, error_message = future.result()
                    processed_pages += 1
                    if not success:
                        failed_pages.append((page.title, error_message))
                        logger.error(f"Failed to process page: {page.title}. Error: {error_message}")
                except Exception as exc:
                    failed_pages.append((page.title, str(exc)))
                    logger.error(f"Exception occurred while processing page: {page.title}. Error: {exc}")
                
                if processed_pages % 10 == 0 or processed_pages == total_pages:
                    logger.info(f"Progress: {processed_pages}/{total_pages} pages processed")

        logger.info("Creating/Updating pages in Confluence Wiki")
        wiki_page_id = config['confluence']['parent_page_id']
        if not confluence_api.create_pages_in_wiki(
            space=config['confluence']['space_key'],
            structure=wiki_structure,
            wiki_page_id=wiki_page_id
        ):
            logger.error("Failed to create/update pages in Confluence Wiki")
            return

        end_time = time.time()
        
        logger.info(f"Wiki migration completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total pages: {total_pages}")
        logger.info(f"Successfully processed: {total_pages - len(failed_pages)}")
        logger.info(f"Failed pages: {len(failed_pages)}")
        
        if failed_pages:
            logger.error("The following pages failed to process:")
            for page, error in failed_pages:
                logger.error(f"- {page}: {error}")

    except Exception as e:
        logger.error(f"An error occurred during migration: {str(e)}")

if __name__ == "__main__":
    main()