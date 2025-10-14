# app.py
import os
import logging
import sqlite3
import time
import re
from datetime import datetime, timezone

from flask import Flask, render_template_string, jsonify, request

# Feedparser, requests, apscheduler are required in requirements.txt
import feedparser
import requests
from requests.adapters import HTTPAdapter
try:
    # urllib3 v1.26+ uses "allowed_methods"
    from urllib3.util.retry import Retry
except Exception:
    # Retry should still be available; we will handle param compatibility below
    from urllib3.util.retry import Retry  # let it raise if it truly doesn't exist

# APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# ---------- Robust zoneinfo fallback ----------
# Prefer stdlib zoneinfo (Python 3.9+). Fall back to backports.zoneinfo, then pytz.
try:
    from zoneinfo import ZoneInfo
    IST_ZONE = ZoneInfo("Asia/Kolkata")
except Exception:
    try:
        # backports.zoneinfo for older Python
        from backports.zoneinfo import ZoneInfo  # type: ignore
        IST_ZONE = ZoneInfo("Asia/Kolkata")
    except Exception:
        # Last resort: use pytz timezone with naive handling
        try:
            import pytz
            IST_ZONE = pytz.timezone("Asia/Kolkata")
        except Exception:
            IST_ZONE = None

# ---------- Configuration ----------
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
# When using gunicorn on Render, it provides $PORT; use it in your run command.
APP_PORT = int(os.getenv("APP_PORT", os.getenv("PORT", "5000")))
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
DB_PATH = os.getenv("DB_PATH", "financial_news.db")
MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "DEMO")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "please-set-a-secret-key")
# -----------------------------------

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY

NEWS_SOURCES = {
    "economic_times": {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "type": "rss",
        "region": "India",
    },
    "business_standard": {
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "type": "rss",
        "region": "India",
    },
    "reuters_business": {
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "rss",
        "region": "Global",
    },
    "marketaux": {
        "url": "https://api.marketaux.com/v1/news/all",
        "type": "api",
        "params": {
            "api_token": "DEMO",
            "symbols": "NIFTY,SENSEX,RELIANCE.BSE,INFY.BSE",
            "limit": 20,
            "language": "en",
        },
        "region": "Mixed",
    },
}

# ---------- Create requests session with retry (compatible with multiple urllib3 versions) ----------
def make_requests_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    # Build Retry object but be compatible with older urllib3 signature
    retry_kwargs = dict(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                        status_forcelist=status_forcelist)
    # newer urllib3 uses "allowed_methods"; older uses "method_whitelist"
    try:
        retry = Retry(**retry_kwargs, allowed_methods=frozenset(["GET", "POST"]))
    except TypeError:
        # fallback for older urllib3 versions
        retry = Retry(**retry_kwargs, method_whitelist=frozenset(["GET", "POST"]))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "FinancialNewsBot/1.0 (+https://example.com)"})
    return session

# ---------- Simple sentiment helper (unchanged) ----------
def analyze_sentiment(text):
    if not text:
        return "Neutral", 0.0, 50
    positive_words = ["gain", "rise", "up", "positive", "growth", "profit", "bullish", "buy", "strong", "good",
                      "surge", "rally", "boom", "increase", "advance", "recovery", "outperform", "beat",
                      "upgraded", "optimistic", "expansion", "milestone", "breakthrough", "success"]
    negative_words = ["fall", "drop", "down", "negative", "loss", "bearish", "sell", "weak", "decline", "bad",
                      "crash", "plunge", "slump", "recession", "crisis", "concern", "worry", "risk",
                      "downgrade", "disappointing", "miss", "struggle", "challenge", "volatility"]
    high_impact_words = ["rbi", "federal", "interest rate", "policy", "gdp", "inflation", "election",
                         "war", "oil", "gold", "dollar", "rupee", "sensex", "nifty", "bankruptcy"]
    text_lower = text.lower()
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    impact_multiplier = 1.0
    for w in high_impact_words:
        if w in text_lower:
            impact_multiplier = 1.5
            break
    if pos_count > neg_count:
        sentiment = "Positive"
        score = min(0.9, (pos_count - neg_count) * 0.3 * impact_multiplier)
    elif neg_count > pos_count:
        sentiment = "Negative"
        score = -min(0.9, (neg_count - pos_count) * 0.3 * impact_multiplier)
    else:
        sentiment = "Neutral"
        score = 0.0
    total = pos_count + neg_count
    confidence = min(95, max(60, total * 15 + 50))
    return sentiment, score, int(confidence)

# ---------- DB init (call at startup) ----------
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    cur.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            category TEXT,
            region TEXT,
            sentiment TEXT,
            sentiment_score REAL,
            confidence INTEGER,
            market_impact TEXT,
            impact_score REAL,
            timestamp DATETIME,
            url TEXT,
            content TEXT,
            UNIQUE(title, source)
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("DB initialized at %s", DB_PATH)

# ---------- RSS fetch ----------
def fetch_rss_news(source_name, source_config, limit_per_feed=10):
    articles = []
    try:
        feed = feedparser.parse(source_config["url"])
        for entry in feed.entries[:limit_per_feed]:
            title = (entry.get("title") or "").strip()
            summary = entry.get("summary", entry.get("description", "") or "")
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = summary[:300] + "..." if len(summary) > 300 else summary
            sentiment, score, confidence = analyze_sentiment(title + " " + summary)
            impact_score = abs(score) * 10
            market_impact = "High" if impact_score >= 7 else ("Medium" if impact_score >= 4 else "Low")
            category = "Market News"
            tl = title.lower()
            if any(w in tl for w in ["rbi", "interest", "policy", "inflation"]):
                category = "Monetary Policy"
            elif any(w in tl for w in ["ipo", "listing", "debut"]):
                category = "IPO"
            elif any(w in tl for w in ["oil", "gold", "commodity"]):
                category = "Commodities"
            elif any(w in tl for w in ["bank", "financial"]):
                category = "Banking"
            ts = datetime.now(IST_ZONE).strftime("%Y-%m-%d %H:%M:%S %z") if IST_ZONE else datetime.utcnow().isoformat()
            articles.append({
                "title": title, "summary": summary, "source": source_name.replace("_", " ").title(),
                "category": category, "region": source_config.get("region", "Unknown"),
                "sentiment": sentiment, "sentiment_score": score, "confidence": confidence,
                "market_impact": market_impact, "impact_score": round(impact_score, 1),
                "timestamp": ts, "url": entry.get("link", ""), "content": summary
            })
    except Exception as e:
        logging.exception("RSS fetch error for %s: %s", source_name, e)
    return articles

# ---------- API fetch (MarketAux) ----------
def fetch_api_news(session=None):
    articles = []
    try:
        session = session or make_requests_session()
        conf = NEWS_SOURCES.get("marketaux", {})
        params = dict(conf.get("params", {}))
        params["api_token"] = MARKETAUX_API_TOKEN or params.get("api_token", "DEMO")
        params["limit"] = int(params.get("limit", 20))
        resp = session.get(conf["url"], params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                for item in data["data"][: params["limit"]]:
                    title = (item.get("title") or "").strip()
                    desc = item.get("description") or ""
                    if not title:
                        continue
                    sentiment, score, confidence = analyze_sentiment(title + " " + desc)
                    impact_score = abs(score) * 10
                    market_impact = "High" if impact_score >= 7 else ("Medium" if impact_score >= 4 else "Low")
                    region = "India" if any(w in title.lower() for w in ["india", "indian", "mumbai", "nse", "bse", "rupee", "rbi"]) else "Global"
                    ts = datetime.now(IST_ZONE).strftime("%Y-%m-%d %H:%M:%S %z") if IST_ZONE else datetime.utcnow().isoformat()
                    articles.append({
                        "title": title,
                        "summary": desc[:300] + "..." if len(desc) > 300 else desc,
                        "source": item.get("source", "MarketAux"),
                        "category": "Market News",
                        "region": region,
                        "sentiment": sentiment,
                        "sentiment_score": score,
                        "confidence": confidence,
                        "market_impact": market_impact,
                        "impact_score": round(impact_score, 1),
                        "timestamp": ts,
                        "url": item.get("url", ""),
                        "content": desc,
                    })
            else:
                logging.warning("MarketAux returned unexpected payload")
        else:
            logging.error("MarketAux request failed: %s %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logging.exception("Error fetching MarketAux news: %s", e)
    return articles

# ---------- Combined fetch & save ----------
def save_articles_to_db(articles):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    saved = 0
    for art in articles:
        try:
            cur.execute('''
                INSERT OR IGNORE INTO news_articles
                (title, summary, source, category, region, sentiment, sentiment_score,
                confidence, market_impact, impact_score, timestamp, url, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (art["title"], art["summary"], art["source"], art["category"], art["region"],
                  art["sentiment"], art["sentiment_score"], art["confidence"],
                  art["market_impact"], art["impact_score"], art["timestamp"],
                  art["url"], art["content"]))
            if cur.rowcount > 0:
                saved += 1
        except Exception:
            logging.exception("Failed to save article: %s", art.get("title"))
    conn.commit()
    conn.close()
    logging.info("Saved %d new articles", saved)

def fetch_all_news():
    logging.info("Starting news fetch...")
    all_articles = []
    session = make_requests_session()
    for name, conf in NEWS_SOURCES.items():
        if conf.get("type") == "rss":
            all_articles.extend(fetch_rss_news(name, conf))
            time.sleep(0.5)
    all_articles.extend(fetch_api_news(session=session))
    if all_articles:
        save_articles_to_db(all_articles)
    else:
        logging.warning("No articles fetched")
    return all_articles

def get_articles_from_db(limit=50, region=None, category=None):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    query = "SELECT * FROM news_articles WHERE 1=1"
    params = []
    if region and region != "all":
        query += " AND region = ?"
        params.append(region)
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    cols = ['id', 'title', 'summary', 'source', 'category', 'region', 'sentiment',
            'sentiment_score', 'confidence', 'market_impact', 'impact_score',
            'timestamp', 'url', 'content']
    return [dict(zip(cols, r)) for r in rows]

# HTML template truncated for brevity in this message but same as earlier; put your full HTML_TEMPLATE here.
HTML_TEMPLATE = """(PUT YOUR FULL TEMPLATE HERE - same template you used earlier)"""

# ---------- Routes ----------
@app.route("/")
def index():
    articles = get_articles_from_db(limit=20)
    if not articles:
        fetch_all_news()
        articles = get_articles_from_db(limit=20)
    total_articles = len(articles)
    positive_news = len([a for a in articles if a['sentiment'] == 'Positive'])
    negative_news = len([a for a in articles if a['sentiment'] == 'Negative'])
    avg_confidence = int(sum(a['confidence'] for a in articles) / max(1, total_articles))
    last_updated = datetime.now(IST_ZONE).strftime('%Y-%m-%d %H:%M') if IST_ZONE else datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    return render_template_string(HTML_TEMPLATE,
                                  articles=articles,
                                  total_articles=total_articles,
                                  positive_news=positive_news,
                                  negative_news=negative_news,
                                  avg_confidence=avg_confidence,
                                  last_updated=last_updated)

@app.route("/api/news")
def api_news():
    region = request.args.get("region")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 50))
    articles = get_articles_from_db(limit=limit, region=region, category=category)
    return jsonify(articles)

@app.route("/manual-fetch")
def manual_fetch():
    try:
        arts = fetch_all_news()
        return jsonify({"message": f"Fetched {len(arts)} articles", "status": "success"})
    except Exception as e:
        logging.exception("Manual fetch failed")
        return jsonify({"error": str(e), "status": "failed"}), 500

# ---------- Startup (only when executed directly) ----------
def start_scheduler():
    try:
        scheduler = BackgroundScheduler(timezone=IST_ZONE if IST_ZONE else None)
        scheduler.add_job(fetch_all_news, "cron", hour=8, minute=0, id="daily_news_fetch")
        scheduler.add_job(fetch_all_news, "cron", hour="9-18/2", minute=0, id="market_hours_fetch")
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        logging.info("Scheduler started")
    except Exception:
        logging.exception("Failed to start scheduler")

if __name__ == "__main__":
    init_db()
    start_scheduler()
    # initial fetch
    try:
        fetch_all_news()
    except Exception:
        logging.exception("Initial fetch failed")
    # Use app.run for local testing only
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)
