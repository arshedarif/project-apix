from playwright.sync_api import sync_playwright
import re, time

def get_full_resolution_url(url):
    if url.startswith('//'):
        url = 'https:' + url
    return re.sub(r'\?.*$', '', url) + "?wid=2000&hei=2000&qlt=90"

def extract_images(page):
    image_urls = set()
    container = page.query_selector('#c-product__photos')
    if container:
        for img in container.query_selector_all('img'):
            for attr in ['src', 'data-src', 'data-zoom', 'data-original']:
                src = img.get_attribute(attr)
                if src and ('jcrew.com' in src or 'jcrewfactory.com' in src):
                    image_urls.add(get_full_resolution_url(src))
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
            title = title_elem.inner_text().strip() if title_elem else "J.Crew Product"

            context.close()
            browser.close()

            return {"title": title, "url": url, "images": images, "error": None}
    except Exception as e:
        return {"title": "Error", "url": url, "images": [], "error": str(e)}
