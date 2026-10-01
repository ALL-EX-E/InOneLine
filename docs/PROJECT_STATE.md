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

## ACCEPTED MAINTENANCE BASELINE — 2026-10-01

Текущий принятый runtime 1.0.8 дополнен maintenance-scope из filesystem/source audit.

- App version: **1.0.8**
- SQLite schema: **19**
- Named migrations: **15**
- Release cadence: **не изменён**
- PR: **#12**
- Accepted candidate head: `6fa7589625027bc47f51757782f66836b5e60293`
- Merge commit: `9d31b4af1ea19c80f257be2fec2b660b3cc4aadb`
- Candidate vs merged tree: **131 blob files / 0 differences**
- Final candidate regression: `36862136841` — **SUCCESS**
- Accepted artifact build: `36862185114` — **SUCCESS**
- Post-merge main regression: `36881245153` — **SUCCESS**
- Maintenance publication: `36881837005` — **SUCCESS**
- Manual Windows QA: **COMPLETE / PASS**
- Canonical QA: `docs/qa/1.0.8-filesystem-maintenance.md`
- Filesystem audit: `docs/audits/FILESYSTEM_AUDIT_2026-10-01.md`

Accepted maintenance release/tag:

**v1.0.8-maintenance-2026-10-01**

Installer: `InOneLine_1.0.8_MAINTENANCE_FINAL.exe`

- Size: `47,629,306` bytes
- SHA-256: `2b469e334480d5073a15f48c0e0d84ce3926b990dd4e415c4c90ff0885ba28f1`

Source: `InOneLine_Source_1.0.8_MAINTENANCE_FINAL.zip`

- Size: `1,408,876` bytes
- SHA-256: `bba8214b87729517036f3d422d5e86b6d56b9f23738d396bd4069b4801429e83`
- Non-empty duplicate groups: **0**

Maintenance changes accepted:
- retired legacy `data/wheel_jingles` with safe migration into `data/soundtrack`;
- preserved 1.0.6 full-backup compatibility;
- retired unused stock `data/import_template.csv` while preserving user-edited copies;
- added conservative stale staging cleanup while preserving recovery/rollback data;
- source snapshots now use Git-tracked bytes only;
- clean-install root/data filesystem and duplicate checks are permanent regression coverage.

The original `v1.0.8` release remains the historical initial 1.0.8 publication. For the latest accepted 1.0.8 maintenance baseline, use `v1.0.8-maintenance-2026-10-01`.

## Контрольный codebase audit — 2026-10-01

Проведён отдельный audit-only проход exact accepted/released 1.0.8.

- Runtime drift accepted candidate -> current main: **0 differences across 83 runtime files**.
- Python compile: PASS.
- Circular imports: не обнаружены.
- Accidental mixin method collisions: не обнаружены.
- Runtime 1.0.8 этим аудитом **не изменялся**.
- Подробный отчёт: `docs/audits/CODEBASE_AUDIT_2026-10-01.md`.

Выполнены первые maintenance-шаги аудита: reuse-first восстановлен постоянный regression/QA foundation, исправлена сборка чистого Source ZIP и завершён filesystem/duplicate audit с принятой maintenance-сборкой 1.0.8. Следующий maintenance-пункт выбирается отдельно.

## Regression foundation — restored 2026-10-01

- PR: **#8**
- Squash merge: `f7386fa324fa82a42cd38f743d655859163ccf11`
- Windows regression gate: `36833625221` — **SUCCESS**
- Publication wording gate: `36833625136` — **SUCCESS**
- Product runtime changes: **0**
- Version/schema/migrations remain **1.0.8 / 19 / 15**
- Canonical QA record: `docs/qa/1.0.8-regression-foundation.md`

Persistent regression coverage now includes exact dependency lock, DB backup/restore and rollback, fresh DB integrity, native GUI current-contract checks, frozen EXE/Browser Source smoke, installer build and silent-install startup.

Permanent repository gate:
- PR: **#11**
- Squash merge: `90ab778f2952dadb203f467b6d69e1930f34751c`
- PR regression: `36835785368` — **SUCCESS**
- Main push regression: `36836121385` — **SUCCESS**
- Main publication wording: `36836120962` — **SUCCESS**
- Runs automatically for relevant product/build/test changes on PRs to `main` and pushes to `main`; documentation-only changes are filtered out.

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
