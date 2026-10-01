# Filesystem / Installed Files Audit — InOneLine 1.0.8

Date: **2026-10-01**

Scope: exact CURRENT 1.0.8 plus maintenance candidate from PR #12.

## Goal

Audit the complete application filesystem lifecycle, not only source code:

- installer-created directories/files;
- first-run/runtime-created directories/files;
- managed media directories;
- backup/restore staging;
- crash leftovers;
- frozen PyInstaller distribution duplicates;
- source ZIP pollution/duplicates;
- legacy files and directories left by older releases.

## Clean install filesystem contract

Validated by Windows regression run `36860717484` — SUCCESS.

After a clean installation, first start and controlled shutdown:

### data directories

- `credentials`
- `music`
- `overlay_backgrounds`
- `soundtrack`
- `wheel_center_icons`

### data files

- `streaming.db`

SQLite `streaming.db-wal` / `streaming.db-shm` may exist transiently while the database is open, but were absent after the validated shutdown.

### root mutable directories

- `data`
- `backups`
- `logs`

`backups` and `logs` are intentionally created by the elevated installer even when empty. The installer grants normal Windows users modify access to these application-owned directories. Removing the empty directories would risk later backup/log creation under a protected installation root such as `C:\InOneLine`.

## Active data directories

### credentials — KEEP

Active DPAPI CredentialStore storage for integration secrets. The Windows credential store creates/uses this directory intentionally.

### music — KEEP

D26 Music Player managed library.

### overlay_backgrounds — KEEP

Managed overlay media.

### soundtrack — KEEP

D26 shared soundtrack library used independently by auction and wheel selections.

### wheel_center_icons — KEEP

D19 wheel/quick-picker center media.

## Retired legacy directory: wheel_jingles

**Finding: real obsolete storage.**

Before D26, wheel soundtrack media used `data/wheel_jingles` and `media_assets.category='wheel_jingles'`.

D26 unified auction/wheel managed soundtrack storage under `data/soundtrack`, but the physical legacy directory/category remained in the current code and backup contract.

PR #12 candidate fixes this by:

- no longer creating `wheel_jingles` on fresh installations;
- migrating legacy managed files into `soundtrack`;
- migrating legacy external media rows to the current category;
- preserving media IDs whenever possible;
- re-pointing the selected wheel soundtrack when a duplicate current soundtrack row already exists;
- never overwriting a different same-name file;
- adopting manually copied legacy audio that has no DB row;
- preserving unsupported/user files instead of deleting them;
- keeping old 1.0.6 full-backup restore compatibility.

Validated markers:

- `LEGACY_WHEEL_JINGLES_MIGRATION=PASS`
- `LEGACY_1_0_6_FULL_BACKUP_RESTORE=PASS`

## Retired legacy file: data/import_template.csv

**Finding: real obsolete installed file.**

The physical template was not read or opened by current runtime code. Current CSV import already contains a richer built-in help dialog with supported headers and examples.

Candidate behavior:

- new installations do not install `import_template.csv`;
- an old copy is removed automatically only when its SHA-256 exactly matches the historical installer template;
- a user-edited file with the same name is preserved.

## Safe stale-runtime cleanup

Candidate startup cleanup is best-effort and never blocks application startup.

Only disposable copies/staging older than 24 hours are eligible:

- `data/.restore_pending_*.db`
- `data/.full_restore_pending_*`
- `data/.full_backup_create_*`
- `data/restore_result.json.tmp`
- `backups/.backup_*.error.txt`
- `backups/.full_restore_safety_work_*`

Validated: `RUNTIME_FILESYSTEM_CLEANUP=PASS`.

### Deliberately NOT auto-deleted

Recovery material is preserved even if old:

- `backups/.full_restore_rollback_*`
- `data/.full_restore_database_*.db`
- `data/.full_restore_db_rollback_*.db`

After a hard failure these files may be the only usable recovery copy.

## Windows temporary Qt plugin staging

For very deep installation paths the long-path compatibility layer may create a per-process Qt plugin staging directory under:

`%TEMP%\InOneLineQt\...`

The current process registers `atexit` cleanup and removes its own stage on normal exit.

No broad age-based deletion was added because another running InOneLine process may still rely on its staged Qt plugins. This is OS temp storage, not persistent application data.

## Frozen distribution duplicate audit

Candidate frozen distribution:

- files: **270**
- uncompressed bytes: **163,100,597**
- exact duplicate groups: **1**
- duplicate extra bytes: **99**

The only exact duplicate content is four 33-byte Qt English translation catalogs:

- `_internal/PySide6/translations/qt_en.qm`
- `_internal/PySide6/translations/qt_help_en.qm`
- `_internal/PySide6/translations/qtbase_en.qm`
- `_internal/PySide6/translations/qtmultimedia_en.qm`

They are framework-owned PySide6 resources. Removing selected Qt translation files to save 99 bytes would add packaging risk for no material benefit, so they are retained.

No other exact duplicate frozen file content was found.

## Dependency payload review

The major non-duplicate runtime dependencies examined are functional:

- QtOpenGLWidgets — wheel OpenGL widget path;
- QtMultimedia — auction/music playback;
- websocket-client — Twitch/DonationAlerts websocket runtimes;
- mutagen format handlers — Music Player metadata/artwork and OGG-family support;
- openpyxl — XLSX integration/export paths.

No dependency was removed merely because a binary/library looked large or similar to another one.

## Clean source snapshot

The old official source workflow copied a post-build workspace and captured build/cache files.

The new source snapshot is produced from Git-tracked bytes only through `tools/create_source_snapshot.py`.

Latest validated candidate:

- tracked source files: **120**
- ZIP bytes: **1,405,361**
- `build/`: absent
- `dist/`: absent
- `__pycache__/`: absent
- `*.pyc`: absent
- generated `conditional_ui_smoke.py`: absent
- `.github/`: intentionally excluded from release source snapshot

Validated: `CLEAN_SOURCE_SNAPSHOT=PASS`.

## Conclusion

Confirmed unnecessary persistent items:

1. `data/wheel_jingles` — obsolete pre-D26 storage; safely migrated/retired.
2. Stock `data/import_template.csv` — obsolete physical template; retired, while user-edited copies are preserved.
3. Old disposable backup/restore staging leftovers after abnormal termination — now cleaned conservatively after 24 hours.

Intentional/required items were not removed:

- active managed-media directories;
- DPAPI credentials directory;
- empty installer-created `backups` and `logs` ACL targets;
- SQLite transient sidecars;
- recovery/rollback material;
- Qt/Python dependency files without proof they are unused;
- the 99 bytes of framework-owned exact Qt translation duplicates.

No other persistent duplicate or unnecessary application-owned directory/file was identified in this filesystem audit.
