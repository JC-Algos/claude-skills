# HSI Daily Range & Direction Forecast

**Date:** 2026-02-01  
**Status:** Design Complete  
**Author:** Oracle 🐷 + Jason

---

## Overview

XGBoost-based model to predict daily HSI trading range and direction probability before market open.

## Targets

| Output | Type | Description |
|--------|------|-------------|
| High % | Regression | Today's high as % from open (typically 0-2%) |
| Low % | Regression | Today's low as % from open (typically -2% to 0%) |
| Direction | Classification | Probability of close > open (0.0-1.0) |

## Features (9 total)

| Feature | Source | Notes |
|---------|--------|-------|
| HSI_close | Yahoo ^HSI | Previous day close |
| HSI_change_pct | Derived | (close - prev_close) / prev_close |
| HSI_EMA20 | Derived | 20-day EMA |
| HSI_MA5 | Derived | 5-day MA (short-term trend) |
| HSI_volatility | Derived | 10-day rolling std of returns |
| SPX_close | Yahoo ^GSPC | S&P 500 previous close |
| NDX_close | Yahoo ^IXIC | Nasdaq previous close |
| USDCNH | Yahoo CNH=X | USD/CNH previous close |
| day_of_week | Derived | 0-4 (Mon-Fri) |

## Model Architecture

```
┌─────────────────────────────────────────────────┐
│                  9 Features                      │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌──────────────┐
│ Model 1│  │ Model 2│  │   Model 3    │
│ XGBoost│  │ XGBoost│  │   XGBoost    │
│  Regr  │  │  Regr  │  │  Classifier  │
└───┬────┘  └───┬────┘  └──────┬───────┘
    ▼           ▼              ▼
  High %      Low %      Direction Prob
 from open   from open    (0.0 - 1.0)
```

| Model | Type | Target | Loss |
|-------|------|--------|------|
| Range High | XGBRegressor | high_pct | MSE |
| Range Low | XGBRegressor | low_pct | MSE |
| Direction | XGBClassifier | up=1/down=0 | Log Loss |

## Validation Strategy

**Walk-Forward with Expanding Window:**

- Training data: 3 years
- Initial train: 18 months
- Test window: 1 month
- Step: Expand by 1 month, test next month
- Result: ~12 independent test periods

```
Year 1        Year 2        Year 3
|────────────|────────────|────────────|
[===TRAIN===]→[TEST1]
[=====TRAIN=====]→[TEST2]
[========TRAIN=======]→[TEST3]
         ...continues monthly...
```

## Metrics

| Model | Metrics |
|-------|---------|
| Range (High/Low) | MAE, RMSE, % predictions within actual range |
| Direction | Accuracy, Precision, Recall, AUC-ROC |

## Data Sources

| Ticker | Description |
|--------|-------------|
| ^HSI | Hang Seng Index |
| ^GSPC | S&P 500 |
| ^IXIC | Nasdaq Composite |
| CNH=X | USD/CNH |

## Project Structure

```
/root/clawd/projects/hsi-forecast/
├── data/
│   ├── raw/              # Downloaded OHLCV
│   └── processed/        # Features + targets
├── models/
│   ├── range_high.json   # Saved XGBoost
│   ├── range_low.json
│   └── direction.json
├── src/
│   ├── fetch_data.py     # Yahoo Finance download
│   ├── features.py       # Feature engineering
│   ├── train.py          # Walk-forward training
│   ├── predict.py        # Daily prediction
│   └── backtest.py       # Performance analysis
├── notebooks/
│   └── exploration.ipynb
└── README.md
```

## Output Format

```json
{
  "date": "2026-02-03",
  "hsi_open": 20500,
  "predicted_high_pct": 0.85,
  "predicted_low_pct": -0.62,
  "predicted_high": 20674,
  "predicted_low": 20373,
  "direction_prob": 0.72,
  "direction": "UP"
}
```

## Integration

- Cron job at 9:00 HKT → run prediction
- Push results to Telegram before market open

---

## Next Steps

1. [ ] Set up project structure
2. [ ] Implement data fetching (fetch_data.py)
3. [ ] Implement feature engineering (features.py)
4. [ ] Implement walk-forward training (train.py)
5. [ ] Backtest and evaluate
6. [ ] Set up daily prediction cron
