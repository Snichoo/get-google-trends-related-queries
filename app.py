# app.py

from flask import Flask, send_file, jsonify
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import threading

app = Flask(__name__)

# ===========================================
# EASY CONFIGURATION - CHANGE THESE VALUES
# ===========================================
KEYWORD = "ai"
COUNTRY = "AU"
LANGUAGE = "en-AU"
DAYS_RANGE = 4
TIMEZONE = "Australia/Sydney"
REFRESH_INTERVAL_MINUTES = 30  # How often to refresh the screenshot
# ===========================================

SCREENSHOT_PATH = "/tmp/google_trends.png"
last_updated = None
update_lock = threading.Lock()


def build_trends_url():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_RANGE - 1)
    date_range = f"{start_date.strftime('%Y-%m-%d')}%20{end_date.strftime('%Y-%m-%d')}"
    return f"https://trends.google.com/trends/explore?date={date_range}&geo={COUNTRY}&q={KEYWORD}&hl={LANGUAGE}"


def generate_screenshot():
    """Generate screenshot in background."""
    global last_updated
    
    with update_lock:
        try:
            print(f"[{datetime.now()}] Generating screenshot...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-extensions',
                        '--single-process',
                        '--no-zygote',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                url = build_trends_url()
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                import time
                time.sleep(2)
                page.reload(wait_until='networkidle', timeout=60000)
                
                try:
                    page.wait_for_selector('fe-line-chart', timeout=30000)
                except:
                    pass
                
                time.sleep(5)
                
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 400)")
                    time.sleep(0.5)
                
                time.sleep(3)
                page.screenshot(path=SCREENSHOT_PATH, full_page=False)
                browser.close()
            
            last_updated = datetime.now()
            print(f"[{last_updated}] Screenshot generated successfully!")
            
        except Exception as e:
            print(f"Error generating screenshot: {e}")


@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoint": "/screenshot",
        "last_updated": last_updated.isoformat() if last_updated else None,
        "config": {
            "keyword": KEYWORD,
            "country": COUNTRY,
            "refresh_interval_minutes": REFRESH_INTERVAL_MINUTES
        }
    })


@app.route('/screenshot')
def get_screenshot():
    """Instantly serve the cached screenshot."""
    if os.path.exists(SCREENSHOT_PATH):
        return send_file(SCREENSHOT_PATH, mimetype='image/png')
    else:
        return jsonify({"error": "Screenshot not ready yet. Try again in a minute."}), 503


# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(generate_screenshot, 'interval', minutes=REFRESH_INTERVAL_MINUTES)
scheduler.start()

# Generate initial screenshot on startup (in background thread)
threading.Thread(target=generate_screenshot, daemon=True).start()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
