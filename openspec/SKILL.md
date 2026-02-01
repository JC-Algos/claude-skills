---
name: openspec
description: Use when writing specs, planning features, or doing spec-driven development. Covers proposal → specs → design → tasks → implementation workflow with delta specs for brownfield codebases.
---

# OpenSpec - Spec-Driven Development

Lightweight spec framework for AI coding assistants. Agree on what to build before code is written.

## Philosophy

```
fluid not rigid       — no phase gates, work on what makes sense
iterative not waterfall — learn as you build, refine as you go
easy not complex      — lightweight setup, minimal ceremony
brownfield-first      — works with existing codebases, not just greenfield
```

## Quick Start

```bash
# Install
npm install -g @fission-ai/openspec@latest

# Initialize in project
cd your-project
openspec init

# Start working
/opsx:new add-feature-name
```

## Core Workflow

```
/opsx:new ──► /opsx:ff ──► /opsx:apply ──► /opsx:verify ──► /opsx:archive
    │            │             │               │                │
  create     generate       implement       validate         complete
  change    all artifacts    tasks         matches specs      & merge
```

## Commands Quick Reference

| Command | Purpose |
|---------|---------|
| `/opsx:explore` | Investigate before committing to a change |
| `/opsx:new <name>` | Start a new change |
| `/opsx:continue` | Create next artifact (step-by-step) |
| `/opsx:ff` | Fast-forward: create all planning artifacts |
| `/opsx:apply` | Implement tasks from the change |
| `/opsx:verify` | Validate implementation matches artifacts |
| `/opsx:sync` | Merge delta specs into main specs |
| `/opsx:archive` | Archive completed change |
| `/opsx:bulk-archive` | Archive multiple changes |
| `/opsx:onboard` | Guided tutorial |

## Folder Structure

```
openspec/
├── specs/                    # Source of truth
│   ├── auth/spec.md
│   └── ui/spec.md
├── changes/                  # Active work
│   └── add-dark-mode/
│       ├── proposal.md       # Why and what
│       ├── specs/ui/spec.md  # Delta specs
│       ├── design.md         # Technical approach
│       └── tasks.md          # Implementation checklist
└── changes/archive/          # Completed work
    └── 2025-01-24-add-dark-mode/
```

## Artifacts

### 1. Proposal (`proposal.md`)

Captures intent, scope, and approach:

```markdown
# Proposal: Add Dark Mode

## Intent
Users want dark mode for nighttime usage.

## Scope
In scope:
- Theme toggle in settings
- System preference detection
- Persist in localStorage

Out of scope:
- Custom color themes (future)

## Approach
CSS custom properties + React context
```

### 2. Specs (Delta Format)

Delta specs describe **what's changing**:

```markdown
# Delta for UI

## ADDED Requirements

### Requirement: Theme Selection
The system SHALL support light and dark themes.

#### Scenario: Toggle theme
- GIVEN the app is in light mode
- WHEN user clicks theme toggle
- THEN the app switches to dark mode
- AND preference is saved to localStorage

## MODIFIED Requirements

### Requirement: Default Theme
The system MUST use system preference as default.
(Previously: Always light mode)

## REMOVED Requirements

### Requirement: High Contrast Mode
(Deprecated - replaced by theme system)
```

**Sections:**
- `## ADDED Requirements` → Appended on archive
- `## MODIFIED Requirements` → Replaces existing
- `## REMOVED Requirements` → Deleted on archive

### 3. Design (`design.md`)

Technical approach and architecture:

```markdown
# Design: Add Dark Mode

## Technical Approach
React Context for state, CSS variables for theming.

## Architecture Decisions

### Decision: Context over Redux
- Simple binary state
- No complex transitions
- Avoids new dependency

## Data Flow
ThemeProvider → ThemeToggle ↔ localStorage → CSS Variables
```

### 4. Tasks (`tasks.md`)

Implementation checklist:

```markdown
# Tasks

## 1. Theme Infrastructure
- [ ] 1.1 Create ThemeContext
- [ ] 1.2 Add CSS custom properties
- [ ] 1.3 Implement localStorage persistence

## 2. UI Components
- [ ] 2.1 Create ThemeToggle component
- [ ] 2.2 Add toggle to settings
```

## Workflow Patterns

### Quick Feature (Clear Scope)

```
/opsx:new add-logout → /opsx:ff → /opsx:apply → /opsx:archive
```

### Exploratory (Unclear Requirements)

```
/opsx:explore → /opsx:new → /opsx:continue → ... → /opsx:apply
```

### Parallel Changes

```
Change A: /opsx:new → /opsx:ff → (pause)
Change B: /opsx:new → /opsx:ff → /opsx:apply → /opsx:archive
Change A: /opsx:apply add-feature-a → /opsx:archive
```

## When to Use What

| Situation | Command |
|-----------|---------|
| Clear requirements | `/opsx:ff` |
| Want to review each step | `/opsx:continue` |
| Exploring options | `/opsx:explore` |
| Ready to code | `/opsx:apply` |
| Before archiving | `/opsx:verify` |
| Multiple completed changes | `/opsx:bulk-archive` |

## Spec Format

```markdown
# Auth Specification

## Purpose
Authentication and session management.

## Requirements

### Requirement: User Authentication
The system SHALL issue JWT token on login.

#### Scenario: Valid credentials
- GIVEN valid credentials
- WHEN user submits login
- THEN JWT is returned
- AND user redirected to dashboard

#### Scenario: Invalid credentials
- GIVEN invalid credentials
- WHEN user submits login
- THEN error displayed
- AND no token issued
```

**RFC 2119 Keywords:**
- **MUST/SHALL** — Absolute requirement
- **SHOULD** — Recommended, exceptions exist
- **MAY** — Optional

## CLI Commands

```bash
# Initialize
openspec init

# List changes
openspec list

# Check status
openspec status --change add-dark-mode

# Update after OpenSpec upgrade
openspec update

# List schemas
openspec schemas
```

## Best Practices

### Keep Changes Focused
One logical unit per change. "Add X and refactor Y" = two changes.

### Name Changes Clearly
```
Good: add-dark-mode, fix-login-redirect, implement-2fa
Bad: feature-1, update, wip, changes
```

### Use Explore for Unclear Requirements
```
/opsx:explore
> How should we handle rate limiting?
```

### Verify Before Archiving
```
/opsx:verify
# Checks: completeness, correctness, coherence
```

### Update vs Start Fresh

**Update existing:**
- Same intent, refined execution
- Scope narrows (MVP first)
- Learning-driven corrections

**Start new:**
- Intent fundamentally changed
- Scope exploded
- Original can be "done" standalone

## Model Recommendations

Works best with high-reasoning models:
- **Claude Opus 4.5** (planning + implementation)
- **GPT 5.2** (planning + implementation)

## Context Hygiene

Clear context before implementation. Maintain clean context throughout session.

## Documentation

- Getting Started: https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md
- Workflows: https://github.com/Fission-AI/OpenSpec/blob/main/docs/workflows.md
- Commands: https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md
- Concepts: https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md
