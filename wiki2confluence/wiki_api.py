import requests
from functools import lru_cache
import re
import logging
import threading
from bs4 import BeautifulSoup
import urllib.parse

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

    def get_page_images(self, page_title):
        params = {
            "action": "query",
            "prop": "images",
            "titles": page_title,
            "imlimit": "max",
            "format": "json"
        }
        try:
            response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            page = next(iter(data['query']['pages'].values()))
            images = page.get('images', [])
            
            image_info = []
            for image in images:
                image_title = image['title']
                image_info.append(self.get_image_info(image_title))
            
            return image_info
        except Exception as e:
            logger.error(f"Error fetching images for page '{page_title}': {e}")
            return []

    def get_image_info(self, image_title):
        params = {
            "action": "query",
            "titles": image_title,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "format": "json"
        }
        try:
            response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            page = next(iter(data['query']['pages'].values()))
            if 'imageinfo' in page:
                info = page['imageinfo'][0]
                return {
                    'title': image_title,
                    'url': info['url'],
                    'size': info['size'],
                    'mime': info['mime']
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching image info for '{image_title}': {e}")
            return None

    def download_image(self, image_url):
        try:
            response = self.session.get(image_url, verify=self.verify_ssl)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image from '{image_url}': {e}")
            return None

    def get_images_from_html(self, page_title):
        html_content = self.get_page_html(page_title)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        images = []

        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urllib.parse.urljoin(self.wiki_url, src)
                images.append({
                    'url': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })

        return images

    def get_page_html(self, page_title):
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "text",
            "format": "json"
        }
        try:
            response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            return data['parse']['text']['*']
        except Exception as e:
            logger.error(f"Error fetching HTML for page '{page_title}': {e}")
            return None

    def get_all_images(self):
        params = {
            "action": "query",
            "list": "allimages",
            "ailimit": "max",
            "aiprop": "url|size|mime",
            "format": "json"
        }
        all_images = []
        while True:
            try:
                response = self.session.get(self.api_url, params=params, verify=self.verify_ssl)
                response.raise_for_status()
                data = response.json()
                
                all_images.extend(data['query']['allimages'])
                
                if 'continue' in data:
                    params['aicontinue'] = data['continue']['aicontinue']
                else:
                    break
            except Exception as e:
                logger.error(f"Error fetching all images: {e}")
                break
        
        return all_images