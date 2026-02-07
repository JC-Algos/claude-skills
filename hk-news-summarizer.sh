#!/bin/bash
# HK News Summarizer - Called when headlines are ready

HEADLINES_FILE="$1"

if [ ! -f "$HEADLINES_FILE" ]; then
    echo "Error: Headlines file not found: $HEADLINES_FILE"
    exit 1
fi

# Extract filename and generate output filename
BASENAME=$(basename "$HEADLINES_FILE" .txt)
TIMESTAMP=$(echo "$BASENAME" | sed 's/headlines-//')
OUTPUT_FILE="/root/clawd/research/hk-daily/${TIMESTAMP}.md"

echo "📰 Summarizing HK market news from: $HEADLINES_FILE"
echo "📝 Output will be saved to: $OUTPUT_FILE"

# Read headlines and generate prompt
HEADLINES=$(cat "$HEADLINES_FILE")

# Create prompt for Claude (this session)
PROMPT="Summarize these Hong Kong/China market news headlines (some in Chinese - translate to English).

Format as:

# HK Market News Update
[Auto-generated timestamp from headlines]

## 📊 Executive Summary
[2-3 sentences covering main market themes and sentiment]

## 🔥 Key Headlines

### 🟢 Bullish Signals
- [List bullish news with sources]

### 🔴 Bearish Signals
- [List bearish news with sources]

### 📰 Policy & Economy
- [Policy/macro news]

## 💡 Market Implications
[Brief trader-focused analysis: What should traders watch? Key levels? Sectors to monitor?]

---

Headlines to summarize:

$HEADLINES

Keep it concise, actionable, and include source attribution."

# For now, just indicate the file is ready - I'll handle it manually when pinged
echo "✅ Ready for summarization"
echo "Prompt prepared (${#PROMPT} chars)"
