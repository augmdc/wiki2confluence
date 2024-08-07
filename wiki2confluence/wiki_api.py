import requests

class WikiAPI:
    def __init__(self, api_url, verify_ssl=True):
        self.api_url = api_url
        self.verify_ssl = verify_ssl

    def get_wiki_content(self, page_title):
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json"
        }
        
        try:
            response = requests.get(self.api_url, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"Error fetching content: {data['error']['info']}")
                return None
            
            wiki_content = data['parse']['wikitext']['*']
            print("Raw wiki content:")
            print(wiki_content[:500])  # Print first 500 characters
            return wiki_content
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
            response = requests.post(self.api_url, data=params, verify=self.verify_ssl)
            response.raise_for_status()
            html_content = response.json()['parse']['text']['*']
            print("Converted HTML content:")
            print(html_content[:500])  # Print first 500 characters
            return html_content
        except requests.RequestException as e:
            print(f"Error converting wiki to HTML: {e}")
            return None