# Multichat Settings Groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the multichat settings into common, Twitch and YouTube groups with connection-aware service settings.

**Architecture:** Keep all persisted keys and runtime behavior. Add section-owned appearance saves, use three appearance editor instances, and let `MultichatTab.refresh()` control only the visibility of service-specific settings bodies.

**Tech Stack:** Python 3.12, PySide6, SQLite settings, unittest, Windows GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-13-multichat-settings-groups-design.md`

## Global Constraints

- Do not change message delivery, ordering, deletion, reconnect or OBS payload behavior.
- Keep all existing settings keys and values compatible.
- Keep connection status/actions available when service-specific settings are hidden.
- Produce a separate candidate and manual QA installer; do not replace the accepted installer.

## Review Focus

- Saving common appearance must not overwrite Twitch or YouTube appearance.
- Saving Twitch appearance must not overwrite common or YouTube appearance.
- Connecting and disconnecting each service must immediately show or hide only its settings body.
- Compact layout must remain usable with nested groups.
- Closing with unsaved drafts must cover all three appearance editors.

---

### Task 1: Section-owned appearance persistence

**Files:**
- Modify: `streaming_manager/chat_appearance.py`
- Modify: `streaming_manager/views/chat_appearance_controls.py`
- Test: `tools/chat_appearance_smoke.py`

**Interfaces:**
- Produces: `save_twitch_appearance(db, twitch)`, `save_common_appearance(db, common)` and `ChatAppearanceEditor(section="all" | "platform" | "common")`.

- [x] Add failing tests proving three editors save only their owned section.
- [x] Run `py -3.12 -m unittest tools.chat_appearance_smoke -v` and confirm the new tests fail for missing interfaces.
- [x] Implement section-owned persistence and editor sections with default `section="all"` compatibility.
- [x] Re-run the appearance smoke and confirm PASS.

### Task 2: Three multichat setting groups

**Files:**
- Modify: `streaming_manager/views/multichat.py`
- Modify: `streaming_manager/views/main_window.py`
- Modify: `streaming_manager/youtube_runtime.py`
- Test: `tools/multichat_windows_smoke.py`

**Interfaces:**
- Consumes: sectioned appearance editors from Task 1.
- Produces: `general_group`, `twitch_group`, `youtube_group`, `twitch_settings_body`, `youtube_settings_body`; `YouTubeChatRuntime.is_connected`.

- [x] Add failing native Qt tests for order, «Мультичат в OBS», connection controls and conditional service bodies.
- [x] Run `py -3.12 -m unittest tools.multichat_windows_smoke -v` and confirm the expected failures.
- [x] Build the three groups and connection-aware visibility with no settings-key changes.
- [x] Include the common editor in unsaved-change handling.
- [x] Re-run the multichat Windows smoke and confirm PASS.

### Task 3: Regression and candidate evidence

**Files:**
- Modify: `docs/Правила_и_дальнейший_распорядок_работ.md`
- Modify: `docs/qa/InOneLine-Twitch-YouTube-multichat-installer-checklist.md`

- [ ] Run appearance, multichat core/Windows/Twitch/YouTube, GUI, R06 list/chat/combined and wording checks.
- [ ] Verify the diff changes only the reopened settings-layout package and its tests/docs.
- [ ] Push a candidate PR and require native Windows CI success.
- [ ] Download and verify the Windows installer artifact, upload an immutable FIX candidate and focused checklist to Google Drive, then wait for manual PASS/FAIL.
