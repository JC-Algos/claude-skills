# Persistence Mode (Ralph) Skill

**Trigger:** User says "ralph:", "persist:", "don't give up:", or "keep trying:" before a task.

## What It Does

Relentless execution mode. Keeps attempting the task until it's **verified complete** — not just "tried". Inspired by the Sisyphus/Ralph pattern: push the boulder until it stays at the top.

## Core Principle

> "It's not done until it's verified done. Failure is just information for the next attempt."

## Behavior

When user triggers persistence mode:

1. **Acknowledge** — "🔄 Persistence mode activated. I won't stop until this is verified complete."

2. **Attempt the task**

3. **Verify the result** — Actually check that it worked (run tests, check output, validate)

4. **If failed:** 
   - Analyze why
   - Try a different approach
   - Repeat from step 2

5. **Only stop when:**
   - ✅ Task is **verified** successful (not just "should work")
   - ❌ Truly impossible (explain why)
   - ⏸️ User explicitly says stop
   - ⚠️ Would cause harm to continue

## Verification Standards

Don't just assume success. Actually verify:

| Task Type | Verification Method |
|-----------|-------------------|
| Code fix | Run the code/tests, confirm no error |
| File creation | Check file exists and has correct content |
| API call | Verify response is as expected |
| Installation | Test the installed thing works |
| Build | Run the build, check output |

## Attempt Strategies

When an attempt fails, try:

1. **Different approach** — Alternative method to achieve same goal
2. **Decomposition** — Break into smaller steps
3. **Research** — Search for solutions others have found
4. **Debug** — Use systematic-debugging skill
5. **Simplify** — Reduce scope to minimum viable

## Example Triggers

```
ralph: fix the authentication bug
persist: get the tests passing
don't give up: deploy to production
keep trying: make the API respond correctly
```

## Output Format

```
🔄 Persistence mode activated.

Goal: [stated goal]

Attempt 1:
- Tried: [approach]
- Result: ❌ Failed - [reason]

Attempt 2:
- Tried: [different approach]
- Result: ❌ Failed - [reason]

Attempt 3:
- Tried: [another approach]
- Result: ✅ Success
- Verification: [how I confirmed it works]

✅ Persistence complete. Task verified successful.
```

## Limits

- **Max attempts:** 5-7 before asking user for guidance
- **Time limit:** If taking too long, checkpoint and ask
- **Scope creep:** Stay focused on original goal
- **Harm prevention:** Don't persist into dangerous territory

## Combining with Autopilot

`ralph autopilot: [task]` = Autonomous + Persistent

The most aggressive mode: work autonomously AND don't give up until verified done.

## Anti-Patterns to Avoid

❌ "I tried and it didn't work" (giving up too early)
❌ "It should work now" (not verifying)
❌ Trying the same thing repeatedly (insanity)
❌ Persisting on impossible tasks forever
