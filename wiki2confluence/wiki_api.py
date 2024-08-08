import requests
from functools import lru_cache
import re
import logging
import threading

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class WikiAPI:
    def __init__(self, api_url, wiki_url, verify_ssl=True):
        self.api_url = api_url
        self.wiki_url = wiki_url
        self.verify_ssl = verify_ssl
        self.local = threading.local()
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()

    @property
    def session(self):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
        return self.local.session

    @staticmethod
    def normalize_title(title):
        # Convert spaces to underscores and remove any invalid characters
        return re.sub(r'[^a-zA-Z0-9_./:;]', '', title.replace(' ', '_'))

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
                logger.info(f"No content found for page: {normalized_title}")
                return ""
            
            page = next(iter(pages.values()))
            if 'missing' in page:
                logger.info(f"Page '{normalized_title}' does not exist in the wiki. Creating new page.")
                return ""
            
            if 'revisions' not in page:
                logger.info(f"No revisions found for page: {normalized_title}")
                return ""
            
            return page['revisions'][0]['slots']['main']['*']
        except requests.RequestException as e:
            logger.error(f"Network error fetching wiki content for '{normalized_title}' from {self.wiki_url}: {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response structure for '{normalized_title}' from {self.wiki_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching wiki content for '{normalized_title}' from {self.wiki_url}: {e}")
        return ""

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
            logger.error(f"Error converting wiki to HTML: {e}")
            return None

    def is_page_empty(self, page_title):
        content = self.get_wiki_content(page_title)
        return content.strip() == ""