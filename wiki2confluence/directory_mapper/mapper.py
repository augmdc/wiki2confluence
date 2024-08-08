import requests
import logging
from .models import WikiStructure, WikiPage

class DirectoryMapper:
    def __init__(self, api_url, verify_ssl=True):
        self.api_url = api_url
        self.verify_ssl = verify_ssl
        self.structure = WikiStructure()
        self.session = requests.Session()
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()
        self.logger = logging.getLogger(__name__)

    def map_wiki_structure(self):
        """
        Map the entire wiki structure by fetching all pages.
        """
        all_pages = self._get_all_pages()
        for page_title in all_pages:
            try:
                self._add_page_to_structure(page_title)
            except Exception as e:
                self.logger.error(f"Failed to add page {page_title} to structure: {str(e)}")
        return self.structure

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
                    all_pages.append(page['title'])
                
                if 'continue' in data:
                    continue_param = data['continue']['apcontinue']
                else:
                    break
            except requests.RequestException as e:
                self.logger.error(f"Error fetching all pages: {e}")
                break
        return all_pages

    def _add_page_to_structure(self, page_title):
        """
        Add a page to the wiki structure.
        """
        if self.structure.get_page(page_title):
            return  # Page already exists in structure

        page = WikiPage(title=page_title)
        parent_title = self._find_parent_title(page_title)
        
        if parent_title:
            parent_page = self.structure.get_page(parent_title)
            if not parent_page:
                parent_page = self._add_page_to_structure(parent_title)
            self.structure.add_page(page, parent_page)
        else:
            self.structure.add_page(page)
        
        return page

    def _find_parent_title(self, page_title):
        """
        Find the parent title of a given page based on its title structure.
        """
        parts = page_title.split('/')
        if len(parts) > 1:
            return '/'.join(parts[:-1])
        return None