from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import re
import time
import json
import random
import logging

logging.basicConfig(level=logging.INFO)

def get_highres_url(img_url):
    """Convert any Lululemon image URL to high-res (2000px) version"""
    if not img_url or 'images.lululemon.com' not in img_url:
        return None
    if img_url.startswith('//'):
        img_url = f'https:{img_url}'
    try:
        parsed = urlparse(img_url)
        query = parse_qs(parsed.query)
        query['wid'] = ['2000']
        query['qlt'] = ['90']
        for param in ['fit', 'op_sharpen', 'op_usm', 'hei']:
            query.pop(param, None)
        new_query = urlencode(query, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception as e:
        logging.warning(f"URL processing failed: {str(e)}")
        return None

def scrape_product(url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,120)}.0.{random.randint(1000,5000)}.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale='en-US'
        )
        page = context.new_page()
        try:
            logging.info(f"Loading Lululemon URL: {url}")
            page.goto(url, timeout=90000, wait_until='networkidle')
            time.sleep(random.uniform(2, 4))

            # Attempt JavaScript state extraction
            images = []
            try:
                product_data = page.evaluate("""() => {
                    return window.__INITIAL_STATE__?.products?.productDetails || 
                           window.productData || 
                           window.__APOLLO_STATE__;
                }""")
                if product_data:
                    if isinstance(product_data, str):
                        product_data = json.loads(product_data)
                    def find_images(obj):
                        urls = []
                        if isinstance(obj, dict):
                            for v in obj.values():
                                if isinstance(v, str) and 'images.lululemon.com' in v:
                                    urls.append(v)
                                elif isinstance(v, (dict, list)):
                                    urls.extend(find_images(v))
                        elif isinstance(obj, list):
                            for item in obj:
                                urls.extend(find_images(item))
                        return urls
                    images = find_images(product_data)
            except Exception as e:
                logging.warning(f"JS state extraction failed: {e}")

            # Fallback to JSON-LD extraction
            if not images:
                try:
                    script = page.query_selector('script[type="application/ld+json"]')
                    if script:
                        data = json.loads(script.inner_text())
                        if isinstance(data, list):
                            data = data[0]
                        if 'image' in data:
                            if isinstance(data['image'], str):
                                images.append(data['image'])
                            elif isinstance(data['image'], list):
                                images.extend(data['image'])
                except Exception as e:
                    logging.warning(f"JSON-LD extraction failed: {e}")

            # Fallback to direct <img> extraction
            if not images:
                img_elements = page.query_selector_all('img[src*="images.lululemon.com"]')
                for img in img_elements:
                    for attr in ['src', 'data-src', 'data-zoom']:
                        src = img.get_attribute(attr)
                        if src and 'images.lululemon.com' in src:
                            images.append(src)

            highres_images = []
            for img_url in images:
                highres = get_highres_url(img_url)
                if highres:
                    highres_images.append(highres)

            # Deduplicate while preserving order
            seen = set()
            unique_images = [x for x in highres_images if not (x in seen or seen.add(x))]

            # Extract title
            title = page.title().strip()
            if 'lululemon' in title.lower():
                title = title.split('|')[0].strip()

            if not unique_images:
                return {
                    'title': title,
                    'url': url,
                    'images': [],
                    'error': 'No images found or page structure may have changed'
                }

            return {
                'title': title,
                'url': url,
                'images': unique_images,
                'error': None
            }

        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            return {
                'title': None,
                'url': url,
                'images': [],
                'error': str(e)
            }
        finally:
            context.close()
            browser.close()
