# JC Algos Website & TradingView Webhook

> **See also:** [jc-algos-backend.md](jc-algos-backend.md) for Supabase, Stripe, pages & infrastructure

## JC Algos Signal Page

### Overview
Trading signal analysis platform — reads TradingView signals from TG channel, enriches with Yahoo Finance close prices, validates signals, calculates P/L.

### Architecture
```
TradingView Alert → TG Bot API → JC Algos NEW Channel (-1003796838384)
                                        ↓
Signal Page Backend (Flask) ← Telethon (user session) reads channel history
        ↓
Yahoo Finance (yfinance 1.1.0) → close prices → valid signal logic → P/L
        ↓
Frontend (Hostinger: JC_Signals.html) ← API calls to backend
```

### Backend
- **Repo:** `/root/clawd/jc-algos-signal-web/`
- **Docker:** `n8n-signal-web-1` container in `/docker/n8n/docker-compose.yml`
- **URL:** https://signal.srv1295571.hstgr.cloud
- **Tech:** Flask 3.0 + Telethon + yfinance 1.1.0 + gunicorn
- **DB:** SQLite at `/app/data/signals.db`

### Frontend (Hostinger)
- **URL:** https://jc-algos.com/JC_Signals.html
- **Files:** `JC_Signals.html`, `app.js`, `style.css` (flat, no subfolders)
- **API_BASE in app.js:** `https://signal.srv1295571.hstgr.cloud`
- **Auth:** Supabase `checkUserAccess()` (same as technical.html)
- **GitHub:** https://github.com/JC-Algos/Signal_page-Transition (hostinger/ folder)

### Telethon Session
- **User session** (not bot — bots can't read channel history via MTProto)
- **Account:** Sand Tai (+85290197440)
- **Session string:** In `/root/clawd/jc-algos-signal-web/backend/app.py`
- **API ID:** 25298694

### Valid Signal Logic ✅ (Confirmed 2026-02-05)
| Sentiment | Strategy | Valid if |
|-----------|----------|---------|
| 看好 | Normal | 收市價 ≥ 觸發價 |
| 看好 | Magic 9/13 | 收市價 ≤ 觸發價 (reversed) |
| 看淡 | Normal | 收市價 ≤ 觸發價 |
| 看淡 | Magic 9/13 | 收市價 ≥ 觸發價 (reversed) |

### Supported Exchanges
HKEX, BATS (US), OANDA (Forex), SSE_DLY (Shanghai), ZSE_DLY (Shenzhen), HSI

### API Endpoints
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serve frontend |
| `/api/auth/login` | POST | Email auth (approved list) |
| `/api/exchanges` | GET | List exchanges |
| `/api/signals/fetch` | POST | Fetch + process signals (main endpoint) |
| `/api/signals/history/<exchange>` | GET | Signal history stats |
| `/api/signals/export` | POST | Export CSV |

### Key Dependencies
- **yfinance ≥ 1.0.0** — v0.2.33 is broken for HK stocks! Must use ≥1.0
- **Telethon 1.34.0** — user session for channel reading
- **pandas, numpy** — data processing

### Troubleshooting
- **No close/valid data:** Check yfinance version (`pip show yfinance`). Must be ≥1.0
- **Auth failed:** Check SESSION_STRING is valid (TG account resets kill sessions)
- **Restart:** `cd /docker/n8n && docker compose restart signal-web`
- **Rebuild:** `cd /docker/n8n && docker compose up -d signal-web --force-recreate`
- **Logs:** `docker compose logs signal-web --tail=50`

### Features
- 🔐 Email Authentication (approved list)
- 📊 Signal Analysis — Buy/Sell detection with validation
- 📈 Real-time close prices via Yahoo Finance
- 🌍 Multi-Exchange: HKEX, US, Shanghai, Shenzhen, Forex
- 📉 P/L Tracking (valid signals only)
- 📜 Signal History (accumulating from Feb 2026)
- 📱 Responsive Design
- 📤 CSV Export

---

## TradingView Webhook Setup

### Webhook Server
- **Port:** 5015
- **URL:** `http://72.62.251.37:5015/webhook/tradingview`
- **Service:** `tradingview-webhook.service` (systemd)
- **Target Channel:** -1003796838384 (JC Algos NEW)

### TradingView Bot
| Bot | Username | ID |
|-----|----------|-----|
| TV_JC-Algos | @TV_JC_AlgosBot | 8548103712 |

⚠️ **Note:** Old bots (@JCTV_alertsbot, @JCTVAlerts_bot) invalid after TG reset (2026-02-04)

### TradingView Alert JSON Format
```json
{
  "chat_id": "-1003796838384",
  "text": "轉淡 Magic 9 看淡 {{exchange}}: {{ticker}}, 信號觸發價 = {{close}} 日期 = {{time}} 風險管理: 策略失效價: 信號觸發當天高位 + 1% - 2% 備注: 交易時段價格仍在變動，信號觸發不等於信號確認 訊號確認：收市價 >= 信號觸發價"
}
```

### Important Rules
⚠️ **Don't create new webhook servers** - Jason has his own TV webhook setup
⚠️ If duplicates appear in channel, check for conflicting webhook servers

---

## Telegram Channels

### JC Algos NEW (-1003796838384)
- **Purpose:** TradingView signals + all reports
- **Status:** ✅ ACTIVE - ALL CONTENT HERE

### JC Algos OLD (-1002288872733)
- **Purpose:** News summaries, reports (DEPRECATED)
- **Status:** ❌ NO LONGER USE

---

## Troubleshooting

### Duplicate Signals in Channel
1. Check if Oracle created a conflicting webhook server
2. Delete any `/root/clawd/*server.py` that handles TV webhooks
3. Only Jason's webhook (port 5015) should be active

### Bot Not Posting
1. Verify correct bot (@JCTV_alertsbot green) is admin
2. Check webhook server is running: `systemctl status tradingview-webhook`
3. Verify channel ID in TradingView alert JSON
