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
                '--disable-dev-shm-usage',  # Important for Docker/limited memory
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--single-process',  # Reduces memory usage
                '--no-zygote',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}  # Smaller viewport = less memory
        )
        page = context.new_page()
        
        url = "https://trends.google.com/trends/explore?date=now%207-d&geo=AU&q=ai&hl=en-AU"
        page.goto(url, timeout=30000)
        
        # Wait then refresh to bypass error
        time.sleep(2)
        page.reload(timeout=30000)
        
        # Wait for content to load
        time.sleep(5)
        
        # Scroll down
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.3)
        
        time.sleep(1)
        
        # Take screenshot
        filepath = "/tmp/google_trends.png"
        page.screenshot(path=filepath, full_page=False)
        
        browser.close()
    
    return send_file(filepath, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)