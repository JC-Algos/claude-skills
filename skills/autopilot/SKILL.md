# Autopilot Skill

**Trigger:** User says "autopilot:", "auto:", or "just do it" before a task.

## What It Does

Full autonomous execution mode. Takes a goal and executes it end-to-end without asking for confirmation at each step. Only stops when done or truly blocked.

## Behavior

When user triggers autopilot mode:

1. **Acknowledge** — "🤖 Autopilot engaged. I'll handle this end-to-end."

2. **Plan silently** — Break down the task internally (don't ask for approval)

3. **Execute continuously** — Work through each step without pausing for confirmation

4. **Handle errors autonomously** — If something fails, try alternatives before asking

5. **Report on completion** — Summarize what was done

## Rules

- **Don't ask "should I proceed?"** — Just proceed
- **Don't ask "which approach?"** — Pick the best one
- **Don't stop for minor issues** — Work around them
- **DO stop for:** Destructive actions (rm -rf), external sends (emails/tweets), ambiguous requirements
- **DO report:** Final summary, any issues encountered, anything that needs user attention

## Example Triggers

```
autopilot: build a REST API for todo items
auto: refactor the auth module  
just do it - migrate the database to postgres
```

## Output Format

```
🤖 Autopilot engaged.

Goal: [stated goal]

Working...
✓ Step 1 complete
✓ Step 2 complete
✓ Step 3 complete

✅ Autopilot complete.

Summary:
- [what was created/changed]
- [any files modified]
- [any issues to note]
```

## When NOT to Use Autopilot

- Ambiguous requirements needing clarification
- Tasks involving money or payments
- Sending communications to external parties
- Deleting important data
- Security-sensitive operations

For these, drop out of autopilot and ask for confirmation.

## Integration

Works with other skills:
- Uses `writing-plans` internally for complex tasks
- Uses `systematic-debugging` if errors occur
- Uses `verification-before-completion` before declaring done
