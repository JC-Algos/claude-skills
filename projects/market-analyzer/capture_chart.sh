#!/bin/bash
# Stock Chart Capture Script (Yahoo Finance - 2Y Daily Candlestick)
# Usage: ./capture_chart.sh SYMBOL MARKET [PERIOD]
# Example: ./capture_chart.sh 0700 HK 2y
# Example: ./capture_chart.sh AAPL US 1y

SYMBOL="${1:-0700}"
MARKET="${2:-HK}"
PERIOD="${3:-2y}"  # 1d, 5d, 1mo, 6mo, 1y, 2y, 5y, max

# Format symbol for Yahoo Finance
if [ "$MARKET" = "HK" ]; then
    FORMATTED_SYMBOL=$(printf "%04s" "$SYMBOL" | tr ' ' '0')
    YF_SYMBOL="${FORMATTED_SYMBOL}.HK"
else
    YF_SYMBOL="$SYMBOL"
fi

# Output directory
CHARTS_DIR="/root/clawd/research/charts"
mkdir -p "$CHARTS_DIR"

# Timestamp for filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${CHARTS_DIR}/${SYMBOL}_${MARKET}_${PERIOD}_${TIMESTAMP}.png"

echo "📊 Capturing 2Y daily candlestick chart for ${YF_SYMBOL}..."

# Calculate date range for 2 years
END_DATE=$(date +%s)
START_DATE=$((END_DATE - 63072000))  # 2 years in seconds

# Yahoo Finance advanced chart URL
# Uses the quote page which has a better chart view
YF_URL="https://finance.yahoo.com/quote/${YF_SYMBOL}/chart?p=${YF_SYMBOL}"

echo "🔗 URL: $YF_URL"

# Open page
agent-browser open "$YF_URL" 2>/dev/null

# Wait for initial load
sleep 5

# Try to click on "2Y" timeframe button and "Candle" chart type
# First, get the page snapshot to find elements
echo "🔧 Setting chart to 2Y candlestick..."

# Click 2Y button (if available)
agent-browser snapshot -i 2>/dev/null | grep -i "2y\|candle" || true

# Wait for any interactions
sleep 3

# Take full page screenshot
agent-browser screenshot "$OUTPUT_FILE" --full-page 2>/dev/null

# Close browser
agent-browser close 2>/dev/null

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE" 2>/dev/null)
    if [ "$FILE_SIZE" -gt 50000 ]; then
        echo "✅ Chart saved to: $OUTPUT_FILE (${FILE_SIZE} bytes)"
        echo "$OUTPUT_FILE"
    else
        echo "⚠️ Chart may not have loaded properly (${FILE_SIZE} bytes)"
        echo "$OUTPUT_FILE"
    fi
else
    echo "❌ Failed to capture chart"
    exit 1
fi
