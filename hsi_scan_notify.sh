#!/bin/bash
# HSI BB Squeeze Scanner - Telegram Notification Wrapper

INTERVAL="$1"
SCAN_TYPE="$2"

cd /root/clawd

# Run the scanner and capture results
RESULTS=$(python3 hsi_bb_squeeze_scanner_yfinance.py "$INTERVAL" 2>&1)

# Extract key metrics
TOTAL=$(echo "$RESULTS" | grep "Total Scanned:" | awk '{print $3}')
SQUEEZES=$(echo "$RESULTS" | grep "Squeezes Found:" | awk '{print $3}')
HIT_RATE=$(echo "$RESULTS" | grep "Hit Rate:" | awk '{print $3}')

# Count by type
BULLISH=$(echo "$RESULTS" | grep -c "BULLISH SETUPS" || echo "0")
BEARISH=$(echo "$RESULTS" | grep -c "BEARISH SETUPS" || echo "0")
NEUTRAL=$(echo "$RESULTS" | grep -c "NEUTRAL/CONSOLIDATING" || echo "0")

# Extract top opportunities (first 3 from each category)
BULLISH_LIST=$(echo "$RESULTS" | sed -n '/📈 BULLISH SETUPS/,/📉 BEARISH SETUPS\|⏳ NEUTRAL/p' | grep "^[0-9]" | head -3 | awk '{print $2, $3, $4, $5, $6}')
BEARISH_LIST=$(echo "$RESULTS" | sed -n '/📉 BEARISH SETUPS/,/⏳ NEUTRAL\|=========/p' | grep "^[0-9]" | head -3 | awk '{print $2, $3, $4, $5, $6}')

# Build notification message
MESSAGE="🔍 *HSI BB Squeeze Report*
⏰ $(date '+%Y-%m-%d %H:%M HKT')
📊 *${SCAN_TYPE} Scan (${INTERVAL})*

📈 Results:
• Total: ${TOTAL} stocks
• Squeezes: ${SQUEEZES} found
• Hit Rate: ${HIT_RATE}

"

if [ "$SQUEEZES" -gt "0" ]; then
    MESSAGE="${MESSAGE}🎯 *Opportunities:*
"
    
    if [ -n "$BULLISH_LIST" ]; then
        MESSAGE="${MESSAGE}
📈 *Top Bullish:*
${BULLISH_LIST}
"
    fi
    
    if [ -n "$BEARISH_LIST" ]; then
        MESSAGE="${MESSAGE}
📉 *Top Bearish:*
${BEARISH_LIST}
"
    fi
    
    MESSAGE="${MESSAGE}
📁 Full report: /root/clawd/hsi_bb_squeeze_results.json"
else
    MESSAGE="${MESSAGE}
✅ No squeeze opportunities found.
Market conditions normal."
fi

# Send to Telegram
echo "$MESSAGE"
