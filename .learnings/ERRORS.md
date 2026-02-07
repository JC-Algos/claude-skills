# Errors Log

Error entries for debugging and future reference.

---

## [ERR-20260127-001] gemini_api

**Logged**: 2026-01-27T14:40:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Gemini API quota exceeded during stock news research

### Error
```
GoogleGenerativeAIError: You've exhausted your daily quota on this model.
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Please retry in 26.380566561s.
```

### Context
- Command/operation attempted: `/stock TSLA` news research via port 5004
- The Gemini CLI (used for deep research) hit free tier quota limits
- TA analysis still worked, only news research failed

### Suggested Fix
1. Wait for quota reset (daily)
2. Consider upgrading to paid Gemini API tier
3. Implement fallback to alternative news source (Perplexity API already in ta_analyzer.py)

### Metadata
- Reproducible: yes (when quota exhausted)
- Related Files: `/root/clawd/projects/market-analyzer/news_research.py`
- Tags: gemini, quota, api-limits

---

## [ERR-20260206-001] clawdbot_config_hallucination

**Logged**: 2026-02-06T14:25:00Z
**Priority**: critical
**Status**: resolved
**Area**: config

### Summary
Hallucinated config key `spawnAllowlist` caused Gateway crash loop for entire day

### Error
```
Unrecognized key: spawnAllowlist
Config invalid - Gateway refuses to start
```

### Context
- Attempted to configure sub-agent spawning permissions
- Used invented key `spawnAllowlist` which doesn't exist in Clawdbot schema
- Correct key is `agents.list[X].subagents.allowAgents`
- Gateway enforces strict schema validation - unrecognized keys crash the service
- User was blocked for entire day until manual fix

### Root Cause
AI hallucinated a config key without verifying against schema first. Clawdbot uses "Deny by Default" policy with strict validation.

### Suggested Fix
**Before any config modification:**
1. Run `gateway action=config.schema` to verify key exists
2. Use `gateway action=config.patch` for safe partial updates (validates before applying)
3. NEVER guess/invent key names - always validate against schema

### Resolution
- **Resolved**: 2026-02-06T14:25:00Z
- **Fix**: `clawdbot doctor --fix` + `clawdbot config set agents.list[0].subagents.allowAgents '["coder", "webdev"]'`
- **Notes**: User had to manually fix via CLI

### Metadata
- Reproducible: yes (any invalid key causes crash)
- Related Files: `/root/.clawdbot/clawdbot.json`
- Tags: config, schema-validation, hallucination, critical

---
