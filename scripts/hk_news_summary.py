#!/usr/bin/env python3
"""
HK News Summary Script
Fetches RSS feeds, filters today's news, categorizes, and formats for broadcast.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
import re
import json
import subprocess
import sys

# Configuration
HK_TZ = pytz.timezone('Asia/Hong_Kong')

# =============================================================================
# RSS FEED CONFIGURATION
# =============================================================================
# You can use:
# - Public RSS feeds (SCMP, Reuters)
# - Public RSSHub instance (https://rsshub.app) for Bloomberg, Mingpao
# - Local RSSHub (localhost:1200) if self-hosted
# - Local custom RSS server (localhost:1201) for HKEJ, AAStocks, etc.
#
# To use public RSSHub, change localhost:1200 to rsshub.app
# Example: 'http://localhost:1200/bloomberg' -> 'https://rsshub.app/bloomberg'
# =============================================================================

# Set to True to use public RSSHub instance instead of local
USE_PUBLIC_RSSHUB = False
RSSHUB_BASE = 'https://rsshub.app' if USE_PUBLIC_RSSHUB else 'http://localhost:1200'
LOCAL_RSS_BASE = 'http://localhost:1201'  # Custom RSS server for HK sources

RSS_FEEDS = {
    # Public RSS (always available)
    'SCMP Business': 'https://www.scmp.com/rss/91/feed/',
    'Reuters': 'https://www.reuters.com/rssFeed/businessNews',
    
    # RSSHub sources (public or local)
    'Mingpao': f'{RSSHUB_BASE}/mingpao/pns/s00004',
    'Bloomberg': f'{RSSHUB_BASE}/bloomberg',
    
    # Local RSS Server sources (requires localhost:1201)
    # Comment out if not available
    'HKEJ Stock': f'{LOCAL_RSS_BASE}/hkej/stock',
    'HKEJ China': f'{LOCAL_RSS_BASE}/hkej/china',
    'AAStocks': f'{LOCAL_RSS_BASE}/aastocks/news',
    'Now Finance': f'{LOCAL_RSS_BASE}/nowfinance',
    'Yahoo Finance HK': f'{LOCAL_RSS_BASE}/yahoo/finance-hk',
    'HK01 Finance': f'{LOCAL_RSS_BASE}/hk01/finance',
}

# Categories and keywords (order matters - first match wins)
CATEGORIES = {
    '大市走勢': ['恒指', '恒生指數', 'HSI', '港股走勢', 'A股', '滬指', '深成指', '科指', '夜期', 'ADR', 'Asian Stocks', 'Hang Seng', '大市'],
    '新股/IPO': ['新股', 'IPO', '招股', '首掛', '暗盤', '中籤', 'listing', 'debut', 'Hong Kong Listing', 'HK Offering'],
    '盈喜/盈警': ['盈喜', '盈警', '預減', '預增', '純利預', 'profit warning', 'earnings'],
    '配股/集資': ['配股', '可轉債', '供股', '折讓', '籌逾', 'placement', 'convertible bond'],
    '異動股': ['異動股', '曾彈', '曾升近', '曾挫', '急升', '飆升', '暴跌', '插水'],
    '大行報告': ['大行', '摩通', '高盛', '花旗', '滙證', '美銀', '中金', '野村', 'JPMorgan', 'Goldman', 'Citi', 'HSBC', '目標價', '評級'],
    'AI/科技': ['AI丨', '人工智能', '機械人', 'robot', '晶片', 'chip', '半導體', 'semiconductor', '智譜', 'OpenAI', 'xAI', 'SpaceX', '特斯拉', '小米', 'Tesla', 'Hynix', 'Samsung', '騰訊元寶', '千問'],
    '商品/外匯': ['金價', '黃金', 'gold', '油價', 'oil', '銅價', 'copper', '外匯', '美元', '澳元', '比特幣', 'Bitcoin'],
    '中國經濟': ['PBOC', '人行', 'PMI', '習近平', 'Xi Jinping', '發改委', '央行', 'China GDP', '中國經濟', 'China Grid', 'China Solar'],
    '國際': ['Trump', '特朗普', 'Fed', '聯儲局', '印度', 'India', 'Australia', '澳洲加息'],
}

def clean_title(title):
    """Clean up title - remove timestamps, descriptions, etc."""
    # Remove common suffixes
    title = re.sub(r'【.*?】.*$', '', title)  # Remove 【本地】 and everything after
    title = re.sub(r'\s*\d+小時\d*分鐘?前\s*$', '', title)  # Remove "X小時前"
    title = re.sub(r'\s*\(\d+\)\s*$', '', title)  # Remove stock codes at end
    title = re.sub(r'AASTOCKS新聞$', '', title)
    title = re.sub(r'格隆匯新聞$', '', title)
    title = re.sub(r'更多$', '', title)
    title = title.strip()
    # Truncate if still too long
    if len(title) > 80:
        title = title[:77] + '...'
    return title

def clean_html(text):
    """Remove HTML tags and clean text"""
    from html import unescape
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_summary(entry, max_len=150):
    """Extract summary from RSS entry"""
    desc = entry.get('description', entry.get('summary', ''))
    if not desc:
        return ''
    clean = clean_html(desc)
    title = entry.get('title', '')
    # Skip if description is same as title
    if clean == title or len(clean) < 20:
        return ''
    # Truncate
    if len(clean) > max_len:
        clean = clean[:max_len] + '...'
    return clean

def fetch_feed(name, url):
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:30]:  # Limit to 30 per source
            title = entry.get('title', '').strip()
            title = clean_title(title)
            if not title or len(title) < 5:
                continue
            link = entry.get('link', '')
            pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
            summary = extract_summary(entry)
            
            if pub_date:
                pub_dt = datetime(*pub_date[:6], tzinfo=pytz.UTC)
            else:
                pub_dt = datetime.now(pytz.UTC)
            
            articles.append({
                'title': title,
                'link': link,
                'pub_date': pub_dt,
                'source': name,
                'summary': summary
            })
        return articles
    except Exception as e:
        print(f"Error fetching {name}: {e}", file=sys.stderr)
        return []

def is_today(dt, now_hk):
    """Check if datetime is today in HK timezone"""
    dt_hk = dt.astimezone(HK_TZ)
    return dt_hk.date() == now_hk.date()

def categorize(title):
    """Categorize article by keywords"""
    title_lower = title.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in title_lower:
                return cat
    return '其他'

def deduplicate(articles):
    """Remove duplicate articles by normalized title"""
    seen = set()
    unique = []
    for a in articles:
        # Normalize title for comparison
        norm = re.sub(r'[\s\-\|｜:：]+', '', a['title'].lower())
        norm = norm[:50]  # Compare first 50 chars
        if norm not in seen:
            seen.add(norm)
            unique.append(a)
    return unique

def is_hk_related(title):
    """Check if article is HK/China/Asia market related"""
    hk_keywords = [
        '港', 'HK', 'Hong Kong', '恒', 'Hang Seng', '中國', 'China', 'Chinese',
        '阿里', 'Alibaba', '騰訊', 'Tencent', '小米', 'Xiaomi', '比亞迪', 'BYD',
        '內地', 'mainland', 'PBOC', 'yuan', '人民幣', 'Asia', '亞洲',
        'Shanghai', '上海', 'Shenzhen', '深圳', 'A-share', 'A股',
        'Samsung', 'Hynix', 'Taiwan', '台灣', 'Korea', '韓國',
        'Eastroc', '東鵬', 'Montage', 'SCMP', 'Xi', '習'
    ]
    return any(kw.lower() in title.lower() for kw in hk_keywords)

def format_telegram(categorized, now_hk):
    """Format for Telegram (Markdown)"""
    lines = [
        f"📰 **港股新聞摘要**",
        f"📅 {now_hk.strftime('%Y-%m-%d %H:%M')} HKT",
        "",
        "━━━━━━━━━━━━━━━"
    ]
    
    # Priority order for categories
    priority = ['大市走勢', '新股/IPO', '異動股', '盈喜/盈警', '配股/集資', 
                '中國經濟', 'AI/科技', '大行報告', '商品/外匯', '國際', '其他']
    
    cat_emoji = {
        '大市走勢': '📊', '新股/IPO': '🆕', '異動股': '📈📉', '盈喜/盈警': '📊',
        '配股/集資': '💰', '中國經濟': '🇨🇳', 'AI/科技': '🤖', '大行報告': '📋',
        '商品/外匯': '💹', '國際': '🌍', '其他': '📌'
    }
    
    for cat in priority:
        if cat in categorized and categorized[cat]:
            emoji = cat_emoji.get(cat, '📌')
            lines.append("")
            lines.append(f"{emoji} **{cat}**")
            lines.append("")
            for i, a in enumerate(categorized[cat][:6]):  # Max 6 per category
                lines.append(f"• {a['title']} [{a['source']}]")
                # Show summary for first 2 articles in important categories
                if i < 2 and a.get('summary') and cat in ['大市走勢', '中國經濟', '大行報告']:
                    lines.append(f"  ↳ {a['summary']}")
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("🐷 Oracle | 來源：信報、明報、AAStocks、Now、Yahoo、Bloomberg、Reuters、SCMP")
    
    return '\n'.join(lines)

def format_whatsapp(categorized, now_hk):
    """Format for WhatsApp (cleaner, shorter source names)"""
    # Shorten source names
    source_map = {
        'HKEJ Stock': 'HKEJ', 'HKEJ China': 'HKEJ', 'AAStocks': 'AAStocks',
        'Now Finance': 'Now', 'Yahoo Finance HK': 'Yahoo', 'HK01 Finance': 'HK01',
        'Mingpao': 'Mingpao', 'Bloomberg': 'Bloomberg', 'Reuters': 'Reuters',
        'SCMP Business': 'SCMP'
    }
    
    lines = [
        f"📰 *港股新聞摘要*",
        f"📅 {now_hk.strftime('%Y-%m-%d %H:%M')} HKT",
        "",
        "━━━━━━━━━━━━━━━"
    ]
    
    priority = ['大市走勢', '新股/IPO', '異動股', '盈喜/盈警', '配股/集資',
                '中國經濟', 'AI/科技', '大行報告', '商品/外匯', '國際']
    
    cat_emoji = {
        '大市走勢': '📊', '新股/IPO': '🆕', '異動股': '📈📉', '盈喜/盈警': '📊',
        '配股/集資': '💰', '中國經濟': '🇨🇳', 'AI/科技': '🤖', '大行報告': '📋',
        '商品/外匯': '💹', '國際': '🌍'
    }
    
    for cat in priority:
        if cat in categorized and categorized[cat]:
            emoji = cat_emoji.get(cat, '📌')
            lines.append("")
            lines.append(f"{emoji} *{cat}*")
            for a in categorized[cat][:4]:  # Max 4 per category for WhatsApp
                src = source_map.get(a['source'], a['source'])
                lines.append(f"• {a['title']} [{src}]")
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("🐷 Oracle | 信報/明報/AAStocks/Now/Yahoo/Bloomberg/Reuters/SCMP")
    
    return '\n'.join(lines)

def send_telegram(message, chat_id):
    """Send via clawdbot message tool (called externally)"""
    print(f"[TELEGRAM:{chat_id}]")
    print(message)
    print("[/TELEGRAM]")

def send_whatsapp(message, jid):
    """Send via wacli"""
    try:
        result = subprocess.run(
            ['wacli', 'send', 'text', '--to', jid, '--message', message],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"✅ WhatsApp sent to {jid}")
        else:
            print(f"❌ WhatsApp failed: {result.stderr}")
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")

def main():
    now_hk = datetime.now(HK_TZ)
    print(f"🕐 HK News Summary - {now_hk.strftime('%Y-%m-%d %H:%M')} HKT")
    print("=" * 50)
    
    # Fetch all feeds
    all_articles = []
    for name, url in RSS_FEEDS.items():
        print(f"📥 Fetching {name}...", end=' ')
        articles = fetch_feed(name, url)
        print(f"{len(articles)} articles")
        all_articles.extend(articles)
    
    print(f"\n📊 Total fetched: {len(all_articles)}")
    
    # Filter today's news
    today_articles = [a for a in all_articles if is_today(a['pub_date'], now_hk)]
    print(f"📅 Today's articles: {len(today_articles)}")
    
    # Filter HK-related for international sources
    filtered = []
    for a in today_articles:
        if a['source'] in ['Bloomberg', 'Reuters', 'SCMP Business']:
            if is_hk_related(a['title']):
                filtered.append(a)
        else:
            filtered.append(a)
    
    print(f"🔍 HK-related: {len(filtered)}")
    
    # Deduplicate
    unique = deduplicate(filtered)
    print(f"✂️ After dedup: {len(unique)}")
    
    # Sort by date (newest first)
    unique.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # Categorize
    categorized = defaultdict(list)
    for a in unique:
        cat = categorize(a['title'])
        categorized[cat].append(a)
    
    print("\n📁 Categories:")
    for cat, articles in sorted(categorized.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(articles)}")
    
    # Format messages
    telegram_msg = format_telegram(categorized, now_hk)
    whatsapp_msg = format_whatsapp(categorized, now_hk)
    
    # Output mode
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == 'telegram':
            print("\n" + "=" * 50)
            print(telegram_msg)
        elif mode == 'whatsapp':
            print("\n" + "=" * 50)
            print(whatsapp_msg)
        elif mode == 'broadcast':
            # Send to all destinations
            print("\n📤 Broadcasting...")
            send_whatsapp(whatsapp_msg, "85269774866@s.whatsapp.net")  # Jason
            send_whatsapp(whatsapp_msg, "85262982502-1545129405@g.us")  # DIM INV
            send_whatsapp(whatsapp_msg, "85292890363-1425994418@g.us")  # Pure Investments
            # Telegram will be sent by Oracle after reading output
            print("\n[TELEGRAM_MSG]")
            print(telegram_msg)
            print("[/TELEGRAM_MSG]")
        elif mode == 'json':
            output = {
                'timestamp': now_hk.isoformat(),
                'count': len(unique),
                'categories': {k: [{'title': a['title'], 'source': a['source']} for a in v] for k, v in categorized.items()},
                'telegram': telegram_msg,
                'whatsapp': whatsapp_msg
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Default: print both formats
        print("\n" + "=" * 50)
        print("TELEGRAM FORMAT:")
        print(telegram_msg)
        print("\n" + "=" * 50)
        print("WHATSAPP FORMAT:")
        print(whatsapp_msg)

if __name__ == '__main__':
    main()
