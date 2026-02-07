# 📊 Forex Analyst Workflow - Complete Setup Guide

## 🎯 Overview

**Your Forex Analyst system has 3 components:**

1. **Python Flask API** (`forex_sentiment_api.py`) - Scrapes MyFXBook + analyzes news with FinBERT
2. **n8n Workflow** - Orchestrates the analysis and sends email reports
3. **Windows BAT Trigger** - Easy one-click execution

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `forex_sentiment_api.py` | Full Python backend (Flask API) |
| `trigger-forex-analysis.bat` | **[Recommended]** BAT file with pair parameter |
| `trigger-forex-simple.bat` | Simple BAT file (no parameters) |
| `n8n-workflow-hardcoded-pair.json` | Sample n8n workflow with hardcoded pair |

---

## 🚀 Setup Instructions

### **Step 1: Install Python Dependencies**

On your **Windows VPS**, open Command Prompt:

```bash
cd C:\B_Drive\Market Sentiment Analysis
pip install flask pandas requests feedparser beautifulsoup4 selenium webdriver-manager undetected-chromedriver torch transformers numpy
```

### **Step 2: Start the Flask API**

```bash
python forex_sentiment_api.py
```

**You should see:**
```
Loading FinBERT model...
Model loaded successfully!
================================================================================
MEGA SERVER STARTED: Retail Scraper + FinBERT Engine
================================================================================
Available Endpoints:
  - GET /sentiment?pair=EURUSD (Raw retail data)
  - GET /run-analysis (Full batch analysis - all pairs)
  - GET /forex-analysis-realtime?pair=EURUSD (*** Real-time single pair analysis)

Data Directory: C:\B_Drive\Market Sentiment Analysis
Supported Pairs: ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD']

 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5002
```

✅ **Keep this terminal window open!** The API must be running.

---

### **Step 3: Configure Your n8n Workflow**

Your workflow is already set up! It's called **"Forex Analyst"** in n8n.

**Current webhook endpoint:**
```
http://localhost:5678/webhook/forex-analysis
```

**Two approaches:**

#### **Approach A: Dynamic Pair (Query Parameter)** ⭐ **Recommended**

- BAT file passes the pair: `?currency_pair=EURUSD`
- Workflow reads from webhook query parameter
- **No workflow changes needed** - your current setup already works this way!

#### **Approach B: Hardcoded Pair**

- Edit the **"Set Currency Pair"** node in your workflow
- Change `{{ $json.query.currency_pair }}` to just `EURUSD` (or your preferred pair)
- Use `trigger-forex-simple.bat` (no parameters needed)

---

## 🎮 Usage

### **Method 1: Using BAT File with Parameter (Recommended)**

1. **Edit `trigger-forex-analysis.bat`:**
   ```batch
   SET CURRENCY_PAIR=EURUSD
   ```
   ↑ Change `EURUSD` to any supported pair

2. **Double-click the BAT file**

3. **Wait 2-5 minutes** for the email report

**Supported Pairs:**
- `EURUSD` - Euro
- `GBPUSD` - British Pound
- `AUDUSD` - Australian Dollar
- `NZDUSD` - New Zealand Dollar
- `USDJPY` - Japanese Yen
- `USDCAD` - Canadian Dollar

---

### **Method 2: Hardcoded Pair in Workflow**

If you want to **always analyze the same pair** without changing the BAT file:

1. **Open n8n workflow editor**

2. **Click on "Set Currency Pair" node**

3. **Change the value from:**
   ```
   {{ $json.query.currency_pair }}
   ```
   **To:**
   ```
   EURUSD
   ```
   (or whichever pair you want)

4. **Save the workflow**

5. **Use the simple BAT file:**
   ```
   trigger-forex-simple.bat
   ```

---

## 🔧 Architecture Diagram

```
┌─────────────────────┐
│  Windows BAT File   │
│  (User clicks)      │
└──────────┬──────────┘
           │ HTTP POST
           │ ?currency_pair=EURUSD
           ▼
┌─────────────────────┐
│   n8n Webhook       │
│   (Port 5678)       │
└──────────┬──────────┘
           │
           ├──► Set Currency Pair
           │
           ├──► HTTP Request → Flask API (Port 5002)
           │    └─► /forex-analysis-realtime?pair=EURUSD
           │        ├─► MyFXBook Scraper (Selenium)
           │        └─► FinBERT News Engine (Google RSS + AI)
           │
           ├──► Get Chart from chart-img.com API
           │
           ├──► AI Technical Analysis (Gemini)
           │
           ├──► AI Retail Sentiment Analysis (MiniMax)
           │
           ├──► Merge All Data
           │
           └──► Send Email Report (HTML + Charts)
```

---

## 🛠️ Troubleshooting

### **Problem: "Connection refused" when triggering BAT file**

**Solution:**
```bash
# Check if n8n is running
netstat -ano | findstr :5678

# If not running, start n8n
n8n start
```

---

### **Problem: "Flask API not responding"**

**Solution:**
```bash
# Check if Python API is running
netstat -ano | findstr :5002

# If not running, start it
python forex_sentiment_api.py
```

---

### **Problem: "ChromeDriver error" in Flask logs**

**Solution:**
```bash
# Update ChromeDriver
pip install --upgrade webdriver-manager selenium undetected-chromedriver
```

---

### **Problem: "FinBERT model download fails"**

**Solution:**
```bash
# Pre-download the model
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoModelForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone'); AutoTokenizer.from_pretrained('yiyanghkust/finbert-tone')"
```

---

## 📊 What Gets Analyzed

For each currency pair, the system generates:

1. **📰 News Sentiment** (FinBERT AI)
   - Scrapes 15+ recent news articles from Google News
   - Analyzes sentiment: BULLISH / BEARISH / NEUTRAL
   - Shows percentage breakdown

2. **👥 Retail Sentiment** (MyFXBook)
   - Live data from MyFXBook Community Outlook
   - Shows SHORT % vs LONG %
   - Contrarian signal (institutions do opposite of retail)

3. **📈 Technical Analysis** (AI + TradingView Chart)
   - RSI, MACD, EMA21 indicators
   - Chart image with indicators
   - AI-powered technical interpretation

4. **💡 Overall Recommendation**
   - Combines all 3 sources
   - BUY / SELL / HOLD signal
   - Risk level assessment

---

## 🎨 Customization Options

### **Change Analysis Timeframe**

Edit the **"Set Currency Pair"** node in n8n:
```json
{
  "currency_pair": "EURUSD",
  "timeframe": "1H"  // Change to: 15m, 1H, 4H, 1D
}
```

### **Change Email Recipients**

Edit the **"Send Email Report"** node in n8n:
- `toEmail`: Primary recipient
- `bccEmail`: Additional recipients (comma-separated)

### **Modify Chart Style**

Edit the **"Set Chart Values"** node:
```json
{
  "chart_style": "candlestick",  // or: "line", "bars", "hollow_candles"
  "indicators": "RSI,MACD,EMA21"  // Add/remove indicators
}
```

---

## 🔐 Security Notes

- ⚠️ **API Keys**: Chart API key is hardcoded (replace if expired)
- ⚠️ **Email Credentials**: Configured in n8n Email node
- ⚠️ **File Paths**: Uses `C:\B_Drive\Market Sentiment Analysis\` - ensure this exists

---

## 📞 Support

**Created for:** Jason (@jasonckb)  
**Date:** 2026-01-25  
**System:** Windows VPS + n8n + Python Flask  

---

## 🚨 Important Notes

1. **Flask API must be running** before triggering the BAT file
2. **Chrome/ChromeDriver** required for MyFXBook scraping
3. **Internet connection** required (fetches live news + retail data)
4. **Processing time:** 2-5 minutes per analysis
5. **Rate limits:** Don't spam the BAT file (Google News + MyFXBook may block)

---

## ✅ Quick Start Checklist

- [ ] Python dependencies installed
- [ ] Flask API running (`python forex_sentiment_api.py`)
- [ ] n8n running (`n8n start`)
- [ ] Workflow imported and active
- [ ] BAT file configured with desired pair
- [ ] Email credentials configured in n8n
- [ ] Test run completed successfully

---

🎉 **You're all set! Double-click the BAT file to run your first analysis!**
