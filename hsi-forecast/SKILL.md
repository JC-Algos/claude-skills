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
  "date": "2026-02-01",
  "direction": "DOWN",
  "confidence": 0.667,
  "diffusion": -3,
  "bullish_count": 3,
  "bearish_count": 6,
  "bullish_factors": [">EMA20", "CNH+0.1%", "VIX=17"],
  "bearish_factors": ["<MA5", "HSI-2.1%", "FXI-2.9%", "SPX-0.4%", "NDX-0.9%", "VIX+3.3%"],
  "model_diffusion_agree": true,
  "predicted_high": 27628,
  "predicted_low": 27129,
  "volatility_regime": "HIGH"
}
```

## Confidence Calculation (Diffusion-Based)

The model uses **9 factors** classified as bullish or bearish:

| Category | Factors |
|----------|---------|
| **Technical** | Price >EMA20, Price >MA5, HSI momentum |
| **Overnight** | FXI change, SPX change, NDX change |
| **Currency** | CNH strength (inverted USDCNH) |
| **Volatility** | VIX level (<20 bullish), VIX change (down=bullish) |

### Diffusion Formula

```
Diffusion = bullish_count - bearish_count
Range: -9 (all bearish) to +9 (all bullish)
```

### Confidence Logic

Confidence depends on whether **model prediction** and **diffusion** agree:

| Model + Diffusion | Formula | Example |
|-------------------|---------|---------|
| **Agree** | 50% + (\|diff\|/9 × 50%) | Model=DOWN, Diff=-3 → 67% |
| **Disagree** | 50% - (\|diff\|/9 × 50%) | Model=DOWN, Diff=+3 → 33% |

**Interpretation:**
- Confidence **>50%**: Model and factors agree → trustworthy signal
- Confidence **<50%**: Model and factors conflict → uncertain signal
- Confidence **=50%**: Diffusion is 0 (neutral factors)

### Example

```
Model: DOWN (75% probability)
Factors: 3🟢 bullish, 6🔴 bearish
Diffusion: -3 (bearish)

Model says DOWN + Diffusion is bearish = AGREE ✓
Confidence = 50% + (3/9 × 50%) = 67%
```

## Model Performance

| Metric | Value |
|--------|-------|
| High Range MAE | 0.50% |
| Low Range MAE | 0.48% |
| Direction Accuracy | 72% |
| Direction AUC-ROC | 0.81 |

## Gap Adjustment Logic

Post-prediction adjustments based on overnight moves:

1. **FXI Overnight Move** (primary):
   - FXI down > 0.5% → expect HK gap down
   - FXI up > 0.5% → expect HK gap up

2. **VIX + US Down** (secondary):
   - VIX rising + US down → additional downside risk

3. **High VIX Level**:
   - VIX > 20 → widen range

## Volatility Regimes

| Regime | Vol Ratio | Multiplier |
|--------|-----------|------------|
| LOW | < 0.7 | ×0.85 |
| NORMAL | 0.7-1.0 | ×1.0 |
| HIGH | 1.0-1.5 | ×1.2 |
| EXTREME | > 1.5 | ×1.5 |

## Retrain Model

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

When user asks "What's the HSI forecast?":

```
🎯 **HSI Forecast** (2026-02-01)

📉 **DOWN** | Confidence: **67%**
[██████░░░░]

📊 Diffusion: **-3** (3🟢 vs 6🔴) ✓

🟢 >EMA20, CNH+0.1%, VIX=17
🔴 <MA5, HSI-2.1%, FXI-2.9%, SPX-0.4%, NDX-0.9%, VIX+3.3%

📈 Range: 27,129 → 27,628
   (-0.94% to +0.88%)

⚡ Vol: HIGH | Ref: 27,387
```

## Limitations

- Direction accuracy is 72% (not 100%)
- Overnight gaps can be missed if FXI/US diverges from HK
- Model uses 3 years of data; may not capture regime changes
- Cannot predict news-driven moves
