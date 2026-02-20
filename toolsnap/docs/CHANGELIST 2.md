# Phase 1 — OcrFieldMatcher + MPN/ISO Field + Dead Code Cleanup

## Summary
Added intelligent OCR field classification that auto-populates identity fields from label scans, 
a 3rd MPN/ISO field for INSERT-category tools, and cleaned up dead code from the old OCR flow.

---

## NEW FILE

### `core/ocr/OcrFieldMatcher.kt`
Fuzzy matching engine that classifies OCR elements into identity fields:
- **Manufacturer matching**: fuzzy-matches against `DropdownOptions.manufacturers` using exact token match (1.0), full name match (0.95), prefix match (0.8), and Levenshtein distance ≤1 (0.7). Handles multi-word manufacturers by combining adjacent same-line tokens.
- **MPN/ISO detection**: regex-based detection of ISO insert designations (e.g. CNMG120408) and broader MPN patterns. Only active for `ToolCategory.INSERT`.
- **Catalog number**: first unconsumed prominent element with digits, falling back to first unconsumed token.
- **Context-aware labeling**: `thirdFieldLabel()` returns "MPN / ISO Designation" for INSERT, null for all others.

---

## MODIFIED FILES

### `core/model/Tool.kt`
- Added `var mpnIso: String? = null` field between `description` and `unitSystem`
- Added `mpnIso` to `hasData` computed property

### `utils/ManifestV3.kt`
- Added `mpnIso` to `ToolManifest` serialization class
- Added `mpnIso` to `toManifest()` writer
- Added `mpnIso` to `readV3()` reader
- Existing V3 manifests without `mpnIso` read cleanly (`ignoreUnknownKeys = true` + nullable default)

### `core/session/ManifestExporter.kt`
- Added `"mpn_iso" -> tool.mpnIso = v` to `buildPrimaryTool()` form data extraction

### `ui/wizard/WizardNavHost.kt`
- Added `OcrFieldMatcher` import
- Added `mpnIso` state variable alongside `edp`/`manufacturer`
- Added `ocrMatchResult` state for passing match results to picker screen
- Wired `OcrFieldMatcher.classify()` call after OCR completion in `OCR_CAPTURE` phase
- Updated `IdentityEntryScreen` call: passes `initialMpnIso`, updated `onNext` lambda to 4 params
- Updated `IdentityOcrPickerScreen` call: passes `category`, `matchResult`, `initialMpnIso`, updated `onConfirm` lambda to 3 params
- Updated `saveTool()`: writes `tool.mpnIso` from state
- All OCR state reset points now also clear `ocrMatchResult`

### `ui/wizard/IdentityOcrPickerScreen.kt` (rewritten)
- Added `category`, `matchResult`, `initialMpnIso` parameters
- Added 3rd `OcrTargetField` for MPN/ISO (only visible for INSERT category)
- Auto-populates fields from `OcrFieldMatcher.MatchResult` via `LaunchedEffect`
- Auto-advances active field to first empty required field after auto-populate
- Updated `onConfirm` callback to 3 params (edp, manufacturer, mpnIso)
- Chip tap logic handles "mpnIso" as a 3rd active field target
- Instruction text is context-aware based on active field and MPN/ISO label
- Header subtitle shows "Auto-filled from scan" when matchResult is present

### `ui/wizard/IdentityEntryScreen.kt`
- Added `OcrFieldMatcher` import
- Added `initialMpnIso` parameter
- Added `mpnIso` state variable
- Added `showMpnIso`/`mpnIsoLabel` computed from `OcrFieldMatcher.thirdFieldLabel(category)`
- Added MPN/ISO `OutlinedTextField` in MANUAL mode (after ManufacturerDropdown, INSERT only)
- Updated `onNext` callback to 4 params (edp, manufacturer, mpnIso, toolName)

### `config/FormTemplates.kt` (stripped)
- Removed all dead TOOL_DATA form template fields
- Removed duplicate option lists (manufacturers, diameters, coatings, etc.) — these live in `DropdownOptions`
- Kept `FormField`, `InputType`, `FormData` classes (used throughout the app)

### `core/model/CaptureField.kt` (stripped)
- Removed `requiresOcr` as a constructor parameter
- Added `requiresOcr` as a computed property (`get() = this == TOOL_DATA`) for backward compatibility
- Simplified enum constructor to 3 params: `displayName`, `fileName`, `instruction`

---

## DELETED FILES

### `ui/wizard/DataEntryChoiceScreen.kt`
Dead code — the old "ENTER MANUALLY / PHOTO+OCR / SKIP" choice screen. Replaced by the integrated identity flow.

### `ui/wizard/OcrReviewScreen.kt`
Dead code — the old raw-text OCR review screen. Replaced by the chip picker flow.

---

## UNCHANGED FILES (in zip for context)
- `config/CaptureConfig.kt` — no changes needed
- `config/ComponentTemplates.kt` — no changes needed (MPN/ISO already in insert template as `iso_designation`)
- `config/DropdownOptions.kt` — no changes needed
- `core/model/ToolCategory.kt` — no changes needed
- `core/ocr/OcrProcessor.kt` — no changes needed
- `core/session/SessionManager.kt` — no changes needed (references `requiresOcr` which is now computed)
- `ui/wizard/NameOcrPickerScreen.kt` — no changes needed
- `ui/wizard/OcrTargetField.kt` — no changes needed

---

## NOTES FOR NEXT TRANCHE

If you need me to continue to Phase 2, I'll need:
- Any files that reference `DataEntryChoiceScreen` or `OcrReviewScreen` (for import cleanup)
- Any files that reference `FormTemplates.templateFor()` (removed method)
- The full `FormTemplates.templateFor()` call sites if any exist beyond the old wizard flow
