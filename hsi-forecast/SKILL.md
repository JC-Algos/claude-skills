---
name: hsi-forecast
description: Predict daily HSI range (high/low) and direction using XGBoost for range and 4 Judges ensemble (CatBoost, GRU, ARIMA, Diffusion) for direction.
---

# HSI Daily Forecast Skill

Predict Hang Seng Index daily trading range and direction before market open.

## When to Use

- User asks for HSI prediction or forecast
- User wants to know expected HSI range for the day
- User asks about HK market outlook
- Before HK market open (9:30 AM HKT)

## Project Location

```
/root/clawd/projects/hsi-forecast/
```

**GitHub:** https://github.com/JC-Algos/hsi-forecast

## Quick Prediction

```bash
cd /root/clawd/projects/hsi-forecast && python3 src/predict.py --format both
```

## Architecture

### Range Prediction (XGBoost)
- **High MAE:** 0.65%
- **Low MAE:** 0.78%

### Direction Prediction (4 Judges)

| Judge | Type | Description |
|-------|------|-------------|
| CatBoost | Machine Learning | Tree-based gradient boosting |
| GRU | Deep Learning | Recurrent neural network (10-day sequence) |
| ARIMA | Statistical | Time series autoregressive model |
| Diffusion | Rule-based | Factor analysis (9 indicators) |

### Consensus Logic

| Vote | Result |
|------|--------|
| 4:0 or 3:1 | ✅ 有信心 (confident) |
| 2:2 | ⚠️ 弱 / 無方向 (weak/no direction) |

## Output Format

### Telegram Message

```
🎯 HSI Daily Forecast - Monday 2 Feb 2026

📊 Predicted Range (from Fri close 27,387):
• High: 27,628 (+0.88%)
• Low: 27,129 (-0.94%)
• Range: 499 pts (1.82%)

📈 Direction: UP (3↑ vs 1↓) | ✅ 有信心

🗳️ 4 Judges:
• CatBoost (ML): 📈 UP (51%)
• GRU (Deep): 📈 UP (68%)
• ARIMA (Stats): 📈 UP (51%)
• Diffusion: 📉 DOWN (3🟢 vs 6🔴)

🟢 Bullish: >EMA20, CNH+0.1%, VIX=17
🔴 Bearish: <MA5, HSI-2.1%, FXI-2.9%, SPX-0.4%, NDX-0.9%, VIX+3.3%

⚡ Volatility: HIGH (×1.2)
```

### JSON Output

```json
{
  "date": "2026-02-01",
  "direction": "UP",
  "gru_direction": "UP",
  "gru_prob": 0.681,
  "arima_direction": "UP",
  "arima_prob": 0.509,
  "diffusion": -3,
  "bullish_count": 3,
  "bearish_count": 6,
  "predicted_high": 27628,
  "predicted_low": 27129,
  "volatility_regime": "HIGH"
}
```

## Diffusion Factors (9 total)

| Category | Factors |
|----------|---------|
| **Technical** | Price >EMA20, Price >MA5, HSI momentum |
| **Overnight** | FXI change, SPX change, NDX change |
| **Currency** | CNH strength (inverted USDCNH) |
| **Volatility** | VIX level (<20 bullish), VIX change (down=bullish) |

## Model Files

```
models/
├── range_high.json      # XGBoost High
├── range_low.json       # XGBoost Low
├── gru_direction.pt     # GRU model
├── gru_scaler.pkl       # GRU scaler
├── arima_params.pkl     # ARIMA parameters
└── ensemble/
    └── direction_cat.cbm # CatBoost
```

## API Endpoint

```bash
# JSON output
curl "https://ta.srv1295571.hstgr.cloud/api/hsi/forecast"

# Telegram-formatted message
curl "https://ta.srv1295571.hstgr.cloud/api/hsi/forecast?format=telegram"
```

## n8n Workflow

- **ID:** `Trgc6ts29L2sv9w2`
- **Schedule:** 8:30 HKT Mon-Fri (cron: `30 0 * * 1-5`)
- **Webhook:** `https://n8n.srv1295571.hstgr.cloud/webhook/hsi-forecast`

## Volatility Regimes

| Regime | Vol Ratio | Multiplier |
|--------|-----------|------------|
| LOW | < 0.7 | ×0.85 |
| NORMAL | 0.7-1.0 | ×1.0 |
| HIGH | 1.0-1.5 | ×1.2 |
| EXTREME | > 1.5 | ×1.5 |

## Retrain Models

```bash
cd /root/clawd/projects/hsi-forecast

# 1. Fetch latest data
python3 src/fetch_data.py

# 2. Create features
python3 src/features.py

# 3. Train XGBoost (range)
python3 src/train.py

# 4. Train ensemble (direction)
python3 src/train_ensemble.py
```

## Docker Dependencies

If updating predict.py with new packages:

```bash
docker exec n8n-ta-api-1 pip install catboost lightgbm torch statsmodels
docker exec n8n-ta-api-1 apt-get install -y libgomp1
docker restart n8n-ta-api-1
```

## Limitations

- 4 Judges accuracy is ~55% (better than single model, still not 100%)
- Overnight gaps can be missed if FXI/US diverges from HK
- Cannot predict news-driven moves
- GRU requires 10 days of historical data
