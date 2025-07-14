import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, parse_qs, urlunparse

def normalize_amazon_image_url(url):
    """Normalize Amazon image URL by removing variable parameters and standardizing format"""
    if not url.startswith('http'):
        url = 'https:' + url
    
    # Parse URL components
    parsed = urlparse(url)
    
    # Remove query parameters (they often cause duplicates)
    clean_url = urlunparse(parsed._replace(query=''))
    
    # Standardize the resolution part of the URL
    clean_url = re.sub(
        r'(_AC_UL\d+_|_AC_SX\d+_|_AC_SY\d+_|_AC_SL\d+_|_AC_UX\d+_|_AC_UY\d+_)',
        '_AC_',
        clean_url
    )
    
    # Remove any remaining size parameters
    clean_url = re.sub(
        r'(_SX\d+_|_SY\d+_|_SL\d+_|_UL\d+_|_UX\d+_|_UY\d+_)',
        '_',
        clean_url
    )
    
    # Remove duplicate underscores that might have been created
    clean_url = clean_url.replace('__', '_')
    
    return clean_url

def extract_amazon_images(soup):
    image_urls = set()
    seen_normalized = set()

      # Method 4: Original fallback (ImageBlockATF)
    if not image_urls:
        for script in soup.find_all('script'):
            if script.string and 'ImageBlockATF' in script.string:
                matches = re.findall(r'"hiRes":"(https:[^"]+)"', script.string)
                for match in matches:
                    url = match.replace('\\u002F', '/')
                    normalized = normalize_amazon_image_url(url)
                    if normalized not in seen_normalized:
                        seen_normalized.add(normalized)
                        high_res = re.sub(r'(_AC_.+?_|_SX\d+_|_SY\d+_|_SL\d+_)', '_AC_', url)
                        image_urls.add(high_res)
                        continue

    # Method 1: Extract from 'imageGalleryData' (New Amazon Layout)
    for script in soup.find_all('script', type='application/json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'imageGalleryData' in data:
                for img in data['imageGalleryData']:
                    if 'mainUrl' in img:
                        url = img['mainUrl']
                        normalized = normalize_amazon_image_url(url)
                        if normalized not in seen_normalized:
                            seen_normalized.add(normalized)
                            image_urls.add(url.replace('_SL75_', '_SL1500_'))
        except (json.JSONDecodeError, AttributeError):
            break

    # Convert to list and ensure proper URL format
    cleaned_urls = []
    for url in image_urls:
        if not url.startswith('http'):
            url = 'https:' + url
        cleaned_urls.append(url)

    return cleaned_urls[:8]  # Return up to 8 unique images

def scrape_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.amazon.com/',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if 'captcha' in response.text.lower():
            raise Exception("Amazon is showing CAPTCHA. Try again later or change your IP.")
            
        soup = BeautifulSoup(response.text, 'lxml')

        title_elem = soup.select_one('#productTitle') or soup.find('title')
        title = title_elem.text.strip() if title_elem else "Amazon Product"

        images = extract_amazon_images(soup)

        return {
            "title": title,
            "url": url,
            "images": images,
            "error": None
        }
    except Exception as e:
        return {
            "title": "Error",
            "url": url,
            "images": [],
            "error": str(e)
        }