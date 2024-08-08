class WikiPage:
    def __init__(self, title, content=None, parent=None):
        self.title = title
        self.content = content
        self.children = []
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

class WikiStructure:
    def __init__(self):
        self.pages = []

    def add_page(self, page, parent=None):
        if parent:
            parent.add_child(page)
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

    def get_all_pages(self):
        all_pages = []
        self._collect_pages(self.pages, all_pages)
        return all_pages

    def _collect_pages(self, pages, all_pages):
        for page in pages:
            all_pages.append(page)
            self._collect_pages(page.children, all_pages)