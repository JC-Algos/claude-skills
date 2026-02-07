#!/usr/bin/env python3
"""
Perplexity AI Client for Stock News Research
Uses Perplexity's API for real-time market news and analysis
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

class PerplexityClient:
    """Client for Perplexity AI API"""
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not set. Set environment variable or pass api_key.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search_news(self, symbol: str, market: str = 'HK', 
                    language: str = 'zh-TW', days: int = 3) -> Dict:
        """
        Search for recent news about a stock
        
        Args:
            symbol: Stock symbol (e.g., "0700", "AAPL")
            market: Market (HK, US)
            language: Response language
            days: Days of news to search
            
        Returns:
            Dict with news summary and sentiment
        """
        # Build search query
        if market.upper() == 'HK':
            stock_name = self._get_hk_stock_name(symbol)
            query = f"""
            搜尋過去{days}天關於 {symbol}.HK {stock_name} 的最新新聞和市場分析。
            包括：
            1. 重要公司公告
            2. 財報或業績相關
            3. 行業新聞
            4. 分析師評級變化
            5. 市場情緒
            
            請用繁體中文總結關鍵要點。
            """
        else:
            query = f"""
            Search for the latest news and market analysis about {symbol} stock in the past {days} days.
            Include:
            1. Important company announcements
            2. Earnings or financial results
            3. Industry news
            4. Analyst rating changes
            5. Market sentiment
            
            Summarize key points in Traditional Chinese.
            """
        
        return self._chat_completion(query)
    
    def _chat_completion(self, query: str, model: str = "llama-3.1-sonar-large-128k-online") -> Dict:
        """
        Call Perplexity chat completion API
        
        Args:
            query: Search query
            model: Model to use (sonar models have online search)
        """
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位專業的股票分析師助手。請提供準確、客觀的市場資訊。使用繁體中文回覆。"
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["reuters.com", "bloomberg.com", "scmp.com", "hk01.com", "finance.yahoo.com"],
                "search_recency_filter": "week"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            return {
                "success": True,
                "content": content,
                "citations": citations,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_hk_stock_name(self, symbol: str) -> str:
        """Get Chinese name for HK stocks"""
        # Common HK stock names
        names = {
            "0700": "騰訊控股",
            "9988": "阿里巴巴",
            "9618": "京東集團",
            "3690": "美團",
            "1810": "小米集團",
            "0005": "匯豐控股",
            "0941": "中國移動",
            "2318": "中國平安",
            "0388": "香港交易所",
            "0027": "銀河娛樂",
            "1299": "友邦保險",
            "0001": "長和",
            "0016": "新鴻基地產",
            "0011": "恒生銀行",
            "0883": "中國海洋石油",
            "2020": "安踏體育",
            "9999": "網易",
            "1211": "比亞迪",
            "0981": "中芯國際",
            "0175": "吉利汽車"
        }
        return names.get(symbol.zfill(4), "")
    
    def analyze_sentiment(self, news_content: str) -> Dict:
        """
        Analyze sentiment from news content
        
        Returns sentiment score and classification
        """
        query = f"""
        基於以下新聞內容，分析市場情緒：

        {news_content[:2000]}

        請評估：
        1. 整體情緒：看漲(BULLISH) / 看跌(BEARISH) / 中性(NEUTRAL)
        2. 信心度：0-100%
        3. 關鍵影響因素
        4. 潛在風險

        以JSON格式回覆：
        {{
            "sentiment": "BULLISH/BEARISH/NEUTRAL",
            "confidence": 0-100,
            "key_factors": ["因素1", "因素2"],
            "risks": ["風險1", "風險2"]
        }}
        """
        
        result = self._chat_completion(query, model="llama-3.1-sonar-small-128k-online")
        
        if result.get("success"):
            try:
                # Try to parse JSON from response
                content = result["content"]
                # Extract JSON if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                sentiment_data = json.loads(content.strip())
                return {
                    "success": True,
                    **sentiment_data
                }
            except:
                return {
                    "success": True,
                    "sentiment": "NEUTRAL",
                    "confidence": 50,
                    "raw_content": result["content"]
                }
        
        return result


def get_stock_news(symbol: str, market: str = 'HK') -> Dict:
    """
    Convenience function to get stock news
    
    Usage:
        from perplexity_client import get_stock_news
        news = get_stock_news("0700", "HK")
    """
    try:
        client = PerplexityClient()
        return client.search_news(symbol, market)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Set PERPLEXITY_API_KEY environment variable"
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python perplexity_client.py SYMBOL [MARKET]")
        print("Example: python perplexity_client.py 0700 HK")
        sys.exit(1)
    
    symbol = sys.argv[1]
    market = sys.argv[2] if len(sys.argv) > 2 else "HK"
    
    print(f"🔍 Searching news for {symbol} ({market})...")
    result = get_stock_news(symbol, market)
    
    if result.get("success"):
        print("\n📰 News Summary:")
        print(result.get("content", "No content"))
        if result.get("citations"):
            print("\n📎 Sources:")
            for citation in result.get("citations", []):
                print(f"  - {citation}")
    else:
        print(f"❌ Error: {result.get('error')}")
