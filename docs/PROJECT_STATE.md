# InOneLine — Current Project State

Обновлено: **2026-10-01**

## CURRENT / RELEASED

- Version: **1.0.8**
- Scope: **Global Conditional UI Visibility / Issue #3**
- Status: **RELEASED / MANUALLY ACCEPTED**
- SQLite schema: **19**
- Named migrations: **15**
- Accepted candidate commit: `af29d033d5d8cf6bcb774355771121c1bdc7d10f`
- Final release commit on `main`: `946365a10fa276f203846f6741da9c0bbce0ad5f`
- Accepted Windows candidate gate: `36739896076` — SUCCESS
- Post-acceptance metadata branch gate: `36746181439` — SUCCESS
- Final main publication wording gate: `36746572696` — SUCCESS
- GitHub publication workflow: `36746572837` — SUCCESS
- Accepted artifact: `11110716356`
- Manual Windows QA: **PASS 1–10 / FINAL**

## Официальные артефакты 1.0.8

Installer: `InOneLine_Setup_1.0.8.exe`

- Size: `47,607,483` bytes
- SHA-256: `b960ece03364788941dacec0723cf4664ea4fb11461ec4322a2c03fb79ca66e4`

Source: `InOneLine_Source_1.0.8.zip`

- Size: `13,816,053` bytes
- Files: `192`
- SHA-256: `babd51bc5f6c3e72924f39848253c28d22d36b9e68c9c5d13a24fca5151e2b15`
- ZIP CRC: PASS

GitHub Release/tag: **v1.0.8**

Publication workflow повторно скачал опубликованные installer/source и подтвердил те же SHA-256.

## Контрольный codebase audit — 2026-10-01

Проведён отдельный audit-only проход exact accepted/released 1.0.8.

- Runtime drift accepted candidate -> current main: **0 differences across 83 runtime files**.
- Python compile: PASS.
- Circular imports: не обнаружены.
- Accidental mixin method collisions: не обнаружены.
- Runtime 1.0.8 этим аудитом **не изменялся**.
- Подробный отчёт: `docs/audits/CODEBASE_AUDIT_2026-10-01.md`.

Первый обязательный шаг аудита выполнен: существующий старый regression/QA foundation из Drive reuse-first восстановлен и адаптирован к exact 1.0.8. Runtime при этом не изменялся. Следующий maintenance-пункт аудита выбирается отдельно.

## Regression foundation — restored 2026-10-01

- PR: **#8**
- Squash merge: `f7386fa324fa82a42cd38f743d655859163ccf11`
- Windows regression gate: `36833625221` — **SUCCESS**
- Publication wording gate: `36833625136` — **SUCCESS**
- Product runtime changes: **0**
- Version/schema/migrations remain **1.0.8 / 19 / 15**
- Canonical QA record: `docs/qa/1.0.8-regression-foundation.md`

Persistent regression coverage now includes exact dependency lock, DB backup/restore and rollback, fresh DB integrity, native GUI current-contract checks, frozen EXE/Browser Source smoke, installer build and silent-install startup.

## Последние принятые функциональные релизы

- **1.0.4 / D19** — пользовательское/анимированное изображение в центре колеса и быстрый выбор.
- **1.0.5 / D43** — OBS Browser Audio Transport через Timer Browser Source + AudioCoordinator foundation.
- **1.0.6 / D21** — формат weighted wheel «Выбывание» + multi-spin verification.
- **1.0.7 / D26** — полноценный Music Player, shared soundtrack library, AudioCoordinator ownership и отдельный OBS Music Player Overlay.
- **1.0.8 / Global Conditional UI Visibility** — логически неприменимые controls скрываются; временно недоступные controls остаются visible + disabled.

Подробности каждой версии находятся в `RELEASE_NOTES_<version>.md`.

## Текущая рабочая очередь

После 1.0.8 новый implementation scope **не выбран автоматически**.

Ближайшие eligible items:

1. **Global Multi-File Import** — Issue #4.
2. **D22 — Battle Royale** — Issue #5, approved post-completion item, отложен и требует fresh design/review.

Issue #3 — **CLOSED / RELEASED in 1.0.8**.

Отдельно зафиксирован maintenance-аудит 2026-10-01. Его recommended safe order начинается с возврата существующего regression/QA foundation, но это ещё не выбранный runtime implementation scope.

Выбор следующего scope требует отдельного решения пользователя и fresh exact-CURRENT review.

## Release cadence

В счёт cadence входят только версии, которые прошли финальную пользовательскую приёмку и стали CURRENT/released. Candidate/FIX версии не считаются.

Последняя явно зафиксированная отметка после 1.0.3 была 16/25; с принятыми 1.0.4–1.0.8 текущая арифметическая отметка — **21/25**. Перед фактическим C1 gate счётчик нужно сверить с release history, а не с candidate APP_VERSION.
