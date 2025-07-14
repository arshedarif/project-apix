import datetime
from flask import Flask, jsonify, render_template, request, send_file
import io, zipfile, requests, os
from urllib.parse import urlparse
from retailer_scrapers import amazon, wayfair, nordstrom, jcrew, quince, walmart, lululemon, zappos, madewell, target

app = Flask(__name__)

def identify_retailer(url):
    domain = urlparse(url).netloc.lower()
    if "amazon.com" in domain:
        return "amazon"
    elif "wayfair.com" in domain:
        return "wayfair"
    elif "nordstrom.com" in domain or "nordstromrack.com" in domain:
        return "nordstrom"
    elif "jcrew.com" in domain:
        return "jcrew"
    elif "quince.com" in domain:
        return "quince"
    elif "walmart.com" in domain:
        return "walmart"
    elif "shop.lululemon.com" in domain:
        return "lululemon"
    elif "zappos.com" in domain:
        return "zappos"
    elif "madewell.com" in domain:
        return "madewell"
    elif "target.com" in domain:
        return "target"
    else:
        return "invalid"

def seo_slug(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        urls = [url.strip() for url in urls if url.strip()]
        for url in urls:
            retailer = identify_retailer(url)
            if retailer == "invalid":
                results.append({
                    "url": url,
                    "title": "Invalid URL",
                    "images": [],
                    "error": "Only supported retailers are allowed"
                })
                continue
            try:
                scraper = getattr(eval(retailer), "scrape_product")
                data = scraper(url)
                results.append(data)
            except Exception as e:
                results.append({
                    "url": url,
                    "title": "Error",
                    "images": [],
                    "error": str(e)
                })
    return render_template("index.html", results=results)

@app.route('/download', methods=['POST'])
def download_images():
    try:
        data = request.get_json()
        if not data or 'images' not in data:
            return jsonify({"error": "No images selected"}), 400

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, img in enumerate(data['images']):
                try:
                    response = requests.get(img['url'], timeout=10)
                    response.raise_for_status()
                    title_slug = seo_slug(img.get('title', 'image'))
                    filename = f"{title_slug}-{idx + 1}.jpg"
                    zipf.writestr(filename, response.content)
                except Exception as e:
                    print(f"Skipping {img['url']} - {e}")

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'Task_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.zip'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
