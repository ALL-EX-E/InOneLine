# Roadmap Reconciliation — 2026-10-02

## Scope

Повторно сверены:
- доступная история рабочих чатов «Программа для стрима» 1–31 и зафиксированные прямые пользовательские решения;
- Google Drive: cumulative current/history/order files, PASS 1–13 reconciliation archives, Pointauc review/audit records и roadmap addenda 2026-09-28–2026-09-30;
- GitHub: current docs, Issues, release notes 1.0.0–1.0.8, current runtime/source and maintenance audit records.

Цель: найти потерянные идеи, неверные статусы, сломанный dependency-order и stale-задачи, которые уже реализованы/отклонены.

## Authority rule

При конфликте используется порядок:
1. более позднее прямое решение пользователя;
2. принятая/released реализация и exact current runtime;
3. поздний canonical reconciliation/status record;
4. более ранние assistant-authored planning/order documents;
5. промежуточные candidate/reference notes.

Само наличие пункта в старом cumulative-файле не делает его текущей задачей.

## Main finding — GitHub roadmap drift

После миграции source-of-truth в GitHub короткий `docs/ROADMAP.md` сохранил только:
- Global Multi-File Import / #4;
- D22 Battle Royale / #5.

Это потеряло часть ранее сохранённого backlog и создало ложное впечатление, что D22 автоматически следует сразу после post-D26 patch.

Drift исправлен 2026-10-02.

## Restored retained dependency/complexity chain

После уже released D26 сохранённая поздняя dependency/complexity chain включает:
- D40 — manual soundtrack/music library order;
- D34 — Tourniquet adapter;
- D41 — cross-platform chat aggregation + standalone OBS chat overlay;
- older YouTube platform/integration candidate;
- D38 — optional LAN access to standalone OBS widgets;
- Public Web / ordinary site presentation;
- D27 — physics/final-stop «Честное колесо»;
- D7 — whole-snapshot cryptographic verification hardening.

Это planning order, а не pre-authorization. Перед каждым пунктом нужен fresh exact-CURRENT review и отдельный user approval.

## Restored parked/approved items

Сохранены и не потеряны:
- D23 — import custom participants;
- D24 — standalone OBS wheel-participant list;
- D25 — cumulative probability <= winner amount; approved post-completion, explicitly «не нужно сейчас»;
- D42 — current lot/sector under arrow during spin.

Также сохранены deferred:
- W1 Space -> existing Spin;
- Saved Auctions + dependent full New Auction workflow;
- A8 compensating Undo;
- B6 Pointauc API adapter contract;
- provider adapters iHAQ Donate v2.0, ODA/OpenDonationAssistant, DonateX, VK Video Live, Kick, Donate Helper, DonatePay;
- Twitch Channel Points/Custom Rewards live verification when eligibility allows.

## Later user decisions that supersede older PASS13 wording

Do NOT restore these old statuses blindly:
- D16 — explicitly deferred;
- D17 — explicitly skipped for now;
- D18 — explicitly skipped for now;
- D20 — explicitly deferred;
- D22 — explicitly deferred on 2026-09-29; Issue #5 remains deferred and is NOT the automatic next item.
- Games/List shared persisted Autoscroll — no longer a live task: on 2026-09-28 the user decided not to add it because required autoscroll behavior already exists.
- Games/List Compact presentation — postponed until a real future need appears.

## Provenance corrections retained

- D15 Twitch AI-bot/neural network is NOT a confirmed InOneLine roadmap item.
- D39 per-scene widget style profiles is assistant-originated historical possibility / NOT ACTIONABLE unless explicitly reopened.
- Historical W3 YouTube URL/video-ID soundtrack source is reference-only, not a direct-user-approved roadmap scope.
- Historical «Трейлер (YouTube)» is resolved/closed.
- D4 separate Wheel page, D6 generic Widgets umbrella, D8 video requests and D14 historical umbrella are rejected/superseded.
- F-series rejected/superseded entries are not backlog.
- H-series are existing behavior to preserve, not new work.

## Items confirmed closed rather than forgotten

- QA-1.0.2-01 unified OBS onboarding/help — closed in 1.0.2.
- QA-1.0.2-02 external donation auto-extension completion — closed in 1.0.3.
- D19 — released 1.0.4.
- D43 — released 1.0.5.
- D21 — released 1.0.6.
- D26 — released 1.0.7.
- Global Conditional UI Visibility / #3 — released 1.0.8.
- Old deferred stale OBS page reload/version handshake — current runtime already has the version/cache-busting overlay handshake.
- Old wheel-overlay infinite RAF concern — current wheel overlay stops RAF when wheel animation is not active.
- Old source/release filesystem hygiene items — handled by the 2026-10-01/02 maintenance audit.

## Review-later inventory retained

Not approved for automatic implementation:
- D1 double timer/count-up;
- D2 pin/unpin lot;
- D3 universal inline editing;
- D5 advanced auction analytics;
- D9 localization;
- D10 GitHub link (public-repo prerequisite now exists);
- D11 Telegram link;
- D12 support/Boosty link;
- D13 Pending/manual-processing queue;
- D28 artificial/fixed probability;
- D29 viewer names in viewer-facing table;
- D30 blind/hidden viewer amounts;
- D31 auto-processing selector dependent on D13;
- D32 viewer-name order text in separate participant mode;
- D33 alternative display sorts;
- D35 per-bet fortune multiplier;
- D36 viewer chooses lot dependent on D35;
- D37 presets export/import;
- Auction Lots Normal/Compact remains only specification-reconciliation territory.

## Current selection state

No product scope is selected automatically by this audit.

- Global Multi-File Import / #4 remains the current post-D26 eligible candidate for fresh review.
- D22 / #5 remains deferred.
- All other retained ideas keep the statuses in `docs/ROADMAP.md`.

## Exhaustive-orphan result

After comparing old cumulative inventories, PASS13, later chat decisions, release notes, current code and Issues:
- no D44 was found;
- no additional durable unnumbered user idea was found that is both unimplemented and absent from the reconciled roadmap;
- no currently closed/rejected item needs to be reopened.

If a future chat surfaces an older idea not listed in the reconciled roadmap, it must be provenance-checked against later direct user decisions before promotion.

## Files updated

- `docs/ROADMAP.md` — full survivable inventory + current statuses.
- `docs/PROJECT_STATE.md` — current queue summary points to reconciled roadmap.
- `docs/DECISIONS.md` — durable reconciliation/status rules.
- `docs/README.md` — this reconciliation added to the canonical reading path.
