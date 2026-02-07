import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
import json
import os

# Load FinBERT model
print("Loading FinBERT model...")
finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
# CRITICAL: Use the model's actual label order!
# Model outputs: [Neutral, Positive, Negative] not [Positive, Negative, Neutral]!
labels = ['Neutral', 'Positive', 'Negative']
print("Model loaded successfully!\n")

# Define asset classes
ASSETS = {
    "US_SPX": {
        "name": "S&P 500 Index (SPX)",
        "queries": [
            "S&P 500 index performance",
            "S&P 500 market outlook",
            "S&P 500 index forecast",
            "S&P 500 market trends",
            "S&P 500 index analysis",
            "Wall Street S&P 500",
            "stock market S&P 500 today"
        ],
        "articles_per_query": 10,
        "days": 5  # Last 5 days for high relevancy
    },
    "US_NDX": {
        "name": "Nasdaq 100 Index (NDX)",
        "queries": [
            "Nasdaq 100 index performance",
            "Nasdaq composite market",
            "Nasdaq index forecast",
            "Nasdaq market outlook",
            "tech sector Nasdaq index",
            "Nasdaq 100 trends",
            "Nasdaq index analysis"
        ],
        "articles_per_query": 10,
        "days": 5
    },
    "HK_HSI": {
        "name": "Hang Seng Index (HSI)",
        "queries": [
            "Hang Seng Index performance",
            "HSI Hong Kong market",
            "Hong Kong stock index",
            "Hang Seng market outlook",
            "HSI index forecast",
            "Hong Kong market trends",
            "Hang Seng index analysis"
        ],
        "articles_per_query": 10,
        "days": 5
    },
    "GOLD": {
        "name": "Gold (XAU/USD)",
        "queries": [
            "gold market",
            "gold price",
            "gold news",
            "gold trends",
            "gold analysis",
            "gold forecast",
            "gold investment"
        ],
        "articles_per_query": 10,
        "days": 5
    },
    "BITCOIN": {
        "name": "Bitcoin (BTC/USD)",
        "queries": [
            "Bitcoin price",
            "BTC market",
            "Bitcoin news",
            "Bitcoin analysis",
            "Bitcoin forecast",
            "crypto Bitcoin",
            "Bitcoin investment"
        ],
        "articles_per_query": 10,
        "days": 5
    }
}


def is_within_days(published_str, days=5):
    """Check if article was published within specified days"""
    try:
        # Parse the published date string
        # Google News uses format like: "Sat, 25 Oct 2025 09:50:18 GMT"
        pub_date = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Check if published date is within range
        is_recent = pub_date >= cutoff_date
        
        if not is_recent:
            days_old = (datetime.utcnow() - pub_date).days
            print(f"   [FILTER] Skipping article from {days_old} days ago (> {days} days)")
        
        return is_recent
    except Exception as e:
        # If parsing fails, include the article (fail-safe)
        print(f"   [WARNING] Could not parse date '{published_str}': {e}")
        return True


def fetch_news(query, num_articles=10, days=5):
    """Fetch news articles from Google News RSS feed within specified days"""
    # Add time filter to get only recent articles
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
    
    # Add time filter (suggestion to Google)
    if days:
        rss_url += f"&when={days}d"
    
    feed = feedparser.parse(rss_url)
    
    articles = []
    filtered_count = 0
    
    # Fetch more than needed since some will be filtered out
    for item in feed.entries[:num_articles * 2]:  # Fetch double to account for filtering
        title = item.title
        link = item.link
        published = item.published if hasattr(item, 'published') else "N/A"
        
        # CRITICAL: Validate date before processing
        if published != "N/A" and not is_within_days(published, days):
            filtered_count += 1
            continue  # Skip this article - it's too old
        
        content = fetch_article_content(link)
        
        articles.append({
            "title": title,
            "link": link,
            "published": published,
            "content": content
        })
        
        # Stop once we have enough articles
        if len(articles) >= num_articles:
            break
    
    if filtered_count > 0:
        print(f"   [FILTER] Removed {filtered_count} articles outside {days}-day window")
    
    return articles


def fetch_article_content(url):
    """Fetch full article content by scraping the webpage"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        return content.strip()
    except requests.RequestException:
        return "Content not retrieved."


def analyze_sentiment(text):
    """Analyze sentiment using FinBERT"""
    if not text.strip():
        return 0.0, 'Neutral'

    inputs = finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = finbert_model(**inputs)

    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1).numpy()[0]
    max_index = np.argmax(probabilities)
    sentiment = labels[max_index]
    confidence = float(probabilities[max_index])  # Convert to Python float for JSON

    return confidence, sentiment


def deduplicate_articles(articles):
    """
    Remove duplicate articles based on title similarity.
    Returns list of unique articles and count of duplicates removed.
    """
    unique_articles = []
    seen_titles = set()
    duplicate_count = 0
    
    for article in articles:
        # Normalize title for comparison (lowercase, remove extra spaces)
        normalized_title = ' '.join(article['title'].lower().split())
        
        # Check if we've seen this title
        if normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_articles.append(article)
        else:
            duplicate_count += 1
    
    return unique_articles, duplicate_count


def classify_sentiment(positive_pct):
    """
    Classify market sentiment based on positive percentage
    
    Rules:
    - 48-52%: Neutral
    - 52-60%: Mild Bullish/Bearish
    - 60-75%: Bullish/Bearish
    - >75%: Strong Bullish/Bearish
    """
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
    else:  # positive_pct < 25
        return "STRONG BEARISH", "Very strong negative sentiment"


def summarize_sentiments(articles, asset_name):
    """Summarize sentiment distribution for articles"""
    summary = {
        "Positive": 0,
        "Negative": 0,
        "Neutral": 0
    }
    
    failed_fetch_count = 0

    for idx, article in enumerate(articles, 1):
        # Check if content was retrieved
        content_retrieved = article['content'] != "Content not retrieved."
        if not content_retrieved:
            failed_fetch_count += 1
        
        # Prepare text for analysis
        # Use first 1000 characters of content to avoid truncation issues
        if content_retrieved:
            content_preview = article['content'][:1000] if len(article['content']) > 1000 else article['content']
            text_to_analyze = article['title'] + ". " + content_preview
        else:
            # If content fetch failed, only use title
            text_to_analyze = article['title']
        
        # Analyze sentiment
        confidence, sentiment = analyze_sentiment(text_to_analyze)
        
        article['sentiment'] = sentiment
        article['confidence'] = confidence
        article['text_length'] = len(text_to_analyze)
        article['content_retrieved'] = content_retrieved
        summary[sentiment] += 1
        
        # DEBUG: Print details for articles with very high confidence
        if confidence >= 0.95:
            print(f"\n[!] DEBUG - High confidence classification:")
            print(f"   Article #{idx}: {article['title'][:80]}...")
            print(f"   Sentiment: {sentiment} (Confidence: {confidence:.2f})")
            print(f"   Text length: {article['text_length']} chars")
            print(f"   Content retrieved: {content_retrieved}")

    # NEW: Calculate percentages excluding neutral articles
    directional_total = summary['Positive'] + summary['Negative']
    
    if directional_total > 0:
        positive_pct = (summary['Positive'] / directional_total * 100)
        negative_pct = (summary['Negative'] / directional_total * 100)
    else:
        positive_pct = 0
        negative_pct = 0
    
    # Classify sentiment based on positive percentage
    sentiment_label, sentiment_desc = classify_sentiment(positive_pct)

    print(f"\n[SENTIMENT] {asset_name} - Sentiment Summary:")
    print(f"  Positive:  {summary['Positive']} articles ({positive_pct:.1f}%)")
    print(f"  Negative:  {summary['Negative']} articles ({negative_pct:.1f}%)")
    print(f"  Neutral:   {summary['Neutral']} articles (excluded from %)")
    print(f"  Total directional: {directional_total} articles")
    print(f"  Total all: {len(articles)} articles")
    print(f"  Classification: {sentiment_label} - {sentiment_desc}")
    
    if failed_fetch_count > 0:
        print(f"[!] WARNING: {failed_fetch_count} articles had content fetch failures (using title only)")
    
    # Return both raw counts and calculated percentages
    summary['positive_percent'] = positive_pct
    summary['negative_percent'] = negative_pct
    summary['directional_total'] = directional_total
    summary['sentiment_label'] = sentiment_label
    summary['sentiment_description'] = sentiment_desc
    
    return summary


def generate_report(results):
    """Generate a text-based report"""
    report = []
    report.append("=" * 100)
    report.append("COMPREHENSIVE MARKET SENTIMENT ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 100)
    report.append("")
    report.append("NOTE: Sentiment percentages exclude neutral articles (Positive + Negative only)")
    report.append("")
    
    # Individual Asset Reports
    for asset_key, result in results.items():
        report.append(f"\n{'='*100}")
        report.append(f"[ASSET] {result['asset_name']}")
        report.append(f"{'='*100}")
        report.append("")
        
        # Article Statistics
        report.append(f"Total Articles Analyzed: {result['total_articles']}")
        report.append(f"Duplicates Removed: {result['duplicate_count']}")
        report.append(f"Directional Articles (Positive + Negative): {result['directional_total']}")
        report.append("")
        
        # Sentiment Distribution (Neutral excluded)
        report.append("Sentiment Distribution:")
        report.append(f"  [+] Positive: {result['positive_count']} articles ({result['positive_percent']:.1f}%)")
        report.append(f"  [-] Negative: {result['negative_count']} articles ({result['negative_percent']:.1f}%)")
        report.append(f"  Total Directional: {result['directional_total']} articles (neutral excluded)")
        report.append("")
        
        # Market Outlook using new classification
        report.append(f"Market Sentiment: [{result['sentiment_label']}] - {result['sentiment_description']}")
        report.append("")
        
        # Show top 5 positive and negative headlines
        report.append("[NEWS] Top Positive Headlines:")
        positive_articles = [a for a in result['articles'] if a.get('sentiment') == 'Positive']
        positive_articles.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        for i, article in enumerate(positive_articles[:5], 1):
            conf = article.get('confidence', 0)
            report.append(f"  {i}. {article['title']} (Confidence: {conf:.2f})")
        if not positive_articles:
            report.append("  (No positive articles found)")
        
        report.append("")
        report.append("[NEWS] Top Negative Headlines:")
        negative_articles = [a for a in result['articles'] if a.get('sentiment') == 'Negative']
        negative_articles.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        for i, article in enumerate(negative_articles[:5], 1):
            conf = article.get('confidence', 0)
            report.append(f"  {i}. {article['title']} (Confidence: {conf:.2f})")
        if not negative_articles:
            report.append("  (No negative articles found)")
        
        report.append("")
    
    # Overall Market Summary
    report.append("\n" + "=" * 100)
    report.append("[GLOBAL] OVERALL MARKET SUMMARY")
    report.append("=" * 100)
    
    for asset_key, result in results.items():
        report.append(f"{result['asset_name']:.<50} [{result['sentiment_label']}]")
    
    report.append("")
    report.append("=" * 100)
    report.append("END OF REPORT")
    report.append("=" * 100)
    
    return "\n".join(report)


def main():
    print("Starting Comprehensive Market Sentiment Analysis...")
    print(f"Assets to analyze: {', '.join([ASSETS[k]['name'] for k in ASSETS.keys()])}")
    print(f"Time range: Last 5 days (high relevancy)")
    print(f"Calculation: Percentages exclude neutral articles (Positive + Negative only)")
    print("")
    
    results = {}
    
    # Analyze each asset
    for asset_key, asset_config in ASSETS.items():
        print(f"\n{'='*80}")
        print(f"Analyzing: {asset_config['name']}")
        print(f"{'='*80}")
        
        all_articles = []
        
        # Fetch articles for each query
        for query in asset_config['queries']:
            print(f"Fetching news articles for '{query}'...")
            articles = fetch_news(query, asset_config['articles_per_query'], asset_config.get('days', 5))
            all_articles.extend(articles)
        
        print(f"\n[NEWS] Total articles fetched: {len(all_articles)}")
        
        # Remove duplicates
        unique_articles, duplicate_count = deduplicate_articles(all_articles)
        print(f"[DUPLICATE] Duplicates removed: {duplicate_count}")
        print(f"[OK] Unique articles for analysis: {len(unique_articles)}")
        
        # Analyze sentiment
        sentiment_summary = summarize_sentiments(unique_articles, asset_config['name'])
        
        # Store results
        total = len(unique_articles)
        results[asset_key] = {
            "asset_name": asset_config['name'],
            "asset_key": asset_key,
            "total_articles": total,
            "duplicate_count": duplicate_count,
            "positive_count": sentiment_summary['Positive'],
            "negative_count": sentiment_summary['Negative'],
            "neutral_count": sentiment_summary['Neutral'],
            "directional_total": sentiment_summary['directional_total'],
            "positive_percent": sentiment_summary['positive_percent'],
            "negative_percent": sentiment_summary['negative_percent'],
            "sentiment_label": sentiment_summary['sentiment_label'],
            "sentiment_description": sentiment_summary['sentiment_description'],
            "articles": unique_articles
        }
    
    # Generate and display report
    print("\n\n")
    report = generate_report(results)
    print(report)
    
    # VPS path for reports
    report_dir = "/root/clawd/projects/market-analyzer/sentiment/reports"
    
    # Create directory if it doesn't exist
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Fixed filename (no timestamp) - overwrites old file
    report_filename = "market_sentiment_report.txt"
    report_path = os.path.join(report_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n{'='*80}")
    print(f"[OK] TEXT REPORT saved to:")
    print(f"   {report_path}")
    print(f"{'='*80}")
    
    # Save detailed JSON results
    json_filename = "sentiment_analysis_detailed.json"
    json_path = os.path.join(report_dir, json_filename)
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "calculation_method": "Percentages exclude neutral articles (Positive + Negative only)",
        "assets": {}
    }
    
    for asset_key, result in results.items():
        output["assets"][asset_key] = {
            "name": result['asset_name'],
            "total_articles": result['total_articles'],
            "duplicate_count": result['duplicate_count'],
            "sentiment_counts": {
                "positive": result['positive_count'],
                "negative": result['negative_count'],
                "neutral": result['neutral_count'],
                "directional_total": result['directional_total']
            },
            "sentiment_percentages": {
                "positive": result['positive_percent'],
                "negative": result['negative_percent']
            },
            "sentiment_classification": {
                "label": result['sentiment_label'],
                "description": result['sentiment_description']
            },
            "articles": result['articles']
        }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"[OK] JSON DATA saved to:")
    print(f"   {json_path}")
    print(f"{'='*80}")
    
    # Trigger n8n workflow to send email report
    print("\n[WEBHOOK] Triggering n8n workflow to send email...")
    try:
        # n8n webhook URL (use Docker gateway IP since n8n is in Docker)
        webhook_url = "http://localhost:5678/webhook/market-sentiment"
        
        webhook_response = requests.post(webhook_url, timeout=30)
        
        if webhook_response.status_code == 200:
            print("[OK] Email workflow triggered successfully!")
            print(f"[OK] Response: {webhook_response.text}")
        else:
            print(f"[!] WARNING: Webhook returned status {webhook_response.status_code}")
            print(f"[!] Response: {webhook_response.text}")
    except requests.exceptions.ConnectionError:
        print("[!] ERROR: Cannot connect to n8n webhook.")
        print("[!] Make sure n8n is running and the workflow is activated.")
        print("[!] Check webhook URL: " + webhook_url)
    except Exception as e:
        print(f"[!] ERROR triggering webhook: {str(e)}")
    
    print("\n[DONE] Analysis complete!")
    print(f"\n[FOLDER] Report directory: {report_dir}")
    
    return results


if __name__ == "__main__":
    main()
