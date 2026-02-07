# 🔄 n8n Workflow Changes - Quick Reference

## 📋 What You Need to Change

To make your workflow run automatically on VPS with hardcoded pair:

### **1️⃣ Replace Webhook Trigger with Schedule Trigger**

**Current (Webhook):**
```
┌─────────────┐
│  Webhook    │ ← Delete this
└─────────────┘
```

**New (Schedule):**
```
┌──────────────────┐
│ Schedule Trigger │ ← Add this
└──────────────────┘
```

**Steps:**
1. Open your "Forex Analyst" workflow in n8n
2. Click the **Webhook** node → Press **Delete**
3. Click **+ Add node** → Search **"Schedule Trigger"**
4. Drag connection from Schedule Trigger to "Set Currency Pair"

---

### **2️⃣ Configure Schedule Trigger**

**Click on Schedule Trigger node:**

- **Trigger Interval:** Custom Cron Expression
- **Cron Expression:** `0 8 * * 1-5`
  - This means: **Mon-Fri at 8:00 AM**

**Common schedules:**
| When | Cron Expression |
|------|----------------|
| Daily 8 AM | `0 8 * * *` |
| Weekdays 8 AM | `0 8 * * 1-5` |
| Every 4 hours | `0 */4 * * *` |
| 9 AM and 3 PM | `0 9,15 * * *` |

---

### **3️⃣ Hardcode Currency Pair**

**Click on "Set Currency Pair" node:**

**Change from:**
```javascript
{{ $json.query.currency_pair }}
```

**To:**
```
EURUSD
```

*(or GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCAD)*

**Full node config should look like:**
```json
{
  "currency_pair": "EURUSD",
  "timeframe": "4H"
}
```

---

### **4️⃣ Update API URLs (If Needed)**

**Find HTTP Request nodes** that call Flask API.

**Change from:**
```
http://host.docker.internal:5002/forex-analysis-realtime?pair={{ ... }}
```

**To:**
```
http://localhost:5002/forex-analysis-realtime?pair={{ $('Set Currency Pair').first().json.currency_pair }}
```

**Or if n8n is in Docker:**
```
http://172.17.0.1:5002/forex-analysis-realtime?pair={{ $('Set Currency Pair').first().json.currency_pair }}
```

---

## 🎨 Visual Guide

### **Before (Webhook):**
```
┌──────────┐      ┌──────────────┐      ┌─────────┐
│ Webhook  │─────▶│ Set Currency │─────▶│ Analysis│
│ (Manual) │      │     Pair     │      │  Nodes  │
└──────────┘      │ (from query) │      └─────────┘
                  └──────────────┘
```

### **After (Scheduled):**
```
┌──────────┐      ┌──────────────┐      ┌─────────┐
│ Schedule │─────▶│ Set Currency │─────▶│ Analysis│
│ (Auto)   │      │     Pair     │      │  Nodes  │
│ 8 AM M-F │      │  (hardcoded) │      └─────────┘
└──────────┘      └──────────────┘
```

---

## ✅ Testing

### **Test Immediately (Don't Wait for Schedule)**

1. Open workflow in n8n editor
2. Click **"Execute Workflow"** button (play icon)
3. Wait 2-5 minutes for execution
4. Check your email inbox

### **View Execution History**

- Go to n8n → **Executions** tab
- Filter by "Forex Analyst" workflow
- Check for errors in failed executions

---

## 🔧 Multiple Pairs Setup

**Want to analyze different pairs automatically?**

### **Option 1: Duplicate Workflow (Simple)**

1. **Duplicate workflow 6 times**
2. **Rename each:**
   - "Forex Analyst - EURUSD"
   - "Forex Analyst - GBPUSD"
   - "Forex Analyst - AUDUSD"
   - etc.

3. **Set different pair** in each workflow's "Set Currency Pair" node

4. **Stagger schedules** to avoid API overload:
   - EURUSD: `0 8 * * 1-5` (8:00 AM)
   - GBPUSD: `30 8 * * 1-5` (8:30 AM)
   - AUDUSD: `0 9 * * 1-5` (9:00 AM)
   - USDJPY: `30 9 * * 1-5` (9:30 AM)
   - USDCAD: `0 10 * * 1-5` (10:00 AM)
   - NZDUSD: `30 10 * * 1-5` (10:30 AM)

**Pros:** Simple, easy to manage  
**Cons:** 6 workflows to maintain

---

### **Option 2: Single Workflow with Loop (Advanced)**

**Add after Schedule Trigger:**

1. **Code Node** - Generate pair array:
```javascript
// Generate all pairs to analyze
return [
  {json: {currency_pair: "EURUSD", timeframe: "4H"}},
  {json: {currency_pair: "GBPUSD", timeframe: "4H"}},
  {json: {currency_pair: "AUDUSD", timeframe: "4H"}},
  {json: {currency_pair: "USDJPY", timeframe: "4H"}},
  {json: {currency_pair: "USDCAD", timeframe: "4H"}},
  {json: {currency_pair: "NZDUSD", timeframe: "4H"}}
];
```

2. **Split in Batches Node** - Process one at a time
   - Batch Size: `1`
   - Options: Reset

3. **Wait Node** (optional) - Pause between pairs
   - 2 minutes between each pair

4. Connect to rest of your analysis nodes

**Pros:** Single workflow, processes all pairs  
**Cons:** Takes longer (2-5 min × 6 pairs = 12-30 min total)

---

## 🎯 Final Workflow Structure

```
┌─────────────────┐
│ Schedule Trigger│
│  (8 AM M-F)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Set Currency    │
│ Pair: EURUSD    │
│ (hardcoded)     │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬───────────┐
    │         │         │           │
    ▼         ▼         ▼           ▼
┌───────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│ Chart │ │ News │ │ Retail │ │Technical│
│  API  │ │  AI  │ │   AI   │ │   AI    │
└───┬───┘ └───┬──┘ └────┬───┘ └────┬────┘
    │         │         │           │
    └────┬────┴────┬────┴───────────┘
         │         │
         ▼         ▼
    ┌─────────────────┐
    │ Prepare Report  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Send Email     │
    │  (12 recipients)│
    └─────────────────┘
```

---

## 📝 Checklist

- [ ] Webhook trigger removed
- [ ] Schedule Trigger added and configured
- [ ] Cron expression set (e.g., `0 8 * * 1-5`)
- [ ] Currency pair hardcoded in "Set Currency Pair" node
- [ ] API URLs updated (localhost:5002)
- [ ] Workflow saved
- [ ] Workflow activated (toggle ON)
- [ ] Test execution successful
- [ ] Email received
- [ ] Execution history checked (no errors)

---

## 🆘 Troubleshooting

### **"Workflow didn't run at scheduled time"**

**Check:**
1. Is workflow **activated**? (toggle should be ON/green)
2. Is schedule correct? `0 8 * * 1-5` = 8 AM weekdays
3. Is n8n running? `docker ps` or `systemctl status n8n`
4. Check n8n timezone: Settings → Time Zone

---

### **"Execution failed immediately"**

**Check Execution Logs:**
1. Go to n8n → Executions
2. Click on failed execution
3. Look for red error nodes
4. Common issues:
   - Flask API not running: `sudo systemctl status forex-api`
   - Wrong API URL: Should be `localhost:5002` or `172.17.0.1:5002`
   - Hardcoded pair typo: Must match exactly (EURUSD, not EUR/USD)

---

### **"Email not received"**

**Check:**
1. Email Send node credentials configured?
2. Recipient email correct?
3. Check spam folder
4. Check n8n execution logs for email errors

---

## 🚀 Quick Start Command

**Just copy-paste this into your existing workflow:**

1. Delete Webhook node
2. Add Schedule Trigger (cron: `0 8 * * 1-5`)
3. Change "Set Currency Pair" value to: `EURUSD`
4. Save & Activate
5. Test with "Execute Workflow" button

**Done!** 🎉

---

**Need help?** Check `VPS-DEPLOYMENT-GUIDE.md` for full details.
