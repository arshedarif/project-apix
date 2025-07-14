from playwright.sync_api import sync_playwright
import re
import time
import random
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)

def get_full_resolution_url(image_url):
    if not image_url or 'n.nordstrommedia.com' not in image_url:
        return None
    base_url = re.sub(r'/size/\d+x\d+', '', image_url.split('?')[0])
    return base_url

def extract_gallery_images(page):
    image_urls = set()
    gallery = page.query_selector('div.PegOI.jnQqe')
    if gallery:
        img_elements = gallery.query_selector_all('img[src*="nordstrommedia.com"]')
        for img in img_elements:
            for attr in ['src', 'data-src', 'data-zoom', 'data-original']:
                src = img.get_attribute(attr)
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    full_res_url = get_full_resolution_url(src)
                    if full_res_url:
                        image_urls.add(full_res_url)
    return list(image_urls)

def extract_product_info(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)  # Use headless=True for Docker, False for testing
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       f"Chrome/{random.randint(100, 122)}.0.{random.randint(1000, 9999)}.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        # Manual stealth: navigator.webdriver undefined, languages, plugins, permissions
        context.add_init_script("""
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
        """)

        page = context.new_page()
        try:
            logging.info(f"Loading URL: {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 5))

            # Scroll slowly to load lazy images
            for _ in range(random.randint(5, 10)):
                page.mouse.wheel(0, random.randint(200, 500))
                time.sleep(random.uniform(1.0, 2.5))

            gallery_images = extract_gallery_images(page)

            # Extract product title
            title = "Title not found"
            for selector in [
                'h1[itemprop="name"]',
                'h1.pip-header-section__title',
                'h1.product-title',
                'h1.heading',
                'h1'
            ]:
                element = page.query_selector(selector)
                if element:
                    title = element.inner_text().strip()
                    break

            # Check for unusual activity block page
            body_text = page.inner_text('body')
            if "We've noticed some unusual activity" in body_text:
                logging.warning("Bot detection triggered on Nordstrom.")
                return {
                    'title': 'Blocked by Nordstrom',
                    'url': url,
                    'images': [],
                    'error': 'Blocked by Nordstrom - unusual activity detected'
                }

            return {
                'title': title,
                'url': url,
                'images': gallery_images,
                'error': None
            }

        except Exception as e:
            logging.error(f"Error processing {url}: {str(e)}")
            return {
                'title': None,
                'url': url,
                'images': [],
                'error': str(e)
            }
        finally:
            context.close()
            browser.close()

def scrape_product(url):
    return extract_product_info(url)
