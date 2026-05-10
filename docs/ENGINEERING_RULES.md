# Engineering Rules — ToolSnap

**Type:** PROJECT-LEVEL
**Owner:** project
**Baseline:** 2026-04-25

**Apply these rules to every delivery. No exceptions.**

---

## 1. How to use this document

This file is **Tier 1** — rules that apply across every phase of work. It loads every session.

Phase-specific rules live in **Tier 2** at `docs/rules/*.md`. Tier 2 files load on demand, not every session, so the context window stays usable for code. See S9 for the pointer table.

### Tier 2 load protocol (ask up front)

At the start of any coding request, identify which Tier 2 files apply and ask for them before writing any code or plan. For each file requested, state the reason in one line. If no Tier 2 file applies, say so explicitly — do not load Tier 2 files "just in case." If mid-turn you realize a Tier 2 file is needed that wasn't requested, stop and ask; do not proceed on memory.

### Session-start checks

Before answering the first coding request of a session:

1. Confirm `ENGINEERING_RULES.md` is visible in context.
2. Check the PK freshness signal (see S10). If stale, say so before writing code.

---

## 2. Core frame-of-mind rules

These apply on every turn, regardless of phase.

### Read before you claim

Before asserting how existing code works, read the actual source and cite file + line numbers in your response. Never infer behavior from memory, method names, or PK — PK copies may be stale. If unsure which file contains relevant logic, ask rather than guess. **Wrong-file edits are worse than a short delay.** This rule has no exceptions.

### Context freshness (stale context prevention)

This codebase is entirely Claude-generated. Claude has no access to the live filesystem at `C:\ToolSnap`. Code reaches Claude through three sources, in priority order:

1. **Conversation output** — code Claude wrote earlier in this conversation. This is the freshest version and always takes priority.
2. **Uploads** — files attached during the conversation. Fresher than PK; used when a file has changed on disk since PK was collected (e.g., extracted from a prior conversation's delivery).
3. **PK** — populated by PK Collect before the session. Authoritative at conversation start; goes stale as deliveries land.

**When PK is authoritative.** A fresh PK Collect captures the component's `.py`/`.md`/`.json`/`.kt` files and governance docs. At the start of a new conversation, PK is the best available source for every file it contains. Claude should treat PK code as the editing baseline for the **first** edit to any file in a session.

**When PK goes stale.** After Claude delivers a file in the current conversation, the PK copy of that file is outdated. PK does not update mid-conversation. For any further edit to that file, Claude must use its own conversation output — the version it just created — not the PK copy. This happens automatically as long as Claude is aware of the priority order above.

**When a re-upload is needed.** A re-upload is only required when the on-disk version has diverged from what Claude can see — specifically:

- The file was delivered in a **prior conversation** and PK wasn't re-collected before this one.
- The user made manual edits to the extracted file (rare in this workflow, but possible).
- The user reports that the extracted version differs from what Claude delivered (e.g., a merge conflict during extraction).

In these cases, the user uploads the current on-disk version and Claude uses that as the new baseline.

**What this means in practice:**

- **First edit in a session** — PK is the source of truth. No upload needed.
- **Second+ edit to the same file, same conversation** — Claude uses the version it already wrote in this conversation. No upload needed. Do not fall back to the PK copy.
- **New conversation, file changed since PK Collect** — user uploads the current version, or runs a fresh PK Collect before starting.
- **File not in PK, uploads, or conversation output** — Claude stops and asks for it. Do not guess from import signatures, method names, or prior-conversation memory.
- **Multi-delivery sessions** — the more deliveries that land, the more PK drifts from disk. For sessions with 3+ deliveries to the same component, consider starting a fresh conversation with a fresh PK Collect.

**Why this matters:** a stale-context edit produces code that passes Claude's review (it matches what Claude sees) but fails on extraction (it doesn't match what's on disk). The resulting bug is invisible to Claude and wastes a full debug cycle.

### Diagnosis first

On a bug report or feature request, the first response is diagnosis and proposed plan — not code. For bugs: identify the root-cause line from the traceback or log, explain why it fails, then propose a fix. For features: identify affected files and outline the approach. **Do not produce code in the same turn as the initial diagnosis.** Trivial single-line fixes are the only exception.

### Minimal surface area

Limit diffs to the smallest surface area that completes the task. Do not refactor, rename, or restructure code that wasn't part of the request. If you notice a nearby issue worth fixing, flag it separately — do not quietly expand the delivery. Scope creep is a Red Flag (S4).

### Trust the validator

`validate_docs.py` and `validate_code.py` run automatically on every delivery via DRH. They enforce structural integrity, delivery standards, module headers, DRH compatibility, line limits, bare-except detection, and documentation rules. **Do not duplicate their checks mentally.** If the validator passes, the mechanical layer is clean — spend attention on the judgment layer (cited reads, diagnosis, minimal surface area, scope match).

---

## 3. Response-format protocol

Two steps on any coding request:

1. **Cited reads.** Before asserting how existing code behaves, confirm the file is visible — either via PK (first edit) or via upload (re-edit after delivery) — and cite file + line numbers. If the file is in neither, ask for it. No exceptions.
2. **Plan, then proceed.** State the plan in 1-3 sentences, then build. No explicit approval turn — the user interrupts if the plan is wrong.

Trivial fixes (single-line, obvious) skip straight to code with minimal diagnosis. The citation requirement still applies: never claim behavior of existing code without having the current version visible in context (PK or upload).

---

## 4. Red Flags

During-coding cognitive signals. If you notice any of these, **stop and address it before continuing**.

1. **"This should work but I haven't actually run it"** — claim without verification. Run it or mark it untestable.
2. **"I'll fix the edge cases later"** — deferring rigor mid-session. Fix now or list explicitly in TESTING_NOTES.
3. **"I'm modifying a file I haven't seen the current version of"** — context gap. For first edits, PK is authoritative. For re-edits after a delivery, the file must be re-uploaded. See S2 Context freshness.
4. **"The request conflicts with an ER rule"** — triggers the conflict protocol (S8).
5. **"I've been asked (or tempted) to refactor beyond what was requested"** — scope creep. Complete the ask, flag the refactor as a separate item.
6. **"I'm about to use a bare `except: pass`"** — silent exception swallowing. See S5.

Mechanical signatures (`sys.path` hacks, TODOs in delivered code, copy-pasted functions, missing module headers) are caught by `validate_code.py`. Red Flags are for things the validator can't detect — state of knowledge and intent, not artifact content.

---

## 5. Coding rules in Tier 1

Rules that apply across phases. Phase-specific rules live in Tier 2 (S9).

### Line limits

- **400 target** / **600 soft** / **800 hard** (requires cohesion justification on the header `Limit:` line)
- **1200 cohesion exception** — permitted when splitting would scatter one responsibility across modules
- **2000 default maximum** — past ~2000 lines Claude's editing reliability degrades; the operational ceiling beats the architectural ceiling when they conflict. Force the split even if it creates some shared-state coupling.

Full discussion (cohesion rationale, internal organization for large files) in `docs/rules/WRITING_CODE.md`.

### Top code style patterns

- **Guard clauses** over nested conditionals. Fail fast, keep the happy path at base indentation.
- **120-char line limit.** Readable on 1080p without horizontal scroll.
- **Quote convention:** double `"` for user-facing strings and docstrings; single `'` for internal identifiers, dict keys, short constants. Be consistent within a file.

Full style guide (f-strings, imports, type hints, naming) in `docs/rules/WRITING_CODE.md`.

### Core config principle

Config is separate from code. Runtime config lives in `settings.json`, loaded at startup. Compile-time constants live in `config/settings.py`. Never hardcode values that differ between environments. All config keys and expected values must be documented in the project README.

Full config handling (loading, validation, JSON format) in `docs/rules/DEPLOYING_CODE.md`.

### Core error handling

- `try`/`except` on all file operations, database calls, and user input.
- **Never use bare `except: pass`** — silent exception swallowing is a Red Flag (S4). Catch specific exception types; log and either recover explicitly or re-raise.
- Distinguish recoverable errors (retry, skip and continue) from fatal (log CRITICAL, shut down cleanly).

Full error category table, retry patterns in `docs/rules/RUNNING_CODE.md`.

### Shared logger

All modules use Python's built-in `logging` module. No bare `print()` in production code. Use structured log messages that include relevant context (tool ID, import directory, operation being performed).

```python
import logging
logger = logging.getLogger(__name__)
```

Full level table, selection guide, rotation settings in `docs/rules/RUNNING_CODE.md`.

### Database integrity

SQLite is the single source of truth for tool data. All writes go through `core/repo.py` using `core/database.transaction()`. Never write SQL directly from UI or import code — route through the repository layer. Foreign keys are enforced (`PRAGMA foreign_keys=ON`). Schema changes require a migration strategy documented in the CHANGELOG.

### Documentation Standard

Seven doc types exist: README, ARCHITECTURE, CHANGELOG, PROJECT-LEVEL, REFERENCE, GUIDE, ADR. Anything that doesn't fit one of these must be folded into an existing doc or archived.

- **Required header** on every `.md` file (except CHANGELOG, auto-generated files, `todo/` files, and `docs/archive/` files): `Type:` and `Owner:` fields only.
- **CHANGELOG prefixes** — every bullet line uses one of five prefixes: `Fixed:`, `Added:`, `Changed:`, `Removed:`, `Breaking:`. No freeform prose in the entries.
- **No STATE docs, no VERSION files.** Retired types — the validator blocks both.
- **No `docs/` subfolder inside a component.** Component docs live at the component root; project-wide docs live in `C:\ToolSnap\docs\`.
- **Whitelists** control what lives at the project root (only `README.md`) and at `docs/` top level (see DS for the list).

Full spec — type definitions, directory layout, templates, ADR format, migration procedure, rationale — in `docs/DOCUMENTATION_STANDARD.md`.

---

## 6. Pre-Delivery Sequence

Walk these in order before producing the zip. Mechanical checks are the validator's job — this sequence covers the judgment layer.

1. **Scope match** — the final file list matches what was requested. No files touched that weren't part of the ask.
2. **Single Source of Truth** — no duplicate modules, no copy-paste across files. Each piece of logic in exactly one place.
3. **Complete Working Code** — imports verified by execution, no stubs, error handling present on I/O / DB / user input.
4. **Test review** — answer the three questions from `docs/rules/WRITING_TESTS.md` Pre-delivery: what was executed, what could have been but wasn't, what can't be tested here. Untestable items go in TESTING_NOTES in CHANGELOG.
5. **CHANGELOG** — entry written per `docs/DOCUMENTATION_STANDARD.md` CHANGELOG Format. TESTING_NOTES and Manual Steps sections if applicable.
6. **Version bump** — `__version__` in `version.py` incremented. README header matches.
7. **Database schema impact** — if the delivery changes the schema in `core/database.py`, note the migration strategy in CHANGELOG Manual Steps.

> The validator (`validate_docs.py` + `validate_code.py`) enforces structural integrity, delivery standards, module headers, DRH compatibility, line limits, bare-except detection, and documentation. Trust the validator — don't duplicate its checks mentally.

---

## 7. Delivery format

All deliveries ship as a single zip via DropRouterHud (DRH).

- **Prefix:** `ts_` for ToolSnap. DRH routes by prefix and auto-switches profiles.
- **Naming:** `ts_{component}_{version}.zip` or `ts_{component}_{version}_{label}.zip`.
- **Paths inside the zip are project-relative**, rooted at `C:\ToolSnap\`. Example: `toolsnap_db/core/importer.py` or `docs/ENGINEERING_RULES.md`. Uncertain destinations go to zip root — DRH drops them in the project root for manual placement.
- **Only changed files.** No unchanged files to pad the zip.

Full zip structure diagram, DRH integration details, audit locations, rollback procedure in `docs/rules/SHIPPING_CODE.md`.

---

## 8. Rule conflict protocol

When a user instruction conflicts with an ER rule, **flag the conflict in one line and proceed with the user instruction**. No approval turn, no severity carve-out, no "which wins."

The flag exists so the transcript contains a breadcrumb for later review. It does not gate the work. The solo dev has override authority by definition.

Example: *"Note: this conflicts with ER S5 line limit (2000 default maximum). Proceeding per your instruction."* — then code.

---

## 9. Pointers to Tier 2

Ask for these files up front when the request enters the phase.

| Phase            | File                           | Load when you see...                                                         |
|------------------|--------------------------------|------------------------------------------------------------------------------|
| Writing new code | `docs/rules/WRITING_CODE.md`   | new module, refactor, style question, naming, UI framework choice            |
| Writing tests    | `docs/rules/WRITING_TESTS.md`  | adding tests, smoke test, pre-delivery test review, pytest question          |
| Runtime behavior | `docs/rules/RUNNING_CODE.md`   | exception, log, thread, signal, callback, retry, database transactions       |
| System setup     | `docs/rules/DEPLOYING_CODE.md` | config file, secret, database path, performance target, sync setup           |
| Shipping         | `docs/rules/SHIPPING_CODE.md`  | zip, CHANGELOG, DRH, rollback, delivery format, audit location               |

Multiple phases often fire together (e.g., a new feature that adds config and touches exception handling needs both DEPLOYING_CODE and RUNNING_CODE). Ask for each with a one-line reason.

If the request is fully covered by Tier 1 rules alone (a quick single-line fix, a naming question answered by S5), say so and proceed without loading Tier 2.

---

## 10. Session-start checklist

Before the first coding turn of a session:

1. **Confirm ER is visible in context.** If missing from PK, flag it before writing code.
2. **PK freshness check — version.py.** If the user provides a `version.py` (in an upload or pasted into chat), compare its `__version__` against the PK copy. Match = PK is fresh, proceed. Mismatch = PK is stale, flag it immediately: *"PK has v{X.Y} but the current version is v{X.Z} — recommend a fresh PK Collect before we continue."* This check costs near-zero context and catches the most common staleness case: deliveries landed since the last PK Collect. If no `version.py` is provided, fall back to module header line counts as secondary signals.
3. **Confirm PK coverage.** Check that PK contains the files needed for the task. If the task touches files outside PK scope, ask for uploads of those files before starting.
4. **Classify the phase.** See S9. Ask for the Tier 2 files that apply, with a one-line reason per file.
5. **One component per conversation.** Prefer a fresh conversation when switching between `toolsnap_db` and the Android app. Run a fresh PK Collect before starting the new conversation so the cycle resets cleanly. Accumulated deliveries make PK increasingly stale — after 3+ deliveries, a fresh conversation is strongly recommended.

---

**End of Tier 1.**
