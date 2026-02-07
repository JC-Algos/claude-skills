# Market Sentiment Analysis - TODO

## When Jason Returns Tonight

- [ ] Check local Windows machine for sentiment analysis code
  - Look in: `C:/B_Drive/Market Sentiment Analysis/`
  - Find script that generates `sentiment_analysis_detailed.json`

- [ ] Upload sentiment analysis code to VPS
  - Path: `/root/clawd/projects/market-sentiment/`
  
- [ ] Configure n8n SMTP credentials
  - Go to: https://n8n.srv1295571.hstgr.cloud
  - Add Gmail SMTP account

- [ ] Activate n8n workflow
  - Toggle "Market Sentiment Analysis" workflow to active

- [ ] Test workflow
  ```bash
  curl -X POST https://n8n.srv1295571.hstgr.cloud/webhook/market-sentiment
  ```

---

## Quick Reference

**Flask API:** `systemctl status sentiment-api`  
**Data file:** `/root/clawd/projects/market-sentiment/sentiment_analysis_detailed.json`  
**Webhook:** `https://n8n.srv1295571.hstgr.cloud/webhook/market-sentiment`  
**Progress doc:** `/root/clawd/projects/market-sentiment/DEPLOYMENT_PROGRESS.md`
