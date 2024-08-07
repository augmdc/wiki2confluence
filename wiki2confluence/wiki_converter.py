from html2text import HTML2Text

class WikiConverter:
    @staticmethod
    def wiki_to_markdown(html_content):
        h = HTML2Text()
        h.ignore_links = False
        markdown_content = h.handle(html_content)
        return markdown_content

    @staticmethod
    def save_to_markdown(content, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Content saved to {filename}")
        except IOError as e:
            print(f"Error saving file: {e}")