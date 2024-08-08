from bs4 import BeautifulSoup
import re
from collections import defaultdict

class WikiConverter:
    @staticmethod
    def clean_title(title):
        # Remove any HTML tags
        cleaned_title = re.sub(r'<.*?>', '', title)
        # Remove any leading/trailing whitespace
        cleaned_title = cleaned_title.strip()
        return cleaned_title

    @staticmethod
    def create_anchor(text):
        # Create a Confluence-style anchor from text
        return re.sub(r'[^a-zA-Z0-9-]+', '-', text.lower()).strip('-')

    @staticmethod
    def wiki_to_markdown(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove edit links
        for edit_link in soup.find_all('span', class_='mw-editsection'):
            edit_link.decompose()
        
        markdown_content = []
        toc_items = []
        
        def process_element(element):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                title = WikiConverter.clean_title(element.get_text())
                anchor = WikiConverter.create_anchor(title)
                toc_items.append((level, title, anchor))
                return f"{'#' * level} {title}\n\n"
            elif element.name == 'p':
                return WikiConverter.process_paragraph(element)
            elif element.name == 'ul':
                # Skip the original table of contents
                if element.find('li', text=re.compile('contents', re.IGNORECASE)):
                    return ""
                content = ''.join(f"* {WikiConverter.process_list_item(li)}\n" for li in element.find_all('li', recursive=False)) + "\n"
                return content
            elif element.name == 'ol':
                return ''.join(f"{i}. {WikiConverter.process_list_item(li)}\n" for i, li in enumerate(element.find_all('li', recursive=False), 1)) + "\n"
            else:
                return element.get_text()

        # Process each element in the HTML while preserving structure
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'div']):
            markdown_content.append(process_element(element))
        
        # Apply structural deduplication
        markdown_content = WikiConverter.remove_structural_duplicates(markdown_content)
        
        # Generate and insert table of contents at the beginning
        toc = WikiConverter.generate_toc(toc_items)
        markdown_content.insert(0, "## Table of Contents\n\n" + toc)
        
        return ''.join(markdown_content)

    @staticmethod
    def process_paragraph(p_element):
        content = []
        for child in p_element.children:
            if child.name == 'a':
                href = child.get('href', '')
                text = child.get_text()
                if href.startswith('http'):
                    content.append(f"[{text}]({href})")
                else:
                    content.append(text)
            elif child.name == 'img':
                src = child.get('src', '')
                alt = child.get('alt', '')
                content.append(f"![{alt}]({src})")
            else:
                content.append(str(child))
        return ''.join(content) + "\n\n"

    @staticmethod
    def process_list_item(li_element):
        content = []
        for child in li_element.children:
            if child.name == 'a':
                href = child.get('href', '')
                text = child.get_text()
                if href.startswith('http'):
                    content.append(f"[{text}]({href})")
                else:
                    content.append(text)
            else:
                content.append(str(child))
        return ''.join(content)

    @staticmethod
    def generate_toc(toc_items):
        toc = []
        for level, title, anchor in toc_items:
            if title.lower() != "contents":  # Skip "Contents" entries
                indent = "  " * (level - 1)
                toc.append(f"{indent}- [{title}](#{anchor})\n")
        return ''.join(toc) + "\n"

    @staticmethod
    def remove_structural_duplicates(content):
        sections = defaultdict(list)
        current_section = []
        current_heading = None

        for item in content:
            if item.startswith('#'):  # It's a heading
                if current_heading:
                    sections[current_heading].append(''.join(current_section))
                current_heading = item.strip()
                current_section = [item]
            else:
                current_section.append(item)

        # Add the last section
        if current_heading:
            sections[current_heading].append(''.join(current_section))

        # Keep only unique sections for each heading
        deduplicated_content = []
        for heading, section_contents in sections.items():
            unique_sections = list(dict.fromkeys(section_contents))  # Remove duplicates while preserving order
            deduplicated_content.extend(unique_sections)

        return deduplicated_content

    @staticmethod
    def save_to_markdown(content, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Content saved to {filename}")
        except IOError as e:
            print(f"Error saving file: {e}")