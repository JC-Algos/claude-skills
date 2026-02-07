# Feature Requests Log

User-requested capabilities for Oracle agent.

---

## [FEAT-20260127-001] telegram_stock_command

**Logged**: 2026-01-27T08:17:00Z
**Priority**: high
**Status**: in_progress
**Area**: backend

### Requested Capability
Telegram slash command `/stock [TICKER] [MARKET]` to trigger full stock analysis

### User Context
User wants quick access to stock analysis directly from Telegram. Single command should return:
1. TA technical analysis report
2. Price chart with EMAs, volume profile, patterns
3. Gemini news research (48h/7d time windows)

### Complexity Estimate
medium

### Suggested Implementation
1. Agent recognizes `/stock` pattern in messages
2. Parse ticker (required) and market (default: HK)
3. Run in parallel:
   - TA API (port 5003) → report + chart
   - News Research API (port 5004) → Gemini analysis
4. Send results as they complete (TA first, news later)

Example:
- `/stock 0700` → Tencent HK
- `/stock 9868 HK` → XPeng HK
- `/stock TSLA US` → Tesla US

### Metadata
- Frequency: recurring (daily use expected)
- Related Features: n8n workflow, TA API, News Research API

---

## [FEAT-20260127-002] async_news_callback

**Logged**: 2026-01-27T08:00:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Requested Capability
Async callback for long-running Gemini research

### User Context
Gemini news research takes 2-3 minutes. Current implementation blocks or times out. Need async pattern where:
1. TA returns immediately
2. News sends when ready (callback/webhook to Telegram)

### Complexity Estimate
medium

### Suggested Implementation
Option A: n8n workflow with separate Telegram send nodes
Option B: Python background task with callback
Option C: Redis queue with worker

### Metadata
- Frequency: every stock analysis
- Related Features: news_research.py, n8n workflow

---
