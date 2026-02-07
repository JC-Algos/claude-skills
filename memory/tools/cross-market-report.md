# Cross-Market Correlation Report

## Schedule
| Slot | Time (HKT) | UTC Cron | Focus |
|------|------------|----------|-------|
| Morning | Mon-Fri 07:00 | `0 23 * * 0-4` | US close recap + overnight signals |
| Evening | Mon-Fri 20:00 | `0 12 * * 1-5` | HK close + full day cross-market |
| Weekend | Sat 07:00 | `0 23 * * 5` | Weekly wrap (US Fri close + HK week) |

## Data Sources
1. HK BB Squeeze: `python3 /root/clawd/scripts/hk_squeeze_rrg_analyzer.py 1h json`
2. US BB Squeeze: `python3 /root/clawd/scripts/squeeze_rrg_analyzer.py 1h json`
3. HK News: `python3 /root/clawd/scripts/hk_news_summary.py json`
4. US News: `docker exec n8n-n8n-1 cat /files/$(docker exec n8n-n8n-1 ls -t /files/ | head -1)`

## Delivery
- Telegram: JC Algos NEW (-1003796838384)

## Report Format (FIXED)
```
🔗 **跨市場關聯分析報告**
📅 [Date Time] HKT | 港股 + 美股 + 新聞

━━━━━━━━━━━━━━━

🎯 **核心主題：[1-line summary of dominant theme]**

[2-3 sentence overview connecting the key story across markets]

━━━━━━━━━━━━━━━

📊 **1. 美股BB Squeeze信號**
• [X] Bullish Breakout, [X] Bearish
• 領先象限：[stocks] — [sector interpretation]
• 改善中：[stocks]
• [X] Neutral Squeeze（蓄勢待發）
→ 🔑 [Key takeaway]

📊 **2. 港股BB Squeeze信號**
• [X] Bullish Breakout, [X] Bearish
• 領先象限：[stocks] — [sector interpretation]
• 改善中：[stocks]
→ 🔑 [Key takeaway]

━━━━━━━━━━━━━━━

🔗 **3. 跨市場關聯發現**

**🟢 共振信號（美港同向）：**
• [bullet points of correlated moves/themes]

**🔴 分歧信號（美港背離）：**
• [bullet points of divergences]

**⚡ 催化劑追蹤：**
• [upcoming events, IPOs, policy, earnings]

━━━━━━━━━━━━━━━

📈 **4. 策略啟示**

• **短線**：[actionable near-term view]
• **板塊**：[sector rotation insight]
• **風險**：[key risks to watch]
• **跨市場**：[cross-market positioning insight]

━━━━━━━━━━━━━━━
🐷 Oracle Cross-Market Intelligence
📡 數據源：BB Squeeze + RRG + 新聞聚合 + 美股掃描
```

## Analysis Direction (FIXED)
0. **ALWAYS run `date` first** to confirm current day of week in HKT (UTC+8). Never assume dates.
1. Run all 4 data scripts, collect JSON output
2. Count bullish/bearish breakouts per market
3. Identify RRG quadrant leaders → map to sectors
4. Cross-reference news headlines with squeeze signals
5. Find correlations (same sector strong both markets) and divergences
6. Extract catalysts from news
7. Derive strategy implications
8. Send to Telegram channel using message tool

## Slot-Specific Focus
- **Morning (7am):** Lead with US overnight performance, futures, how Asia should react
- **Evening (8pm):** Lead with HK session results, cross-reference with US setup for tonight
- **Saturday (7am):** Weekly summary, cumulative sector rotation, week-ahead outlook
