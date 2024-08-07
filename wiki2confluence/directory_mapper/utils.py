import os

def print_structure(pages, level=0):
    for page in pages:
        print("  " * level + f"- {page.title}")
        print_structure(page.children, level + 1)

def verify_structure(base_path):
    for root, dirs, files in os.walk(base_path):
        level = root.replace(base_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")

def sanitize_filename(filename):
    """
    Sanitize a filename to be safe for most file systems.
    """
    # Replace problematic characters with underscores
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        filename = filename.replace(char, '_')
    # Trim leading/trailing spaces and periods
    return filename.strip('. ')