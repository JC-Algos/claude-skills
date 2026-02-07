# TA Report Format Reference

Jason's preferred format for technical analysis output.

## Template

```
📊 {STOCK_NAME} ({TICKER})
━━━━━━━━━━━━━━━━━━━━━━

💰 價格資訊
現價: {PRICE}
漲跌: {CHANGE} ({CHANGE_PCT}%)

📈 趨勢分析 (EMA)
{TREND_EMOJI} {TREND_DESCRIPTION}
排列順序: {EMA_ORDER}
• EMA10: {EMA10}
• EMA20: {EMA20}
• EMA60: {EMA60}
• EMA200: {EMA200}

📏 趨勢強度 (DMI/ADX)
ADX: {ADX}
DI+: {DI_PLUS} | DI-: {DI_MINUS}
趨勢強度: {TREND_STRENGTH}
方向: {DIRECTION}
{DMI_SIGNALS}

📐 斐波那契關鍵位
📍 上方阻力: {RESISTANCE_LEVEL}% @ {RESISTANCE_PRICE}
📍 下方支撐: {SUPPORT_LEVEL}% @ {SUPPORT_PRICE}
• 高點: {HIGH}
• 低點: {LOW}

📊 成交量分析
{VOLUME_STATUS}
近期成交量趨勢: {VOLUME_TREND}
{VOLUME_PRICE_RELATION}

📈 成交量分佈 (Volume Profile)
• PoC (控制點): {POC}
• VAH (價值區高): {VAH}
• VAL (價值區低): {VAL}
• 價值區範圍: {VAL} - {VAH}
📍 {PRICE_VS_VALUE_AREA}
⚠️ {DISTANCE_WARNING}
關注{SUPPORT_OR_RESISTANCE}: {LEVEL_TO_WATCH}

🕯️ K線形態
📊 最新K線: {CANDLE_TYPE}
{CANDLESTICK_PATTERNS}

━━━━━━━━━━━━━━━━━━━━━━
⏰ 分析時間: {TIMESTAMP} UTC
📌 數據週期: {DATA_PERIOD}
```

## Key Elements

1. **Price Info** - Current price with change
2. **EMA Trend** - All 4 EMAs (10/20/60/200) with order and trend description (ALL values must be 2 decimal places)
   - **多頭排列**: EMA10 > EMA20 > EMA60 > EMA200 (完美多頭)
   - **空頭排列**: EMA10 < EMA20 < EMA60 < EMA200 (完美空頭)
   - **上升趨勢**: 60 > 200 (長線多頭)
   - **上升趨勢整固**: 60 > 200 但 10 < 20 (短期回調整理，長線仍多頭)
   - **下降趨勢**: 60 < 200 (長線空頭)
   - **下降趨勢整固**: 60 < 200 但 10 > 20 (短期反彈整理，長線仍空頭)
   - **趨勢轉換期**: 其他混合排列
3. **DMI/ADX** - Trend strength indicator (MUST INCLUDE)
4. **Fibonacci** - Key support/resistance levels
5. **Volume Analysis** - Volume status and trend
6. **Volume Profile** - PoC, VAH, VAL with price position analysis
7. **Candlestick Patterns** - Latest candle + detected patterns

## Notes

- Use Traditional Chinese (繁體中文)
- Include emoji indicators for visual clarity
- DMI/ADX section is important - don't skip it
- Volume Profile should show relationship to current price
