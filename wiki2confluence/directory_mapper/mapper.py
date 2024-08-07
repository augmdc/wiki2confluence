import requests
from .models import WikiStructure, WikiPage
from wiki_api import WikiAPI

class DirectoryMapper:
    def __init__(self, api_url, verify_ssl=True):
        self.api_url = api_url
        self.verify_ssl = verify_ssl
        self.structure = WikiStructure()
        self.wiki_api = WikiAPI(api_url, verify_ssl=verify_ssl)

    def map_wiki_structure(self, start_page="Main Page"):
        """
        Map the entire wiki structure starting from the given page.
        """
        visited = set()
        self._map_page(start_page, visited)
        return self.structure

    def _map_page(self, page_title, visited, parent=None):
        """
        Recursively map a page and its subpages.
        """
        if page_title in visited:
            return

        visited.add(page_title)
        page_info = self._get_page_info(page_title)

        if not page_info:
            return

        current_page = WikiPage(title=page_title, content=page_info['content'])
        self.structure.add_page(current_page, parent)

        for subpage in page_info['subpages']:
            self._map_page(subpage, visited, current_page)

    def _get_page_info(self, page_title):
        """
        Fetch page information from the MediaWiki API.
        """
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "revisions|links",
            "rvprop": "content",
            "format": "json"
        }

        try:
            response = requests.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            page = next(iter(data['query']['pages'].values()))
            content = page['revisions'][0]['*'] if 'revisions' in page else ""
            subpages = [link['title'] for link in page.get('links', []) if 'title' in link]

            return {'content': content, 'subpages': subpages}
        except requests.RequestException as e:
            print(f"Error fetching page info: {e}")
            return None