from playwright.sync_api import sync_playwright
import re, time

def get_highest_resolution_url(url):
    if url.startswith('//'):
        url = 'https:' + url
    
    # Option 1: Replace with higher resolution
    url = url.replace('SR920,736', 'SR2000,2000')
    
    # Option 2: Or completely remove the size parameter
    # url = re.sub(r'SR\d+,\d+', '', url)
    
    # Remove other Amazon modifiers
    url = re.sub(r'\._([A-Za-z0-9]+_)', '.', url)
    url = re.sub(r'\.jpg_.*$', '.jpg', url)
    url = re.sub(r'\?.*$', '', url)
    
    return url

def extract_images(page):
    image_urls = set()
    container = page.query_selector('div.Te-z')
    container = page.query_selector('div.Pf-z')
    if container:
        for img in container.query_selector_all('img'):
            for attr in ['src', 'data-src', 'data-zoom', 'data-original']:
                src = img.get_attribute(attr)
                if src and 'm.media-amazon.com' in src:
                    image_urls.add(get_highest_resolution_url(src))
    return list(image_urls)

def scrape_product(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)
            images = extract_images(page)
            title_elem = page.query_selector('h1') or page.query_selector('title')
            title = title_elem.inner_text().strip() if title_elem else "Zappos Product"

            context.close()
            browser.close()

            return {"title": title, "url": url, "images": images, "error": None}
    except Exception as e:
        return {"title": "Error", "url": url, "images": [], "error": str(e)}