# HK News Summary Script

Python script to aggregate HK stock market news from multiple RSS sources.

## Features

- Fetches from 10+ RSS sources (HKEJ, Mingpao, Bloomberg, Reuters, SCMP, etc.)
- Filters today's news only
- Auto-categorizes (大市走勢, 新股/IPO, 異動股, 中國經濟, AI/科技, 大行報告, etc.)
- Deduplicates articles
- Outputs formatted Telegram/WhatsApp messages

## Usage

```bash
python3 hk_news_summary.py telegram   # Telegram format
python3 hk_news_summary.py whatsapp   # WhatsApp format  
python3 hk_news_summary.py json       # JSON output
python3 hk_news_summary.py broadcast  # Send to all (requires wacli)
```

## RSS Sources

### Always Available (Public)
| Source | URL |
|--------|-----|
| SCMP Business | `https://www.scmp.com/rss/91/feed/` |
| Reuters | `https://www.reuters.com/rssFeed/businessNews` |

### RSSHub (Public or Self-hosted)
| Source | Public URL | Self-hosted |
|--------|------------|-------------|
| Mingpao | `https://rsshub.app/mingpao/pns/s00004` | `http://localhost:1200/mingpao/pns/s00004` |
| Bloomberg | `https://rsshub.app/bloomberg` | `http://localhost:1200/bloomberg` |

To use public RSSHub, set `USE_PUBLIC_RSSHUB = True` in the script.

### Local RSS Server (requires setup)

These sources require a custom RSS server at `localhost:1201`:

| Source | URL |
|--------|-----|
| HKEJ Stock | `http://localhost:1201/hkej/stock` |
| HKEJ China | `http://localhost:1201/hkej/china` |
| AAStocks | `http://localhost:1201/aastocks/news` |
| Now Finance | `http://localhost:1201/nowfinance` |
| Yahoo Finance HK | `http://localhost:1201/yahoo/finance-hk` |
| HK01 Finance | `http://localhost:1201/hk01/finance` |

See `rss_server.py` for the custom RSS server implementation.

## Dependencies

```bash
pip install feedparser pytz requests
```

## Configuration

Edit the top of `hk_news_summary.py`:

```python
# Use public RSSHub instance
USE_PUBLIC_RSSHUB = True  # or False for self-hosted

# Or comment out unavailable sources in RSS_FEEDS dict
```

## Output Categories

- 📊 大市走勢 (Market Movement)
- 🆕 新股/IPO
- 📈📉 異動股 (Movers)
- 📊 盈喜/盈警 (Earnings)
- 💰 配股/集資 (Placement/Fundraising)
- 🇨🇳 中國經濟 (China Economy)
- 🤖 AI/科技 (AI/Tech)
- 📋 大行報告 (Analyst Reports)
- 💹 商品/外匯 (Commodities/FX)
- 🌍 國際 (International)
