from atlassian import Confluence
import markdown2

class ConfluenceAPI:
    def __init__(self, url, username, api_token):
        self.confluence = Confluence(
            url=url,
            username=username,
            password=api_token,
            cloud=True
        )

    def markdown_to_html(self, markdown_content):
        return markdown2.markdown(markdown_content)

    def get_page_id(self, space, title):
        try:
            page = self.confluence.get_page_by_title(space, title)
            return page['id'] if page else None
        except Exception as e:
            print(f"Error checking for existing page: {e}")
            return None

    def create_or_update_page(self, space, title, body, parent_id=None):
        try:
            html_body = self.markdown_to_html(body)
            existing_page_id = self.get_page_id(space, title)

            if existing_page_id:
                page = self.confluence.update_page(
                    page_id=existing_page_id,
                    title=title,
                    body=html_body,
                    parent_id=parent_id
                )
                print(f"Page updated: {page['id']}")
            else:
                page = self.confluence.create_page(
                    space=space,
                    title=title,
                    body=html_body,
                    parent_id=parent_id
                )
                print(f"Page created: {page['id']}")

            return page['id']
        except Exception as e:
            print(f"Error creating or updating Confluence page: {e}")
            return None