import requests
import logging
from wiki_api import WikiAPI

class WikiPageCollector:
    def __init__(self, api_url, wiki_url, verify_ssl=True):
        self.api_url = api_url
        self.wiki_url = wiki_url
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.wiki_api = WikiAPI(api_url, wiki_url, verify_ssl)
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.unprocessed_pages = []

    def collect_all_pages(self):
        """
        Collect all pages from the wiki, including empty ones.
        """
        return self._get_all_pages()

    def _get_all_pages(self):
        """
        Fetch all pages from the MediaWiki API.
        """
        all_pages = []
        continue_param = ''
        while True:
            params = {
                "action": "query",
                "list": "allpages",
                "apfrom": continue_param,
                "aplimit": "max",
                "format": "json"
            }
            try:
                response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
                response.raise_for_status()
                data = response.json()
                
                for page in data['query']['allpages']:
                    all_pages.append(self.wiki_api.normalize_title(page['title']))
                
                if 'continue' in data:
                    continue_param = data['continue']['apcontinue']
                else:
                    break
            except requests.RequestException as e:
                self.logger.error(f"Error fetching all pages: {e}")
                break
        return all_pages

    def save_pages_to_file(self, pages, filename):
        """
        Save the list of pages to a text file, add a page count, and list unprocessed pages.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("All Wiki Pages:\n")
                for page in pages:
                    f.write(f"{page}\n")
                
                f.write(f"\nTotal number of pages: {len(pages)}\n")
                
            self.logger.info(f"Page list saved to {filename} with page count")
        except IOError as e:
            self.logger.error(f"Error saving page list to file: {e}")