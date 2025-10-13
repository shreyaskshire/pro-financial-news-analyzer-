// Sample Financial News Data
const sampleNewsData = [
  {
    id: 1,
    title: "RBI Keeps Repo Rate Unchanged at 6.5%, Maintains Accommodative Stance",
    summary: "The Reserve Bank of India maintained its key policy rate at 6.5% in the latest monetary policy committee meeting, citing inflation concerns and global economic uncertainty. The central bank emphasized continued support for economic growth while monitoring price stability.",
    source: "Economic Times",
    category: "Monetary Policy",
    region: "India",
    sentiment: "Neutral",
    sentiment_score: 0.1,
    confidence: 85,
    market_impact: "Medium",
    impact_score: 7.2,
    timestamp: "2025-10-13 09:30:00",
    related_sectors: ["Banking", "Real Estate", "Auto"],
    key_points: [
      "Repo rate maintained at 6.5% for third consecutive meeting",
      "Inflation target of 4% remains priority",
      "GDP growth projection revised to 7.2%"
    ]
  },
  {
    id: 2,
    title: "Tata Capital Makes Muted Market Debut After $1.75 Billion IPO",
    summary: "Tata Capital shares listed at Rs 330 on BSE and NSE, representing just 1.2% premium over the issue price of Rs 325. Despite the lukewarm listing, analysts remain optimistic about the company's long-term prospects given its strong parentage and diversified financial services portfolio.",
    source: "CNBC",
    category: "IPO",
    region: "India",
    sentiment: "Slightly Negative",
    sentiment_score: -0.3,
    confidence: 78,
    market_impact: "Medium",
    impact_score: 6.8,
    timestamp: "2025-10-13 10:15:00",
    related_sectors: ["Financial Services", "NBFC"],
    key_points: [
      "Listing at 1.2% premium below expectations",
      "Strong institutional investor participation",
      "Tata Group backing provides credibility"
    ]
  },
  {
    id: 3,
    title: "China's Market Rally Faces Test as US Trade Tensions Resurface",
    summary: "Chinese markets are experiencing volatility as renewed US-China trade tensions threaten the recent market recovery. Export data showed better-than-expected performance, but concerns about tariffs and trade restrictions are weighing on investor sentiment.",
    source: "Reuters",
    category: "Global Markets",
    region: "Global",
    sentiment: "Negative",
    sentiment_score: -0.6,
    confidence: 82,
    market_impact: "High",
    impact_score: 8.5,
    timestamp: "2025-10-13 08:45:00",
    related_sectors: ["Technology", "Manufacturing", "Export"],
    key_points: [
      "US-China trade tensions escalating again",
      "Export data beats expectations despite concerns",
      "Market volatility expected to continue"
    ]
  },
  {
    id: 4,
    title: "Bank of America Raises Gold Price Forecast to $5,000/oz for 2026",
    summary: "Bank of America Global Research has significantly increased its precious metals outlook, setting a new gold price target of $5,000 per ounce for 2026, with an average expectation around $4,400. This bullish forecast is driven by inflation hedging demand and geopolitical uncertainties.",
    source: "Reuters",
    category: "Commodities",
    region: "Global",
    sentiment: "Very Positive",
    sentiment_score: 0.8,
    confidence: 88,
    market_impact: "High",
    impact_score: 8.8,
    timestamp: "2025-10-13 11:00:00",
    related_sectors: ["Precious Metals", "Mining", "Banking"],
    key_points: [
      "Gold target raised to $5,000/oz for 2026",
      "Average expectation around $4,400/oz",
      "Driven by inflation and geopolitical factors"
    ]
  },
  {
    id: 5,
    title: "Indian State-Owned Refiners Cut Russian Oil Imports by 45%",
    summary: "State-owned oil refiners in India have significantly reduced Russian crude oil imports by 45% between June and September 2025, according to Kpler data. However, private refiners like Reliance Industries have increased their imports, maintaining India's overall energy security strategy.",
    source: "The Hindu Business",
    category: "Energy",
    region: "India",
    sentiment: "Neutral",
    sentiment_score: 0.0,
    confidence: 75,
    market_impact: "Medium",
    impact_score: 7.0,
    timestamp: "2025-10-13 07:30:00",
    related_sectors: ["Oil & Gas", "Refining", "Energy"],
    key_points: [
      "State refiners cut Russian oil by 45%",
      "Private refiners increased imports",
      "Overall energy security maintained"
    ]
  }
];

// Market Sentiment Data
const marketSentimentData = {
  overall_sentiment: "Slightly Negative",
  overall_score: -0.2,
  confidence: 79,
  trend: "Declining",
  regional_sentiment: {
    India: {
      score: -0.1,
      trend: "Stable",
      key_drivers: ["Monetary Policy", "IPO Performance", "Energy Policy"]
    },
    Global: {
      score: -0.3,
      trend: "Declining",
      key_drivers: ["Trade Tensions", "Commodity Prices", "Geopolitical Issues"]
    }
  },
  sector_sentiment: {
    Banking: {
      score: 0.1,
      trend: "Positive"
    },
    Technology: {
      score: -0.4,
      trend: "Negative"
    },
    Energy: {
      score: 0.0,
      trend: "Neutral"
    },
    "Precious Metals": {
      score: 0.8,
      trend: "Very Positive"
    },
    "Financial Services": {
      score: -0.2,
      trend: "Slightly Negative"
    }
  }
};

// Trending Topics Data
const trendingTopics = [
  {
    topic: "RBI Monetary Policy",
    mentions: 45,
    sentiment: "Neutral"
  },
  {
    topic: "China Trade Relations",
    mentions: 38,
    sentiment: "Negative"
  },
  {
    topic: "Gold Price Surge",
    mentions: 32,
    sentiment: "Very Positive"
  },
  {
    topic: "IPO Market Performance",
    mentions: 28,
    sentiment: "Mixed"
  },
  {
    topic: "Russian Oil Imports",
    mentions: 22,
    sentiment: "Neutral"
  }
];

// Global variables
let currentTheme = 'light';
let filteredNews = [...sampleNewsData];
let charts = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  initializeApp();
});

function initializeApp() {
  setupEventListeners();
  renderDashboard();
  initializeCharts();
  updateStats();
}

function setupEventListeners() {
  // Navigation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const target = this.getAttribute('href').substring(1);
      showSection(target);
      
      // Update active nav
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });

  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', toggleTheme);

  // Filters
  document.getElementById('regionFilter').addEventListener('change', applyFilters);
  document.getElementById('categoryFilter').addEventListener('change', applyFilters);
  document.getElementById('sentimentFilter').addEventListener('change', applyFilters);
  document.getElementById('dateFilter').addEventListener('change', applyFilters);
}

function showSection(sectionId) {
  // Hide all sections
  document.querySelectorAll('section').forEach(section => {
    section.classList.add('d-none');
  });
  
  // Show target section
  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.classList.remove('d-none');
    
    // Initialize section-specific content
    if (sectionId === 'news') {
      renderDetailedNews();
    } else if (sectionId === 'sentiment') {
      renderSentimentOverview();
    }
  }
}

function renderDashboard() {
  renderNews();
  renderTrendingTopics();
}

function renderNews() {
  const container = document.getElementById('newsContainer');
  if (!container) return;
  
  container.innerHTML = '';
  
  filteredNews.forEach(news => {
    const newsItem = createNewsItem(news);
    container.appendChild(newsItem);
  });
}

function createNewsItem(news) {
  const div = document.createElement('div');
  div.className = 'news-item';
  div.onclick = () => showNewsDetail(news);
  
  const sentimentClass = getSentimentClass(news.sentiment_score);
  const sentimentText = getSentimentText(news.sentiment_score);
  
  div.innerHTML = `
    <div class="d-flex justify-content-between align-items-start mb-2">
      <div class="flex-grow-1">
        <h6 class="mb-1">${news.title}</h6>
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="badge bg-secondary">${news.source}</span>
          <span class="badge bg-info">${news.category}</span>
          <span class="badge bg-warning">${news.region}</span>
          <span class="sentiment-badge sentiment-${sentimentClass}">${sentimentText}</span>
        </div>
      </div>
      <div class="text-end">
        <div class="impact-score">Impact: ${news.impact_score}/10</div>
        <small class="text-muted d-block mt-1">${formatTime(news.timestamp)}</small>
      </div>
    </div>
    <p class="text-muted mb-2">${news.summary.substring(0, 200)}...</p>
    <div class="d-flex justify-content-between align-items-center">
      <div class="confidence-bar" style="width: 100px;">
        <div class="confidence-fill" style="width: ${news.confidence}%;"></div>
      </div>
      <small class="text-muted">Confidence: ${news.confidence}%</small>
    </div>
  `;
  
  return div;
}

function showNewsDetail(news) {
  const modal = new bootstrap.Modal(document.getElementById('newsDetailModal'));
  const modalTitle = document.getElementById('modalTitle');
  const modalBody = document.getElementById('modalBody');
  
  modalTitle.textContent = news.title;
  
  const sentimentClass = getSentimentClass(news.sentiment_score);
  const sentimentText = getSentimentText(news.sentiment_score);
  
  modalBody.innerHTML = `
    <div class="row mb-3">
      <div class="col-md-6">
        <strong>Source:</strong> ${news.source}<br>
        <strong>Category:</strong> ${news.category}<br>
        <strong>Region:</strong> ${news.region}<br>
        <strong>Published:</strong> ${formatTime(news.timestamp)}
      </div>
      <div class="col-md-6">
        <strong>Sentiment:</strong> <span class="sentiment-badge sentiment-${sentimentClass}">${sentimentText}</span><br>
        <strong>Confidence:</strong> ${news.confidence}%<br>
        <strong>Market Impact:</strong> ${news.market_impact} (${news.impact_score}/10)<br>
        <strong>Sentiment Score:</strong> ${news.sentiment_score.toFixed(2)}
      </div>
    </div>
    
    <div class="mb-3">
      <h6>Summary</h6>
      <p>${news.summary}</p>
    </div>
    
    <div class="key-points mb-3">
      <h6>Key Points</h6>
      <ul>
        ${news.key_points.map(point => `<li>${point}</li>`).join('')}
      </ul>
    </div>
    
    <div class="mb-3">
      <h6>Related Sectors</h6>
      ${news.related_sectors.map(sector => `<span class="badge bg-secondary me-1">${sector}</span>`).join('')}
    </div>
    
    <div class="sentiment-analysis">
      <h6>Sentiment Analysis</h6>
      <p>The AI analysis indicates a <strong>${sentimentText.toLowerCase()}</strong> sentiment with a confidence level of <strong>${news.confidence}%</strong>. 
      This assessment is based on the tone of the news content, market terminology used, and potential impact on investor sentiment.</p>
    </div>
  `;
  
  modal.show();
}

function renderTrendingTopics() {
  const container = document.getElementById('trendingTopics');
  if (!container) return;
  
  container.innerHTML = '';
  
  trendingTopics.forEach(topic => {
    const div = document.createElement('div');
    div.className = 'trending-item';
    
    const sentimentClass = getSentimentClassFromText(topic.sentiment);
    
    div.innerHTML = `
      <div>
        <div class="fw-medium">${topic.topic}</div>
        <div class="trending-mentions">${topic.mentions} mentions</div>
      </div>
      <span class="sentiment-badge sentiment-${sentimentClass}">${topic.sentiment}</span>
    `;
    
    container.appendChild(div);
  });
}

function initializeCharts() {
  initializeSentimentGauge();
  initializeSectorChart();
}

function initializeSentimentGauge() {
  const ctx = document.getElementById('sentimentGauge');
  if (!ctx) return;
  
  const score = marketSentimentData.overall_score;
  const normalizedScore = ((score + 1) * 50); // Convert -1 to 1 scale to 0-100
  
  charts.sentimentGauge = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [normalizedScore, 100 - normalizedScore],
        backgroundColor: [
          score >= 0 ? '#1FB8CD' : '#DB4545',
          '#ECEBD5'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      circumference: 180,
      rotation: -90,
      cutout: '80%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      }
    }
  });
}

function initializeSectorChart() {
  const ctx = document.getElementById('sectorChart');
  if (!ctx) return;
  
  const sectors = Object.keys(marketSentimentData.sector_sentiment);
  const scores = sectors.map(sector => marketSentimentData.sector_sentiment[sector].score);
  
  charts.sectorChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sectors,
      datasets: [{
        label: 'Sentiment Score',
        data: scores,
        backgroundColor: scores.map(score => {
          if (score > 0.3) return '#1FB8CD';
          if (score > -0.3) return '#FFC185';
          return '#B4413C';
        }),
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          min: -1,
          max: 1,
          ticks: {
            callback: function(value) {
              return value.toFixed(1);
            }
          }
        },
        x: {
          ticks: {
            maxRotation: 45
          }
        }
      }
    }
  });
}

function renderSentimentOverview() {
  initializeRegionalChart();
  initializeTrendChart();
}

function initializeRegionalChart() {
  const ctx = document.getElementById('regionalChart');
  if (!ctx) return;
  
  if (charts.regionalChart) {
    charts.regionalChart.destroy();
  }
  
  const regions = Object.keys(marketSentimentData.regional_sentiment);
  const scores = regions.map(region => marketSentimentData.regional_sentiment[region].score);
  
  charts.regionalChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: regions,
      datasets: [{
        label: 'Regional Sentiment',
        data: scores,
        backgroundColor: ['#1FB8CD', '#FFC185'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          min: -1,
          max: 1
        }
      }
    }
  });
}

function initializeTrendChart() {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;
  
  if (charts.trendChart) {
    charts.trendChart.destroy();
  }
  
  // Generate sample 7-day trend data
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const trendData = [-0.1, -0.05, 0.1, 0.05, -0.15, -0.2, -0.2];
  
  charts.trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: days,
      datasets: [{
        label: 'Sentiment Trend',
        data: trendData,
        borderColor: '#1FB8CD',
        backgroundColor: 'rgba(31, 184, 205, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          min: -1,
          max: 1
        }
      }
    }
  });
}

function renderDetailedNews() {
  const container = document.getElementById('detailedNewsContainer');
  if (!container) return;
  
  container.innerHTML = '';
  
  filteredNews.forEach(news => {
    const card = document.createElement('div');
    card.className = 'card mb-4';
    
    const sentimentClass = getSentimentClass(news.sentiment_score);
    const sentimentText = getSentimentText(news.sentiment_score);
    
    card.innerHTML = `
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-start">
          <h6 class="mb-0">${news.title}</h6>
          <span class="sentiment-badge sentiment-${sentimentClass}">${sentimentText}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="row mb-3">
          <div class="col-md-8">
            <p>${news.summary}</p>
            <div class="key-points">
              <h6>Key Points:</h6>
              <ul>
                ${news.key_points.map(point => `<li>${point}</li>`).join('')}
              </ul>
            </div>
          </div>
          <div class="col-md-4">
            <div class="mb-3">
              <strong>Source:</strong> ${news.source}<br>
              <strong>Category:</strong> ${news.category}<br>
              <strong>Region:</strong> ${news.region}<br>
              <strong>Impact:</strong> ${news.impact_score}/10<br>
              <strong>Confidence:</strong> ${news.confidence}%
            </div>
            <div>
              <strong>Related Sectors:</strong><br>
              ${news.related_sectors.map(sector => `<span class="badge bg-secondary me-1 mb-1">${sector}</span>`).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
    
    container.appendChild(card);
  });
}

function applyFilters() {
  const regionFilter = document.getElementById('regionFilter').value;
  const categoryFilter = document.getElementById('categoryFilter').value;
  const sentimentFilter = document.getElementById('sentimentFilter').value;
  const dateFilter = document.getElementById('dateFilter').value;
  
  filteredNews = sampleNewsData.filter(news => {
    let matches = true;
    
    if (regionFilter !== 'all' && news.region !== regionFilter) {
      matches = false;
    }
    
    if (categoryFilter !== 'all' && news.category !== categoryFilter) {
      matches = false;
    }
    
    if (sentimentFilter !== 'all') {
      const sentimentCategory = getSentimentCategory(news.sentiment_score);
      if (sentimentCategory !== sentimentFilter) {
        matches = false;
      }
    }
    
    return matches;
  });
  
  renderNews();
  updateStats();
}

function getSentimentCategory(score) {
  if (score > 0.1) return 'positive';
  if (score < -0.1) return 'negative';
  return 'neutral';
}

function getSentimentClass(score) {
  if (score > 0.1) return 'positive';
  if (score < -0.1) return 'negative';
  return 'neutral';
}

function getSentimentText(score) {
  if (score > 0.5) return 'Very Positive';
  if (score > 0.1) return 'Positive';
  if (score > -0.1) return 'Neutral';
  if (score > -0.5) return 'Negative';
  return 'Very Negative';
}

function getSentimentClassFromText(text) {
  const lower = text.toLowerCase();
  if (lower.includes('positive')) return 'positive';
  if (lower.includes('negative')) return 'negative';
  return 'neutral';
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: true
  });
}

function updateStats() {
  document.getElementById('totalNews').textContent = filteredNews.length;
  document.getElementById('marketSentiment').textContent = marketSentimentData.overall_sentiment;
  document.getElementById('avgConfidence').textContent = marketSentimentData.confidence + '%';
  
  const indiaNews = filteredNews.filter(news => news.region === 'India').length;
  const indiaPercentage = Math.round((indiaNews / filteredNews.length) * 100);
  document.getElementById('regionalFocus').textContent = indiaPercentage + '%';
  
  // Update sentiment score and confidence
  document.getElementById('sentimentScore').textContent = marketSentimentData.overall_score.toFixed(2);
  document.getElementById('sentimentConfidence').textContent = marketSentimentData.confidence + '%';
}

function toggleTheme() {
  const body = document.body;
  const themeToggle = document.getElementById('themeToggle');
  const icon = themeToggle.querySelector('i');
  
  if (currentTheme === 'light') {
    body.setAttribute('data-color-scheme', 'dark');
    icon.className = 'fas fa-sun';
    currentTheme = 'dark';
  } else {
    body.setAttribute('data-color-scheme', 'light');
    icon.className = 'fas fa-moon';
    currentTheme = 'light';
  }
}

function exportReport() {
  showLoadingOverlay();
  
  // Simulate report generation
  setTimeout(() => {
    const reportData = {
      timestamp: new Date().toISOString(),
      total_news: filteredNews.length,
      overall_sentiment: marketSentimentData.overall_sentiment,
      confidence: marketSentimentData.confidence,
      news_summary: filteredNews.map(news => ({
        title: news.title,
        sentiment: getSentimentText(news.sentiment_score),
        impact_score: news.impact_score,
        confidence: news.confidence
      }))
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `financial-news-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    hideLoadingOverlay();
    
    // Show success message
    alert('Report exported successfully!');
  }, 1500);
}

function shareAnalysis() {
  if (navigator.share) {
    navigator.share({
      title: 'FinanceIQ - Market Analysis',
      text: `Current market sentiment: ${marketSentimentData.overall_sentiment} (${marketSentimentData.confidence}% confidence)`,
      url: window.location.href
    });
  } else {
    // Fallback for browsers that don't support Web Share API
    const text = `FinanceIQ Market Analysis: ${marketSentimentData.overall_sentiment} sentiment with ${marketSentimentData.confidence}% confidence`;
    navigator.clipboard.writeText(text).then(() => {
      alert('Analysis copied to clipboard!');
    });
  }
}

function showLoadingOverlay() {
  document.getElementById('loadingOverlay').classList.remove('d-none');
}

function hideLoadingOverlay() {
  document.getElementById('loadingOverlay').classList.add('d-none');
}

// Auto-refresh functionality
setInterval(() => {
  // In a real application, this would fetch new data from the server
  console.log('Auto-refreshing data...');
  
  // Update timestamp
  const now = new Date();
  const timeString = now.toLocaleString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata'
  });
  document.getElementById('lastUpdated').textContent = `Last updated: ${timeString} IST`;
}, 900000); // Update every 15 minutes

// Initialize theme based on system preference
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
  currentTheme = 'dark';
  document.getElementById('themeToggle').querySelector('i').className = 'fas fa-sun';
}
