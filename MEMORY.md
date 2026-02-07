# MEMORY.md - Long-Term Memory

## About Me
- **Created:** 2026-01-25
- **Identity:** Oracle, a smart pink pig 🐷
- **Purpose:** Direct and efficient assistant for Jason

## About Jason
- **Timezone:** UTC+8 (Hong Kong)
- **Communication:** Telegram
- **Preferences:** Direct, efficient communication

## Key Events
- **2026-01-25:** First boot. Identity established, memory system initialized.
- **2026-01-26:** n8n Forex Analyst workflow fixed (Docker networking: use 172.18.0.1 for host services)
- **2026-01-27:** Major TA system upgrade - RRG + RS integration, cron jobs fixed
- **2026-01-27:** Chart & report format overhaul (see `.learnings/LEARNINGS.md`)

## Technical Systems

### Stock Analysis (`/stock` command)
- **API Endpoint:** `POST http://localhost:5003/analyze/complete`
- **Returns:** report + technical_chart path + rrg_chart path
- **Features:** EMA, DMI/ADX, Fibonacci, Volume Profile, K-line patterns, RRG, RS ranking
- **Files:** `/root/clawd/projects/market-analyzer/`

**Chart Design Standards:**
- EMA: Blue tones (light→dark), increasing thickness (1→5)
- RRG: 100 as center, Chinese labels (領先/改善中/落後/轉弱), fontsize=22
- Report sections: Use `─ ─ ─ ─ ─ ─ ─ ─ ─ ─` dividers (Telegram collapses blank lines)

### Cron Jobs
- Use `wakeMode: "now"` (not "next-heartbeat")
- HK scans: 09:00-16:00 HKT Mon-Fri
- US scans: 21:00-12:00 HKT (US market hours)

### n8n Integration
- n8n runs in Docker → use `172.18.0.1:PORT` to reach host services
- Workflow: "Stock Technical Analyzer" (ID: 0IELKXByeMks9yOW)

## Jason's Preferences
- TA reports in Traditional Chinese (粵語)
- EMA values: 2 decimal places
- RRG labels: 資產輪動, 相對強度比率, 相對強度動能
- No unnecessary footnotes (e.g., "唔喺原有籃子")

---

*This is your curated long-term memory. Update it as you learn and grow.*
