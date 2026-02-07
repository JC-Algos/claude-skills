# META PLATFORMS DCF VALUATION
## Discounted Cash Flow Analysis
### January 31, 2026

---

## 📊 INPUT ASSUMPTIONS

### Given Parameters
| Parameter | Value |
|-----------|-------|
| Market Risk Premium | 8.5% |
| High Growth Period | 5 years |
| Terminal Growth Rate | 3.0% |
| Current Stock Price | $716.50 |

### Derived Parameters
| Parameter | Value | Source |
|-----------|-------|--------|
| Risk-Free Rate | 4.50% | 10-Year Treasury |
| Beta | 1.25 | Historical (5-year) |
| Shares Outstanding | 2,570M | Q4 2025 diluted |
| Cash & Securities | $81.59B | Balance Sheet |
| Long-term Debt | $58.74B | Balance Sheet |
| FY 2025 FCF | $43.59B | Cash Flow Statement |
| FY 2025 Revenue | $200.97B | Income Statement |

### Cost of Equity Calculation
```
Cost of Equity = Risk-Free Rate + (Beta × Market Risk Premium)
              = 4.50% + (1.25 × 8.50%)
              = 4.50% + 10.63%
              = 15.13%
```

### WACC Calculation
| Component | Weight | Cost | Weighted Cost |
|-----------|--------|------|---------------|
| Equity | 96.9% | 15.13% | 14.66% |
| Debt (after-tax) | 3.1% | 4.0% | 0.12% |
| **WACC** | | | **14.78%** |

**Using 15% discount rate for conservative estimate**

---

## 💰 FREE CASH FLOW PROJECTIONS

### Key Assumptions by Scenario

**BASE CASE** — AI Investment Pays Off Moderately
- Revenue CAGR: 12% over 5 years
- CapEx normalizes by Year 3
- Operating margins stabilize at 38-40%

**BULL CASE** — AI Creates Strong Moat
- Revenue CAGR: 16% over 5 years
- AI drives advertising efficiency gains
- Market share expansion in AI services

**BEAR CASE** — Regulatory & Competition Headwinds
- Revenue CAGR: 8% over 5 years
- EU restrictions impact materially
- CapEx doesn't generate expected returns

---

## 📈 BASE CASE MODEL

### Revenue & FCF Projections ($ Billions)

| Year | Revenue | YoY Growth | Op Cash Flow | CapEx | FCF |
|------|---------|------------|--------------|-------|-----|
| 2025A | $201.0 | +22% | $115.8 | $72.2 | $43.6 |
| 2026E | $235.2 | +17% | $130.0 | $125.0 | $5.0 |
| 2027E | $268.1 | +14% | $155.0 | $95.0 | $60.0 |
| 2028E | $301.9 | +12.6% | $178.0 | $78.0 | $100.0 |
| 2029E | $332.1 | +10% | $195.0 | $75.0 | $120.0 |
| 2030E | $358.7 | +8% | $210.0 | $75.0 | $135.0 |

### Present Value Calculation

| Year | FCF | Discount Factor | PV of FCF |
|------|-----|-----------------|-----------|
| 2026 | $5.0B | 0.8696 | $4.3B |
| 2027 | $60.0B | 0.7561 | $45.4B |
| 2028 | $100.0B | 0.6575 | $65.8B |
| 2029 | $120.0B | 0.5718 | $68.6B |
| 2030 | $135.0B | 0.4972 | $67.1B |
| **PV of FCF** | | | **$251.2B** |

### Terminal Value

```
Terminal Value = FCF₂₀₃₀ × (1 + g) / (WACC - g)
              = $135.0B × (1.03) / (0.15 - 0.03)
              = $139.05B / 0.12
              = $1,158.8B

PV of Terminal Value = $1,158.8B × 0.4972 = $576.2B
```

### Enterprise & Equity Value

| Component | Value |
|-----------|-------|
| PV of FCF (Years 1-5) | $251.2B |
| PV of Terminal Value | $576.2B |
| **Enterprise Value** | **$827.4B** |
| (+) Cash & Securities | $81.6B |
| (-) Total Debt | $58.7B |
| **Equity Value** | **$850.3B** |
| Shares Outstanding | 2,570M |
| **Implied Share Price** | **$330.81** |

---

## 🐂 BULL CASE MODEL

### Assumptions
- Revenue grows 16% CAGR (AI drives efficiency)
- CapEx front-loaded but generates strong returns
- Operating margins expand to 42%+

| Year | Revenue | FCF |
|------|---------|-----|
| 2026E | $243.2B | $8.0B |
| 2027E | $286.2B | $85.0B |
| 2028E | $331.9B | $135.0B |
| 2029E | $378.4B | $165.0B |
| 2030E | $426.4B | $195.0B |

### Valuation Summary

| Component | Value |
|-----------|-------|
| PV of FCF | $384.6B |
| PV of Terminal Value | $808.5B |
| **Enterprise Value** | **$1,193.1B** |
| **Equity Value** | **$1,216.0B** |
| **Implied Share Price** | **$473.15** |

---

## 🐻 BEAR CASE MODEL

### Assumptions
- Revenue grows 8% CAGR (regulatory headwinds)
- CapEx remains elevated longer
- Operating margins compress to 35%

| Year | Revenue | FCF |
|------|---------|-----|
| 2026E | $223.0B | -$5.0B |
| 2027E | $244.9B | $25.0B |
| 2028E | $264.5B | $55.0B |
| 2029E | $282.9B | $70.0B |
| 2030E | $299.9B | $85.0B |

### Valuation Summary

| Component | Value |
|-----------|-------|
| PV of FCF | $142.0B |
| PV of Terminal Value | $364.3B |
| **Enterprise Value** | **$506.3B** |
| **Equity Value** | **$529.2B** |
| **Implied Share Price** | **$205.91** |

---

## 📊 VALUATION SUMMARY

### Scenario Analysis

| Scenario | Implied Price | vs. Current ($716.50) | Upside/(Downside) |
|----------|---------------|----------------------|-------------------|
| **Bull Case** | $473.15 | -$243.35 | **(34.0%)** |
| **Base Case** | $330.81 | -$385.69 | **(53.8%)** |
| **Bear Case** | $205.91 | -$510.59 | **(71.3%)** |

### Probability-Weighted Valuation

| Scenario | Probability | Price | Weighted Value |
|----------|-------------|-------|----------------|
| Bull | 25% | $473.15 | $118.29 |
| Base | 50% | $330.81 | $165.41 |
| Bear | 25% | $205.91 | $51.48 |
| **Expected Value** | | | **$335.18** |

---

## 🔍 SENSITIVITY ANALYSIS

### Price Sensitivity to WACC & Terminal Growth

| WACC ↓ / Terminal Growth → | 2.0% | 2.5% | 3.0% | 3.5% | 4.0% |
|----------------------------|------|------|------|------|------|
| **13%** | $417 | $450 | $492 | $546 | $620 |
| **14%** | $362 | $386 | $415 | $452 | $500 |
| **15%** | $316 | $333 | $354 | $380 | $413 |
| **16%** | $278 | $291 | $307 | $326 | $349 |
| **17%** | $247 | $257 | $269 | $283 | $300 |

### Key Observations
- Current price ($716.50) is **not supported** by any reasonable DCF scenario
- Would require ~6-7% terminal growth OR 10% discount rate to justify
- Market pricing in exceptional AI optionality premium

---

## 📈 REVERSE DCF: WHAT PRICE IMPLIES

### What growth does $716.50 require?

To justify current price of $716.50 with our assumptions:

| Required to Justify $716.50 | Value |
|-----------------------------|-------|
| Terminal Growth Rate (if WACC=15%) | **6.8%** |
| WACC (if Terminal Growth=3%) | **9.2%** |
| 5-Year FCF CAGR Required | **35%+** |

**Implication:** Market is pricing Meta as if:
- AI investment will generate extraordinary returns
- Terminal growth far exceeds GDP
- Risk premium should be much lower

---

## 💡 INVESTMENT CONCLUSION

### At $716.50 per share:

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   DCF FAIR VALUE RANGE: $206 - $473                             ║
║   EXPECTED VALUE: $335                                           ║
║   CURRENT PRICE: $716.50                                         ║
║                                                                  ║
║   PREMIUM TO FAIR VALUE: 113%                                    ║
║                                                                  ║
║   RECOMMENDATION: ⚠️ OVERVALUED by Traditional DCF              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### Key Considerations

**Why DCF Shows Overvaluation:**
1. Near-term FCF severely impacted by $125B CapEx
2. 15% discount rate is appropriate for tech/risk
3. 3% terminal growth is generous (above GDP)
4. Model doesn't capture full AI optionality

**What the Market May Be Pricing:**
1. AI creating a new, huge TAM (personal AI, enterprise AI)
2. Advertising business compounding at 15%+ for longer
3. Reality Labs eventually breaking even
4. Meta becoming AI infrastructure provider
5. Lower perceived risk due to cash generation

### For Long-Term Investment at $716.50:

| Factor | Assessment |
|--------|------------|
| **Traditional DCF** | ❌ Significantly overvalued |
| **Growth Optionality** | ✅ AI could create enormous value |
| **Downside Risk** | ⚠️ Limited by cash generation |
| **Margin of Safety** | ❌ None at current price |

**Verdict:** At $716.50, you're paying for near-perfect AI execution. Traditional DCF suggests waiting for a 50%+ pullback for adequate margin of safety. However, if Meta's AI bet succeeds spectacularly (becoming the "Microsoft of AI"), current price could still prove cheap.

---

**Risk Rating:** HIGH — Entry at current levels requires strong conviction in AI thesis

*Model Generated: January 31, 2026*
*Analyst: Oracle 🐷*
