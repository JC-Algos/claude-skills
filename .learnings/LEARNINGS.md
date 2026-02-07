# Learnings Log

Corrections, knowledge gaps, and best practices discovered during development.

---

## [LRN-20260204-001] best_practice

**Logged**: 2026-02-04T07:25:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
n8n workflows with data pipelines should have single trigger path, not duplicate cron + webhook triggers

### Details
**Problem**: Market sentiment email workflow had stale data for 4+ hours.

**Root cause investigation**:
1. Checked sentiment API - returning data with old timestamp (03:31 vs current 07:17)
2. Checked n8n workflow executions - workflow ran at 07:00 but data wasn't refreshed
3. Found: Python script generates data AND triggers n8n webhook
4. Found: n8n workflow ALSO had its own cron schedule trigger
5. Result: n8n cron ran independently, fetching stale cached data

**Architecture issue**: Two triggers existed:
- System cron → Python script → generates data → triggers n8n webhook ✅
- n8n schedule trigger → directly runs email workflow with cached data ❌

**The fix**: Removed n8n schedule trigger connections, keeping only webhook trigger.

### Suggested Action
For data pipelines with generate→send pattern:
1. Generator script should trigger the sender (single path)
2. Don't add separate cron triggers to both generator AND sender
3. If n8n workflow needs both webhook and cron triggers, ensure they don't duplicate

### Metadata
- Source: user_feedback
- Related Files: 
  - `/root/clawd/projects/market-analyzer/sentiment/market_sentiment.py`
  - n8n workflow ID: M6GuLyuCliDOSTg8
- Tags: n8n, cron, webhook, data-pipeline, stale-data
- Promoted: TOOLS.md (memory/tools/n8n-workflows.md)

### Resolution
- **Resolved**: 2026-02-04T07:23:00Z
- **Method**: Used mcporter to disconnect Schedule Trigger node in n8n workflow
- **Command**: `mcporter call n8n.update_workflow workflowId:M6GuLyuCliDOSTg8 connections:...`

---

## [LRN-20260204-002] best_practice

**Logged**: 2026-02-04T07:25:00Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Debugging stale data issues: check timestamps at each stage of the pipeline

### Details
**Effective debugging pattern for "data not updating" issues**:

1. **Check the data source** - What timestamp does the API/file show?
   ```bash
   curl -s http://api/data | jq '.timestamp'
   stat --format="%y" /path/to/data.json
   ```

2. **Check execution history** - Did the jobs actually run?
   ```bash
   mcporter call n8n.list_executions workflowId:XXX limit:5
   tail /tmp/cron.log
   ```

3. **Trace the trigger chain** - Who triggers what?
   - System cron → what script?
   - Script → does it trigger downstream?
   - Workflow → does it have its own schedule?

4. **Look for duplicate triggers** - Multiple schedulers often cause issues

### Suggested Action
Add to debugging checklist for scheduled jobs:
- Timestamp at data source
- Execution logs for all components
- Trigger chain diagram
- Check for duplicate/competing schedules

### Metadata
- Source: conversation
- Tags: debugging, cron, stale-data, timestamps, pipelines

---

## [LRN-20260204-003] correction

**Logged**: 2026-02-04T09:09:00Z
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
Short selling report WhatsApp messages should show top 10 (same as Telegram), not shortened to 5

### Details
When sending short selling report to WhatsApp destinations, I incorrectly shortened the list to only 5 items per section. Jason corrected that WhatsApp should show the same top 10 as Telegram.

**Wrong**: Shortened WhatsApp to top 5 to save space
**Correct**: WhatsApp gets same top 10 as Telegram

### Suggested Action
Always send top 10 for both SFC positions and HKEX daily data to ALL destinations (Telegram AND WhatsApp)

### Metadata
- Source: user_feedback
- Tags: short-selling, whatsapp, telegram, report-format

### Resolution
- **Resolved**: 2026-02-04T09:09:00Z
- **Notes**: Will use top 10 for all destinations going forward

---

## [LRN-20260206-001] best_practice

**Logged**: 2026-02-06T14:25:00Z
**Priority**: critical
**Status**: promoted
**Area**: config

### Summary
NEVER invent config keys - always validate against schema before modifying Clawdbot config

### Details
**Incident**: Used hallucinated key `spawnAllowlist` instead of correct `subagents.allowAgents`. Clawdbot enforces strict schema validation - any unrecognized key crashes the Gateway in a loop. User was blocked for entire day.

**Problem pattern**:
1. AI "guesses" a config key name that seems logical
2. Key doesn't exist in schema
3. Gateway refuses to start with "Config invalid"
4. Service stuck in crash loop until manual intervention

**Correct approach**:
1. **Check schema first**: `gateway action=config.schema`
2. **Use safe methods**: `gateway action=config.patch` validates before applying
3. **Never invent keys**: If unsure, check schema or ask user

### Suggested Action
Add to AGENTS.md as mandatory rule for config changes

### Metadata
- Source: error
- Related Files: `/root/.clawdbot/clawdbot.json`
- Tags: config, schema, hallucination, critical, prevention
- See Also: ERR-20260206-001
- Promoted: AGENTS.md

---

## [LRN-20260207-001] correction

**Logged**: 2026-02-07T10:07:00Z
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
Consistently wrong day-of-week mapping in weekly market report — assumed Feb 3 was Monday when it was Tuesday.

### Details
When generating the Weekly Cross-Market Correlation Report (Feb 2-7, 2026), I:
1. **Assumed** Feb 3 = Monday without verifying. The actual mapping: Feb 2 (Mon), Feb 3 (Tue), Feb 4 (Wed), Feb 5 (Thu), Feb 6 (Fri), Feb 7 (Sat).
2. **Missed an entire trading day** (Monday Feb 2) because I only checked memory files for Feb 3-6.
3. **Never ran `date` to verify** despite having shell access.

### Root Cause Analysis
- **Primary:** LLM date intuition is unreliable. I "felt" Feb 3 was Monday because "first weekday of month = Monday" is a common human heuristic, but wrong in this case.
- **Secondary:** I relied on memory file existence (Feb 3-6) instead of checking the actual calendar. Feb 2 had a memory file too, but I never looked.
- **Tertiary:** No verification step existed in the report workflow. The cross-market-report.md template had no "check date first" rule.

### Suggested Action
1. ✅ ALWAYS run `date -d 'YYYY-MM-DD' '+%A'` before labeling days in reports
2. ✅ Added Step 0 to cross-market-report.md: "ALWAYS run `date` first"
3. Promote to AGENTS.md and SOUL.md as a general rule

### Resolution
- **Resolved**: 2026-02-07T10:07:00Z
- **Fix Applied**: Updated `memory/tools/cross-market-report.md` with mandatory date check
- **Report**: Corrected version resent to Telegram channel

### Metadata
- Source: user_feedback
- Related Files: `memory/tools/cross-market-report.md`
- Tags: date-verification, market-reports, assumption-error, never-assume
- See Also: None (first occurrence, but pattern is systemic)

---

## [LRN-20260207-002] best_practice

**Logged**: 2026-02-07T10:07:00Z
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
Never trust LLM date/time intuition — always verify with system commands.

### Details
LLMs have no reliable internal calendar. Day-of-week calculations are frequently wrong, especially for future dates or dates in non-obvious positions (e.g., "what day is Feb 3, 2026?"). This applies to:
- Day-of-week labels in reports
- Cron schedule reasoning (which UTC day maps to which HKT day)
- "Today is X" assumptions without checking

### Suggested Action
Before ANY date-dependent output:
```bash
# Check specific date
date -d '2026-02-03' '+%A %Y-%m-%d'

# Check current time in HKT
TZ='Asia/Hong_Kong' date '+%A %Y-%m-%d %H:%M %Z'

# Check a range
for d in {2..7}; do date -d "2026-02-0$d" '+%A %Y-%m-%d'; done
```

### Metadata
- Source: user_feedback
- Tags: date-verification, best-practice, always-verify, system-commands
- Promoted: AGENTS.md, SOUL.md, memory/tools/cross-market-report.md

---
