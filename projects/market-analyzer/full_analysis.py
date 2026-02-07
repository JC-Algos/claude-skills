#!/usr/bin/env python3
"""
完整股票分析 - Full Stock Analysis
Combines: Technical Analysis + TradingView Chart + Perplexity News
"""

import os
import sys
import subprocess
import json
from datetime import datetime

# Add module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ta_analyzer import MarketAnalyzer

def capture_chart(symbol: str, market: str, period: str = '2y') -> str:
    """Generate candlestick chart using Python (mplfinance)"""
    try:
        from generate_chart import generate_chart as gen_chart
        return gen_chart(symbol, market, period)
    except Exception as e:
        print(f"❌ Chart generation failed: {e}")
        return None

def get_perplexity_news(symbol: str, market: str) -> dict:
    """Get news from Perplexity"""
    if not os.environ.get('PERPLEXITY_API_KEY'):
        return {'success': False, 'error': 'PERPLEXITY_API_KEY not set'}
    
    try:
        from perplexity_client import PerplexityClient
        client = PerplexityClient()
        return client.search_news(symbol, market)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_to_telegram(message: str, media: str = None, chat_id: str = '1016466977') -> bool:
    """Send message/media to Telegram"""
    try:
        cmd = [
            '/usr/bin/clawdbot', 'message', 'send',
            '--channel', 'telegram',
            '--target', chat_id,
            '--message', message
        ]
        
        if media and os.path.exists(media):
            cmd.extend(['--media', media])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
        return False

def run_full_analysis(ticker: str, market: str = 'US', 
                      include_chart: bool = True,
                      include_news: bool = True,
                      chat_id: str = '1016466977'):
    """
    Run complete analysis pipeline
    
    Args:
        ticker: Stock symbol (e.g., "0700", "AAPL")
        market: Market (HK, US)
        include_chart: Whether to capture TradingView chart
        include_news: Whether to include Perplexity news
        chat_id: Telegram chat ID to send results
    """
    print(f"🚀 Starting full analysis for {ticker} ({market})...")
    
    # 1. Technical Analysis
    print("\n📈 Running Technical Analysis...")
    analyzer = MarketAnalyzer()
    analysis = analyzer.full_analysis(ticker, market)
    ta_report = analyzer.generate_report_zh(analysis)
    
    # 2. Perplexity News
    news_report = ""
    if include_news:
        print("\n📰 Fetching news from Perplexity...")
        news = get_perplexity_news(ticker, market)
        if news.get('success'):
            news_report = f"""

📰 **新聞面分析 (Perplexity AI)**
━━━━━━━━━━━━━━━━━━━━━━

{news.get('content', 'N/A')}
"""
            if news.get('citations'):
                news_report += "\n📎 資料來源:\n"
                for cite in news.get('citations', [])[:5]:
                    news_report += f"• {cite}\n"
        else:
            news_report = f"\n⚠️ 新聞獲取: {news.get('error', 'Failed')}\n"
    
    # 3. Combine reports
    full_report = ta_report + news_report
    
    # 4. Capture chart (using Yahoo Finance)
    chart_file = None
    if include_chart:
        chart_file = capture_chart(ticker, market, '1y')
    
    # 5. Send to Telegram
    print("\n📤 Sending to Telegram...")
    
    # Send chart first if available
    if chart_file:
        chart_msg = f"📊 {ticker} ({market}) 圖表 - Yahoo Finance"
        send_to_telegram(chart_msg, chart_file, chat_id)
    
    # Send report
    sent = send_to_telegram(full_report, chat_id=chat_id)
    
    print(f"\n{'✅' if sent else '❌'} Analysis complete!")
    
    return {
        'success': analysis.get('success', False),
        'sent': sent,
        'chart': chart_file,
        'ticker': ticker,
        'market': market
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Full Stock Analysis')
    parser.add_argument('ticker', help='Stock ticker (e.g., 0700, AAPL)')
    parser.add_argument('--market', '-m', default='HK', 
                       help='Market: HK or US (default: HK)')
    parser.add_argument('--no-chart', action='store_true',
                       help='Skip chart capture')
    parser.add_argument('--no-news', action='store_true',
                       help='Skip Perplexity news')
    parser.add_argument('--chat-id', default='1016466977',
                       help='Telegram chat ID')
    
    args = parser.parse_args()
    
    result = run_full_analysis(
        ticker=args.ticker,
        market=args.market,
        include_chart=not args.no_chart,
        include_news=not args.no_news,
        chat_id=args.chat_id
    )
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
