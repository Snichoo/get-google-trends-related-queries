from flask import Flask, send_file, jsonify
from playwright.sync_api import sync_playwright
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "endpoint": "/screenshot"})

@app.route('/screenshot')
def take_screenshot():
    with sync_playwright() as p:
        # Memory-optimized browser launch
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--single-process',
                '--no-zygote',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        
        url = "https://trends.google.com/trends/explore?date=now%207-d&geo=AU&q=ai&hl=en-AU"
        
        # First load
        page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Refresh to bypass any initial errors
        time.sleep(2)
        page.reload(wait_until='networkidle', timeout=60000)
        
        # Wait for the trend graph to actually appear
        try:
            page.wait_for_selector('fe-line-chart', timeout=30000)
        except:
            pass  # Continue even if not found
        
        # Extra wait for charts to render
        time.sleep(5)
        
        # Scroll down to load more content
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        # Final wait for any lazy-loaded content
        time.sleep(3)
        
        # Take screenshot
        filepath = "/tmp/google_trends.png"
        page.screenshot(path=filepath, full_page=False)
        
        browser.close()
    
    return send_file(filepath, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)