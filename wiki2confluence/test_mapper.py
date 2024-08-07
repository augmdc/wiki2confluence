import os
import sys
import yaml
import logging
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from directory_mapper import DirectoryMapper
from wiki_api import WikiAPI

CONFIG_PATH = r"C:\Users\achabris\Documents\GitHub\wiki2confluence\config.yaml"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
        raise

def save_structure_as_json(structure, output_dir):
    def structure_to_dict(pages):
        return [{'title': page.title, 'children': structure_to_dict(page.children)} for page in pages]
    
    structure_dict = structure_to_dict(structure.pages)
    json_path = os.path.join(output_dir, 'wiki_structure.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(structure_dict, f, ensure_ascii=False, indent=2)
    logging.info(f"Wiki structure saved to {json_path}")

def main(output_dir):
    try:
        # Load configuration
        logging.info("Loading configuration...")
        config = load_config()
        
        # Initialize DirectoryMapper with SSL verification disabled
        logging.info("Initializing DirectoryMapper...")
        mapper = DirectoryMapper(config['mediawiki']['api_url'], verify_ssl=False)
        
        logging.info("Mapping wiki structure...")
        wiki_structure = mapper.map_wiki_structure()
        
        if not wiki_structure.pages:
            logging.warning("No pages were mapped in the wiki structure.")
        else:
            logging.info(f"Mapped {len(wiki_structure.pages)} top-level pages.")
        
        # Save the structure as JSON
        save_structure_as_json(wiki_structure, output_dir)
        
        logging.info("Script completed successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error occurred: {e}")
        logging.info("Please check your network connection and the MediaWiki API URL in the config file.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Script execution finished.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python test_mapper.py <output_directory>")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    if not os.path.exists(CONFIG_PATH):
        logging.error(f"Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        logging.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
    
    main(output_dir)