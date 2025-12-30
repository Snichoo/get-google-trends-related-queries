# app.py

from flask import Flask, jsonify
from pytrends.request import TrendReq
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import threading

app = Flask(__name__)

# ===========================================
# CONFIGURATION
# ===========================================
KEYWORD = "ai"
COUNTRY = "AU"
DAYS_RANGE = 4
REFRESH_INTERVAL_MINUTES = 30
# ===========================================

cached_data = None
last_updated = None
update_lock = threading.Lock()


def fetch_related_queries():
    """Fetch related queries from Google Trends API."""
    global cached_data, last_updated
    
    with update_lock:
        try:
            print(f"[{datetime.now()}] Fetching related queries...")
            
            pytrends = TrendReq(hl='en-AU', tz=660)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=DAYS_RANGE)
            timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
            
            pytrends.build_payload([KEYWORD], cat=0, timeframe=timeframe, geo=COUNTRY)
            
            related = pytrends.related_queries()
            
            result = {
                "keyword": KEYWORD,
                "country": COUNTRY,
                "timeframe": timeframe,
                "top": [],
                "rising": []
            }
            
            # Extract top queries
            if related[KEYWORD]['top'] is not None:
                result["top"] = related[KEYWORD]['top'].to_dict('records')
            
            # Extract rising queries
            if related[KEYWORD]['rising'] is not None:
                result["rising"] = related[KEYWORD]['rising'].to_dict('records')
            
            cached_data = result
            last_updated = datetime.now()
            print(f"[{last_updated}] Related queries fetched successfully!")
            
        except Exception as e:
            print(f"Error fetching data: {e}")


@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoint": "/related-queries",
        "last_updated": last_updated.isoformat() if last_updated else None
    })


@app.route('/related-queries')
def get_related_queries():
    if cached_data:
        return jsonify({
            "last_updated": last_updated.isoformat(),
            "data": cached_data
        })
    else:
        return jsonify({"error": "Data not ready yet. Try again in a minute."}), 503


# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_related_queries, 'interval', minutes=REFRESH_INTERVAL_MINUTES)
scheduler.start()

# Fetch on startup
threading.Thread(target=fetch_related_queries, daemon=True).start()


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)