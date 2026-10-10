# Common OBS Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. This session executes inline, with one independent final branch review.

**Goal:** Apply the accepted persisted show-mode and preview override to all seven existing OBS Browser Sources.

**Architecture:** One Python registry normalizes saved modes and supplies read-only visibility descriptors from existing database snapshots. One shared browser helper hides the viewer presentation without suspending polling, business state or audio. Music retains its existing event state machine; wheel context shares the exact local predicate.

**Tech Stack:** Python 3.12, SQLite schema19, PySide6/Qt6.11.2, existing HTTP server and HTML/JavaScript Browser Sources, Windows QA/installer workflow.

**Spec:** `docs/ACTIVE_REVIEW_LEDGER.md`, accepted GLOBAL-OBS-VISIBILITY-001 and UI-078 wheel visibility contract, 2026-10-06; P09 closure and P10 continuation, 2026-10-10.

## Global Constraints

- App 1.0.8 / SQLite schema19 / 15 named migrations; no dependency or schema change.
- Seven existing routes: `/overlay`, `/list-overlay`, `/timer-overlay`, `/music-player-overlay`, `/auction-lots-overlay`, `/rules-overlay`, `/wheel-overlay`.
- `Не показывать` = `hidden`; `Показывать постоянно` = `always`. Main/list/timer/lots/rules have only these two meaningful modes, default `always`.
- Music retains `track_change` / `При смене трека` default and its existing duration/animation/direction behavior. Wheel has `context` / `Когда колесо используется` default.
- `?preview=1` overrides presentation only, including hidden/context-false modes; no setting writes or synthetic events.
- Save applies through existing polling to open Browser Sources; mode persists across restart.
- No changes to RNG, auction/timer/list/points lifecycle, audio ownership/output, API availability, local operator visibility, or embedded main-overlay component switches.
- UI-045/UI-046/UI-049/UI-055 and wheel appearance UI-079 remain later isolated steps. This candidate implements only common visibility, including the UI-078-required wheel mode/Save.
- All existing handlers, routes and media pipelines are reused. Rules legacy `rules_overlay_visible` is a fallback only when the new mode is absent, never a competing active switch.

## Review Focus

1. Existing Rules installations with legacy visibility off must stay hidden after upgrade until explicit Save; test absent/new/malformed mode precedence (Task 1).
2. Wheel Max phases, actual tie-wheel transition and return to clean prestart must use actual local relevance, not broad sectors/session existence; test every predicate class and real API provider (Task 1).
3. Hidden pages must keep receiving data and audio/event state; preview and changing Music mode must not create track-change events; test real open browser pages and event serial (Task 3).
4. Saving one widget mode must not overwrite another widget or embedded-list/content controls; test actual Qt Save handlers, restart and complete settings snapshots (Task 2).
5. Preview with empty data and normal→hidden→always changes must render without reload, layout residue or duplicate polling; test all seven real Chromium pages plus narrow/wide UI and packaged helper route (Tasks 2/3).

---

### Task 1: Shared policy and existing API snapshots

**Files:** Create `streaming_manager/obs_visibility.py`; modify `streaming_manager/db/services.py`, `db/rules.py`, `db/wheel.py`, `music_player.py`, `api_server.py`, `views/auction_parts/state.py`; create `tools/obs_visibility_smoke.py`.

**Interfaces:** Produces `WIDGETS` registry with setting key/default/options; `show_mode(settings, widget) -> str`; `visibility_payload(settings, widget, context_visible=True) -> dict`; `wheel_context_relevant(session, selected_mode='max_amount') -> bool`. Existing stream payload gains `visibility` map for overlay/list; timer/lots/rules/wheel gain one descriptor. Music retains normalized `appearance.show_mode`.

- [x] Write policy/API tests: seven defaults/options, invalid values, legacy Rules off/on/new-mode precedence, no DB writes, and every approved wheel context with unchanged business payload fields.
- [x] Run `python tools/obs_visibility_smoke.py --policy`; expect failure on missing visibility contract before implementation.
- [x] Implement registry and descriptors using existing settings/connection snapshots. Extract the local wheel predicate into the pure helper and delegate both local UI and API to it. Reuse the AuctionTab runtime-state provider for prestart selection.
- [x] Run policy/API tests, existing timer/wheel/rules/DB smoke and compile; expect PASS and unchanged existing payload business semantics.
- [x] Commit `feat: share persisted OBS visibility policy and payloads`.

### Task 2: Seven mode controls and real Save/restart behavior

**Files:** Modify `streaming_manager/views/stream.py`, `tools/gui_regression_smoke.py`, `tools/obs_visibility_smoke.py`.

**Interfaces:** Consumes Task 1 registry; exposes `obs_show_modes` mapping of widget id to existing `ScrollSafeComboBox`. Existing Music combo remains the same object/handler. Five old saves retain their handlers; wheel adds one small isolated mode Save.

- [x] Write real Qt tests for exact labels/options/defaults, URL→copy→preview→mode Tab sequence, hidden embedded list with usable standalone mode, Rules legacy presentation, all existing Saves plus wheel Save, independent settings and restart.
- [x] Run `python tools/obs_visibility_smoke.py --ui`; expect failure on missing common mode controls.
- [x] Add first-setting `Показ виджета:` using the registry in every section, retaining main's accepted two-row typography form in its own group. Replace Rules checkbox with mode; reuse and move Music combo; add wheel mode/Save. Append mode keys to existing settings batches and refresh from normalized saved values.
- [x] Update earlier P09 assertions only for the deliberately inserted mode row/Tab target; run new Qt tests plus prior P09/P08 fixture-restoring checks at 520/1100/2560 widths.
- [x] Commit `feat: expose OBS show modes through existing settings saves`.

### Task 3: Shared browser boundary, real browser verification and Windows package

**Files:** Create `streaming_manager/web/obs_visibility.js`; modify seven `web/*overlay.html`, `api_server.py`, `tools/obs_visibility_smoke.py`, `.github/workflows/regression-foundation-1.0.8.yml`.

**Interfaces:** Consumes Task 1 descriptors. Browser `ObsVisibility.apply(descriptor)` sets `data-obs-visible` on the document root; `ObsVisibility.preview` is read-only. No replacement fetch/timer/polling or widget business state machine. Static `/obs-visibility.js` is served from the existing bundled web directory.

- [x] Add real QWebEngine tests loading all seven normal/preview URLs through the HTTP server: hidden transparent versus preview visible; live always/hidden Save without navigation; empty-data preview; Rules legacy; wheel context changes; Music playing+hidden preview and unchanged event serial.
- [x] Run `python tools/obs_visibility_smoke.py --browser`; expect failure before browser helper integration.
- [x] Implement one root opacity boundary and small payload calls in existing polling handlers. Preserve Music animation/event semantics while making preview unconditional; provide Rules sample only for empty preview. Load helper before each widget inline script and default normal pages hidden until first payload to avoid saved-hidden flashes.
- [x] Run full new smoke, compileall/diff, prior focused GUI and appropriate existing DB/media/position/audio smoke. Add native browser smoke and packaged helper-route checks to existing Windows QA workflow.
- [x] Commit `feat: apply shared OBS visibility without stopping live sources`.
- [ ] Obtain one fresh independent final branch review, rule on findings and fix important defects with regression tests. Publish isolated draft candidate and wait exact full Windows/wording PASS.
- [ ] Verify installer ZIP bytes/digest/CRC, save to existing Drive QA folder, update canonical QA-ready docs, and deliver one complete manual checklist. Candidate stays unmerged until user manual acceptance.

## Plan self-review

All GLOBAL requirements map to Tasks 1–3. UI-078 is limited to approved visibility/Save, leaving its appearance work open. Interface names agree across tasks. Each Review Focus condition has a concrete real policy/UI/browser test. The already approved continuation supplies implementation authorization; no new approval pause is needed.
