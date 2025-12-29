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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        url = "https://trends.google.com/trends/explore?date=now%207-d&geo=AU&q=ai&hl=en-AU"
        page.goto(url)
        
        # Wait then refresh to bypass error
        time.sleep(3)
        page.reload()
        
        # Wait for content to load
        time.sleep(8)
        
        # Scroll down
        for i in range(5):
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
        
        time.sleep(2)
        
        # Take screenshot
        filepath = "/tmp/google_trends.png"
        page.screenshot(path=filepath, full_page=False)
        
        browser.close()
    
    return send_file(filepath, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)