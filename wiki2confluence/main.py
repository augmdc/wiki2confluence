import argparse
import yaml
import os
from wiki_api import WikiAPI
from wiki_converter import WikiConverter
from confluence_api import ConfluenceAPI

CONFIG_FILE = '../config.yaml'  # Hardcoded config file path

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main(page_title, output_file=None):
    config = load_config()
    
    wiki_api = WikiAPI(config['mediawiki']['api_url'])
    
    print(f"Fetching content for page: {page_title}")
    wiki_content = wiki_api.get_wiki_content(page_title)
    
    if wiki_content:
        print("Converting content to HTML")
        html_content = wiki_api.convert_to_html(wiki_content)
        
        if html_content:
            print("Converting HTML to Markdown")
            markdown_content = WikiConverter.wiki_to_markdown(html_content)
            
            if markdown_content:
                if output_file is None:
                    output_file = config['output']['default_file']
                WikiConverter.save_to_markdown(markdown_content, output_file)
                
                # Create Confluence page
                confluence_api = ConfluenceAPI(
                    url=config['confluence']['url'],
                    username=config['confluence']['username'],
                    api_token=config['confluence']['api_token']
                )
                
                page_id = confluence_api.create_page(
                    space=config['confluence']['space_key'],
                    parent_id=config['confluence']['parent_page_id'],
                    title=page_title,
                    body=markdown_content
                )
                
                if page_id:
                    print(f"Confluence page created with ID: {page_id}")
                else:
                    print("Failed to create Confluence page")
            else:
                print("Failed to convert content to Markdown")
        else:
            print("Failed to convert content to HTML")
    else:
        print("Failed to fetch wiki content")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a wiki page to Markdown and create Confluence page")
    parser.add_argument("page_title", help="Title of the wiki page to convert")
    parser.add_argument("-o", "--output", help="Output Markdown file name (optional)")
    
    args = parser.parse_args()
    
    main(args.page_title, args.output)