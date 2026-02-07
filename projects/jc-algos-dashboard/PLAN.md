# JC Algos Dashboard — HSI Forecast + Market Intelligence

## Goal
Add a new "Market Intelligence" dashboard page to jc-algos.com showing:
1. **Daily HSI Forecast** — auto-updated from predict.py output
2. **Cross-Market HK/US Summary** — consolidated portfolio view with BB Squeeze + RRG data

## Architecture

### Backend (Coder → runs on this VPS srv1295571)
```
Flask API: /root/clawd/projects/jc-algos-dashboard/backend/
Port: 5020
Traefik route: dashboard.srv1295571.hstgr.cloud

Endpoints:
  GET /api/forecast/latest    → Latest HSI forecast (from predictions.jsonl)
  GET /api/forecast/history   → Last 30 days of forecasts
  GET /api/market/summary     → Latest cross-market summary (HK+US squeeze+RRG)
  GET /api/market/portfolio   → Portfolio watchlist performance
  GET /api/health             → Health check
```

**Data sources (read-only, no duplication):**
- HSI forecast: `/root/clawd/projects/hsi-forecast/data/predictions.jsonl`
- HK squeeze: `python3 /root/clawd/scripts/hk_squeeze_rrg_analyzer.py 1d json`
- US squeeze: `python3 /root/clawd/scripts/squeeze_rrg_analyzer.py 1d json`
- Cross-market reports: cached from cron outputs

**Stack:** Flask + gunicorn, Docker container, Traefik reverse proxy

### Frontend (WebDev → pushed to GitHub for Hostinger deploy)
```
Repo: JC-Algos/jc-algos-dashboard (new)
Files: dashboard.html, dashboard.js, dashboard.css
Deploy: Hostinger auto-deploy from GitHub
URL: https://jc-algos.com/dashboard.html
```

**Design:**
- Match existing jc-algos.com style (dark theme, Chinese labels)
- Responsive (mobile-first)
- Supabase auth: `checkUserAccess()` (free registered users)
- Auto-refresh every 5 minutes

**Sections:**
1. 🎯 HSI Forecast card (direction, range, judges, confidence)
2. 📊 HK Market Overview (top squeezes, RRG quadrants)
3. 📊 US Market Overview (top squeezes, RRG quadrants)
4. 🔗 Cross-Market Correlation highlights
5. 📈 Forecast accuracy tracker (predicted vs actual)

### Integration
- Cron job updates data at market open/close
- Frontend polls backend API every 5 min
- No websockets needed (data changes only a few times/day)

## Task Split

### Coder (Backend)
1. Create Flask API project structure
2. Read predictions.jsonl and serve as JSON
3. Run squeeze scripts on-demand or serve cached results
4. Dockerize with docker-compose entry
5. Set up Traefik route
6. Add forecast accuracy tracking (predicted vs actual close)

### WebDev (Frontend)
1. Create new GitHub repo `jc-algos-dashboard`
2. Build dashboard.html with dark theme matching jc-algos.com
3. dashboard.js — API calls, data rendering, auto-refresh
4. dashboard.css — responsive layout, cards, charts
5. Supabase auth integration (same as technical.html)
6. Push to GitHub (Jason deploys via Hostinger)
