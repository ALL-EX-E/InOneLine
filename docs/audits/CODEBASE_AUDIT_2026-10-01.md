# Codebase Audit — InOneLine 1.0.8

Date: **2026-10-01**

Scope: exact accepted/released **InOneLine 1.0.8**, SQLite schema **19**, named migrations **15**.

Accepted source identity:
- Source ZIP: `InOneLine_Source_1.0.8.zip`
- Size: `13,816,053` bytes
- SHA-256: `babd51bc5f6c3e72924f39848253c28d22d36b9e68c9c5d13a24fca5151e2b15`
- Files in official source ZIP: `192`

## Maintenance execution status — 2026-10-02

The findings below are retained as the historical audit record. Current execution status:

- **A1** source snapshot pollution — CLOSED in accepted filesystem maintenance.
- **A2** missing permanent regression foundation — CLOSED.
- **A3** non-reproducible build dependencies — CLOSED via exact build lock.
- **A4** repeated managed-media SQLite connections — **CLOSED / MANUALLY ACCEPTED / MERGED** in PR #13; post-merge regression `36949173717` SUCCESS.
- **A10** documentation drift — CLOSED.
- **A5** verified unused/stale imports — **CLOSED / MANUALLY ACCEPTED / MERGED** in PR #14; post-merge regression `36952721884` SUCCESS.
- **A6** confirmed dead private helpers / compatibility no-ops — next unresolved maintenance item; requires fresh compatibility review.
- **A7–A9** remain pending their own exact-current review.

Canonical A4 QA: `docs/qa/1.0.8-media-sync-maintenance.md`.
Canonical A5 QA: `docs/qa/1.0.8-unused-import-maintenance.md`.

## Audit goal

Check the current program for:
- dead/unreachable branches;
- duplicate or obsolete mechanisms;
- unnecessary imports/code;
- logical interaction between modules;
- opportunities to reuse existing mechanisms instead of creating new ones;
- performance improvements that do not trade away stability;
- release/QA infrastructure weaknesses that could make later refactoring unsafe.

No runtime change was made by this audit.

## Verified clean / protected areas

### Accepted candidate -> current main drift

The accepted candidate commit `af29d033d5d8cf6bcb774355771121c1bdc7d10f` was compared with current `main`.

Result:
- runtime files compared: **83**
- differing runtime files: **0**

The comparison covered `app.py`, `streaming_manager/**`, installer files, data and assets. Post-acceptance changes are documentation/release metadata only.

### Python structure

- `compileall`: PASS.
- Duplicate function/method definitions in the same scope: none found.
- Import-cycle scan: no circular Python import chain found.
- Database mixin method collision scan: no accidental same-name method conflicts found.
- Auction UI mixin method collision scan: no accidental same-name method conflicts found.

### Existing release validation

Accepted 1.0.8 Windows gate `36739896076` passed:
- compile + conditional-UI semantic smoke;
- static UI invariants;
- protected RNG-source diff;
- PyInstaller build;
- Inno Setup build;
- frozen install/start/API smoke.

Manual QA is already recorded as **PASS 1–10 / FINAL**.

## Findings

### A1 — Official source ZIP is polluted by build/cache output

**Priority: HIGH / release infrastructure**

The official source ZIP is created from the already-used CI workspace after compile/build operations.

It contains:
- **72** `.pyc` / `__pycache__` files;
- **11** files under `build/`;
- generated `conditional_ui_smoke.py`.

Compressed size contribution:
- `build/`: about **11.65 MB**;
- bytecode/cache: about **0.78 MB**.

A clean estimate using the same source while excluding build/cache/generated smoke contains about **108 files / 1.37 MB**, instead of 192 files / 13.82 MB.

The repository already has correct `.gitignore` rules for `build/`, `__pycache__/` and `*.pyc`. The workflow bypasses those rules by copying the dirty workspace directly.

**Recommended reuse-first fix:** build the source snapshot from Git-tracked files (or another clean tracked-file staging method), not from the post-build workspace.

Do not rewrite the already released v1.0.8 asset retroactively. Fix the workflow for the next candidate/release.

### A2 — Permanent regression suite is missing from current GitHub source

**Priority: HIGH / safety before refactoring**

Current GitHub source has no persistent `tests/` suite. Important checks for 1.0.7/1.0.8 are embedded directly in workflow YAML.

However the old Drive QA archive still contains reusable test infrastructure, including:
- `tools/gui_smoke_test.py` — ~2170 lines;
- `tools/exe_smoke_test.py`;
- `tools/installer_qa.py`;
- full backup/restore smoke tests;
- frozen-dist audit;
- build-lock tooling.

This is not lost work.

**Recommended reuse-first fix:** restore/adapt this existing QA foundation to current 1.0.8 before broad runtime cleanup. Update only obsolete version/schema/browser-source expectations and add D43/D26/1.0.8 checks.

### A3 — Build dependencies are not fully reproducible

**Priority: MEDIUM-HIGH / stability**

Current `requirements.txt` uses ranges:
- `PySide6>=6.8,<7`
- `openpyxl>=3.1,<4`
- `websocket-client>=1.8,<2`
- `mutagen>=1.47,<2`

The accepted 1.0.8 build actually used:
- PySide6 **6.11.2**
- openpyxl **3.1.5**
- websocket-client **1.9.2**
- mutagen **1.48.1**
- PyInstaller **6.22.2**

The old QA kit already contains a pinned build lock. Reuse it instead of inventing a new dependency mechanism.

**Recommended fix:** maintain a separate exact build/release lock while optionally keeping user/developer requirements range-based.

### A4 — Managed music/soundtrack sync opens SQLite repeatedly

**Priority: MEDIUM / performance**

`sync_managed_media_category()` calls `ensure_managed_media_asset()` once per file. Each call opens its own SQLite connection and re-queries the managed category.

Measured current behavior:
- 20 managed music files -> **22 SQLite connections** for one sync.

The per-file scan also repeatedly walks already-known DB rows, so the cost grows unnecessarily with library size.

**Recommended fix:** one connection/transaction, load the current managed-name index once, insert missing rows, remove stale rows, then return the final list. Preserve all D26 source-of-truth and duplicate semantics.

### A5 — Large amount of stale imports after module splitting

**Priority: MEDIUM-LOW / maintainability**

Static review found large clusters of imports whose names are never referenced in their module, especially:
- `views/main_window.py`
- `views/public.py`
- `views/stream.py`
- `views/auction.py`
- `views/settings.py`
- `views/games.py`
- several `auction_parts/*` modules.

Some apparent cases are intentional re-exports (`database.py`, `ui.py`) and must not be removed mechanically.

**Recommended fix:** clean only verified unused imports, with compile/regression checks after each group.

### A6 — Confirmed dead private helpers / compatibility no-ops

**Priority: LOW / cleanup after regression suite restoration**

Private helpers with no call/reference in current source include candidates such as:
- `AuctionTab._integration_status_text`
- `AuctionTab._format_seconds`
- `AuctionRngMixin._random_org_client`
- `AuctionSessionMixin._remaining_from_session`
- `RulesMixin._normalized_rule_template_name`
- `AuctionWheelWidget._short_title`
- both legacy no-op `_shrink_window_to_controls()` methods.

Two deprecated Twitch B4 compatibility shims also have no current internal callers:
- `set_channel_points_enabled()`
- `set_link_to_auction()`

Do not delete these solely from grep results. Remove only after the restored regression suite and a fresh compatibility review confirm they are not external/legacy contracts.

### A7 — Active publish workflows are duplicated per historical release

**Priority: LOW-MEDIUM / CI maintenance**

Separate active workflows exist for `publish-1.0.4.yml` through `publish-1.0.8.yml` with mostly identical logic.

Old workflows remain triggerable if their historical release-note file changes; they then intentionally fail because the tag already exists.

**Recommended fix:** move to one reusable/current publication workflow, while keeping historical release facts in Git history and release metadata.

### A8 — GitHub Actions versions already emit deprecation warnings

**Priority: LOW / CI maintenance**

The 1.0.8 gate used older major versions of `actions/checkout`, `actions/setup-python` and `actions/upload-artifact`. The Windows runner emitted a Node 20 deprecation warning and forced Node 24.

This does not invalidate 1.0.8, but it should be refreshed in the next workflow maintenance scope, with the build lock and regression checks active.

### A9 — Installer emits an admin/HKCU warning

**Priority: REVIEW / do not change casually**

Inno Setup reports:
- `PrivilegesRequired=admin`
- installer also touches HKCU keys.

This can be intentional, but Inno warns that per-user changes during administrative install may target an unexpected user context.

Because installer location/update behavior is sensitive, this should receive a dedicated installer review before any change. Do not silently switch privilege mode.

### A10 — Canonical documentation has minor drift/format defects

**Priority: LOW / metadata only**

Examples found:
- literal `\\n` sequences in current README formatting;
- `docs/DECISIONS.md` still describes both post-D26 UX items as eligible even though Conditional UI was released in 1.0.8.

These are safe documentation corrections and do not require runtime rebuild.

## Architectural hotspots

Several modules are now very large:
- `db/auction_session.py` ~2773 lines;
- `views/auction.py` ~2625 lines;
- `views/settings.py` ~2462 lines;
- `db/services.py` ~2253 lines;
- `views/stream.py` ~2251 lines.

The existing mixin/module extraction is working and has no detected method-collision problem. Therefore do **not** launch a broad rewrite merely because the files are large.

Use the current extraction pattern and reuse existing helpers when a future feature actually needs a boundary.

## Safe implementation order

1. **Restore/adapt the existing regression/QA foundation from Drive into GitHub.**
2. **Fix source-snapshot packaging** so build/cache/generated files cannot enter official source ZIPs.
3. **Add exact release/build dependency lock**, reusing the old build-lock mechanism.
4. **Fix documentation-only drift** and literal `\\n` formatting.
5. **Optimize managed music/soundtrack DB sync** with one transaction/index.
6. **Clean verified unused imports.**
7. **Remove confirmed dead private helpers/shims only after tests cover their surrounding paths.**
8. **Consolidate CI publish workflows / refresh GitHub Actions versions.**
9. Review the Inno Setup privilege/HKCU warning separately.
10. Only after these gates, consider any larger architectural split.

## Audit conclusion

No evidence was found of:
- post-acceptance runtime drift;
- duplicate mixin methods silently overriding one another;
- Python import cycles;
- a new RNG-path defect caused by 1.0.8;
- a critical data-corruption path discovered by this static/structural audit.

The largest immediate risk is not a currently observed user-facing runtime failure. It is **loss of regression protection plus non-reproducible/dirty release infrastructure**, which would make future cleanup riskier than necessary.

Therefore the next maintenance scope should start by restoring the already-existing QA foundation, not by rewriting runtime architecture.
