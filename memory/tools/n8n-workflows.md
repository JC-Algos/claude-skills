# n8n Workflows

## 1. Forex Analyst
- **Workflow ID:** pl2w62mCX-7BC9zOezfgs
- **Status:** Active
- **Trigger:** `/forex [PAIR]` (e.g., `/forex XAUUSD`)
- **Webhook:** `http://localhost:5678/webhook/forex-analysis?pair=[PAIR]`
- **Output:** Email report with price, chart, retail sentiment, news analysis, technical indicators
- **Supported pairs:** XAUUSD, EURUSD, GBPUSD, USDJPY, etc.

## 2. Group Forex Analyst
- **Workflow ID:** pPbKW9He8etUBO9M
- **Status:** Active
- **Schedule:** Mon-Fri 08:00, 12:00, 16:00, 20:00 HKT (0 0,4,8,12 * * 1-5 UTC)
- **Current pair:** AUDUSD (changes weekly)
- **Output:** 📧 **EMAIL ONLY** to jasonckb0411@gmail.com + BCC list
- **Supported pairs:** EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCAD, XAUUSD
- **Updated:** 2026-02-05

## 3. Market Sentiment Analysis
- **Workflow ID:** M6GuLyuCliDOSTg8
- **Status:** Active
- **Trigger:** Webhook only (`/webhook/market-sentiment`) - triggered by Python script
- **Schedule:** System cron 07:30, 11:30, 15:30, 19:30 HKT (30 23,3,7,11 * * * UTC)
- **Data Source:** `http://172.18.0.1:5001/sentiment-data`
- **Generator Script:** `/root/clawd/projects/market-analyzer/sentiment/market_sentiment.py`
- **Assets:** SPX, NDX, HSI, Gold, Bitcoin
- **Output:** 📧 **EMAIL ONLY** to jasonckb0411@gmail.com + BCC list

### Trigger Flow (IMPORTANT)
```
System cron (30 23,3,7,11 * * *) 
  → /root/clawd/scripts/run_sentiment.sh
    → Python script (fetches news, analyzes, saves JSON)
      → POST /webhook/market-sentiment
        → n8n sends email with fresh data
```

⚠️ **Do NOT add n8n schedule trigger** - causes stale data (fixed 2026-02-04)

### Sentiment Cron Schedule (System cron, NOT n8n)
```
30 23 * * * - 07:30 HKT
30 3  * * * - 11:30 HKT
30 7  * * * - 15:30 HKT
30 11 * * * - 19:30 HKT
```

## 4. US Market News
- **Workflow ID:** 6eDaBc1NjT6viIjV
- **Status:** Active
- **Output:** Saves to `/files/` in n8n container

## 5. HK Market News - With Yahoo Finance
- **Workflow ID:** Z409Z8fwwonXdJdP
- **Status:** Active

## 6. HSI Daily Forecast
- **Workflow ID:** Trgc6ts29L2sv9w2
- **Status:** Active
- **Trigger:** Cron 0 0 * * 1-5 UTC (08:00 HKT)

## 7. Stock Technical Analyzer
- **Workflow ID:** 0IELKXByeMks9yOW
- **Status:** Active
- **Trigger:** Manual/webhook

---

## API Endpoints

### Forex Sentiment API (port 5002)
- `GET /sentiment?pair=XAUUSD` - Retail sentiment data
- `GET /run-analysis` - Trigger full analysis
- `GET /forex-analysis-realtime` - Real-time analysis

### Market Sentiment API (port 5001)
- `GET /sentiment-data` - JSON sentiment data
- `GET /health` - Health check
- `GET /report` - Text report

---

## ⚠️ Best Practices

### Data Pipeline Triggers
For workflows that send data (email, notifications):
- **Single trigger path** - Generator script should trigger sender via webhook
- **Don't duplicate crons** - Having both system cron AND n8n schedule causes stale data
- **Webhook > Schedule** for data that needs to be fresh before sending

### Debugging Stale Data
1. Check API/file timestamps: `curl http://api | jq '.timestamp'`
2. Check execution history: `mcporter call n8n.list_executions workflowId:XXX`
3. Trace the trigger chain - who calls what?
4. Look for duplicate/competing schedules
