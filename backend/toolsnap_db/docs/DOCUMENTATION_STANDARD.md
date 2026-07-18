# Documentation Standard

**Type:** PROJECT-LEVEL
**Owner:** project
**Baseline:** 2026-04-25

---

## Purpose

This is the canonical specification for all documentation in the `C:\ToolSnap\toolsnap_db` ecosystem. It contains the full spec — templates, directory layout, migration procedure, rationale, and edge cases.

The three artifacts involved in doc governance are:

- **`docs/ENGINEERING_RULES.md`** — the human-readable enforceable summary. What Claude consults during delivery planning.
- **`tools/DropRouterHud/validate_docs.py`** — the executable spec. What blocks deliveries at extraction time.
- **This document** — the reference. Full type definitions, directory layout, templates, rationale.

If any two of these disagree on what's enforceable, the validator is the source of truth — it's the one that actually blocks deliveries. If the validator and this doc disagree on procedural detail (templates, wording, migration steps), this doc wins. If the validator and the rules doc disagree on a rule's scope, reconcile them before shipping the next DRH delivery.

---

## The Seven Doc Types

Only these types exist. Anything else must be renamed to fit one, merged into an existing doc, or archived to `docs/archive/`.

| Type | Canonical file | Where | Scope |
|------|----------------|-------|-------|
| README | `README.md` | Component root or project root | What a component is, how to run it |
| ARCHITECTURE | `ARCHITECTURE.md` | Component root | Internal design: module map, data flow, signals, gotchas |
| CHANGELOG | `CHANGELOG.md` | Component root (and project `docs/` for cross-cutting) | Dated version history per delivery |
| PROJECT-LEVEL | whitelisted files | Root, `docs/` top level, or `docs/rules/` | Cross-cutting governance (Engineering Rules, Tier 2 rules, this doc, etc.) |
| REFERENCE | `docs/reference/{topic}.md` | Project `docs/reference/` | External API, protocol, integration notes |
| GUIDE | `docs/guides/{topic}.md` | Project `docs/guides/` | Operational runbooks, playbooks, how-tos |
| ADR | `docs/adr/NNNN-{slug}.md` | Project `docs/adr/` | Numbered, append-only architecture decision records |

### Retired doc types

**STATE docs are retired.** Multi-session work-in-progress context lives in `todo/{component}-{feature}.md` or in the current chat. Validator rule DOC002 rejects any `*STATE*.md` or `*_State.md` filename.

**VERSION files are retired.** `version.py` is the single source of truth. Validator rule DOC003 rejects any loose `VERSION` file at a component root.

### Choosing the right type

When you're about to create a new `.md` file, walk this checklist:

1. **Is it about a specific component?** → README (what/how), ARCHITECTURE (internal design), or CHANGELOG (history). No other type goes at a component root.
2. **Is it a decision worth preserving the reasoning for?** → ADR in `docs/adr/`. Numbered, dated inside the file, immutable once written.
3. **Is it an operational runbook or how-to?** → GUIDE in `docs/guides/`.
4. **Is it external API, protocol, or integration detail?** → REFERENCE in `docs/reference/`.
5. **Is it cross-cutting governance?** → PROJECT-LEVEL. If it's a phase-specific engineering rule, it lives in `docs/rules/` as a Tier 2 doc (see ER §9). Otherwise, its filename must be on the `docs/` top-level whitelist. If it isn't on either whitelist, it probably shouldn't exist — consider folding into an existing PROJECT-LEVEL doc.
6. **Is it work-in-progress context for a feature that spans sessions?** → `todo/{component}-{feature}.md`, not a doc.
7. **None of the above?** → The doc shouldn't exist. Either fold it into one of the above, or the information belongs in docstrings, code comments, or config files.

---

## Directory Layout

### Project root

```
C:\ToolSnap\toolsnap_db\
├── README.md                             # project overview (only .md allowed at root)
├── core/                                 # database, models, importer, repo, dedup
├── config/                               # settings.py, settings.json
├── ui/                                   # PySide6 application
├── utils/                                # helpers (time, text, JSON, manifest, BOM export)
├── tests/                                # pytest test suite
├── todo/                                 # work-in-progress notes
└── docs/                                 # see docs/ Layout
```

### docs/ layout

```
docs/
├── ENGINEERING_RULES.md        # the rules — enforceable summary (Tier 1)
├── DOCUMENTATION_STANDARD.md   # this file
├── CHANGELOG.md                # project-wide, cross-cutting only
├── rules/                      # Tier 2 engineering rules (see ER §9)
│   ├── WRITING_CODE.md
│   ├── WRITING_TESTS.md
│   ├── RUNNING_CODE.md
│   ├── DEPLOYING_CODE.md
│   └── SHIPPING_CODE.md
├── reference/                  # REFERENCE docs — topic subdirectories allowed
│   └── ...
├── guides/                     # GUIDE docs
│   ├── tablet_sync.md
│   └── ...
├── adr/                        # ADR docs — numbered, append-only
│   └── ...
├── templates/                  # starter templates for each doc type
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── REFERENCE.md
│   ├── GUIDE.md
│   └── ADR.md
└── archive/                    # superseded docs, never deleted
    └── ...
```

### TODO files

Work-in-progress context that spans sessions lives in `todo/{component}-{feature}.md`. These are not governed docs — they have no required header, no validator rules, and no type classification. They exist to bridge the gap between conversations.

- **Created** when a multi-session feature needs persistent context that doesn't belong in CHANGELOG (not yet shipped) or ARCHITECTURE (not yet built).
- **Naming:** `{component}-{feature}.md` — e.g., `importer-v4-migration.md`, `ui-photo-gallery.md`.
- **Content:** free-form. Open questions, design sketches, intermediate decisions, blockers. Whatever the next session needs to pick up where this one left off.
- **Deleted** when the work ships. Shipped content moves to CHANGELOG (`Added:` / `Fixed:`); structural changes move to ARCHITECTURE; decision rationale moves to an ADR. The `todo/` file is the scratch pad, not the record.
- **Staleness:** a `todo/` file older than 30 days with no matching recent delivery is likely abandoned. On contact, either revive it (update and continue) or delete it.

---

## Hard Rules

These are enforced by `validate_docs.py` at delivery time. Each rule cites its validator rule ID — that's what you'll see in DRH's tree dialog if the delivery fails.

1. **No version numbers in `.md` filenames** (DOC004). Version lives in `version.py` and CHANGELOG entries. Exception: ADR files use a leading number for ordering (`0007-use-sqlite.md`), which the validator distinguishes from versioning.
2. **No dates in filenames** (DOC004).
3. **No `_OLD`, `_NEW`, `_FINAL`, `_v2`, `_backup`, `_reminder`, `_guardrails`, `_draft`, `_copy` suffixes** (DOC005). If superseded, move to `docs/archive/`. If current, use the canonical name.
4. **No `docs/` subfolder inside a component.** Component docs live at the component root. Project-wide docs live in `C:\ToolSnap\toolsnap_db\docs\`.
5. **No duplicate `.md` filenames across the tree** (DOC009). Same filename in two places means one is wrong. Per-component files (`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`) are exempt — they're expected to repeat per component.
6. **No STATE docs** (DOC002). Retired. Session context lives in `todo/` or current chat.
7. **No VERSION files** (DOC003). Retired. `version.py` is the single source of truth.
8. **Required header on every `.md` file** (DOC010), except CHANGELOG, auto-generated files, `todo/` files, and `docs/archive/` files:

```
# {Title}

**Type:** {README | ARCHITECTURE | REFERENCE | GUIDE | ADR | PROJECT-LEVEL}
**Owner:** {component or project}
```

The header is intentionally minimal — two fields only.

---

## Whitelists

### Project root whitelist (DOC006)

Only this `.md` file may live at `C:\ToolSnap\toolsnap_db\`:

- `README.md`

### docs/ top-level whitelist (DOC007)

Only these `.md` files may live at `docs/` top level:

- `ENGINEERING_RULES.md`
- `DOCUMENTATION_STANDARD.md`
- `CHANGELOG.md`

Everything else under `docs/` goes in `rules/`, `reference/`, `guides/`, `adr/`, `templates/`, or `archive/`.

### docs/ subdirectory whitelist

Only these subdirectories may exist directly under `docs/`:

| Directory | Governed by | Contents |
|-----------|-------------|----------|
| `rules/` | ER §9 pointer table | Tier 2 engineering rule docs (PROJECT-LEVEL). |
| `reference/` | This doc (Seven Doc Types) | REFERENCE docs. Topic subdirectories allowed. |
| `guides/` | This doc (Seven Doc Types) | GUIDE docs — operational runbooks, playbooks, how-tos. |
| `adr/` | This doc (ADR section) | Architecture Decision Records — numbered, append-only. |
| `templates/` | This doc (Templates section) | Starter templates for each doc type. |
| `archive/` | This doc (Hard Rules) | Superseded docs — never deleted, never referenced by live docs. |

Any other subdirectory under `docs/` is a violation.

---

## ARCHITECTURE.md Required Sections

Every component with more than ~5 interacting modules has an `ARCHITECTURE.md` at its root. These sections are advisory — Claude should include all sections when writing or updating an ARCHITECTURE.md.

1. **Header** — the standard required header (Type / Owner)
2. **System Overview** — 2-3 sentences. What it does, what it connects to, what modes it runs in.
3. **Module Map** — table of file, line count, one-line responsibility.
4. **Data Flow** — inline mermaid or ASCII diagrams for major flows. Each followed by 2-3 sentences of context.
5. **External Surfaces** — tablet sync, import pipeline, database schema.
6. **Signal Map** — who emits, who consumes, payload type (PySide6 components only).
7. **Known Gotchas** — short list of things that have caused bugs, with fix references.

### Design decisions don't go here

They go in ADRs. ARCHITECTURE.md describes what the system *is* (current state); ADRs record *why it is that way* (historical reasoning).

### Update cadence

Ships with every point release. Module map line counts change, new flows or gotchas get added. Gated by the Pre-Delivery Checklist (ER §6).

---

## Architecture Decision Records (ADRs)

ADRs capture architecturally significant decisions: why we use SQLite over Postgres, why manifests migrate to V3 in memory, why dedup matches on catalogNumber+manufacturer. Short, dated, immutable.

### Location and numbering

`docs/adr/NNNN-{slug}.md` where `NNNN` is a zero-padded 4-digit sequence number. Slugs are lowercase-kebab-case describing the decision.

### Format

```markdown
# ADR-0001: Use SQLite for local tool database

**Type:** ADR
**Owner:** project

**Date:** 2026-04-25
**Status:** Accepted

## Context

What situation or problem prompted this decision?

## Decision

What we decided.

## Consequences

What follows — positive, negative, and tradeoffs accepted.
```

### When to write an ADR

Any decision you'd want to explain to yourself six months from now:

- Database schema choices (why the Components table uses a composite PK)
- Import pipeline design (why V1→V3 migration happens in memory)
- Dedup strategy (why catalogNumber+manufacturer, not name)
- Sync architecture (why ADB push, not network sync)
- UI framework choice (why PySide6 for the desktop app)

Not ADR-worthy: variable naming, button colors, log message formatting.

### Status field values

- `Proposed` — drafted, not yet adopted
- `Accepted` — active and in force
- `Superseded by ADR-NNNN` — replaced
- `Deprecated` — no longer followed

Editing an ADR's `Status:` is the only permitted edit after it's been accepted. Content is immutable.

---

## CHANGELOG Format

Use [Keep a Changelog](https://keepachangelog.com/) structure. Newest entry at the top. Validator enforces prefix format (DOC011) and requires a dated entry matching the bumped version (DOC012).

```markdown
# CHANGELOG — toolsnap_db

## v1.3 — 2026-02-20

- Fixed: importer crashed on V1 manifests with missing tool_data field
- Fixed: photo path resolution failed on relative paths
- Added: BOM export panel
- Changed: dedup now merges photo lists instead of replacing
- Removed: deprecated `_migrate_v0()` function
- Breaking: `ImportResult` fields renamed for consistency

### TESTING_NOTES
- Tablet sync not tested (requires physical device)
- Verify ADB connection after extract

### Manual Steps
- Add `"qr_label_prefix": "TS"` to settings.json
```

### Prefixes

Five prefixes for bullet lines: `Fixed:`, `Added:`, `Changed:`, `Removed:`, `Breaking:`. No freeform prose. Validator rule DOC011 rejects lines that don't start with one of these.

- **`Fixed:`** — bug fix, behavior correction.
- **`Added:`** — new feature, new capability, new module.
- **`Changed:`** — non-breaking behavioral change, refactor, or performance improvement.
- **`Removed:`** — deleted module, dropped feature, removed config key.
- **`Breaking:`** — API or behavior change that requires consumer updates.

### Optional sections

- **`TESTING_NOTES`** — what wasn't tested and why.
- **`Manual Steps`** — config changes, migrations, one-time actions the user must perform after extraction.

These are section headers (`### TESTING_NOTES`), not prefixes, and their body content is free-form prose.

### Version entry format

- `## v{major}.{minor} — YYYY-MM-DD`
- Date is the delivery date in ISO format
- Version must match `version.py` — validator rule DOC012 catches drift

### Header exemption

CHANGELOG does not carry the standard required header.

---

## Legacy Docs Migration

The existing ToolSnap tree has several files that predate this standard. Migration is on-contact, not bulk.

### Known legacy files to migrate on contact

- `docs/ToolSnap_Current_State.md` — STATE doc → fold into CHANGELOG (what shipped) and `todo/` (what's pending), then delete.
- `docs/ToolSnap_Architecture.md` — move to project root as `ARCHITECTURE.md`, reformat to match required sections.
- `docs/CHANGELIST 2.md` — rename to `CHANGELOG.md`, reformat entries to use prefixes.
- `ToolSnap_Hardening_Punch_List.md` (exists in two places) — fold into `todo/toolsnap-hardening.md`, delete both copies.
- `ToolSnap_V2_Data_Model.md` — move to `docs/reference/data_model.md` or fold into ARCHITECTURE.
- `ToolSnap_V2_Relational_Redesign.md` — move to `docs/adr/` as a decision record, or `docs/archive/` if superseded.
- `TOOLSNAP_DATA_MODEL.md` — consolidate with the V2 data model doc. One source of truth.
- `ToolSnap_PC_Database_Prompt.md` — archive to `docs/archive/`.
- `TOOLSNAP_SYNC_GUIDE.md` — move to `docs/guides/tablet_sync.md`.
- `claude state on error.txt` — delete (scratch file).

### Don't bulk-migrate

Clean up only what you're already touching. Routine deliveries do on-contact cleanup only.

---

## Templates

Starter templates live in `docs/templates/`. Copy and fill out rather than writing from scratch.

- `docs/templates/README.md` — for component READMEs
- `docs/templates/ARCHITECTURE.md` — for component architecture docs
- `docs/templates/CHANGELOG.md` — for component changelogs (first entry skeleton)
- `docs/templates/REFERENCE.md` — for `docs/reference/` entries
- `docs/templates/GUIDE.md` — for `docs/guides/` entries
- `docs/templates/ADR.md` — for `docs/adr/` entries

---

## Enforcement

The enforcement stack, from weakest to strongest:

1. **This document** — the reference. Readable but not runnable.
2. **Engineering Rules §5 Documentation Standard** — the summary. Informs Claude's pre-delivery decisions.
3. **Engineering Rules Pre-Delivery Sequence (§6)** — the self-audit hook. Claude walks it before shipping.
4. **`validate_docs.py`** — the executable spec. Runs in DRH pre-extraction. Blocks the delivery if rules fail.

The validator is the only layer that cannot be skipped or forgotten. If a rule isn't in the validator, it isn't really enforced — it's a suggestion.
