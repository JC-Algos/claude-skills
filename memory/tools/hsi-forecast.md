# HSI Daily Forecast

## Overview
4 Judges system for HSI direction prediction

## Script
```bash
cd /root/clawd/projects/hsi-forecast && python3 src/predict.py --format telegram --save
```

## Output Format
```
🎯 HSI Daily Forecast - [Day] [Date]

📊 Predicted Range (from [prev close]):
• High: [price] (+X.XX%)
• Low: [price] (-X.XX%)
• Range: XXX pts (X.XX%)

📈 Direction: UP/DOWN (X↑ vs X↓) | ✅/⚠️ 信心

🗳️ 4 Judges:
• CatBoost (ML): 📈/📉 UP/DOWN (XX%)
• GRU (Deep): 📈/📉 UP/DOWN (XX%)
• ARIMA (Stats): 📈/📉 UP/DOWN (XX%)
• Diffusion: 📈/📉 UP/DOWN (X🟢 vs X🔴)

🟢 Bullish: [signals]
🔴 Bearish: [signals]

⚡ Volatility: LOW/MEDIUM/HIGH (×X.X)
```

## 4 Judges Explained
1. **CatBoost (ML):** Gradient boosting model
2. **GRU (Deep):** Recurrent neural network
3. **ARIMA (Stats):** Statistical time series
4. **Diffusion:** Monte Carlo simulation

## Schedule
- **Cron:** 0 0 * * 1-5 UTC (08:00 HKT)
- **Delivery:** Telegram ONLY (-1003796838384)
  - ❌ NO WhatsApp

## Data Location
- Predictions saved to: `/root/clawd/projects/hsi-forecast/data/predictions.jsonl`

## Key Signals Tracked
- HSI previous day change
- CNH (offshore RMB)
- VIX level and change
- FXI (China ETF)
- SPX, NDX changes
- EMA20, MA5 positions
