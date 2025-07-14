from playwright.sync_api import sync_playwright
import time
import random
from urllib.parse import urlparse
import re

def adjust_image_url(url):
    if not url:
        return None
    if url.startswith('//'):
        url = 'https:' + url
    if 'target.scene7.com' in url:
        # Remove query parameters and add high-res parameters
        url = re.sub(r'\?.*$', '', url)
        url += '?wid=2000&hei=2000&qlt=90'
    return url

def apply_stealth(page):
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    """)
    page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    """)
    page.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);
    """)

def scrape_product(url):
    parsed_url = urlparse(url)
    if "target.com" not in parsed_url.netloc:
        return {"title": "Invalid URL", "url": url, "images": [], "error": "Not a Target URL"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,120)}.0.{random.randint(1000,5000)}.0 Safari/537.36",
            viewport={"width": random.randint(1200, 1920), "height": random.randint(800, 1080)},
            java_script_enabled=True,
        )
        page = context.new_page()
        apply_stealth(page)

        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            time.sleep(random.uniform(2, 4))

            # Slow scroll to trigger image lazy loading
            for _ in range(random.randint(5, 10)):
                scroll_distance = random.randint(300, 800)
                page.mouse.wheel(0, scroll_distance)
                time.sleep(random.uniform(0.5, 1.2))

            images = []

            # Extract images within the product image container
            product_container_selector = 'div.sc-db7dde0c-6.dDqzNW'
            container = page.query_selector(product_container_selector)
            if container:
                img_elements = container.query_selector_all('img[src*="target.scene7.com"]')
                for img in img_elements:
                    for attr in ['src', 'data-src', 'data-zoom', 'data-original', 'data-image']:
                        src = img.get_attribute(attr)
                        if src and 'target.scene7.com' in src:
                            highres = adjust_image_url(src)
                            if highres:
                                images.append(highres)

            # Deduplicate while preserving order
            seen = set()
            unique_images = [x for x in images if not (x in seen or seen.add(x))]

            # Extract product title
            title = page.title() or "Target Product"
            if 'target' in title.lower():
                title = title.split('|')[0].strip()

            if not unique_images:
                return {
                    "title": title,
                    "url": url,
                    "images": [],
                    "error": "No product images found. Structure may have changed."
                }

            return {
                "title": title,
                "url": url,
                "images": unique_images,
                "error": None
            }

        except Exception as e:
            return {"title": "Error", "url": url, "images": [], "error": f"Error: {str(e)}"}

        finally:
            context.close()
            browser.close()
