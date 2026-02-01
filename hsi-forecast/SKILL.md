---
name: hsi-forecast
description: Predict daily HSI range (high/low) and direction using XGBoost. Uses overnight FXI, US markets, VIX as key features.
---

# HSI Daily Forecast Skill

Predict Hang Seng Index daily trading range and direction before market open using XGBoost models.

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

## Output Format

```json
{
  "date": "2026-02-03",
  "reference_price": 27387.11,
  "predicted_high": 27628,
  "predicted_high_pct": 0.88,
  "predicted_low": 27129,
  "predicted_low_pct": -0.94,
  "predicted_range": 499,
  "direction": "DOWN",
  "direction_prob": 0.25,
  "volatility_regime": "HIGH",
  "gap_adjustment": "FXI -2.9% → gap down"
}
```

## Model Performance

| Metric | Value |
|--------|-------|
| High Range MAE | 0.50% |
| Low Range MAE | 0.48% |
| Direction Accuracy | 72% |
| Direction AUC-ROC | 0.81 |

## Key Features (16 total)

| Feature | Importance | Description |
|---------|------------|-------------|
| fxi_change_pct | 10.3% | FXI ETF overnight change (best HK proxy) |
| day_of_week | 9.0% | Day effects (Monday, etc.) |
| hsi_volatility | 8.3% | 10-day rolling volatility |
| spx_close | 8.3% | S&P 500 close |
| vix | 5.3% | CBOE Volatility Index |
| vix_change_pct | 5.2% | VIX change (fear spike) |

## Gap Adjustment Logic

The model applies post-prediction adjustments based on:

1. **FXI Overnight Move** (primary):
   - FXI down > 0.5% → expect HK gap down
   - FXI up > 0.5% → expect HK gap up
   - Adjustment: Low gets 1.5x FXI move, High gets 0.8x

2. **VIX + US Down** (secondary):
   - VIX rising + US down → additional downside risk
   - Adds 1.5x US average change to low

3. **High VIX Level**:
   - VIX > 20 → widen range by (VIX-20)/100

## Volatility Regimes

| Regime | Vol Ratio | Multiplier |
|--------|-----------|------------|
| LOW | < 0.7 | ×0.85 |
| NORMAL | 0.7-1.0 | ×1.0 |
| HIGH | 1.0-1.5 | ×1.2 |
| EXTREME | > 1.5 | ×1.5 |

## Retrain Model

When you want to update with new data:

```bash
cd /root/clawd/projects/hsi-forecast

# 1. Fetch latest data (3 years)
python3 src/fetch_data.py

# 2. Create features
python3 src/features.py

# 3. Train with walk-forward validation
python3 src/train.py

# 4. Run backtest
python3 src/backtest.py
```

## Generate Charts

```bash
python3 src/visualize.py
```

Creates in `charts/`:
- fitting_chart.png
- correlation_heatmap.png
- direction_analysis.png
- feature_importance.png
- optimization_heatmap.png
- residual_analysis.png

## Data Sources

| Ticker | Source | Description |
|--------|--------|-------------|
| ^HSI | Yahoo | Hang Seng Index |
| FXI | Yahoo | iShares China Large Cap ETF |
| ^GSPC | Yahoo | S&P 500 |
| ^IXIC | Yahoo | Nasdaq Composite |
| ^VIX | Yahoo | CBOE Volatility Index |
| CNH=F | Yahoo | USD/CNH Futures |

## Example Response

When user asks "What's the HSI forecast for tomorrow?":

1. Run prediction:
```bash
cd /root/clawd/projects/hsi-forecast && python3 src/predict.py --format telegram
```

2. Report results:
```
🎯 HSI Forecast for Monday 3 Feb

📊 Predicted Range (from Fri close 27,387):
• High: 27,628 (+0.88%)
• Low: 27,129 (-0.94%)  
• Range: 499 pts

📉 Direction: DOWN (75% probability)

⚠️ Key Signals:
• FXI -2.9% overnight → gap down likely
• VIX elevated at 17.4
• Volatility regime: HIGH
```

## Limitations

- Direction accuracy is 72% (not 100%)
- Overnight gaps can be missed if FXI/US diverges from HK
- Model uses 3 years of data; may not capture regime changes
- Cannot predict news-driven moves
