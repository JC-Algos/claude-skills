# Telegram / WhatsApp Summaries

## BB Squeeze + RRG Scanner

### Scripts (RRG Format Only)
- **港股:** `python3 /root/clawd/scripts/hk_squeeze_rrg_analyzer.py [timeframe] telegram`
- **美股:** `python3 /root/clawd/scripts/squeeze_rrg_analyzer.py [timeframe] telegram`

Timeframes: `1h`, `4h`, `1d`

### Schedule
#### HK BB Squeeze
- **1h Cron:** `0 1,2,3,4,5,6,7 * * 1-5` UTC = 09:00-15:00 HKT (Mon-Fri)
- **1d Cron:** `0 1 * * 1-5` UTC = 09:00 HKT (Mon-Fri)

#### US BB Squeeze
- **1h Cron:** `0 13,14,15,16 * * 1-5` UTC = 21:00-00:00 HKT
- **2h Cron:** `0 18,20 * * 1-5` UTC = 02:00, 04:00 HKT

### Delivery
- ✅ **Telegram:** JC Algos NEW (-1003796838384)
- ❌ **NO WhatsApp** (Telegram only)

### Output Format
```
🇭🇰 港股 BB Squeeze + RRG 分析
📅 [Date] [Time] | [Timeframe]
Scanned: X symbols | Found: X squeezes

━━━━━━━━━━━━━━━

📈 BULLISH SQUEEZE (X) 已突破上軌

🟢 LEADING 領先 (X)
  • [Stock] $[Price] BBW:[X] RSI:[X]

🔵 IMPROVING 改善中 (X)
🟡 WEAKENING 轉弱 (X)
🔴 LAGGING 落後 (X)

━━━━━━━━━━━━━━━

📉 BEARISH SQUEEZE (X) 已跌穿下軌

━━━━━━━━━━━━━━━
🐷 Oracle | RS>100=強於恒指/大市
```

### Schedule (Clawdbot Cron)
| Scan | Schedule (UTC) | HKT |
|------|----------------|-----|
| HK 1h | 1,2,3,4,5,6,7 | 09-15 |
| HK 1d | 1 | 09:00 |
| US 1h | 13,14,15,16 | 21-00 |
| US 2h | 18,20 | 02,04 |

### Notes
- 只報 **BREAKOUT**（已突破上軌/跌穿下軌）
- 唔報 in-squeeze（正在收窄但未 breakout）
- RRG 四象限表示相對強弱動量

---

## News Summaries

### HK News Summary
- **Script:** `python3 /root/clawd/scripts/hk_news_summary.py telegram`
- **Cron:** `0 1-8,10,12,14 * * 1-5` UTC
- **Schedule (HKT):**
  - **Hourly:** 09:00-16:00 (1-8 UTC)
  - **Every 2h:** 18:00, 20:00, 22:00 (10,12,14 UTC)
- **Delivery:**
  - ✅ Telegram: JC Algos NEW (-1003796838384)
  - ✅ WhatsApp: DIM INV Library + Pure Investments
- **Sources:** 信報、明報、AAStocks、Now、Yahoo、Bloomberg、Reuters、SCMP
- **Categories:** 大市走勢, 新股/IPO, 異動股, 盈喜/盈警, AI/科技, 大行報告, 中國經濟, 國際

### US News Summary
- **Source:** `docker exec n8n-n8n-1 cat /files/$(docker exec n8n-n8n-1 ls -t /files/ | head -1)`
- **Cron:** `5 13,14,15,16,18,20,22 * * 1-5` UTC
- **Schedule (HKT):** 21:05-00:05 (hourly), then 02:05, 04:05, 06:05
- **Delivery:**
  - ✅ Telegram: JC Algos NEW (-1003796838384)
  - ❌ NO WhatsApp
- **Categories:** 大市走勢, 黃金/商品, 科技/AI, 政策/Fed, 企業動態, 加密貨幣

---

## Delivery Targets

### Telegram
- **Jason DM:** Sand Tai (id: 90197440)
- **JC Algos Channel:** -1003796838384 (NEW)
- **Bot:** @Oracle_Piggybot (8225795790)

### WhatsApp (via wacli)
- ❌ **Jason:** NO SUMMARIES TO WHATSAPP (requested 2026-02-04)
- **DIM INV Library:** 85262982502-1545129405@g.us
- **Pure Investments:** 85292890363-1425994418@g.us

### Format Rules
⚠️ **IMPORTANT:** Always use COMPLETE/ORIGINAL format - no simplified versions!

---

## Short Selling Report

### Script
`cd /root/clawd/projects/market-analyzer && python3 short_selling_report.py --top 20`

### Schedule
Daily 08:30 UTC (16:30 HKT)

### Delivery
- ✅ Telegram JC Algos: -1003796838384
- ✅ DIM INV Library: 85262982502-1545129405@g.us
- ✅ Pure Investments: 85292890363-1425994418@g.us
- ❌ Jason WhatsApp (removed 2026-02-04)

### Format Requirements
⚠️ **TOP 10 for BOTH Telegram AND WhatsApp** - same content, no shortening!
- SFC累計沽空倉位: Top 10 by % of float
- HKEX今日沽空成交: Top 10 by % of float

### WhatsApp Notes
- wacli store locks when `wacli sync --follow` is running
- Kill sync process before sending: `pkill -f "wacli sync"`
- No markdown tables on WhatsApp - use bullet lists

---

## Cross-Market Correlation Report (跨市場關聯分析)

### Details
- **Config:** `memory/tools/cross-market-report.md`
- **Data Sources:** HK BB Squeeze + US BB Squeeze + HK News + US News (n8n)
- **Session:** Isolated agentTurn (Opus 4-6)

### Schedule (HKT, Mon-Fri + Sat)
| Slot | HKT | UTC Cron | Focus |
|------|-----|----------|-------|
| 🌅 Morning | Mon-Fri 07:00 | `0 23 * * 0-4` | US close recap + HK open signals |
| 🌙 Evening | Mon-Fri 20:00 | `0 12 * * 1-5` | HK close + US tonight setup |
| 📋 Weekend | Sat 07:00 | `0 23 * * 5` | Weekly wrap + week-ahead outlook |

### Delivery
- ✅ Telegram: JC Algos NEW (-1003796838384)

### Format
Fixed template — see `memory/tools/cross-market-report.md` for full spec.
Sections: 核心主題 → 美股BB Squeeze → 港股BB Squeeze → 跨市場關聯(共振/分歧/催化劑) → 策略啟示

---

## Weekly Portfolio Review (每週回顧)

### Schedule
- **Sat 09:00 HKT** (`0 1 * * 6` UTC)

### Data Sources
- All 4 scan scripts (HK/US BB Squeeze + HK/US News)
- Daily memory files (memory/YYYY-MM-DD.md) for the full trading week
- US news files from n8n for each trading day

### Delivery
- ✅ Telegram: JC Algos NEW (-1003796838384)

### Format
核心敘事 → 美股五日紀錄 → 港股表現+板塊 → 跨市場關聯趨勢 → 下週展望
