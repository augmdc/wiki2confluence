import requests
import logging
from wiki_api import WikiAPI

class WikiPageCollector:
    def __init__(self, api_url, verify_ssl=True):
        self.api_url = api_url
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.wiki_api = WikiAPI(api_url, verify_ssl)
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)

    def collect_non_empty_pages(self):
        """
        Collect all non-empty pages from the wiki.
        """
        all_pages = self._get_all_pages()
        non_empty_pages = []
        for page_title in all_pages:
            if not self.wiki_api.is_page_empty(page_title):
                non_empty_pages.append(page_title)
        return non_empty_pages

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
                    # Store the title with underscores
                    all_pages.append(page['title'])
                
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
        Save the list of pages to a text file.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for page in pages:
                    # Write the underscore version of the title
                    f.write(f"{page}\n")
            self.logger.info(f"Page list saved to {filename}")
        except IOError as e:
            self.logger.error(f"Error saving page list to file: {e}")