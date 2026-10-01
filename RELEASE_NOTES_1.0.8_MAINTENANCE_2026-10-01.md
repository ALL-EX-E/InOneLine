# InOneLine 1.0.8 Maintenance — 2026-10-01

This maintenance release keeps the application version at **1.0.8** and SQLite schema at **19**. It does not advance the normal release cadence.

## Accepted maintenance changes

- Retired the obsolete pre-D26 `data/wheel_jingles` storage.
- Added safe migration of legacy wheel soundtrack files/rows into the shared D26 `data/soundtrack` catalog.
- Preserved compatibility with full backups created by 1.0.6.
- Retired the unused stock `data/import_template.csv`; user-edited legacy copies are preserved.
- Added conservative cleanup of stale disposable backup/restore staging artifacts while preserving recovery/rollback data.
- Replaced post-build workspace copying with a Git-tracked-only source snapshot.
- Added persistent filesystem/source duplicate regression checks.
- Verified the complete clean-install root/data filesystem contract.

## Verification

Accepted candidate head:

`6fa7589625027bc47f51757782f66836b5e60293`

Merged content:

`9d31b4af1ea19c80f257be2fec2b660b3cc4aadb`

The accepted candidate tree and merged tree contain **131 blob files with 0 content differences**.

Automated Windows gates:

- Final candidate regression: `36862136841` — SUCCESS
- Accepted artifact build: `36862185114` — SUCCESS
- Post-merge main regression: `36881245153` — SUCCESS
- Legacy wheel migration: PASS
- Legacy 1.0.6 full-backup restore: PASS
- Runtime filesystem cleanup: PASS
- Source non-empty duplicate groups: 0
- Clean-install filesystem: PASS

Manual Windows QA:

- clean install / first start filesystem: PASS
- wheel soundtrack shared storage and restart persistence: PASS
- auction soundtrack independent persistence: PASS
- Music Player playback/persistence/filesystem: PASS
- full backup/create/restore: PASS
- CSV import/help after template retirement: PASS
- stale-runtime cleanup and recovery preservation: PASS

## Exact accepted artifacts

Installer:

- `InOneLine_1.0.8_MAINTENANCE_FINAL.exe`
- 47,629,306 bytes
- SHA-256 `2b469e334480d5073a15f48c0e0d84ce3926b990dd4e415c4c90ff0885ba28f1`

Source:

- `InOneLine_Source_1.0.8_MAINTENANCE_FINAL.zip`
- 1,408,876 bytes
- SHA-256 `bba8214b87729517036f3d422d5e86b6d56b9f23738d396bd4069b4801429e83`

The published files are the exact manually accepted bytes; they are not rebuilt after acceptance.
