import re

def generate_seo_filename(title: str) -> str:
    title = title.lower()
    title = re.sub(r'[^a-z\s]', '', title)
    title = re.sub(r'\s+', '-', title)
    title = re.sub(r'-+', '-', title)
    title = title.strip('-')
    return title
