# HSI Enhanced Forecast — 5-Judge System v2.2

## Overview
5 Judges system for HSI direction + range prediction.
Upgraded Feb 7, 2026: AI 5th Judge + Futures Anchor + Dynamic Gap Fill.

## Script
```bash
cd /root/clawd/projects/hsi-forecast && python3 src/predict.py --format telegram --save
```

## 5 Judges Explained
1. **CatBoost (ML):** Gradient boosting classifier for direction
2. **GRU (Deep):** Recurrent neural network for direction
3. **ARIMA (Stats):** Statistical time series for direction
4. **Diffusion:** Rule-based signal alignment (9 factors weighted)
5. **🧠 AI Judge (NEW):** Opus 4.6 qualitative analysis — reads news, BB squeeze, macro narrative, cross-references with quantitative judges. Runs as part of isolated cron agentTurn.

## Key Features (v2.2)

### Futures Anchor
- Scrapes overnight HSI futures (AT session) from etnet.com.hk
- `src/fetch_futures.py` → gets regular + after-hours last price & premium
- If AT gap > 0.2% from close, shifts predicted range to anchor on futures
- Fixes issue where predicted high was below futures price

### Direction-Skewed Range
- Range allocation skewed by direction consensus
- e.g., 3 UP vs 1 DOWN = 75% range on upside (clamped 30-70%)
- Fixes structural issue where high_pct < abs(low_pct) even when direction = UP

### Dynamic Gap Fill Factor
- Based on 8-month rolling HSI backtest
- Factors loaded from `models/gap_fill_factors.json`
- Updated weekly by `src/backtest_gap_fill.py`

| Gap Size | Median Fill | Factor |
|----------|-------------|--------|
| Small 0.2-0.5% | 93% | 0.93 |
| Medium 0.5-1% | 76% | 0.76 |
| Large 1-2% | 47% | 0.47 |
| Huge >2% | — | 0.35 |

## Schedule
| Job | Cron (UTC) | HKT | Purpose |
|-----|-----------|-----|---------|
| HSI Forecast | `0 0 * * 1-5` | 08:00 Mon-Fri | Daily 5-Judge forecast |
| Gap Fill Backtest | `0 0 * * 6` | 08:00 Sat | Weekly factor update |

- **Delivery:** Telegram JC Algos (-1003796838384)
- **Session:** Isolated agentTurn (includes AI 5th Judge analysis)
- ❌ NO WhatsApp

## Output Format
```
🎯 HSI Enhanced Forecast — [Day] [Date]
🐷 Oracle 5-Judge System (v2.2 · Futures-Anchored)

━━━━━━━━━━━━━━━
📊 Predicted Range (from [day] close [price]):
• High: [price] (+X.XX%)
• Low: [price] (X.XX%)
• Range: XXX pts (X.XX%)
🔧 夜期錨定: [futures] ([+/-]XXX點[高水/低水])

📈 Direction: [UP/DOWN] (X↑ vs X↓) | [confidence]

━━━━━━━━━━━━━━━
🗳️ 5 Judges:
• CatBoost (ML): [emoji] [DIR] (XX%)
• GRU (Deep): [emoji] [DIR] (XX%)
• ARIMA (Stats): [emoji] [DIR] (XX%)
• Diffusion: [emoji] [DIR] (X🟢 vs X🔴)
• 🧠 AI Judge: [emoji] [DIR] (XX%)

━━━━━━━━━━━━━━━
🧠 AI 第5法官分析
[3-4 bullet points in 粵語 with reasoning]

⚠️ 風險：[downside]
✅ 確認：[upside]
━━━━━━━━━━━━━━━
```

## Data Locations
- Predictions: `data/predictions.jsonl`
- Gap fill factors: `models/gap_fill_factors.json`
- Futures scraper: `src/fetch_futures.py`
- Backtest script: `src/backtest_gap_fill.py`

## Key Signals Tracked
- HSI previous day change, EMA20, MA5 positions
- FXI (China ETF) — best overnight HK proxy
- SPX, NDX changes
- VIX level and change
- CNH (offshore RMB)
- **HSI Futures AT session** (overnight anchor)
