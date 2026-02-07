# JC Algos Backend & Infrastructure

## Servers

### Backend Server (srv1238641)
- **IP:** `72.62.78.163`
- **API:** `https://api.jc-algos.com`
- **Backend:** `/root/stripe_backend.py`
- **Logs:** `/root/stripe_backend.log`
- **venv:** `/root/venv/bin/python3`

### This VPS (srv1295571)
- **IP:** `72.62.251.37`
- **Local repo:** `/root/clawd/jc-algos-signal-web/`
- **TA API:** Docker container `n8n-ta-api-1`

---

## Supabase Integration

- **Purpose:** User auth + subscription status
- **Tables:** Users, subscriptions
- **Events handled:**
  - `customer.subscription.created` - Trial subscriptions
  - Checkout completion → user upgrade

---

## Stripe Setup

### Webhook Configuration
- **Secret:** Must include `whsec_` prefix
- **Events to enable:** `customer.subscription.created`, `checkout.session.completed`
- **Dashboard:** Verify webhook events are enabled

### Stripe Payment Links (with promo)
| Product | Link |
|---------|------|
| Trend Momentum | https://buy.stripe.com/6oU7sD4ex61e2d23aI77O01?prefilled_promo_code=INDICATOR75 |
| MA Band Breakout | https://buy.stripe.com/00w4grcL32P29Fu6mU77O02?prefilled_promo_code=INDICATOR75 |
| SMR Dashboard | https://buy.stripe.com/7sY7sD7qJ0GU5pedPm77O03?prefilled_promo_code=INDICATOR75 |
| Combo Bundle ($1299) | https://buy.stripe.com/cNi5kvcL3bly3h63aI77O04?prefilled_promo_code=INDICATOR75 |

### Promo Code
- **Code:** `INDICATOR75`
- **Discount:** 75% off

---

## Frontend Pages (jc-algos.com / Hostinger)

### Main Pages
| Page | File | Purpose | Access |
|------|------|---------|--------|
| Home | `index.html` | Landing page, nav to all features | Public |
| Indicators | `indicators.html` | TradingView indicators shop (4 products) | Public |
| Signal Analysis | (in index.html) | Buy/Sell detection + validation | Registered users |
| Technical Analysis | `technical.html` | Interactive/static charts, TA | Registered users (free) |
| Retirement Calculator | `index-retirement.html` | Financial planning tool | Registered users (free) |

### Auth System
- **Free users:** Can access Technical Analysis, Retirement Calculator
- **Premium users:** Full signal analysis, P/L tracking
- **Function:** `checkUserAccess()` - allows any registered user
- **Old function:** `checkPremiumStatus()` - premium only (deprecated)

---

## Backend Files (GitHub)

### Essential backend/ files:
```
ta_api.py                     # Flask API (main entry)
ta_analyzer.py                # TA analysis logic
generate_chart.py             # Static chart + Pattern detection
generate_interactive_chart.py # Interactive Plotly chart (CDN, 39KB)
rrg_rs_analyzer.py            # RRG rotation chart
stripe_backend.py             # Payment handling (on srv1238641)
```

### Docker (TA API)
- **Container:** `n8n-ta-api-1`
- **Restart:** `docker restart n8n-ta-api-1`
- **Full rebuild:** `cd /docker/n8n && docker compose up -d ta-api --force-recreate`
- **Plotly:** Added to container pip install

---

## API Endpoints

### TA API (this VPS)
- **Static chart:** `http://172.18.0.1:PORT/api/ta?symbol=...`
- **Interactive chart:** `http://172.18.0.1:PORT/api/ta/interactive?symbol=...`

### Economic Data Scraper API (this VPS)
- **URL:** `https://econ.srv1295571.hstgr.cloud`
- **Service:** `systemctl restart economic-scraper`
- **Code:** `/root/clawd/projects/economic-scraper/app.py`
- **GitHub:** https://github.com/JC-Algos/economic-data-scraper
- **Proxy:** ScraperAPI (bypasses Cloudflare on investing.com)
- **ScraperAPI key:** env var `SCRAPER_API_KEY` in systemd service
- **Free tier:** 5,000 req/month (~113 full scans)
- **Endpoints:**
  - `/scrape?country=US` — 26 US economic indicators
  - `/scrape?country=China` — 18 China economic indicators
  - `/debug` — test single URL
- **Frontend:** `economic_data_analysis.html` on Hostinger (jc-algos.com)
- **Traefik route:** `econ.srv1295571.hstgr.cloud` → `localhost:5005`
- **Config:** `/docker/n8n/traefik-dynamic/economic-scraper.yml`
- **Parallel fetch:** 5 workers, ~1 min per country
- **Note:** investing.com blocked by Cloudflare since Feb 2026. Direct requests/cloudscraper/playwright all fail. ScraperAPI with `render=true` is the workaround.

### Backend API (srv1238641)
- **Stripe webhook:** `https://api.jc-algos.com/webhook/stripe`

---

## Charts

### Interactive Plotly Charts
- **Size:** 39KB (CDN) vs 4.7MB (inline) - 120x smaller
- **Features:** Candlestick, EMAs (10/20/60/200), Volume Profile, Volume bars
- **Height:** 480px (no scrolling)
- **Gaps:** Weekend/holiday gaps removed with `rangebreaks`

### Toggle UI
- 互動 (Interactive) / 靜態 (Static) buttons in `technical.html`

---

## TradingView Indicators

| # | Name (中文) | Name (English) | Price | indicator_id |
|---|-------------|----------------|-------|--------------|
| 1 | 趨勢動量 | Trend Momentum | $399 | trend_momentum |
| 2 | 自動均線通道突破 | Automatic MA Band Breakout | $399 | ma_band_breakout |
| 3 | SMR Dashboard | SMR Dashboard | $599 | smr_dashboard |
| 4 | 完整指標套裝 | Complete Bundle | $1299 | combo_package |

---

## GitHub

- **Account:** JC-Algos
- **Email:** jcalgossignal@gmail.com
- **Profile:** https://github.com/JC-Algos

---

## Deployment

- **Hosting:** Hostinger
- **Auto-deploy:** From GitHub
- **CDN cache:** Can delay updates ~20-30 mins

---

## API Routes (Complete)

### TA API Routes (this VPS - Docker `n8n-ta-api-1`)
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ta` | GET | Static chart generation |
| `/api/ta/interactive` | GET | Interactive Plotly chart (39KB CDN) |
| `/analyze/complete` | GET | Full report + technical chart + RRG chart paths |

**Query params:** `?symbol=0005.HK` or `?symbol=AAPL`

### Stripe Backend Routes (srv1238641)
| Route | Method | Purpose |
|-------|--------|---------|
| `/webhook/stripe` | POST | Stripe webhook handler |
| `/api/subscription/status` | GET | Check user subscription |

### n8n Webhook Routes
| Route | Purpose |
|-------|---------|
| `/webhook/forex-analysis` | Forex Analyst trigger |
| `/webhook/market-sentiment` | Market sentiment analysis |
| `/webhook/stock-analysis` | Stock TA trigger |

---

## Problems Fixed & Lessons Learned

### 1. Stripe Webhook Signature Validation (2026-01-26)
**Problem:** Webhook returning 400 errors, signature validation failing
**Root cause:** `STRIPE_WEBHOOK_SECRET` missing `whsec_` prefix
**Fix:** Include full secret with prefix: `whsec_xxxxx...`
**Lesson:** Always copy full webhook secret from Stripe Dashboard

### 2. Users Not Upgraded After Payment (2026-01-26)
**Problem:** Users paid but subscription status not updated
**Root cause:** Missing `customer.subscription.created` event handling (only had `checkout.session.completed`)
**Fix:** Add handler for `customer.subscription.created` event for trial subscriptions
**Lesson:** Trial subscriptions fire different events than regular purchases

### 3. Free Tools Showing "Premium Required" (2026-01-28)
**Problem:** Technical analysis & retirement calculator blocked for free users
**Root cause:** Old code used `checkPremiumStatus()` which only allowed premium
**Fix:** Changed to `checkUserAccess()` that allows ANY registered user
**Files changed:** `frontend/technical.html`, `frontend/index-retirement.html`
**Commits:** 6e536e3, 1c45e37
**Lesson:** Distinguish between "logged in" vs "premium" access levels

### 4. Interactive Charts Too Large (2026-01-28)
**Problem:** Plotly charts were 4.7MB (inline JS)
**Fix:** Use `include_plotlyjs='cdn'` → 39KB (120x smaller!)
**Lesson:** Always use CDN for Plotly in production

### 5. Docker Container Missing Plotly (2026-01-28)
**Problem:** `/api/ta/interactive` returned 500 error
**Root cause:** `n8n-ta-api-1` container didn't have plotly installed
**Fix:** Added plotly to pip install in `/docker/n8n/docker-compose.yml`
**Restart:** `docker restart n8n-ta-api-1`

### 6. n8n Can't Reach Host APIs (2026-01-26)
**Problem:** n8n HTTP Request nodes failed with ECONNREFUSED
**Root cause:** n8n runs in Docker, `localhost` = container, not host
**Fix:** Use Docker gateway `172.18.0.1:PORT` to reach host services
**Lesson:** Always use `172.18.0.1` in n8n for host APIs

### 7. Hostinger CDN Cache Delay
**Problem:** Code changes not appearing on live site
**Root cause:** Hostinger CDN caches files for ~20-30 mins
**Workaround:** Wait, or clear CDN cache in Hostinger panel
**Lesson:** Auto-deploy from GitHub ≠ instant live update

### 8. HK Chart Timezone Issues (2026-01-28)
**Problem:** HK stock charts showing wrong timezone
**Fix:** Use pytz for proper timezone handling
**Code:** `import pytz; hk_tz = pytz.timezone('Asia/Hong_Kong')`
**Learning ID:** LRN-20260128-001

---

## Frontend Auth System

### Access Levels
| Level | Function | Access |
|-------|----------|--------|
| Public | (none) | Landing, indicators shop |
| Registered | `checkUserAccess()` | Technical analysis, retirement calc |
| Premium | `checkPremiumStatus()` | Full signal analysis, P/L tracking |

### Auth Flow (Supabase)
1. User signs up → Supabase creates user record
2. User purchases → Stripe webhook fires
3. `customer.subscription.created` → Backend updates Supabase
4. Frontend checks `checkUserAccess()` or `checkPremiumStatus()`

### Common Auth Mistakes
- ❌ Using `checkPremiumStatus()` for free tools
- ❌ Not handling trial subscription events
- ❌ Missing webhook event types in Stripe Dashboard

---

## Troubleshooting

### Webhook 400/Signature Errors
1. Check `STRIPE_WEBHOOK_SECRET` has `whsec_` prefix
2. Verify events enabled in Stripe Dashboard
3. Check logs: `/root/stripe_backend.log`

### Users Not Upgraded After Payment
1. Check `customer.subscription.created` event handling
2. Verify Supabase integration is working
3. Check user's subscription status in Supabase

### Free Tools Showing "Premium Required"
1. Use `checkUserAccess()` not `checkPremiumStatus()`
2. Files: `technical.html`, `index-retirement.html`

### API 500 Errors
1. Check if container has required packages (`docker exec -it n8n-ta-api-1 pip list`)
2. Check logs: `docker logs n8n-ta-api-1`
3. Restart: `docker restart n8n-ta-api-1`

### n8n Can't Reach APIs
1. Use `172.18.0.1:PORT` not `localhost`
2. Check if service is running on host
3. Check firewall isn't blocking Docker bridge
