#!/bin/bash
# Usage: ./analyze.sh TICKER MARKET
# Example: ./analyze.sh 0700 HK
# Example: ./analyze.sh AAPL US

TICKER="${1:-AAPL}"
MARKET="${2:-US}"

# Call TA API
RESULT=$(curl -s -X POST http://localhost:5003/analyze/report \
  -H "Content-Type: application/json" \
  -d "{\"ticker\":\"$TICKER\",\"market\":\"$MARKET\"}")

# Extract report
REPORT=$(echo "$RESULT" | jq -r '.report // "Analysis failed"')

if [ "$REPORT" = "Analysis failed" ]; then
  echo "❌ Analysis failed for $TICKER ($MARKET)"
  echo "$RESULT"
  exit 1
fi

# Send to Telegram via clawdbot
# Send to Telegram - use clawdbot message send
/usr/bin/clawdbot message send --channel telegram --target 1016466977 --message "$REPORT"

echo "✅ Sent analysis for $TICKER ($MARKET)"
