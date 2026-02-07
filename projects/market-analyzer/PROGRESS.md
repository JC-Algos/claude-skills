# Market Analyzer - Progress Log

## 2026-01-27

### Chart Generation Tool (`generate_chart.py`)

**Status:** ✅ Functional

**Features Implemented:**
1. **Candlestick Charts** - Professional mplfinance charts
2. **EMAs** - 10, 20, 60, 200 (calculated on 2-year data for accuracy)
3. **Volume Profile** - YTD calculation with PoC, VAH, VAL lines
4. **Pattern Detection:**
   - Bullish/Bearish Engulfing
   - Double Top/Bottom
   - Head & Shoulders
   - Inverse Head & Shoulders

**Latest Parameter Updates (2026-01-27 07:33 UTC):**
- Double Top/Bottom detection window: **10-60 days** (min 10 days to filter short-term noise)
- Price tolerance between tops/bottoms: **3%** max
- Rationale: Minimum 10-day span ensures meaningful patterns, not just noise

### Detection Parameters

| Pattern | Time Window | Price Tolerance |
|---------|-------------|-----------------|
| Double Top | 10-60 days | 3% |
| Double Bottom | 10-60 days | 3% |
| Head & Shoulders | 30 days per segment | 5% shoulder diff |
| Inv H&S | 30 days per segment | 5% shoulder diff |
| Engulfing | 1 day | 1% gap tolerance |

### Output Location
- Charts saved to: `/root/clawd/research/charts/`
- Naming: `{symbol}_{market}_{period}_{timestamp}.png`

### Usage
```bash
cd /root/clawd/projects/market-analyzer
source venv/bin/activate
python generate_chart.py 0700 --market HK
python generate_chart.py AAPL --market US
```

---

## Next Steps
- [ ] Generate Tencent technical analysis report
- [ ] Add support levels/resistance detection
- [ ] Trend line detection
- [ ] RSI/MACD indicators (optional)
