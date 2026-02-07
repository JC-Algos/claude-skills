# AGENTS.md - Coder Agent

## Every Session
1. Read `SOUL.md` — your identity
2. Check current task/project context
3. Use git worktrees for isolation

## Workspace
- Main: `/root/clawd` (read-only for reference)
- Projects: Work in git worktrees, not main workspace
- Isolated: Each project gets its own worktree

## Your Human
- **Name:** Jason
- **Timezone:** UTC+8 (HKT)
- **Language:** English for code, Chinese OK for chat

## Development Flow
1. Understand requirements
2. Create worktree/branch
3. Plan implementation
4. Write tests
5. Implement
6. Verify
7. Submit for review

## Skills to Load
- `brainstorming` - design phase
- `writing-plans` - planning phase
- `test-driven-development` - implementation
- `verification-before-completion` - before done

## Daily Memory
Log significant events to `/root/clawd/memory/YYYY-MM-DD.md`
