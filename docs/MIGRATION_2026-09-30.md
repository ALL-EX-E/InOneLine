# Documentation migration — 2026-09-30

## Goal

Stop depending on Google Drive cumulative project files for normal continuation of InOneLine development.

## Canonical GitHub documents

The current facts previously spread across project-state, roadmap, workflow, backlog and audit files are consolidated into:

- `PROJECT_STATE.md`
- `ROADMAP.md`
- `DECISIONS.md`
- `WORKFLOW.md`
- `SOURCE_OF_TRUTH.md`
- `qa/1.0.7-D26.md`
- `history/RECONCILIATION_2026-09-27.md`

Release history remains available through `RELEASE_NOTES_1.0.0.md` … `RELEASE_NOTES_1.0.7.md`, Git history, tags and GitHub Releases.

## Cutover boundary

From **2026-09-30** onward:

- GitHub is authoritative for current project state and roadmap.
- Google Drive is a backup/archive only.
- New durable decisions must be written into GitHub documentation.
- Normal project continuation should not require reading Drive first.

## Raw legacy archive

The connected repository is public. The Drive archive contains large cumulative internal/history files, old screenshots, redundant state snapshots and material that was not necessarily prepared for public publication.

Those raw bytes are therefore **not blindly bulk-published into this public repository**. Doing that without a privacy/secrets review would be unsafe and would also restore the stale-`CURRENT` problem this migration is intended to remove.

The raw Drive archive remains noncanonical forensic backup. If a byte-for-byte GitHub mirror of that archive is desired later, use a separate private repository after a privacy/secrets review.

No Drive file was deleted by this migration.
