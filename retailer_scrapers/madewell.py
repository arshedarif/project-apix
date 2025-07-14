from playwright.sync_api import sync_playwright
import re, time

def get_full_resolution_url(url):
    if url.startswith('//'):
        url = 'https:' + url
    # Remove any existing query parameters and add high quality parameters
    return re.sub(r'\?.*$', '', url) + "?wid=1400&hei=1779&qlt=90"

def extract_images(page):
    image_urls = set()
    # Find the image gallery container
    container = page.query_selector('div.ImageGallery_pdpImagesGrid__hHV7D')
    if container:
        # Find all img elements within the container
        for img in container.query_selector_all('img'):
            for attr in ['src', 'data-src', 'data-zoom', 'data-original', 'data-main-img']:
                src = img.get_attribute(attr)
                if src and 'www.madewell.com' in src:
                    image_urls.add(get_full_resolution_url(src))
    return list(image_urls)

def scrape_product(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Scroll to load images
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)
            
            images = extract_images(page)
            
            # Try to get product title
            title_elem = page.query_selector('h1.product-title') or page.query_selector('h1')
            title = title_elem.inner_text().strip() if title_elem else "Madewell Product"

            context.close()
            browser.close()

            return {"title": title, "url": url, "images": images, "error": None}
    except Exception as e:
        return {"title": "Error", "url": url, "images": [], "error": str(e)}