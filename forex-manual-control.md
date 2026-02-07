# 📊 Forex Analyst - Manual Control Guide

## 🎯 How It Works

**You tell me:** "Analyze EURUSD"  
**I will:**
1. Update the workflow with your pair
2. Trigger the workflow
3. Monitor execution
4. Confirm when email is sent

---

## 💬 Commands You Can Use

### **Analyze a Currency Pair**
```
Analyze EURUSD
Run forex analysis for GBPUSD
Check AUDUSD
```

### **Check Status**
```
What's the status?
Is it done yet?
Did the email send?
```

### **Change Timeframe**
```
Use 1H timeframe
Change to 4H chart
Set timeframe to 1D
```

---

## 🔧 Supported Pairs

- **EURUSD** - Euro / US Dollar
- **GBPUSD** - British Pound / US Dollar
- **AUDUSD** - Australian Dollar / US Dollar
- **NZDUSD** - New Zealand Dollar / US Dollar
- **USDJPY** - US Dollar / Japanese Yen
- **USDCAD** - US Dollar / Canadian Dollar

---

## 📈 Supported Timeframes

- **15m** - 15 minutes
- **1H** - 1 hour
- **4H** - 4 hours (default)
- **1D** - 1 day

---

## ⚙️ Technical Details

Your workflow is configured to:
1. Accept webhook trigger (manual)
2. Read currency pair from "Set Currency Pair" node
3. Call Flask API at `http://host.docker.internal:5002`
4. Generate comprehensive report
5. Email to 13 recipients

**Workflow ID:** `pl2w62mCX-7BC9zOezfgs`  
**Webhook URL:** `http://localhost:5678/webhook/forex-analysis`

---

## 🚀 Quick Start

Just tell me:

> **"Analyze EURUSD"**

And I'll handle the rest!

---

## 📝 Examples

### Example 1: Analyze with default settings
```
You: Analyze GBPUSD
Me: Running Forex Analysis for GBPUSD (4H timeframe)...
    [2-5 minutes later]
    ✅ Analysis complete! Email sent to 13 recipients.
```

### Example 2: Analyze with custom timeframe
```
You: Analyze USDJPY with 1H chart
Me: Running Forex Analysis for USDJPY (1H timeframe)...
    ✅ Analysis complete!
```

### Example 3: Check status mid-execution
```
You: What's the status?
Me: ⏳ Still running...
    Progress: Technical analysis in progress (node 5/8)
```

---

## 🛠️ Behind the Scenes (What I Do)

When you say "Analyze EURUSD":

1. **Update workflow node:**
   ```javascript
   // I update "Set Currency Pair" node to:
   {
     currency_pair: "EURUSD",
     timeframe: "4H"
   }
   ```

2. **Trigger workflow:**
   ```bash
   # I call n8n API:
   curl -X POST "http://localhost:5678/webhook/forex-analysis?currency_pair=EURUSD"
   ```

3. **Monitor execution:**
   ```bash
   # I check execution status every 30 seconds
   # Until it completes or fails
   ```

4. **Report back to you:**
   ```
   ✅ Done! Email sent.
   ```

---

## 🔍 Troubleshooting

### "Workflow didn't complete"
- Check Flask API: `sudo systemctl status forex-api`
- Check n8n logs: Executions tab in n8n UI
- Check email credentials in workflow

### "Email not received"
- Check spam folder
- Verify email addresses in workflow
- Check n8n execution logs for errors

### "Flask API not responding"
- Start API: `sudo systemctl start forex-api`
- Check logs: `sudo journalctl -u forex-api -f`
- Test API: `curl http://localhost:5002/forex-analysis-realtime?pair=EURUSD`

---

## ✨ That's It!

No BAT files, no schedules, no manual workflow editing.

**Just tell me what pair you want analyzed, and I'll handle everything!** 🐷
