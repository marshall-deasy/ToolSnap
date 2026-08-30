# ToolSnap — Production Hardening Punch List

**Goal:** Turn the working prototype into a reliable shop-floor tool that doesn't lose data.

---

## Priority 1 — Will Crash or Lose Data (Delivery 7)

### P1.1 — Runtime Permission Requests
**Problem:** App declares CAMERA and storage permissions in the manifest but never requests them at runtime. On Android 6+ (API 23+) the app will crash or silently fail on first launch.  
**Fix:** Add `rememberLauncherForActivityResult` in `MainActivity.kt` for CAMERA permission. Check and request on first wizard entry. Show a clear "ToolSnap needs camera access" rationale screen if denied. Storage permissions only needed on API ≤ 28 (already declared with `maxSdkVersion`); on API 29+ scoped storage to Documents is automatic.

### P1.2 — Manifest Write Failure Protection
**Problem:** `persistActiveSession()` calls `JsonUtils.writeManifest()` with no try/catch. If storage is full, the tablet is ejected mid-write, or the file system errors out, the manifest gets corrupted or half-written. The session is unrecoverable.  
**Fix:** Write to a temp file first (`manifest.json.tmp`), then atomically rename to `manifest.json`. Wrap in try/catch, show a Snackbar error if write fails. Keep the previous manifest intact on failure.

### P1.3 — Image Save Failure Handling
**Problem:** `ImageUtils.saveAndCompress()` could fail (disk full, I/O error) but the caller in `SessionManager.savePhoto()` only checks the boolean return. No user-visible feedback — the photo just silently vanishes.  
**Fix:** Propagate errors to the UI. Show a Snackbar: "Photo save failed — storage may be full." Don't advance the wizard on failure.

### P1.4 — OCR Crash Guard
**Problem:** ML Kit `extractText()` can throw if the image is corrupt, too large, or the ML Kit model hasn't downloaded. The coroutine in `WizardNavHost` has no try/catch around it. Unhandled exception crashes the app.  
**Fix:** Wrap OCR call in try/catch. On failure, show "OCR failed — try retaking the photo" with a RETAKE button. Don't leave the user stuck on a blank screen.

### P1.5 — Tool Name Sanitization for Folder Names
**Problem:** `CaptureConfig.sessionFolderName()` uses regex to clean the name, but characters like `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` are invalid on Windows NTFS. If any slip through, the PC sync script will fail to read the session folder.  
**Fix:** Strip all NTFS-invalid characters. Limit folder name length to 100 chars. Handle empty result after sanitization (fallback to session ID).

---

## Priority 2 — Bad UX, No Data Loss (Delivery 8)

### P2.1 — Back Button / Navigation Handling
**Problem:** No `BackHandler` anywhere. Pressing the hardware/gesture back button during the wizard either does nothing or dumps you to the Android home screen, abandoning the session with no warning.  
**Fix:** Add `BackHandler` in `WizardNavHost`. Back from capture → go to previous step. Back from first step → show "Discard this session?" confirmation dialog. Back from summary → go back to last field. Never silently abandon a session.

### P2.2 — Empty Form Validation
**Problem:** SAVE button on `ManualEntryScreen` fires unconditionally. A user can tap ENTER MANUALLY then immediately tap SAVE with every field blank — the session marks the field as CAPTURED with zero data.  
**Fix:** Require at least one non-empty field to enable SAVE. Gray out the button until something is entered. Show a brief message: "Enter at least one value."

### P2.3 — Loading / Progress Indicators
**Problem:** No loading spinners anywhere. Image compression, OCR processing, and session saving all happen with zero visual feedback. On a slow tablet, the user will tap buttons repeatedly thinking nothing happened.  
**Fix:** Add `CircularProgressIndicator` during photo save (after crop), OCR extraction (already has `ocrProcessing` flag but verify the indicator is visible), and session finalization. Disable action buttons while processing.

### P2.4 — Duplicate Session Name Handling
**Problem:** If the user creates two sessions with the same tool name on the same day, `sessionFolderName()` generates identical folder names. Second session overwrites the first.  
**Fix:** Append a counter suffix when a collision is detected: `2026-02-03_boring-bar-A123`, `2026-02-03_boring-bar-A123_2`. Check in `SessionManager.createSession()`.

### P2.5 — Snackbar / Toast Infrastructure
**Problem:** Zero user-facing error messages in the entire app. Every failure is silent.  
**Fix:** Add a `SnackbarHostState` at the scaffold level in `MainActivity`. Pass it down or use a shared state holder. Wire up error messages for: save failure, OCR failure, permission denial, storage full, session delete confirmation.

---

## Priority 3 — Polish and Robustness (Delivery 9)

### P3.1 — Session Auto-Save / Crash Recovery
**Problem:** If the app is killed mid-wizard (Android kills background apps aggressively), all progress since the last `persistActiveSession()` is lost. Photos are saved incrementally, but if the kill happens between photo capture and the persist call, the manifest is stale.  
**Fix:** Call `persistActiveSession()` after every state change, not just after field captures. Verify on wizard launch that the active session's manifest on disk matches in-memory state. On app restart, detect incomplete sessions and offer to resume.

### P3.2 — Confirm Before Deleting Sessions
**Problem:** `deleteSession` in `SessionManager` just deletes. No confirmation dialog exists except for the bulk "CLEAR SYNCED" flow.  
**Fix:** Add a confirmation dialog in `SessionDetailScreen` before deleting individual sessions: "Delete [tool name]? This cannot be undone."

### P3.3 — Storage Space Check
**Problem:** No awareness of available storage. If the tablet is nearly full, photos will fail and the user won't know why until it's too late.  
**Fix:** Check available space on session creation. Warn if below 100 MB: "Low storage — X MB remaining. Free space before capturing more tools." Block new sessions below 20 MB.

### P3.4 — PC Sync Script — Error Logging to File
**Problem:** Sync script uses `print()` for everything. If run headless or via watch mode, errors scroll off and are lost.  
**Fix:** Add Python `logging` module. Write to `toolsnap_sync.log` with rotation (5 MB max, 3 backups). Log each import with timestamp, session ID, success/failure, error details.

### P3.5 — PC Sync Script — Graceful Failure on Locked Files
**Problem:** If the tablet is disconnected mid-sync (USB yank), the script will crash on file I/O. Partially imported sessions may be marked `.synced` without completing.  
**Fix:** Only write `.synced` marker after successful DB commit AND successful image copy. Wrap the per-session import in try/except so one bad session doesn't abort the entire batch.

### P3.6 — PC Sync Script — Database Backup
**Problem:** `toolsnap.db` is the only copy of all imported data. One bad sync or SQLite corruption and everything's gone.  
**Fix:** Auto-backup the DB before each sync run. Keep last 5 backups: `toolsnap_backup_2026-02-03_143000.db`. Delete older backups automatically.

---

## Priority 4 — Nice to Have (Future Deliveries)

### P4.1 — Landscape / Rotation Lock
Lock the app to portrait to prevent layout issues during camera capture.

### P4.2 — Session Search / Filter on Home Screen
As the session list grows, add a search bar to filter by tool name.

### P4.3 — Bulk Export to ZIP
One-tap export of all sessions (or selected sessions) to a single ZIP file.

### P4.4 — Dark Mode Support
Shop floors with dim lighting benefit from a dark theme.

### P4.5 — Session Edit History
Track when fields were modified, by which method, with timestamps.

---

## Delivery Plan

| Delivery | Scope | Files Touched |
|---|---|---|
| **7** | P1.1–P1.5 (crash/data-loss prevention) | MainActivity, SessionManager, WizardNavHost, ImageUtils, JsonUtils, FileUtils, CaptureConfig |
| **8** | P2.1–P2.5 (UX hardening) | WizardNavHost, ManualEntryScreen, MainActivity, SessionManager, NavHost |
| **9** | P3.1–P3.6 (polish + PC sync hardening) | SessionManager, WizardNavHost, HomeScreen, SessionDetailScreen, toolsnap_sync.py |
| **10+** | P4.x features on a solid foundation | As needed |

---

## Rules for Hardening Work

1. **No new features during hardening** — we're fixing what exists, not adding scope
2. **Every fix gets a user-visible message** — if something goes wrong, the machinist knows
3. **Test on the happy path AND the failure path** — simulate disk full, camera deny, mid-wizard kill
4. **Don't break the manifest schema** — PC sync compatibility must be maintained
5. **Each delivery is independently deployable** — no delivery depends on a future one
