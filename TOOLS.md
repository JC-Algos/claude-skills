# TOOLS.md - Index

Quick reference for Oracle's tools and configs. Detailed docs in sub-files.

## 📁 Labeled Memory (memory/tools/)

| File | Category | Content |
|------|----------|---------|
| [n8n-workflows.md](memory/tools/n8n-workflows.md) | n8n | Workflows, APIs, endpoints |
| [tg-whatsapp-summaries.md](memory/tools/tg-whatsapp-summaries.md) | Reports | BB+RRG, News summaries, delivery targets |
| [hsi-forecast.md](memory/tools/hsi-forecast.md) | HSI | 4 Judges prediction system |
| [accounts.md](memory/tools/accounts.md) | Accounts | Jason's accounts, channels, WhatsApp groups |
| [jc-algos-web.md](memory/tools/jc-algos-web.md) | JC Algos | Website, TradingView webhook |
| [jc-algos-backend.md](memory/tools/jc-algos-backend.md) | JC Algos | Supabase, Stripe, pages, dashboard API, infrastructure |

**Usage (Lazy Load):**
- n8n task? → read `n8n-workflows.md`
- Send summary? → read `tg-whatsapp-summaries.md`
- HSI forecast? → read `hsi-forecast.md`
- Account/channel lookup? → read `accounts.md`
- JC Algos / TradingView? → read `jc-algos-web.md`
- Supabase / Stripe / pages? → read `jc-algos-backend.md`
- **Topic not found above?** → Search Misc below or `memory/*.md` files

---

## 🖥️ Server Access (SSH)

### Hostinger (Frontend)
- **Host:** 217.21.73.253
- **Port:** 65002
- **User:** u452726456
- **Web Root:** `~/domains/jc-algos.com/public_html/`
- **Connect:** `ssh -p 65002 u452726456@217.21.73.253`

### srv1238641 (Backend API)
- **Host:** 72.62.78.163
- **Port:** 22
- **User:** root
- **Domain:** api.jc-algos.com
- **Connect:** `ssh root@72.62.78.163`
- **Services:** Stripe, RRG, RS, Fundamental, HSI-SPX, Pinbar, Portfolio, Signals (ports 5000-5008, 8000)

### srv1295571 (This VPS - Oracle)
- **Host:** 72.62.251.37
- **Services:** n8n, Docker, TA API, Signal Web, Dashboard API, Economic Scraper

---

## 📦 Misc (Quick Reference)

*Search here when topic cannot be found in labeled memory above.*

### Telegram
- **Jason:** Sand Tai (id: 90197440)
- **Bot:** @Oracle_Piggybot (8225795790)
- **Channel:** -1003796838384 (JC Algos NEW)

### WhatsApp
- **Jason:** 85269774866@s.whatsapp.net
- **DIM INV:** 85262982502-1545129405@g.us
- **Pure Inv:** 85292890363-1425994418@g.us

### Key Scripts
```bash
# BB Squeeze + RRG
python3 /root/clawd/scripts/hk_squeeze_rrg_analyzer.py 1h telegram
python3 /root/clawd/scripts/squeeze_rrg_analyzer.py 1h telegram

# News Summary
python3 /root/clawd/scripts/hk_news_summary.py telegram

# HSI Forecast
cd /root/clawd/projects/hsi-forecast && python3 src/predict.py --format telegram --save

# Market Sentiment
cd /root/clawd/projects/market-analyzer/sentiment && python3 market_sentiment.py
```

### Commands
- `/forex [PAIR]` - Trigger Forex Analyst (e.g., `/forex XAUUSD`)
- `/bb [MARKET] [TF]` - BB Squeeze Scanner (e.g., `/bb HK 1h`)

---

## 🔧 OpenClaw Config & Session Behavior

### Model Switching (2026-02-06)
- **Config changes don't affect active sessions** — existing sessions keep their model
- **Only NEW sessions** pick up the updated model from config
- To force a model change: restart/clear the session
- Use `session_status` to verify actual running model vs config

### Web UI Auth
- **"device identity required" (1008)** = need to login first
- Go to base URL: `http://<IP>:18789/` and login with password
- Then navigate to chat session
- Password: check `gateway.auth.password` in config

### Default Model (current)
- Using **opus 4-5** (`anthropic/claude-opus-4-5`) as default
- 4-6 had issues with getting "stuck" during transfers

---

## 🔧 OpenClaw Config Management

**Fix invalid config (crash loop):**
```bash
openclaw doctor --fix
```

**Set sub-agent permissions correctly:**
```bash
openclaw config set agents.list[0].subagents.allowAgents '["coder", "webdev"]'
```

**Restart Gateway after changes:**
```bash
openclaw gateway restart
```

**Check schema before modifying config:**
```bash
# Via tool
gateway action=config.schema

# Via CLI
openclaw config schema
```

⚠️ **Never invent config keys** — use `config.schema` to verify keys exist first!

---

## ⚠️ Important Rules

1. **Format:** Always use COMPLETE/ORIGINAL format for blasts
2. **Channel:** Use NEW channel (-1003796838384), not OLD (-1002288872733)
3. **WhatsApp:** No markdown tables - use bullet lists
4. **wacli:** Kill sync before sending: `pkill -f "wacli sync"`
5. **TradingView:** Don't create webhook servers - Jason has his own
6. **Telegram links:** Tickers like `01991.HK` get auto-linked as URLs → use `·HK` (middle dot) in TG messages

---

*For detailed info, read the sub-files in memory/tools/*
*For unlabeled topics, search daily memory files: memory/YYYY-MM-DD.md*
