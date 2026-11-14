# Clean-install Journal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent automatic first-launch defaults from appearing as user changes in the journal without changing version 1.0.12.

**Architecture:** Add a missing-only, non-audited settings initializer to the database service. Route only constructor-time Music Player and Multichat persistence through it; retain existing audited setters after initialization.

**Tech Stack:** Python 3.12, SQLite, PySide6, unittest smoke scripts.

**Spec:** `docs/superpowers/specs/2026-11-14-clean-install-journal-design.md`

## Global Constraints

- Keep application and installer version at 1.0.12.
- Do not modify or install into `C:\InOneLine`.
- Never overwrite an existing setting through the initializer.
- Ordinary setting changes remain audited.

## Review Focus

- Empty database: Music Player and Multichat initialization leaves `change_log` empty.
- Existing setting: initialization preserves its exact value.
- First real change: normal setter creates exactly one audit row.
- Repeated same value: normal setter creates no duplicate audit row.
- Existing invalid or stale runtime state: initialization must not silently overwrite it.

---

### Task 1: Missing-only database initializer

**Files:**
- Modify: `streaming_manager/db/services.py`
- Create: `tools/clean_install_journal_smoke.py`

**Interfaces:**
- Produces: `Database.initialize_settings(values: dict[str, Any]) -> int`, inserting only absent non-secret keys without audit and returning the number inserted.

- [x] Write a failing real-SQLite test for silent insertion, preservation, audited later change, and repeated same value.
- [x] Run the test and confirm it fails because `initialize_settings` is absent.
- [x] Implement the minimal initializer using one transaction and `INSERT ... ON CONFLICT DO NOTHING`.
- [x] Run the test and confirm it passes.

### Task 2: Constructor-only use

**Files:**
- Modify: `streaming_manager/music_player.py`
- Modify: `streaming_manager/views/multichat.py`
- Modify: `tools/clean_install_journal_smoke.py`

**Interfaces:**
- Consumes: `Database.initialize_settings(values: dict[str, Any]) -> int`.

- [x] Extend the failing test to construct Music Player and Multichat on a clean real database and assert no initialization audit rows.
- [x] Run it and confirm the current constructors create the reproduced rows.
- [x] Add a constructor-only initialization flag/path; all post-construction writes continue using audited setters.
- [x] Run the focused smoke tests and confirm they pass.

### Task 3: Regression verification

**Files:**
- Verify all modified files; no version files.

- [x] Run compileall, the clean-install smoke, music/multichat/journal smokes, version consistency, and `git diff --check`.
- [x] Confirm the diff contains no version-number change and no files under `C:\InOneLine` were modified.
