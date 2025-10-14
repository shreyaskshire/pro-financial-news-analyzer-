from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import requests
import logging
import atexit
import json
import os
import feedparser
import time
import re
import sys

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'financial-news-secret-key')

# Test imports
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    logger.info("APScheduler imported successfully")
except Exception as e:
    logger.error(f"Failed to import APScheduler: {e}")
    raise

# Get database path - use /tmp for Render ephemeral storage
DB_PATH = os.environ.get('DATABASE_PATH', '/tmp/financial_news.db')
logger.info(f"Database path set to: {DB_PATH}")

# NEWS SOURCES - Real RSS feeds and APIs
NEWS_SOURCES = {
    'economic_times': {
        'url': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
        'type': 'rss',
        'region': 'India'
    },
    'business_standard': {
        'url': 'https://www.business-standard.com/rss/markets-106.rss',
        'type': 'rss',
        'region': 'India'
    },
    'reuters_business': {
        'url': 'https://feeds.reuters.com/reuters/businessNews',
        'type': 'rss',
        'region': 'Global'
    },
    'marketaux': {
        'url': 'https://api.marketaux.com/v1/news/all',
        'type': 'api',
        'params': {
            'api_token': os.environ.get('MARKETAUX_API_KEY', 'DEMO'),
            'symbols': 'NIFTY,SENSEX,RELIANCE.BSE,INFY.BSE',
            'limit': 20,
            'language': 'en'
        },
        'region': 'Mixed'
    }
}

def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
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
        logger.info(f"Database initialized at {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

def analyze_sentiment(text):
    """Advanced sentiment analysis for financial news"""
    if not text:
        return 'Neutral', 0.0, 50
    
    # Financial positive words
    positive_words = [
        'gain', 'rise', 'up', 'positive', 'growth', 'profit', 'bullish', 'buy', 'strong', 'good',
        'surge', 'rally', 'boom', 'increase', 'advance', 'recovery', 'outperform', 'beat',
        'upgraded', 'optimistic', 'expansion', 'milestone', 'breakthrough', 'success'
    ]
    
    # Financial negative words
    negative_words = [
        'fall', 'drop', 'down', 'negative', 'loss', 'bearish', 'sell', 'weak', 'decline', 'bad',
        'crash', 'plunge', 'slump', 'recession', 'crisis', 'concern', 'worry', 'risk',
        'downgrade', 'disappointing', 'miss', 'struggle', 'challenge', 'volatility'
    ]
    
    # Market impact words (multiply score)
    high_impact_words = [
        'rbi', 'federal', 'interest rate', 'policy', 'gdp', 'inflation', 'election',
        'war', 'oil', 'gold', 'dollar', 'rupee', 'sensex', 'nifty', 'bankruptcy'
    ]
    
    text_lower = text.lower()
    
    # Count sentiment words
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    # Check for high impact
    impact_multiplier = 1.0
    for impact_word in high_impact_words:
        if impact_word in text_lower:
            impact_multiplier = 1.5
            break
    
    # Calculate sentiment
    if pos_count > neg_count:
        sentiment = 'Positive'
        score = min(0.9, (pos_count - neg_count) * 0.3 * impact_multiplier)
    elif neg_count > pos_count:
        sentiment = 'Negative'
        score = -min(0.9, (neg_count - pos_count) * 0.3 * impact_multiplier)
    else:
        sentiment = 'Neutral'
        score = 0.0
    
    # Calculate confidence
    total_sentiment_words = pos_count + neg_count
    confidence = min(95, max(60, total_sentiment_words * 15 + 50))
    
    return sentiment, score, int(confidence)

def fetch_rss_news(source_name, source_config):
    """Fetch news from RSS feeds"""
    articles = []
    
    try:
        feed = feedparser.parse(source_config['url'])
        
        for entry in feed.entries[:10]:  # Limit to 10 articles per source
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', ''))
            
            # Clean HTML tags from summary
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:300] + '...' if len(summary) > 300 else summary
            
            # Analyze sentiment
            sentiment, score, confidence = analyze_sentiment(title + ' ' + summary)
            
            # Calculate market impact
            impact_score = abs(score) * 10
            if impact_score >= 7:
                market_impact = 'High'
            elif impact_score >= 4:
                market_impact = 'Medium'
            else:
                market_impact = 'Low'
            
            # Determine category
            category = 'Market News'
            title_lower = title.lower()
            if any(word in title_lower for word in ['rbi', 'interest', 'policy', 'inflation']):
                category = 'Monetary Policy'
            elif any(word in title_lower for word in ['ipo', 'listing', 'debut']):
                category = 'IPO'
            elif any(word in title_lower for word in ['oil', 'gold', 'commodity']):
                category = 'Commodities'
            elif any(word in title_lower for word in ['bank', 'financial']):
                category = 'Banking'
            
            article = {
                'title': title,
                'summary': summary,
                'source': source_name.replace('_', ' ').title(),
                'category': category,
                'region': source_config['region'],
                'sentiment': sentiment,
                'sentiment_score': score,
                'confidence': confidence,
                'market_impact': market_impact,
                'impact_score': round(impact_score, 1),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': entry.get('link', ''),
                'content': summary
            }
            
            articles.append(article)
            
    except Exception as e:
        logger.error(f"Error fetching RSS from {source_name}: {e}")
    
    return articles

def fetch_api_news():
    """Fetch news from MarketAux API"""
    articles = []
    
    try:
        source_config = NEWS_SOURCES['marketaux']
        response = requests.get(source_config['url'], params=source_config['params'], timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                for item in data['data'][:10]:
                    title = item.get('title', '').strip()
                    description = item.get('description', '')
                    
                    if not title:
                        continue
                    
                    # Analyze sentiment
                    sentiment, score, confidence = analyze_sentiment(title + ' ' + description)
                    
                    # Calculate market impact
                    impact_score = abs(score) * 10
                    if impact_score >= 7:
                        market_impact = 'High'
                    elif impact_score >= 4:
                        market_impact = 'Medium'
                    else:
                        market_impact = 'Low'
                    
                    # Determine region
                    region = 'India' if any(word in title.lower() for word in 
                                          ['india', 'indian', 'mumbai', 'nse', 'bse', 'rupee', 'rbi']) else 'Global'
                    
                    article = {
                        'title': title,
                        'summary': description[:300] + '...' if len(description) > 300 else description,
                        'source': item.get('source', 'MarketAux'),
                        'category': 'Market News',
                        'region': region,
                        'sentiment': sentiment,
                        'sentiment_score': score,
                        'confidence': confidence,
                        'market_impact': market_impact,
                        'impact_score': round(impact_score, 1),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'url': item.get('url', ''),
                        'content': description
                    }
                    
                    articles.append(article)
                    
    except Exception as e:
        logger.error(f"Error fetching API news: {e}")
    
    return articles

def fetch_all_news():
    """Fetch news from all sources and analyze"""
    logger.info("Starting comprehensive news fetch...")
    all_articles = []
    
    # Fetch from RSS sources
    for source_name, source_config in NEWS_SOURCES.items():
        if source_config['type'] == 'rss':
            try:
                articles = fetch_rss_news(source_name, source_config)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source_name}")
                time.sleep(1)  # Be nice to servers
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
    
    # Fetch from API sources
    try:
        api_articles = fetch_api_news()
        all_articles.extend(api_articles)
        logger.info(f"Fetched {len(api_articles)} articles from API")
    except Exception as e:
        logger.error(f"Failed to fetch from API: {e}")
    
    # Save to database
    if all_articles:
        save_articles_to_db(all_articles)
        logger.info(f"Successfully processed {len(all_articles)} total articles")
    else:
        logger.warning("No articles fetched from any source")
    
    return all_articles

def save_articles_to_db(articles):
    """Save articles to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news_articles 
                    (title, summary, source, category, region, sentiment, sentiment_score, 
                     confidence, market_impact, impact_score, timestamp, url, content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'], article['summary'], article['source'], 
                    article['category'], article['region'], article['sentiment'],
                    article['sentiment_score'], article['confidence'], 
                    article['market_impact'], article['impact_score'], 
                    article['timestamp'], article['url'], article['content']
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                logging.error(f"Error saving article: {e}")
        
        conn.commit()
        conn.close()
        logging.info(f"Saved {saved_count} new articles to database")
    except Exception as e:
        logging.error(f"Database save error: {e}")

def get_articles_from_db(limit=50, region=None, category=None):
    """Get articles from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM news_articles WHERE 1=1"
        params = []
        
        if region and region != 'all':
            query += " AND region = ?"
            params.append(region)
        
        if category and category != 'all':
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'title', 'summary', 'source', 'category', 'region', 
                   'sentiment', 'sentiment_score', 'confidence', 'market_impact', 
                   'impact_score', 'timestamp', 'url', 'content']
        
        return [dict(zip(columns, article)) for article in articles]
    except Exception as e:
        logging.error(f"Database read error: {e}")
        return []

# HTML Template for the dashboard
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial News Analyzer - Live AI Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .sentiment-positive { color: #28a745; font-weight: bold; }
        .sentiment-negative { color: #dc3545; font-weight: bold; }
        .sentiment-neutral { color: #ffc107; font-weight: bold; }
        .news-item { border-left: 4px solid #007bff; margin-bottom: 1rem; padding: 1rem; }
        .impact-high { background: #dc3545; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; }
        .impact-medium { background: #ffc107; color: black; padding: 0.2rem 0.5rem; border-radius: 0.3rem; }
        .impact-low { background: #28a745; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; }
        .auto-refresh { position: fixed; top: 10px; right: 10px; background: #28a745; color: white; padding: 0.5rem; border-radius: 0.5rem; z-index: 1000; }
    </style>
</head>
<body class="bg-light">
    <div class="auto-refresh">
        <i class="fas fa-sync-alt"></i> Auto-updates every 30min
    </div>
    
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <h1 class="display-6 fw-bold text-primary mb-1">
                    <i class="fas fa-chart-line me-3"></i>AI Financial News Analyzer
                </h1>
                <p class="lead text-muted">Real-time sentiment analysis of Indian & global financial markets</p>
                <small class="text-muted">Last updated: {{ last_updated }} IST | Total articles: {{ total_articles }}</small>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h3>{{ total_articles }}</h3>
                        <p class="mb-0">Live Articles</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h3>{{ positive_news }}</h3>
                        <p class="mb-0">Positive News</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-danger text-white">
                    <div class="card-body text-center">
                        <h3>{{ negative_news }}</h3>
                        <p class="mb-0">Negative News</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h3>{{ avg_confidence }}%</h3>
                        <p class="mb-0">Avg Confidence</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-newspaper me-2"></i>Latest Financial News & AI Analysis</h5>
                    </div>
                    <div class="card-body">
                        {% if articles %}
                            {% for article in articles %}
                            <div class="news-item">
                                <div class="row">
                                    <div class="col-md-8">
                                        <h6 class="fw-bold mb-2">{{ article.title }}</h6>
                                        <p class="mb-2">{{ article.summary }}</p>
                                        <div class="mb-2">
                                            <span class="badge bg-secondary">{{ article.source }}</span>
                                            <span class="badge bg-info">{{ article.region }}</span>
                                            <span class="badge bg-warning">{{ article.category }}</span>
                                            <span class="sentiment-{{ article.sentiment.lower() }}">{{ article.sentiment }}</span>
                                        </div>
                                    </div>
                                    <div class="col-md-4 text-end">
                                        <div class="impact-{{ article.market_impact.lower() }} mb-2">
                                            Impact: {{ article.impact_score }}/10
                                        </div>
                                        <div class="mb-2">
                                            <strong>AI Confidence:</strong> {{ article.confidence }}%
                                        </div>
                                        <small class="text-muted">{{ article.timestamp }}</small>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>Loading news articles... Please refresh in a moment.
                            </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 minutes
        setTimeout(() => location.reload(), 1800000);
    </script>
</body>
</html>
'''

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    articles = get_articles_from_db(limit=20)
    
    if not articles:
        # If no articles, try to fetch some
        try:
            fetch_all_news()
            articles = get_articles_from_db(limit=20)
        except Exception as e:
            logging.error(f"Failed to fetch news: {e}")
    
    # Calculate stats
    total_articles = len(articles)
    positive_news = len([a for a in articles if a['sentiment'] == 'Positive'])
    negative_news = len([a for a in articles if a['sentiment'] == 'Negative'])
    avg_confidence = int(sum(a['confidence'] for a in articles) / max(1, total_articles)) if total_articles > 0 else 0
    
    return render_template_string(HTML_TEMPLATE,
                                articles=articles,
                                total_articles=total_articles,
                                positive_news=positive_news,
                                negative_news=negative_news,
                                avg_confidence=avg_confidence,
                                last_updated=datetime.now().strftime('%Y-%m-%d %H:%M'))

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/news')
def api_news():
    """API endpoint for news"""
    region = request.args.get('region')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 50))
    
    articles = get_articles_from_db(limit=limit, region=region, category=category)
    return jsonify(articles)

@app.route('/manual-fetch')
def manual_fetch():
    """Manual news fetch endpoint"""
    try:
        articles = fetch_all_news()
        return jsonify({
            'message': f'Successfully fetched and analyzed {len(articles)} articles',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

# Initialize database
init_db()

# Set up scheduler for automatic news fetching
scheduler = BackgroundScheduler()

# Fetch news every 2 hours
scheduler.add_job(
    func=fetch_all_news,
    trigger="interval",
    hours=2,
    id='periodic_news_fetch',
    max_instances=1
)

scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Initial fetch on startup (with error handling)
    try:
        logging.info("Running initial news fetch...")
        fetch_all_news()
    except Exception as e:
        logging.error(f"Initial fetch failed: {e}")
    
    # Get port from environment variable (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
