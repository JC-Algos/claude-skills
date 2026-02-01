---
name: claude-code-mastery
description: Use when helping deploy, configure, or use Claude Code effectively. Covers installation, CLI commands, settings, CLAUDE.md memory files, skills, subagents, MCP integrations, hooks, headless/SDK mode, GitHub Actions, and best practices.
---

# Claude Code Mastery

Complete reference for deploying and using Claude Code as an agentic coding assistant.

## Overview

Claude Code is an agentic coding tool that reads files, runs commands, makes changes, and works autonomously. Unlike chatbots, it takes action directly on your codebase.

**Key Constraint:** Context window fills fast, and performance degrades as it fills. Manage context aggressively.

## Installation

```bash
# macOS/Linux/WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Homebrew
brew install --cask claude-code

# WinGet
winget install Anthropic.ClaudeCode
```

Start: `cd your-project && claude`

## Essential CLI Commands

| Command | Description |
|---------|-------------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start with initial prompt |
| `claude -p "query"` | One-shot query, then exit (headless) |
| `claude -c` | Continue most recent conversation |
| `claude -r` | Resume a previous conversation |
| `claude commit` | Create a Git commit |
| `claude --model opus` | Use specific model (sonnet/opus/haiku) |

### Key CLI Flags

| Flag | Description |
|------|-------------|
| `--allowedTools` | Auto-approve specific tools |
| `--disallowedTools` | Block specific tools |
| `--append-system-prompt` | Add to system prompt |
| `--system-prompt` | Replace entire system prompt |
| `--max-turns N` | Limit agentic turns (headless) |
| `--output-format json` | Structured output |
| `--dangerously-skip-permissions` | Bypass all permissions |

## CLAUDE.md Memory Files

Claude reads CLAUDE.md at session start. Include:
- Bash commands Claude can't guess
- Code style rules differing from defaults
- Testing instructions
- Repository etiquette
- Architectural decisions

**Locations:**
- `~/.claude/CLAUDE.md` - All projects (personal)
- `./CLAUDE.md` or `.claude/CLAUDE.md` - Project-specific
- `CLAUDE.local.md` - Personal, gitignored

**Keep it concise!** Bloated files cause Claude to ignore instructions.

```markdown
# Code style
- Use ES modules (import/export), not CommonJS
- Destructure imports when possible

# Workflow
- Typecheck when done with code changes
- Prefer single tests over full suite
```

## Settings Configuration

Settings live in JSON files with scope hierarchy:
1. **Managed** (highest) - `/Library/Application Support/ClaudeCode/` or `/etc/claude-code/`
2. **Local** - `.claude/settings.local.json`
3. **Project** - `.claude/settings.json`
4. **User** (lowest) - `~/.claude/settings.json`

### Key Settings

```json
{
  "permissions": {
    "allow": ["Bash(npm run *)", "Bash(git *)"],
    "deny": ["Read(./.env)", "WebFetch"],
    "defaultMode": "acceptEdits"
  },
  "model": "claude-sonnet-4-5-20250929",
  "env": { "NODE_ENV": "development" }
}
```

### Permission Modes
- `default` - Standard permission prompts
- `acceptEdits` - Auto-accept file edits
- `plan` - Read-only exploration
- `bypassPermissions` - Skip all checks

## Skills

Skills extend Claude with custom instructions. Create `.claude/skills/<name>/SKILL.md`:

```yaml
---
name: api-conventions
description: REST API design conventions
disable-model-invocation: true  # Only manual /invoke
allowed-tools: Read, Grep, Glob
context: fork  # Run in subagent
---

# API Conventions
- Use kebab-case for URL paths
- Use camelCase for JSON properties
```

Invoke: `/api-conventions` or let Claude load automatically.

**String substitutions:** `$ARGUMENTS`, `$0`, `$1`, `${CLAUDE_SESSION_ID}`

## Subagents

Subagents run in isolated context with custom prompts/tools.

**Built-in:** Explore (fast, read-only), Plan (research for planning), general-purpose

**Create custom:** `.claude/agents/<name>.md`

```yaml
---
name: code-reviewer
description: Reviews code for quality
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: plan
---

You are a senior code reviewer. Focus on quality and security.
```

**CLI:** `claude --agents '{"reviewer":{"description":"...","prompt":"..."}}'`

## MCP (Model Context Protocol)

Connect external tools and data sources.

```bash
# Add remote HTTP server
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Add local stdio server
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "postgresql://user:pass@localhost:5432/db"

# List servers
claude mcp list

# Check status
/mcp
```

**Scopes:** local (default), project (.mcp.json), user

## Hooks

Hooks run commands at lifecycle events.

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./scripts/validate.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "./scripts/lint.sh"
      }]
    }]
  }
}
```

**Events:** SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PermissionRequest, Stop, SubagentStart/Stop

**Exit codes:** 0=success, 2=block action, other=non-blocking error

## Headless/SDK Mode

```bash
# One-off query
claude -p "Explain what this project does"

# Structured output
claude -p "Summarize" --output-format json

# With schema
claude -p "Extract functions" --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array"}}}'

# Continue conversation
session_id=$(claude -p "Start review" --output-format json | jq -r '.session_id')
claude -p "Continue" --resume "$session_id"
```

## GitHub Actions

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "/review"
          claude_args: "--max-turns 5"
```

Install: `/install-github-app` in Claude Code

Use `@claude` in PR/issue comments to trigger.

## Best Practices

### Give Claude Verification
```
"write validateEmail function. Test cases: test@example.com=true, invalid=false"
```

### Explore First, Then Plan, Then Code
Use Plan Mode (`Shift+Tab`) to analyze before implementing.

### Provide Specific Context
```
"add tests for foo.py covering logout edge case. avoid mocks."
```

### Manage Context Aggressively
- `/clear` between unrelated tasks
- `/compact` to summarize
- Use subagents for investigation

### Course-Correct Early
- `Esc` to stop mid-action
- `Esc Esc` or `/rewind` to restore state
- After 2 failed corrections, `/clear` and rewrite prompt

## Common Workflows

### Fix a Bug
```
"the build fails with: [paste error]. Fix it and verify build succeeds."
```

### Create PR
```
/commit-push-pr
```

### Code Review
```
"Review my changes and suggest improvements"
```

### Run Tests
```
"Run the test suite and fix any failures"
```

## Tools Available

| Tool | Permission Required |
|------|---------------------|
| Read | No |
| Write, Edit | Yes |
| Bash | Yes |
| Glob, Grep | No |
| WebFetch, WebSearch | Yes |
| Task (subagent) | No |
| MCP tools | Configurable |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for SDK |
| `CLAUDE_CODE_USE_BEDROCK` | Use AWS Bedrock |
| `CLAUDE_CODE_USE_VERTEX` | Use Google Vertex AI |
| `MAX_THINKING_TOKENS` | Override thinking budget |
| `DISABLE_TELEMETRY` | Opt out of telemetry |

## Quick Reference

```bash
# Start Claude
claude

# Interactive commands
/help          # Show commands
/config        # Open settings
/clear         # Reset context
/compact       # Summarize context
/mcp           # MCP server status
/hooks         # Manage hooks
/permissions   # Manage permissions
/resume        # Resume conversation
/rewind        # Restore checkpoint
```

## Documentation

- Official: https://code.claude.com/docs
- GitHub Action: https://github.com/anthropics/claude-code-action
- MCP: https://modelcontextprotocol.io
