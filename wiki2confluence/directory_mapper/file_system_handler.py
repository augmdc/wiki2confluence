import os
import re

class FileSystemHandler:
    @staticmethod
    def sanitize_filename(filename):
        # Remove characters that are invalid in Windows filenames
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '', filename)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Trim to 255 characters (maximum filename length in Windows)
        return sanitized[:255]

    @staticmethod
    def create_directory_structure(structure, base_path):
        """
        Create the directory structure on the local machine.
        """
        for page in structure.pages:
            FileSystemHandler._create_page_file(page, base_path)

    @staticmethod
    def _create_page_file(page, base_path, current_path=''):
        sanitized_title = FileSystemHandler.sanitize_filename(page.title)
        page_path = os.path.join(base_path, current_path, sanitized_title)
        os.makedirs(os.path.dirname(page_path), exist_ok=True)
        
        try:
            with open(f"{page_path}.md", 'w', encoding='utf-8') as f:
                f.write(page.content)
        except Exception as e:
            print(f"Error writing file {page_path}.md: {e}")

        for child in page.children:
            FileSystemHandler._create_page_file(child, base_path, os.path.join(current_path, sanitized_title))