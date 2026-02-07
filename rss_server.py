#!/usr/bin/env python3
"""
Custom RSS Feed Server
======================
Generates RSS feeds from sites that don't offer them.
Port: 1201
"""

from flask import Flask, Response, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import hashlib

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User agent for scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def create_rss_feed(title, link, description, items):
    """Create RSS 2.0 XML feed"""
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'link').text = link
    ET.SubElement(channel, 'description').text = description
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    ET.SubElement(channel, 'language').text = 'zh-hk'
    
    for item in items:
        item_elem = ET.SubElement(channel, 'item')
        ET.SubElement(item_elem, 'title').text = item.get('title', '')
        ET.SubElement(item_elem, 'link').text = item.get('link', '')
        ET.SubElement(item_elem, 'description').text = item.get('description', '')
        if item.get('pubDate'):
            ET.SubElement(item_elem, 'pubDate').text = item['pubDate']
        # Generate guid from link
        guid = hashlib.md5(item.get('link', '').encode()).hexdigest()
        ET.SubElement(item_elem, 'guid').text = guid
    
    # Pretty print
    xml_str = ET.tostring(rss, encoding='unicode')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

# =============================================================================
# HKEJ (信報) Stock News
# =============================================================================

@app.route('/hkej/stock')
def hkej_stock():
    """HKEJ Stock News RSS Feed"""
    try:
        url = 'https://www.hkej.com/instantnews/stock'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # Find news articles
        articles = soup.select('div.content_list_main a, article a, .news-item a, h3 a, .article-title a')
        
        seen_links = set()
        for article in articles:
            title = article.get_text(strip=True)
            href = article.get('href', '')
            
            if not title or len(title) < 5:
                continue
            if not href:
                continue
                
            # Build full URL
            if href.startswith('/'):
                link = f'https://www.hkej.com{href}'
            elif not href.startswith('http'):
                link = f'https://www.hkej.com/{href}'
            else:
                link = href
            
            # Skip duplicates
            if link in seen_links:
                continue
            seen_links.add(link)
            
            # Skip non-article links
            if '/article/' not in link and '/instantnews/' not in link:
                continue
            
            items.append({
                'title': title,
                'link': link,
                'description': title,
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        rss = create_rss_feed(
            title='信報即時新聞 - 港股直擊',
            link='https://www.hkej.com/instantnews/stock',
            description='Hong Kong Economic Journal - Stock News',
            items=items
        )
        
        logger.info(f"HKEJ Stock: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"HKEJ Stock error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# HKEJ (信報) Property News
# =============================================================================

@app.route('/hkej/property')
def hkej_property():
    """HKEJ Property News RSS Feed"""
    try:
        url = 'https://www.hkej.com/instantnews/property'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        articles = soup.select('div.content_list_main a, article a, .news-item a, h3 a, .article-title a')
        
        seen_links = set()
        for article in articles:
            title = article.get_text(strip=True)
            href = article.get('href', '')
            
            if not title or len(title) < 5:
                continue
            if not href:
                continue
                
            if href.startswith('/'):
                link = f'https://www.hkej.com{href}'
            elif not href.startswith('http'):
                link = f'https://www.hkej.com/{href}'
            else:
                link = href
            
            if link in seen_links:
                continue
            seen_links.add(link)
            
            if '/article/' not in link and '/instantnews/' not in link:
                continue
            
            items.append({
                'title': title,
                'link': link,
                'description': title,
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        rss = create_rss_feed(
            title='信報即時新聞 - 地產',
            link='https://www.hkej.com/instantnews/property',
            description='Hong Kong Economic Journal - Property News',
            items=items
        )
        
        logger.info(f"HKEJ Property: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"HKEJ Property error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# HKEJ (信報) International News
# =============================================================================

@app.route('/hkej/international')
def hkej_international():
    """HKEJ International News RSS Feed"""
    try:
        url = 'https://www.hkej.com/instantnews/international'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        articles = soup.select('div.content_list_main a, article a, .news-item a, h3 a, .article-title a')
        
        seen_links = set()
        for article in articles:
            title = article.get_text(strip=True)
            href = article.get('href', '')
            
            if not title or len(title) < 5:
                continue
            if not href:
                continue
                
            if href.startswith('/'):
                link = f'https://www.hkej.com{href}'
            elif not href.startswith('http'):
                link = f'https://www.hkej.com/{href}'
            else:
                link = href
            
            if link in seen_links:
                continue
            seen_links.add(link)
            
            if '/article/' not in link and '/instantnews/' not in link:
                continue
            
            items.append({
                'title': title,
                'link': link,
                'description': title,
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        rss = create_rss_feed(
            title='信報即時新聞 - 國際',
            link='https://www.hkej.com/instantnews/international',
            description='Hong Kong Economic Journal - International News',
            items=items
        )
        
        logger.info(f"HKEJ International: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"HKEJ International error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# Generic HKEJ Section
# =============================================================================

@app.route('/hkej/<section>')
def hkej_section(section):
    """Generic HKEJ section RSS Feed"""
    valid_sections = ['stock', 'property', 'international', 'china', 'hongkong', 'current']
    
    if section not in valid_sections:
        return Response(f"Invalid section. Valid: {valid_sections}", status=400)
    
    try:
        url = f'https://www.hkej.com/instantnews/{section}'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        articles = soup.select('div.content_list_main a, article a, .news-item a, h3 a, .article-title a')
        
        seen_links = set()
        for article in articles:
            title = article.get_text(strip=True)
            href = article.get('href', '')
            
            if not title or len(title) < 5:
                continue
            if not href:
                continue
                
            if href.startswith('/'):
                link = f'https://www.hkej.com{href}'
            elif not href.startswith('http'):
                link = f'https://www.hkej.com/{href}'
            else:
                link = href
            
            if link in seen_links:
                continue
            seen_links.add(link)
            
            if '/article/' not in link and '/instantnews/' not in link:
                continue
            
            items.append({
                'title': title,
                'link': link,
                'description': title,
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        section_names = {
            'stock': '港股直擊',
            'property': '地產',
            'international': '國際',
            'china': '中國',
            'hongkong': '香港',
            'current': '時事'
        }
        
        rss = create_rss_feed(
            title=f'信報即時新聞 - {section_names.get(section, section)}',
            link=url,
            description=f'Hong Kong Economic Journal - {section.title()} News',
            items=items
        )
        
        logger.info(f"HKEJ {section}: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"HKEJ {section} error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# AAStocks News
# =============================================================================

@app.route('/aastocks/news')
def aastocks_news():
    """AAStocks News RSS Feed"""
    try:
        url = 'http://www.aastocks.com/tc/stocks/news/aafn-con/NOW.0/all/1'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # Find news items - AAStocks uses specific classes
        news_items = soup.select('div[class*="newshead"], div[class*="newscontent"], a[class*="news"]')
        
        # Alternative: find all links with news URLs
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            if not title or len(title) < 10:
                continue
            
            # Filter for news links
            if '/news/' not in href and '/analyse/' not in href:
                continue
            
            # Build full URL
            if href.startswith('/'):
                full_link = f'http://www.aastocks.com{href}'
            elif not href.startswith('http'):
                full_link = f'http://www.aastocks.com/{href}'
            else:
                full_link = href
            
            # Skip duplicates and non-news
            if any(x in href.lower() for x in ['javascript', '#', 'login']):
                continue
            
            items.append({
                'title': title[:200],
                'link': full_link,
                'description': title[:200],
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        # Deduplicate by title
        seen = set()
        unique_items = []
        for item in items:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_items.append(item)
        
        rss = create_rss_feed(
            title='AAStocks 財經新聞',
            link='http://www.aastocks.com/tc/stocks/news/',
            description='AAStocks Financial News',
            items=unique_items
        )
        
        logger.info(f"AAStocks News: Generated {len(unique_items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"AAStocks News error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# Yahoo Finance HK
# =============================================================================

@app.route('/yahoo/finance-hk')
def yahoo_finance_hk():
    """Yahoo Finance HK News RSS Feed"""
    try:
        url = 'https://hk.finance.yahoo.com/news/'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # Find news articles - Yahoo uses various link patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            if not title or len(title) < 10:
                continue
            
            # Filter for news links
            if '/news/' not in href and '/m/' not in href:
                continue
            if any(x in href.lower() for x in ['javascript', '#', 'login', 'signup']):
                continue
            
            # Build full URL
            if href.startswith('/'):
                full_link = f'https://hk.finance.yahoo.com{href}'
            elif not href.startswith('http'):
                continue
            else:
                full_link = href
            
            items.append({
                'title': title[:200],
                'link': full_link,
                'description': title[:200],
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_items.append(item)
        
        rss = create_rss_feed(
            title='Yahoo 財經香港',
            link='https://hk.finance.yahoo.com/news/',
            description='Yahoo Finance Hong Kong News',
            items=unique_items
        )
        
        logger.info(f"Yahoo Finance HK: Generated {len(unique_items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"Yahoo Finance HK error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# RTHK News
# =============================================================================

@app.route('/rthk/<section>')
def rthk_news(section):
    """RTHK News RSS Feed"""
    section_map = {
        'local': ('本地', 'clocal'),
        'finance': ('財經', 'cfinance'),
        'china': ('中國', 'cgreaterchina'),
        'international': ('國際', 'cinternational'),
    }
    
    if section not in section_map:
        return Response(f"Invalid section. Valid: {list(section_map.keys())}", status=400)
    
    try:
        section_name, url_section = section_map[section]
        url = f'https://news.rthk.hk/rthk/ch/component/k2/1755841-20250131.htm?spTabChangeable=0&archive=true&section={url_section}'
        
        # Try the API endpoint instead
        api_url = f'https://news.rthk.hk/rthk/webpageCache/services/loadModuleBy498.php?lang=zh-TW&newsType={url_section}'
        
        response = requests.get(api_url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        items = []
        
        try:
            data = response.json()
            for news_item in data.get('items', [])[:30]:
                items.append({
                    'title': news_item.get('title', ''),
                    'link': f"https://news.rthk.hk{news_item.get('href', '')}",
                    'description': news_item.get('summary', news_item.get('title', '')),
                    'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                })
        except:
            # Fallback to HTML scraping
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if not title or len(title) < 5:
                    continue
                if not href or '/rthk/' not in href:
                    continue
                
                if href.startswith('/'):
                    full_link = f'https://news.rthk.hk{href}'
                else:
                    full_link = href
                
                items.append({
                    'title': title,
                    'link': full_link,
                    'description': title,
                    'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                })
                
                if len(items) >= 30:
                    break
        
        rss = create_rss_feed(
            title=f'香港電台新聞 - {section_name}',
            link='https://news.rthk.hk/',
            description=f'RTHK News - {section.title()}',
            items=items
        )
        
        logger.info(f"RTHK {section}: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"RTHK {section} error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# Sing Tao (星島)
# =============================================================================

@app.route('/singtao/<section>')
def singtao_news(section):
    """Sing Tao News RSS Feed"""
    section_map = {
        'hongkong': ('港聞', 'hongkong'),
        'finance': ('財經', 'finance'),
        'china': ('中國', 'china'),
        'international': ('國際', 'international'),
    }
    
    if section not in section_map:
        return Response(f"Invalid section. Valid: {list(section_map.keys())}", status=400)
    
    try:
        section_name, url_section = section_map[section]
        url = f'https://std.stheadline.com/realtime/{url_section}'
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # Find news articles
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not title or len(title) < 8:
                continue
            if '/realtime/' not in href and '/article/' not in href:
                continue
            if any(x in href.lower() for x in ['javascript', '#']):
                continue
            
            if href.startswith('/'):
                full_link = f'https://std.stheadline.com{href}'
            elif not href.startswith('http'):
                continue
            else:
                full_link = href
            
            items.append({
                'title': title[:200],
                'link': full_link,
                'description': title[:200],
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_items.append(item)
        
        rss = create_rss_feed(
            title=f'星島日報 - {section_name}',
            link=url,
            description=f'Sing Tao Daily - {section.title()} News',
            items=unique_items
        )
        
        logger.info(f"Sing Tao {section}: Generated {len(unique_items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"Sing Tao {section} error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# HK01 (via API)
# =============================================================================

@app.route('/hk01/<section>')
def hk01_news(section):
    """HK01 News RSS Feed via API"""
    section_map = {
        'finance': ('財經', '5'),
        'hongkong': ('港聞', '1'),
        'china': ('中國', '4'),
        'tech': ('數碼生活', '35'),
        'hot': ('熱門', 'hot'),
        'instant': ('即時', 'latest'),
    }
    
    if section not in section_map:
        return Response(f"Invalid section. Valid: {list(section_map.keys())}", status=400)
    
    try:
        section_name, zone_id = section_map[section]
        items = []
        
        # Use HK01 API
        if section == 'hot':
            api_url = 'https://web-data.api.hk01.com/v2/feed/hot?offset=0&limit=30'
        elif section == 'instant':
            api_url = 'https://web-data.api.hk01.com/v2/feed/category/latest?offset=0&limit=30'
        else:
            api_url = f'https://web-data.api.hk01.com/v2/feed/zone/{zone_id}?offset=0&limit=30'
        
        response = requests.get(api_url, headers=HEADERS, timeout=30)
        data = response.json()
        
        for article in data.get('items', []):
            article_data = article.get('data', {})
            title = article_data.get('title', '')
            article_id = article_data.get('articleId', '')
            
            if not title or not article_id:
                continue
            
            items.append({
                'title': title,
                'link': f'https://www.hk01.com/article/{article_id}',
                'description': article_data.get('description', title),
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
        
        rss = create_rss_feed(
            title=f'香港01 - {section_name}',
            link=f'https://www.hk01.com/zone/{zone_id}' if zone_id.isdigit() else f'https://www.hk01.com/{zone_id}',
            description=f'HK01 - {section.title()} News',
            items=items
        )
        
        logger.info(f"HK01 {section}: Generated {len(items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"HK01 {section} error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# Now Finance (Now財經)
# =============================================================================

@app.route('/nowfinance')
def now_finance():
    """Now Finance News RSS Feed"""
    try:
        url = 'https://finance.now.com/news'
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not title or len(title) < 8:
                continue
            if '/news/' not in href:
                continue
            
            if href.startswith('/'):
                full_link = f'https://finance.now.com{href}'
            elif not href.startswith('http'):
                continue
            else:
                full_link = href
            
            items.append({
                'title': title[:200],
                'link': full_link,
                'description': title[:200],
                'pubDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            })
            
            if len(items) >= 30:
                break
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_items.append(item)
        
        rss = create_rss_feed(
            title='Now 財經',
            link='https://finance.now.com/news',
            description='Now Finance News',
            items=unique_items
        )
        
        logger.info(f"Now Finance: Generated {len(unique_items)} items")
        return Response(rss, mimetype='application/rss+xml')
        
    except Exception as e:
        logger.error(f"Now Finance error: {e}")
        return Response(f"Error: {e}", status=500)

# =============================================================================
# Status & Index
# =============================================================================

@app.route('/')
def index():
    """List available feeds"""
    feeds = {
        'HKEJ Stock': '/hkej/stock',
        'HKEJ Property': '/hkej/property',
        'HKEJ International': '/hkej/international',
        'HKEJ China': '/hkej/china',
        'HKEJ Hong Kong': '/hkej/hongkong',
        'AAStocks News': '/aastocks/news',
        'Yahoo Finance HK': '/yahoo/finance-hk',
        'RTHK Local': '/rthk/local',
        'RTHK Finance': '/rthk/finance',
        'Sing Tao Hong Kong': '/singtao/hongkong',
        'Sing Tao Finance': '/singtao/finance',
        'HK01 Finance': '/hk01/finance',
        'HK01 Hong Kong': '/hk01/hongkong',
        'HK01 Hot': '/hk01/hot',
        'Now Finance': '/nowfinance',
    }
    
    html = '<h1>Custom RSS Server</h1><ul>'
    for name, path in feeds.items():
        html += f'<li><a href="{path}">{name}</a> - <code>http://localhost:1201{path}</code></li>'
    html += '</ul>'
    
    return html

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}

# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1201, debug=False)
