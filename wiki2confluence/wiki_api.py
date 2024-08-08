import requests
from functools import lru_cache
import re
import logging

logger = logging.getLogger(__name__)

class WikiAPI:
    def __init__(self, api_url, verify_ssl=True):
        self.api_url = api_url
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()

    @staticmethod
    def normalize_title(title):
        return re.sub(r'\s+', '_', title.strip())

    @lru_cache(maxsize=1000)
    def get_wiki_content(self, page_title):
        normalized_title = self.normalize_title(page_title)
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": normalized_title,
            "rvprop": "content",
            "rvslots": "main",
            "format": "json"
        }
        
        try:
            response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            
            pages = data['query'].get('pages', {})
            if not pages:
                logger.error(f"No pages found for title: {normalized_title}")
                return None
            
            page = next(iter(pages.values()))
            if 'missing' in page:
                logger.error(f"Page '{normalized_title}' does not exist in the wiki")
                return None
            
            if 'revisions' not in page:
                logger.error(f"No revisions found for page: {normalized_title}")
                return None
            
            return page['revisions'][0]['slots']['main']['*']
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching wiki content for '{normalized_title}': {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response structure for '{normalized_title}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching wiki content for '{normalized_title}': {e}")
        return None


    @lru_cache(maxsize=1000)
    def convert_to_html(self, wiki_content):
        params = {
            "action": "parse",
            "text": wiki_content,
            "contentmodel": "wikitext",
            "format": "json"
        }
        
        try:
            response = self.session.post(self.api_url, data=params, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()['parse']['text']['*']
        except Exception as e:
            print(f"Error converting wiki to HTML: {e}")
            return None