#!/bin/bash
# HK News Scanner - Triggers n8n workflow and generates summary

set -e

echo "🔄 Starting HK news scan..."

# Trigger n8n workflow
echo "📡 Triggering n8n workflow: HK Market News..."
mcporter call n8n.run_webhook workflowName:"HK Market News - With Yahoo Finance" data:'{"trigger":"cron"}' || {
    echo "❌ Failed to trigger n8n workflow"
    exit 1
}

# Wait for headlines file to be generated
echo "⏳ Waiting for headlines file..."
LATEST_HEADLINES=""
for i in {1..30}; do
    LATEST_HEADLINES=$(find /root/clawd/research/hk-daily -name "headlines-*.txt" -type f -mmin -5 2>/dev/null | sort -r | head -1)
    if [ -n "$LATEST_HEADLINES" ]; then
        echo "✅ Found headlines: $LATEST_HEADLINES"
        break
    fi
    sleep 2
done

if [ -z "$LATEST_HEADLINES" ]; then
    echo "❌ No headlines file found within 60 seconds"
    exit 1
fi

# Generate summary in Traditional Chinese
echo "📝 Generating Traditional Chinese summary..."

HEADLINES_CONTENT=$(cat "$LATEST_HEADLINES")
TIMESTAMP=$(basename "$LATEST_HEADLINES" .txt | sed 's/headlines-//')

# Output file
OUTPUT_FILE="/root/clawd/research/hk-daily/${TIMESTAMP}.md"

# Use clawdbot to generate summary
cat > /tmp/hk_news_prompt.txt << 'EOFPROMPT'
根據以下香港/中國市場新聞標題，生成繁體中文摘要：

格式：

# 港股市場新聞摘要
**[自動生成時間戳]**

## 📊 執行摘要
[2-3句話概括主要市場主題和情緒]

## 🔥 重點新聞

### 🟢 看漲訊號
• [列出看漲新聞並註明來源]

### 🔴 看跌訊號
• [列出看跌新聞並註明來源]

### 📰 政策與經濟
• [政策/宏觀新聞]

## 💡 市場影響
[簡潔、針對交易員的分析：應該關注什麼？關鍵水平？應監察的板塊？]

注意事項：
- 海外擴張 = 增長機會（看漲）
- 美國減少干預 = 對中港有利（看漲）
- 政策放寬 = 利好股市（看漲）
- 保持樂觀但實事求是的語氣
- 包括來源引用

---

標題內容：

EOFPROMPT

echo "$HEADLINES_CONTENT" >> /tmp/hk_news_prompt.txt

# Generate summary via Claude (in current session)
echo "🤖 Calling Claude for summary generation..."
echo "GENERATE_HK_NEWS_SUMMARY|$OUTPUT_FILE|$TIMESTAMP" > /tmp/hk_news_trigger.flag

echo "✅ News scan pipeline initiated"
echo "📁 Headlines: $LATEST_HEADLINES"
echo "📄 Summary will be saved to: $OUTPUT_FILE"
