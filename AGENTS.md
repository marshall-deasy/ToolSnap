# ToolSnap AGENTS.md

## Overview
Android machine shop tooling capture app + Windows Python database & sync system.  
Governed by PromptClip context management, DropRouter atomic deliveries, and strict Engineering Rules.

## Agent Roles (Flexible Hybrid)

### Planner
- **Primary**: Claude Code (Plan Mode) — excels at structured, multi-step planning.
- **Alternative**: Grok (high-level reasoning, architecture, creative exploration).
- **Decision**: Use Claude for complex flows/data models; Grok for fast high-level reasoning or when already in Grok session.
- **Deliverables**: Task spec, acceptance criteria, PromptClip collection guidance, and handoff notes.

### Implementer
- **Primary**: Grok Build / Grok CLI — production code, ER/DS compliance, validation.
- Can use Claude when needed for specific modules.

### Reviewer / Validator
- Pre-delivery checklist, governance gates, freshness checks, regression tests.

## Execution Models
**Preferred: Concurrent Agents** (recommended for medium+ tasks)
- Planner in one terminal/window.
- Implementer (Grok Build) in another.
- Handoff via shared Markdown files.

**Fallback: Single Terminal**
- Switch between models in one window (simpler for small tasks).

## Coordination & Handoff
- Use `plans/current-task.md` (or numbered task files) as the living handoff document.
- Always include: Planner model, task description, context pack, acceptance criteria.
- Update this `AGENTS.md` when roles or processes change.

## Current Tasks (2026-07-18)
- Reorganize code references after folder restructure (`android/`, `backend/`)
- Regenerate file trees and PromptClip collections
- ...

## Agent Operating Boundaries

These bind every agent (Claude Code, Grok Build/CLI, or any model) acting on this repo.

### Write scope
- **Editable:** `android/`, `backend/`, `docs/`, `tools/`, and root config files when the task requires.
- **Never edit without an explicit instruction naming the file:** `.git/`, `local.properties`,
  `*.db` / `*.sqlite3`, `*.keystore` and any signing material, and anything outside `C:\ToolSnap`.
- One task per branch. Keep diffs to the smallest surface that completes the task (ER: minimal surface area).

### Stop-and-confirm (pause and ask the human first)
- Any `git commit`, `push`, force-push, branch delete, history rewrite, or `git reset --hard`.
- Deleting or overwriting files the agent did not create; running `PURGE_DB.bat`; overwriting `toolsnap.db`.
- Anything reaching an external service (network publish, email, cloud) or using credentials.

### Authority model
- **Planner** — reasoning, decomposition, review; may edit docs/plans. Does **not** make production
  code changes unless explicitly asked to act as Implementer for a small, scoped task.
- **Implementer** — production code within the write scope, following ENGINEERING_RULES and DOCUMENTATION_STANDARD.
- **Either role** — changes land on a branch; **nothing merges to `main` without human review.**
  Branch + review is the interim gate until CI / the governance kernel exists.

### Operating-model note
ENGINEERING_RULES §2 (PromptClip context, no filesystem access, DropRouterHud zip delivery) describes a
**legacy transport**. Direct-filesystem agents edit in place, and the DRH validators are not currently
present in `tools/`. Until the governance kernel lands, the real safety gate is **branch + human review**
(plus CI once added) — treat "trust the validator" as aspirational, not active.

## Governance Reminders
- Focused, fresh context only.
- Atomic changes + backups via DropRouter.
- Follow ENGINEERING_RULES.md and DOCUMENTATION_STANDARD.md strictly.

---

**Last Updated**: 2026-07-18