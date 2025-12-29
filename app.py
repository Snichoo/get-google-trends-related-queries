from flask import Flask, send_file, jsonify
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
import os

app = Flask(__name__)

# ===========================================
# EASY CONFIGURATION - CHANGE THESE VALUES
# ===========================================
KEYWORD = "ai"           # Search term
COUNTRY = "AU"           # Country code (AU, US, GB, etc.)
LANGUAGE = "en-AU"       # Language code (en-AU, en-US, en-GB, etc.)
DAYS_RANGE = 4           # Number of days to look back
TIMEZONE = "Australia/Sydney"  # Timezone (Australia/Sydney, Australia/Melbourne, etc.)
# ===========================================


def build_trends_url():
    """Build Google Trends URL with dynamic date range."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_RANGE - 1)
    
    date_range = f"{start_date.strftime('%Y-%m-%d')}%20{end_date.strftime('%Y-%m-%d')}"
    
    url = f"https://trends.google.com/trends/explore?date={date_range}&geo={COUNTRY}&q={KEYWORD}&hl={LANGUAGE}"
    return url


@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoint": "/screenshot",
        "config": {
            "keyword": KEYWORD,
            "country": COUNTRY,
            "language": LANGUAGE,
            "days_range": DAYS_RANGE
        }
    })


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
        
        url = build_trends_url()
        
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