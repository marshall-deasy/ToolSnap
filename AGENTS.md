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

## Governance Reminders
- Focused, fresh context only.
- Atomic changes + backups via DropRouter.
- Follow ENGINEERING_RULES.md and DOCUMENTATION_STANDARD.md strictly.

---

**Last Updated**: 2026-07-18