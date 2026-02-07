#!/bin/bash
# Stock Analysis Command Handler
# Usage: ./stock_analysis.sh TICKER [MARKET]

TICKER="${1:-}"
MARKET="${2:-HK}"
CHAT_ID="${3:-1016466977}"

if [ -z "$TICKER" ]; then
    echo "Usage: $0 TICKER [MARKET] [CHAT_ID]"
    exit 1
fi

# Normalize ticker (remove leading zeros for display but keep for HK)
TICKER_UPPER=$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')
MARKET_UPPER=$(echo "$MARKET" | tr '[:lower:]' '[:upper:]')

echo "📊 Analyzing $TICKER_UPPER ($MARKET_UPPER)..."

# Run TA analysis
echo "1. Running TA analysis..."
TA_RESULT=$(curl -s -X POST http://localhost:5003/analyze/report \
    -H "Content-Type: application/json" \
    -d "{\"ticker\":\"$TICKER_UPPER\",\"market\":\"$MARKET_UPPER\"}")

TA_REPORT=$(echo "$TA_RESULT" | jq -r '.report // "TA analysis failed"')

# Generate chart
echo "2. Generating chart..."
cd /root/clawd/projects/market-analyzer
source venv/bin/activate
CHART_OUTPUT=$(python3 generate_chart.py "$TICKER_UPPER" --market "$MARKET_UPPER" --period 13mo 2>&1)
CHART_PATH=$(echo "$CHART_OUTPUT" | grep "Chart saved:" | sed 's/.*: //' | cut -d' ' -f1)

# Run news research (background with timeout)
echo "3. Running Gemini news research..."
NEWS_RESULT=$(timeout 180 curl -s -X POST http://localhost:5004/research \
    -H "Content-Type: application/json" \
    -d "{\"ticker\":\"$TICKER_UPPER\",\"market\":\"$MARKET_UPPER\"}")

NEWS_REPORT=$(echo "$NEWS_RESULT" | jq -r '.report // "News research failed or timed out"')

echo "4. Analysis complete!"
echo "---"
echo "TA Report:"
echo "$TA_REPORT"
echo "---"
echo "Chart: $CHART_PATH"
echo "---"
echo "News Report:"
echo "$NEWS_REPORT"
