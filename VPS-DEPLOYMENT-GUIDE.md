# 🚀 VPS Deployment Guide - Forex Analyst Scheduled Workflow

## 🎯 Goal

Run the Forex Analyst workflow **automatically on VPS** with:
- ⏰ **Time-based trigger** (e.g., daily at 8 AM)
- 💱 **Currency pair hardcoded** in workflow (no BAT file)
- 🔄 **Auto-start Flask API** on VPS boot

---

## 📋 Step-by-Step Setup

### **Step 1: Update n8n Workflow Trigger**

**Option A: Manual Update in n8n UI** (Recommended)

1. Open your **Forex Analyst** workflow in n8n editor
2. **Delete the Webhook node** (first node)
3. **Add Schedule Trigger:**
   - Click **+** → Search **"Schedule Trigger"**
   - Connect it to "Set Currency Pair" node

4. **Configure Schedule Trigger:**
   ```
   Mode: Custom
   Cron Expression: 0 8 * * 1-5
   ```
   ☝️ This runs Mon-Fri at 8:00 AM

5. **Hardcode Currency Pair:**
   - Click **"Set Currency Pair"** node
   - Change `currency_pair` value from:
     ```
     {{ $json.query.currency_pair }}
     ```
     To:
     ```
     EURUSD
     ```
     (or whichever pair you want)

6. **Save and Activate** the workflow

---

**Option B: Import New Workflow** (Quick)

1. **Go to n8n** → Workflows → **Import**
2. **Paste** the content from `forex-workflow-scheduled.json`
3. **Copy** all other nodes from your original workflow
4. **Connect** them after "Set Currency Pair"
5. **Save and Activate**

---

### **Step 2: Deploy Flask API on VPS**

#### **A. Copy Python File to VPS**

```bash
# From your local machine:
scp forex_sentiment_api.py root@YOUR_VPS_IP:/root/forex-sentiment/

# Or manually copy the file content
```

#### **B. Install Dependencies**

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Create directory
mkdir -p /root/forex-sentiment
cd /root/forex-sentiment

# Install Python packages
pip3 install flask pandas requests feedparser beautifulsoup4 selenium webdriver-manager undetected-chromedriver torch transformers numpy

# Create data directory
mkdir -p /root/forex-sentiment/data
```

#### **C. Update File Paths in Python**

Edit `forex_sentiment_api.py`:

**Change this line:**
```python
DATA_FILE = r"C:\B_Drive\Market Sentiment Analysis\forex_sentiment_detailed.json"
```

**To:**
```python
DATA_FILE = "/root/forex-sentiment/data/forex_sentiment_detailed.json"
```

#### **D. Test Flask API**

```bash
cd /root/forex-sentiment
python3 forex_sentiment_api.py
```

**You should see:**
```
Loading FinBERT model...
Model loaded successfully!
================================================================================
MEGA SERVER STARTED: Retail Scraper + FinBERT Engine
================================================================================
 * Running on http://127.0.0.1:5002
```

**Test it:**
```bash
curl "http://localhost:5002/forex-analysis-realtime?pair=EURUSD"
```

If you see JSON output with news + retail data, ✅ it's working!

---

### **Step 3: Auto-Start Flask API (systemd Service)**

**Create systemd service:**

```bash
sudo nano /etc/systemd/system/forex-api.service
```

**Paste this:**
```ini
[Unit]
Description=Forex Sentiment Analysis API (Flask)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/forex-sentiment
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /root/forex-sentiment/forex_sentiment_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable forex-api.service
sudo systemctl start forex-api.service
```

**Check status:**
```bash
sudo systemctl status forex-api.service
```

**View logs:**
```bash
sudo journalctl -u forex-api.service -f
```

**Now Flask API will auto-start on VPS boot!** 🎉

---

### **Step 4: Update n8n Workflow API URL**

In your n8n workflow, find the **HTTP Request** nodes that call Flask API.

**Change this:**
```
http://host.docker.internal:5002/forex-analysis-realtime?pair={{ ... }}
```

**To:**
```
http://localhost:5002/forex-analysis-realtime?pair={{ $('Set Currency Pair').first().json.currency_pair }}
```

**OR if Flask is in Docker, use:**
```
http://172.17.0.1:5002/forex-analysis-realtime?pair={{ $('Set Currency Pair').first().json.currency_pair }}
```

---

### **Step 5: Test the Workflow**

1. **Open n8n** → Your Forex Analyst workflow
2. **Click "Execute Workflow"** (test button)
3. **Wait 2-5 minutes**
4. **Check your email** for the report

If you receive the email, ✅ **it's working!**

---

## ⏰ Common Cron Schedules

Change the **Schedule Trigger** cron expression as needed:

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| **Daily 8 AM** | `0 8 * * *` | Every day at 8:00 AM |
| **Weekdays 8 AM** | `0 8 * * 1-5` | Mon-Fri at 8:00 AM |
| **Every 4 hours** | `0 */4 * * *` | 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 |
| **Twice daily** | `0 9,15 * * *` | 9:00 AM and 3:00 PM |
| **Mon/Wed/Fri 9 AM** | `0 9 * * 1,3,5` | Only Mon, Wed, Fri at 9 AM |
| **Every hour (9-5)** | `0 9-17 * * 1-5` | Weekdays 9 AM to 5 PM, every hour |

**Cron format:** `minute hour day month weekday`

---

## 🔧 Multiple Pairs Setup

**Want to analyze different pairs at different times?**

### **Option 1: Duplicate Workflow**

1. Duplicate your workflow 6 times (one per pair)
2. Set different pair in each workflow
3. Set different schedules (stagger them)

Example:
- **Workflow 1:** EURUSD at 8:00 AM
- **Workflow 2:** GBPUSD at 8:30 AM
- **Workflow 3:** AUDUSD at 9:00 AM
- **Workflow 4:** USDJPY at 9:30 AM
- **Workflow 5:** USDCAD at 10:00 AM
- **Workflow 6:** NZDUSD at 10:30 AM

### **Option 2: Loop Through Pairs**

1. **Add Code node** after Schedule Trigger
2. **Generate array of pairs:**
   ```javascript
   return [
     {json: {currency_pair: "EURUSD", timeframe: "4H"}},
     {json: {currency_pair: "GBPUSD", timeframe: "4H"}},
     {json: {currency_pair: "AUDUSD", timeframe: "4H"}},
     {json: {currency_pair: "USDJPY", timeframe: "4H"}},
     {json: {currency_pair: "USDCAD", timeframe: "4H"}},
     {json: {currency_pair: "NZDUSD", timeframe: "4H"}}
   ];
   ```
3. **Split in Batches** node (process one at a time)
4. Rest of workflow processes each pair sequentially

---

## 📊 Monitoring & Logs

### **Check Flask API Logs**
```bash
sudo journalctl -u forex-api.service -f
```

### **Check n8n Execution History**
- Go to n8n → **Executions**
- Filter by workflow name
- Check for errors

### **Email Alerts on Failure**

Add an **Error Trigger** node to your workflow:
1. Create new workflow: "Forex Analyst Error Alert"
2. Trigger: **Error Trigger** → Select your Forex workflow
3. Action: **Send Email** with error details

---

## 🛠️ Troubleshooting

### **Problem: Flask API not starting**

**Check logs:**
```bash
sudo journalctl -u forex-api.service -n 50
```

**Common fixes:**
- Missing dependencies: `pip3 install -r requirements.txt`
- Wrong Python path: `which python3` (update service file)
- Port already in use: `sudo netstat -tulpn | grep 5002`

---

### **Problem: n8n can't reach Flask API**

**Test connection:**
```bash
curl http://localhost:5002/forex-analysis-realtime?pair=EURUSD
```

**If Docker networking issue:**
```bash
# Find Docker bridge IP
docker network inspect bridge | grep Gateway

# Use that IP in n8n workflow
# Example: http://172.17.0.1:5002/...
```

---

### **Problem: ChromeDriver fails on VPS**

**Install Chrome on VPS:**
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y
```

**Or use headless chromium:**
```bash
sudo apt install chromium-browser chromium-chromedriver -y
```

---

## 🔐 Security Notes

1. **Firewall:** Block port 5002 from external access
   ```bash
   sudo ufw deny 5002
   sudo ufw allow from 127.0.0.1 to any port 5002
   ```

2. **Run as non-root user** (optional):
   ```bash
   sudo useradd -m -s /bin/bash forexuser
   sudo chown -R forexuser:forexuser /root/forex-sentiment
   # Update systemd service: User=forexuser
   ```

3. **API Key for n8n ↔ Flask** (optional):
   - Add authentication to Flask routes
   - Store API key in n8n credentials

---

## ✅ Final Checklist

- [ ] Flask API deployed to VPS
- [ ] Dependencies installed
- [ ] File paths updated (Linux paths, not Windows)
- [ ] systemd service created and enabled
- [ ] Flask API auto-starts on boot
- [ ] n8n workflow updated to use Schedule Trigger
- [ ] Currency pair hardcoded in workflow
- [ ] HTTP Request URLs updated (localhost:5002)
- [ ] Test workflow executed successfully
- [ ] Email received with analysis report
- [ ] Cron schedule configured (8 AM weekdays)
- [ ] Logs verified (both Flask and n8n)

---

## 🎉 You're Done!

Your Forex Analyst will now run automatically on VPS at the scheduled time, analyze the specified pair, and email the report!

**To change pair:** Edit the "Set Currency Pair" node in n8n  
**To change schedule:** Edit the Schedule Trigger cron expression  
**To check logs:** `sudo journalctl -u forex-api.service -f`

---

**Created by:** Oracle 🐷  
**Date:** 2026-01-25  
**For:** Jason (@jasonckb)
