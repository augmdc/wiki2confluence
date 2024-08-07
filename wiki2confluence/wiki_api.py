import requests

class WikiAPI:
    def __init__(self, api_url):
        self.api_url = api_url

    def get_wiki_content(self, page_title):
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json"
        }
        
        try:
            response = requests.get(self.api_url, params=params, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"Error fetching content: {data['error']['info']}")
                return None
            
            return data['parse']['wikitext']['*']
        except requests.RequestException as e:
            print(f"Error fetching wiki content: {e}")
            return None

    def convert_to_html(self, wiki_content):
        params = {
            "action": "parse",
            "text": wiki_content,
            "contentmodel": "wikitext",
            "format": "json"
        }
        
        try:
            response = requests.post(self.api_url, data=params, verify=False)
            response.raise_for_status()
            html_content = response.json()['parse']['text']['*']
            return html_content
        except requests.RequestException as e:
            print(f"Error converting wiki to HTML: {e}")
            return None