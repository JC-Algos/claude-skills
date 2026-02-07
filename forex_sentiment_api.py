"""
ULTIMATE FOREX SENTIMENT ENGINE (Full Uncut Version)
================================================================
PART A: MyFXBook Retail Scraper (Your Original 200+ Lines)
PART B: FinBERT News Engine (Your Original 300+ Lines)
PART C: Flask API Server (The Bridge)
"""

from flask import Flask, jsonify, request
import pandas as pd
import re
import time
import json
import os
import threading
import requests
import feedparser

# [FIX] Added missing typing imports to prevent NameError crash
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Global Application Object
app = Flask(__name__)

# ==============================================================================
# PART A: YOUR ORIGINAL MYFXBOOK API CLASS (Restored)
# ==============================================================================

class MyFXBookAPI:
    """
    API wrapper for MyFXBook sentiment scraping - MATCHES JUPYTER CODE EXACTLY
    """
    def __init__(self, debug=True):
        self.debug = debug
        self.sentiment_url = "https://www.myfxbook.com/community/outlook"
        self.target_symbols = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD', "USDCNH"]

    def _log(self, message):
        """Debug logging - MATCHES JUPYTER"""
        if self.debug:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {message}")

    def _setup_chrome_driver(self):
        """[FIX] Setup Chrome driver with undetected-chromedriver (Headless)"""
        try:
            self._log("🔧 Setting up ChromeDriver...")
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            driver_path = ChromeDriverManager().install()
            driver = uc.Chrome(driver_executable_path=driver_path, options=options, use_subprocess=False)
            self._log("✓ ChromeDriver ready")
            return driver
        except Exception as e:
            self._log(f"❌ Driver Error: {e}")
            raise e

    def _extract_sentiment_from_html(self, html_content: str) -> List[Dict]:
        """Extract sentiment data from HTML content - EXACT JUPYTER LOGIC"""
        sentiment_data = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for tables with sentiment data - EXACT JUPYTER LOGIC
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text()
                
                # Check if this table contains our symbols
                symbols_in_table = [s for s in self.target_symbols if s in table_text]
                
                if len(symbols_in_table) >= 2:
                    self._log(f"✓ Found sentiment table with symbols: {symbols_in_table}")
                    
                    # Extract data from each row
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                            
                            for symbol in self.target_symbols:
                                if symbol in row_text:
                                    # Extract percentages and volumes
                                    percentages = re.findall(r'(\d+)\s*%', row_text)
                                    volumes = re.findall(r'([\d,]+\.?\d*)\s*lots', row_text, re.IGNORECASE)
                                    
                                    if len(percentages) >= 2:
                                        try:
                                            # MATH FIX: Find the pair that sums to 100%
                                            raw_nums = [int(p) for p in percentages]
                                            short_pct = 0
                                            long_pct = 0
                                            found_valid = False
                                            
                                            for i in range(len(raw_nums)):
                                                for j in range(i + 1, len(raw_nums)):
                                                    if 99 <= (raw_nums[i] + raw_nums[j]) <= 101:
                                                        short_pct = raw_nums[i]
                                                        long_pct = raw_nums[j]
                                                        found_valid = True
                                                        break
                                                if found_valid:
                                                    break
                                            
                                            # Fallback to original logic if math check fails (rare)
                                            if not found_valid:
                                                short_pct = int(percentages[0])
                                                long_pct = int(percentages[1])
                                            
                                            short_vol = float(volumes[0].replace(',', '')) if len(volumes) >= 1 else 0.0
                                            long_vol = float(volumes[1].replace(',', '')) if len(volumes) >= 2 else 0.0
                                            
                                            # Calculate sentiment
                                            if short_pct >= 70:
                                                sentiment = "Very Bearish"
                                                sentiment_score = -2
                                            elif short_pct >= 60:
                                                sentiment = "Bearish"
                                                sentiment_score = -1
                                            elif short_pct >= 55:
                                                sentiment = "Slightly Bearish"
                                                sentiment_score = -0.5
                                            elif short_pct >= 45:
                                                sentiment = "Neutral"
                                                sentiment_score = 0
                                            elif short_pct >= 35:
                                                sentiment = "Slightly Bullish"
                                                sentiment_score = 0.5
                                            else:
                                                sentiment = "Bullish"
                                                sentiment_score = 1
                                            
                                            sentiment_data.append({
                                                'Symbol': symbol,
                                                'Short_Percentage': short_pct,
                                                'Long_Percentage': long_pct,
                                                'Short_Volume': short_vol,
                                                'Long_Volume': long_vol,
                                                'Sentiment': sentiment,
                                                'Sentiment_Score': sentiment_score,
                                                'Total_Volume': short_vol + long_vol,
                                                'Status': 'Success'
                                            })
                                            self._log(f"✓ Extracted {symbol}: {short_pct}% short, {long_pct}% long")
                                            break
                                        except (ValueError, IndexError) as e:
                                            self._log(f"⚠️ Error parsing {symbol} data: {e}")
            
            # *** CRITICAL: ADD MISSING FALLBACK REGEX PATTERNS FROM JUPYTER ***
            if not sentiment_data:
                self._log("🔍 Trying regex extraction...")
                for symbol in self.target_symbols:
                    patterns = [
                        f'{symbol}.*?Short.*?(\\d+)\\s*%.*?([\\d,]+\\.?\\d*)\\s*lots.*?Long.*?(\\d+)\\s*%.*?([\\d,]+\\.?\\d*)\\s*lots',
                        f'{symbol}.*?(\\d+)\\s*%.*?([\\d,]+\\.?\\d*)\\s*lots.*?(\\d+)\\s*%.*?([\\d,]+\\.?\\d*)\\s*lots',
                        f'{symbol}.*?(\\d+)\\s*%.*?(\\d+)\\s*%'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                        if match:
                            groups = match.groups()
                            if len(groups) >= 4:
                                try:
                                    short_pct = int(groups[0])
                                    long_pct = int(groups[2])
                                    short_vol = float(groups[1].replace(',', ''))
                                    long_vol = float(groups[3].replace(',', ''))
                                    
                                    # Sentiment Logic
                                    if short_pct >= 60:
                                        sentiment = "Bearish"
                                        score = -1
                                    elif short_pct <= 40:
                                        sentiment = "Bullish"
                                        score = 1
                                    else:
                                        sentiment = "Neutral"
                                        score = 0
                                    
                                    sentiment_data.append({
                                        'Symbol': symbol,
                                        'Short_Percentage': short_pct,
                                        'Long_Percentage': long_pct,
                                        'Short_Volume': short_vol,
                                        'Long_Volume': long_vol,
                                        'Sentiment': sentiment,
                                        'Sentiment_Score': score,
                                        'Total_Volume': short_vol + long_vol,
                                        'Status': 'Success'
                                    })
                                    self._log(f"✓ Regex extracted {symbol}")
                                    break
                                except:
                                    continue
        
        except Exception as e:
            self._log(f"❌ HTML extraction error: {e}")
        
        return sentiment_data

    def get_sentiment_data(self, currency_pair=None):
        """Get live sentiment data from MyFXBook - EXACT JUPYTER LOGIC"""
        start_time = time.time()
        self._log("🚀 Starting MyFXBook sentiment extraction...")
        
        driver = None
        try:
            driver = self._setup_chrome_driver()
            
            self._log("📡 Navigating to MyFXBook...")
            driver.get(self.sentiment_url)
            
            self._log("⏳ Waiting for page load...")
            time.sleep(10)
            
            self._log("🔍 Extracting sentiment data...")
            page_source = driver.page_source
            
            symbols_found = [s for s in self.target_symbols if s in page_source]
            self._log(f"✓ Found symbols: {symbols_found}")
            
            if len(symbols_found) >= 3:
                sentiment_data = self._extract_sentiment_from_html(page_source)
                
                if currency_pair and sentiment_data:
                    sentiment_data = [item for item in sentiment_data if item['Symbol'] == currency_pair]
                
                if sentiment_data:
                    return {'status': 'success', 'data': sentiment_data}
            
            return {'status': 'error', 'message': 'Insufficient data'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        finally:
            if driver:
                driver.quit()

# ==============================================================================
# PART B: YOUR ORIGINAL NEWS ENGINE (FinBERT + RSS)
# ==============================================================================

print("Loading FinBERT model...")
finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
labels = ['Neutral', 'Positive', 'Negative']
print("Model loaded successfully!")

ASSETS = {
    "EURUSD": {
        "name": "Euro (EUR/USD)",
        "queries": ["EURUSD forex", "EUR USD forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False
    },
    "GBPUSD": {
        "name": "British Pound (GBP/USD)",
        "queries": ["GBPUSD forex", "GBP USD forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False
    },
    "AUDUSD": {
        "name": "Australian Dollar (AUD/USD)",
        "queries": ["AUDUSD forex", "AUD USD forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False
    },
    "NZDUSD": {
        "name": "New Zealand Dollar (NZD/USD)",
        "queries": ["NZDUSD forex", "NZD USD forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False
    },
    "USDJPY": {
        "name": "Japanese Yen (USD/JPY)",
        "queries": ["USDJPY forex", "USD JPY forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False  # Fixed: queries are pair-specific, no inversion needed
    },
    "USDCAD": {
        "name": "Canadian Dollar (USD/CAD)",
        "queries": ["USDCAD forex", "USD CAD forecast"],
        "articles_per_query": 5,
        "days": 2,
        "inverted": False  # Fixed: queries are pair-specific, no inversion needed
    }
}

def is_within_days(published_str, days=2):
    try:
        pub_date = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")
        return pub_date >= (datetime.utcnow() - timedelta(days=days))
    except:
        return True

def fetch_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return ' '.join([p.get_text() for p in paragraphs]).strip()
    except:
        return "Content not retrieved."

def analyze_sentiment(text):
    if not text.strip():
        return 0.0, 'Neutral'
    
    inputs = finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = finbert_model(**inputs)
    
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1).numpy()[0]
    max_index = np.argmax(probabilities)
    
    return float(probabilities[max_index]), labels[max_index]

def fetch_news(query, num_articles=5, days=2):
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en&when={days}d"
    feed = feedparser.parse(rss_url)
    
    articles = []
    for item in feed.entries[:num_articles]:
        if hasattr(item, 'published') and not is_within_days(item.published, days):
            continue
        
        content = fetch_article_content(item.link)
        articles.append({
            "title": item.title,
            "link": item.link,
            "published": item.published if hasattr(item, 'published') else "N/A",
            "content": content
        })
    
    return articles

def deduplicate_articles(articles):
    unique = []
    seen = set()
    for a in articles:
        norm = ' '.join(a['title'].lower().split())
        if norm not in seen:
            seen.add(norm)
            unique.append(a)
    return unique, len(articles) - len(unique)

def classify_sentiment(positive_pct):
    if 48 <= positive_pct <= 52:
        return "NEUTRAL", "Balanced sentiment"
    elif 52 < positive_pct <= 60:
        return "MILD BULLISH", "Moderately positive outlook"
    elif 60 < positive_pct <= 75:
        return "BULLISH", "Positive market sentiment"
    elif positive_pct > 75:
        return "STRONG BULLISH", "Very strong positive sentiment"
    elif 40 <= positive_pct < 48:
        return "MILD BEARISH", "Moderately negative outlook"
    elif 25 <= positive_pct < 40:
        return "BEARISH", "Negative market sentiment"
    else:
        return "STRONG BEARISH", "Very strong negative sentiment"

def invert_sentiment(label, desc):
    inv_map = {
        "STRONG BULLISH": ("STRONG BEARISH", "Very strong negative"),
        "BULLISH": ("BEARISH", "Negative market sentiment"),
        "MILD BULLISH": ("MILD BEARISH", "Moderately negative"),
        "NEUTRAL": ("NEUTRAL", "Balanced"),
        "MILD BEARISH": ("MILD BULLISH", "Moderately positive"),
        "BEARISH": ("BULLISH", "Positive market sentiment"),
        "STRONG BEARISH": ("STRONG BULLISH", "Very strong positive")
    }
    return inv_map.get(label, (label, desc))

def process_news_for_asset(asset_key, config):
    all_articles = []
    for query in config['queries']:
        all_articles.extend(fetch_news(query, config['articles_per_query'], config['days']))
    
    unique, _ = deduplicate_articles(all_articles)
    
    pos, neg, neu = 0, 0, 0
    processed_articles = []
    
    for a in unique:
        text = a['title'] + ". " + (a['content'][:500] if a['content'] else "")
        conf, sent = analyze_sentiment(text)
        a['sentiment'] = sent
        a['confidence'] = conf
        processed_articles.append(a)
        
        if sent == 'Positive':
            pos += 1
        elif sent == 'Negative':
            neg += 1
        else:
            neu += 1
    
    directional = pos + neg
    pos_pct = (pos / directional * 100) if directional > 0 else 0
    neg_pct = (neg / directional * 100) if directional > 0 else 0
    
    label, desc = classify_sentiment(pos_pct)
    
    if config.get('inverted'):
        label, desc = invert_sentiment(label, desc)
    
    return {
        "name": config['name'],
        "total_articles": len(unique),
        "sentiment_counts": {
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "directional_total": directional
        },
        "sentiment_percentages": {
            "positive": pos_pct,
            "negative": neg_pct
        },
        "sentiment_classification": {
            "label": label,
            "description": desc
        },
        "articles": processed_articles
    }

# ==============================================================================
# PART C: FLASK SERVER & EXECUTION BRIDGE
# ==============================================================================

# Initialize Retail API
retail_api = MyFXBookAPI(debug=True)

DATA_FILE = r"C:\B_Drive\Market Sentiment Analysis\forex_sentiment_detailed.json"

@app.route('/sentiment', methods=['GET'])
def get_retail_sentiment():
    """Original Endpoint for Retail Data"""
    pair = request.args.get('pair', '').upper()
    return jsonify(retail_api.get_sentiment_data(pair))

@app.route('/run-analysis', methods=['GET'])
def trigger_full_analysis():
    """Trigger the heavy FinBERT Analysis"""
    final_output = {
        "timestamp": datetime.now().isoformat(),
        "assets": {}
    }
    
    for key, config in ASSETS.items():
        print(f"Processing News for {key}...")
        final_output["assets"][key] = process_news_for_asset(key, config)
    
    # 2. RUN RETAIL SCRAPE IN BACKGROUND AND MERGE
    try:
        retail_data = retail_api.get_sentiment_data()  # Scrape all
        if retail_data['status'] == 'success':
            for item in retail_data['data']:
                symbol = item['Symbol']
                if symbol in final_output['assets']:
                    final_output['assets'][symbol]['retail_sentiment'] = item
    except Exception as e:
        print(f"Retail Scrape Failed during Merge: {e}")
    
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
    
    return jsonify({
        "status": "success",
        "message": "Full Analysis Complete",
        "file": DATA_FILE
    })

@app.route('/forex-analysis-realtime', methods=['GET'])
def get_realtime_analysis():
    """
    REAL-TIME ANALYSIS ENDPOINT
    Generates fresh news + retail sentiment for a specific currency pair
    This is what n8n workflow should call
    """
    try:
        pair = request.args.get('pair', 'EURUSD').upper().replace('/', '')
        print(f"\n{'='*80}")
        print(f"🚀 REAL-TIME ANALYSIS REQUEST FOR: {pair}")
        print(f"{'='*80}\n")
        
        # Step 1: Check if pair is supported
        if pair not in ASSETS:
            return jsonify({
                "status": "error",
                "message": f"Currency pair {pair} not supported. Available pairs: {list(ASSETS.keys())}"
            }), 400
        
        # Step 2: Generate fresh news sentiment for this pair
        print(f"📰 Fetching fresh news sentiment for {pair}...")
        config = ASSETS[pair]
        news_data = process_news_for_asset(pair, config)
        print(f"✅ News analysis complete: {news_data['sentiment_classification']['label']}")
        
        # Step 3: Fetch retail sentiment for this pair
        print(f"👥 Fetching retail sentiment for {pair}...")
        retail_response = retail_api.get_sentiment_data(pair)
        
        retail_data = None
        if retail_response['status'] == 'success' and retail_response.get('data'):
            # Extract the specific pair data
            for item in retail_response['data']:
                if item['Symbol'] == pair:
                    retail_data = item
                    break
            
            if retail_data:
                print(f"✅ Retail data retrieved: {retail_data['Short_Percentage']}% SHORT, {retail_data['Long_Percentage']}% LONG")
            else:
                print(f"⚠️ No retail data found for {pair}")
        else:
            print(f"⚠️ Retail API returned error: {retail_response.get('message', 'Unknown')}")
        
        # Step 4: Build comprehensive response
        response_data = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "currency_pair": pair,
            "pair_name": config['name'],
            "inverted": config.get('inverted', False),
            "news_sentiment": {
                "total_articles": news_data['total_articles'],
                "sentiment_counts": news_data['sentiment_counts'],
                "sentiment_percentages": news_data['sentiment_percentages'],
                "sentiment_classification": news_data['sentiment_classification'],
                "articles": news_data['articles'][:15]  # Limit to 15 most recent articles
            },
            "retail_sentiment": retail_data if retail_data else {
                "available": False,
                "message": "Retail sentiment data temporarily unavailable"
            },
            "data_source": "Real-time API Analysis"
        }
        
        print(f"\n{'='*80}")
        print(f"✅ REAL-TIME ANALYSIS COMPLETE FOR {pair}")
        print(f"{'='*80}\n")
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"\n❌ ERROR in real-time analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
            "currency_pair": request.args.get('pair', 'UNKNOWN')
        }), 500

if __name__ == '__main__':
    print("="*80)
    print("MEGA SERVER STARTED: Retail Scraper + FinBERT Engine")
    print("="*80)
    print("Available Endpoints:")
    print("  - GET /sentiment?pair=EURUSD (Raw retail data)")
    print("  - GET /run-analysis (Full batch analysis - all pairs)")
    print("  - GET /forex-analysis-realtime?pair=EURUSD (*** Real-time single pair analysis)")
    print(f"\nData Directory: {os.path.dirname(DATA_FILE)}")
    print(f"Supported Pairs: {list(ASSETS.keys())}\n")
    
    app.run(host='0.0.0.0', port=5002, debug=False)
