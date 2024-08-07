from atlassian import Confluence

class ConfluenceAPI:
    def __init__(self, url, username, api_token):
        self.confluence = Confluence(
            url=url,
            username=username,
            password=api_token,
            cloud=True
        )

    def create_page(self, space, parent_id, title, body):
        try:
            page = self.confluence.create_page(
                space=space,
                parent_id=parent_id,
                title=title,
                body=body
            )
            print(f"Page created: {page['id']}")
            return page['id']
        except Exception as e:
            print(f"Error creating Confluence page: {e}")
            return None

    def update_page(self, page_id, title, body):
        try:
            page = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body
            )
            print(f"Page updated: {page['id']}")
            return page['id']
        except Exception as e:
            print(f"Error updating Confluence page: {e}")
            return None