class WikiPage:
    def __init__(self, title, content):
        self.title = title
        self.content = content
        self.children = []

class WikiStructure:
    def __init__(self):
        self.pages = []

    def add_page(self, page, parent=None):
        if parent:
            parent.children.append(page)
        else:
            self.pages.append(page)

    def get_page(self, title):
        return self._find_page(self.pages, title)

    def _find_page(self, pages, title):
        for page in pages:
            if page.title == title:
                return page
            found = self._find_page(page.children, title)
            if found:
                return found
        return None