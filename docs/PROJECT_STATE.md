# InOneLine — Current Project State

Обновлено: **2026-10-02**

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

Maintenance-последовательность контрольного аудита завершена: regression/QA foundation восстановлен, Source/filesystem cleanup принят, а последующие A4–A9 закрыты и слиты. Все A1–A10 findings этого аудита теперь CLOSED; следующего незакрытого maintenance-пункта из него нет.

## A4 Managed Media Sync — accepted 2026-10-02

Maintenance scope A4 from the codebase audit is complete.

- Status: **CLOSED / MANUALLY ACCEPTED / MERGED**
- PR: **#13**
- Accepted candidate head: `8269dc99db3398ae4fa861fdcea3ef085ff517a1`
- Squash merge on `main`: `278b77ca037756e1ef17f9b8f8634ad05d88e1fc`
- Final candidate workflow: `36890302480` — **SUCCESS**
- Final candidate artifact: `11176662125`
- Post-merge main regression: `36949173717` — **SUCCESS**
- Manual Windows QA: **COMPLETE / PASS**
- Canonical QA: `docs/qa/1.0.8-media-sync-maintenance.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted optimization:
- managed-media category sync uses one SQLite connection/transaction instead of reopening/re-querying once per file;
- D26 music/soundtrack stale-row semantics, external rows, IDs, original names and non-D26 recovery behavior remain preserved;
- permanent regression now includes `tools/media_sync_smoke.py`.

Exact accepted candidate bytes:
- Installer: 47,618,508 bytes; SHA-256 `72151570eb5d6e3b29c3ea51942ea7ba8dd5be476bb8a0b8c05fa48869ff9e5e`
- Source: 1,415,954 bytes; SHA-256 `54f77e99e5d6dafc49c566d109514be3c2f2a74c3bb1fa5217c529d4ca2dca42`

A5, A6, A7 and A8 are closed. A9 is now closed. No unresolved maintenance findings remain from the 2026-10-01 control audit.

## A5 Verified Unused Imports — accepted 2026-10-02

Maintenance scope A5 from the codebase audit is complete.

- Status: **CLOSED / MANUALLY ACCEPTED / MERGED**
- PR: **#14**
- Candidate build commit: `8a7a79e38b34912ab77493c20372bf4f9d75b3d4`
- Final clean PR head: `9f13c0ceff19217bcf62dfebc3b5dc15a86886b1`
- Squash merge on `main`: `15990f955e596d87436044b38548f53d3b033e00`
- Corrected candidate regression: `36950070546` — **SUCCESS**
- Candidate build: `36950066325` — **SUCCESS**
- Candidate artifact: `11203681918`
- Final clean PR regression: `36950474408` — **SUCCESS**
- Post-merge main regression: `36952721884` — **SUCCESS**
- Manual Windows QA: **COMPLETE / PASS**
- Canonical QA: `docs/qa/1.0.8-unused-import-maintenance.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted cleanup:
- removed **366** verified unused imported names from 10 UI modules;
- preserved intentional re-exports and compatibility contracts;
- the permanent GUI gate caught and prevented accidental removal of the `AuctionTimeDialog` compatibility re-export;
- A6 private helpers and compatibility shims were not touched.

Exact accepted candidate bytes:
- Installer: 47,629,836 bytes; SHA-256 `85e5d006f9bbfddea3c27bd4b2f98b458a9f46b1c3040cd2087eea54bba305f9`
- Source: 1,416,072 bytes; SHA-256 `e852f8df397389d775ef09d48a95b6e8917a0edfebe0664a12c73a8f336c3305`

A6, A7 and A8 are closed. A9 is now closed. No unresolved maintenance findings remain from the 2026-10-01 control audit.

## A6 Dead Private Helpers — accepted 2026-10-02

Maintenance scope A6 from the codebase audit is complete.

- Status: **CLOSED / MANUALLY ACCEPTED / MERGED**
- PR: **#15**
- Corrected candidate build head: `d176e5bd91357eabcbed58ca05221ba8bd174395`
- Final clean PR head: `81aef4a3ae9cda20b6c2ba1cb7270749b491d064`
- Squash merge on `main`: `452daf5742a62e95b2c5470ae476b509e05908e8`
- Corrected candidate workflow: `36958423991` — **SUCCESS**
- Corrected candidate artifact: `11206613134`
- Final clean PR regression: `36958711684` — **SUCCESS**
- Post-merge main regression: `36959577220` — **SUCCESS**
- Corrected manual Windows QA: **COMPLETE / PASS**
- Canonical QA: `docs/qa/1.0.8-dead-helper-maintenance.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted cleanup:
- removed **7** verified dead/private helpers;
- retained `AuctionSessionMixin._remaining_from_session` and both deprecated Twitch B4 compatibility shims;
- first A6 candidate artifact `11205260970` was rejected after manual QA exposed a missing `normalize_text_key` runtime dependency;
- fresh review also found and prevented a missing `RandomOrgClient` runtime dependency;
- permanent regression now includes `tools/a6_dependency_smoke.py`.

Exact accepted corrected candidate bytes:
- Installer: 47,627,232 bytes; SHA-256 `8b1a213989cdd8d3e8c864d2b299327d72ef2fc7426e6c7c3bebbbf9669164c9`
- Source: 1,419,509 bytes; SHA-256 `5da7afe8f167413a4718bb1b9e0e42ae8b0f5b03090a059d682037766cf963da`

A7 and A8 are closed. A9 is now closed. No unresolved maintenance findings remain from the 2026-10-01 control audit.

## A7 Publication CI Consolidation — accepted 2026-10-02

Maintenance scope A7 from the codebase audit is complete.

- Status: **CLOSED / ACCEPTED / MERGED**
- PR: **#16**
- Accepted PR head: `a04cea9852367dc39a8f40fea2c12b0d1f1ba23a`
- Squash merge on `main`: `d03602f5f8197abcda2d21eee10d86abb4b98d62`
- PR publisher parse-only run: `36961378735` — **SKIPPED AS DESIGNED**
- Final PR regression: `36961378739` — **SUCCESS**
- Post-merge publication wording: `36962356350` — **SUCCESS**
- Post-merge main regression: `36962356315` — **SUCCESS**
- Manual Windows QA: **N/A — CI/release infrastructure only**
- Canonical QA: `docs/qa/1.0.8-publication-ci-maintenance.md`
- Publication contract: `docs/RELEASE_PUBLICATION.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted infrastructure change:
- retired active per-release publishers `publish-1.0.4.yml` through `publish-1.0.8.yml`;
- historical releases/tags/assets/release notes remain unchanged and are preserved by Git history;
- future publication uses one `.github/workflows/publish-accepted-release.yml`;
- normal publication requires a newly added immutable `.github/release/requests/*.json` manifest containing the exact accepted artifact ID, target commit, public asset names and SHA-256 values;
- publisher refuses existing tags/releases, verifies accepted bytes before publication and verifies downloaded release bytes again afterward;
- no A7 publication request was added, therefore A7 merge did not create any GitHub Release;
- permanent regression now includes `tools/publication_ci_smoke.py`.

Immediately after A7 merge, the public release set remains unchanged: 10 tags from `v1.0.0` through `v1.0.8-maintenance-2026-10-01`.

A8 is now closed. A9 is now closed. No unresolved maintenance findings remain from the 2026-10-01 control audit.

## A8 GitHub Actions Version Refresh — accepted 2026-10-02

Maintenance scope A8 from the codebase audit is complete.

- Status: **CLOSED / ACCEPTED / MERGED**
- PR: **#17**
- Accepted clean PR head: `bc266c8be8916611846a7c7ff50a28de03ecebcd`
- Squash merge on `main`: `488865ab7420239ff07d6c4eb8244d46cb54b520`
- Direct Actions v7 validation: `36963052321` — **SUCCESS**
- Final clean PR regression: `36963105972` — **SUCCESS**
- Post-merge publication wording: `36964693488` — **SUCCESS / NO DEPRECATION WARNINGS**
- Post-merge main regression: `36964693520` — **SUCCESS**
- Manual Windows QA: **N/A — CI-only**
- Canonical QA: `docs/qa/1.0.8-actions-version-maintenance.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted infrastructure change:
- all active `actions/checkout`, `actions/setup-python` and `actions/upload-artifact` references now use major `v7`;
- product/build semantics, Python versions, build lock and artifact naming were not changed;
- temporary direct-action validation proved checkout/setup-python/upload-artifact v7 execute successfully without the Node 20 deprecation warning;
- permanent regression now includes `tools/actions_version_smoke.py`;
- the permanent regression triggers on any `.github/workflows/**` change.

A9 is now closed. No unresolved maintenance findings remain from the 2026-10-01 control audit.


## A9 Installer User-State / HKCU Ownership — accepted 2026-10-02

Maintenance scope A9 from the codebase audit is complete.

- Status: **CLOSED / MANUALLY ACCEPTED / MERGED**
- PR: **#18**
- Corrected V2 candidate build head: `f0f4a47aa7c6b51f1ca531f4a6d673cd56b7b361`
- Final clean runtime PR head before acceptance documentation: `340022e9d3ca35052c5ab2dad269dc0413cdc07c`
- Manual-acceptance documentation head: `3ba9f3bb0e9402c9267d80a0b1879884139ad892`
- Squash merge on `main`: `74ad16c5772d5cc191f7e307203b6a574af7815c`
- Corrected candidate workflow: `36972036097` — **SUCCESS**
- Corrected candidate artifact: `11211662949`
- Final clean PR regression: `36972339831` — **SUCCESS**
- Post-merge publication wording: `36978675956` — **SUCCESS**
- Post-merge main regression: `36978675944` — **SUCCESS**
- Manual Windows QA: **COMPLETE / PASS**
- Canonical QA: `docs/qa/1.0.8-installer-user-state-maintenance.md`
- App version/schema/migrations remain **1.0.8 / 19 / 15**
- Normal accepted-release cadence is unchanged.

Accepted maintenance:
- elevated installer mode remains intentionally `PrivilegesRequired=admin`;
- administrative installer no longer owns or deletes per-user HKCU UI state;
- MainWindow state is now app-owned in `data/ui_state.ini`;
- frozen Windows migration checks both Registry32 and Registry64 views;
- legacy state is copied to `data/legacy_ui_state_backup.ini` before cleanup;
- legacy Registry is cleared only after successful INI write and backup;
- post-install launch uses `runasoriginaluser`;
- per-install `QLockFile` single-instance protection prevents concurrent UI-state writers;
- permanent regression covers dual-view migration, legacy backup and single-instance behavior.

Corrected A9 V2 accepted bytes:
- Package: 49,060,040 bytes; SHA-256 `a4707ed4c149085ebb52c550fb9bca236e944591774c46a31ba84ac753ceb044`
- Installer: 47,618,014 bytes; SHA-256 `38540d8bc6aa8268c5ec727120cd4646f186e6c38759f5c32bd348fdfe08b402`
- Source: 1,441,202 bytes; SHA-256 `0414cb0e15c449bf6965d725e48fe632ce71a4e17d96b0a68353ba5db5fa8211`

The first A9 candidate artifact `11210430783` remains **REJECTED / DO NOT ACCEPT**.

With A9 accepted and merged, **all A1–A10 findings from the 2026-10-01 control codebase audit are closed**. No larger architectural rewrite is implied by this closeout.


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

## Текущая рабочая очередь — reconciled 2026-10-02

После принятия A9 все maintenance findings контрольного codebase audit закрыты. Новый product implementation scope **не выбран автоматически**.

Отдельно после повторной cross-source сверки 2026-10-02 зафиксирован **QA-1.0.8-01 — Conduct integration last-event visibility**:
- исторический B1 contract прямо включал показ времени последнего принятого integration event в compact Conduct integration status;
- current 1.0.8 продолжает сохранять `integration_connections.last_event_at` и Settings показывает последнюю принятую активность;
- current Conduct integration status/dialog это время не показывает;
- более позднего direct-user superseding decision не найдено;
- статус: **ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT FIXED / NOT AUTO-AUTHORIZED**;
- version/schema/migrations остаются **1.0.8 / 19 / 15**, runtime этим documentation pass не изменялся.

- **Global Multi-File Import / Issue #4** — текущий post-D26 eligible candidate для fresh review; это не pre-authorization.
- **Repository hygiene:** PR #9 `Make 1.0.8 regression foundation persistent` всё ещё открыт, хотя его purpose уже superseded/closed более поздним принятым PR #11 `Make 1.0.8 regression foundation permanent`. PR #9 не содержит нового product scope и не меняет CURRENT; это stale repository object, оставленный без автоматического закрытия в ходе documentation audit.
- **QA-1.0.8-02 — B2 test-event safety contract gap:** direct user acceptance was recovered for the adapter-neutral rule that provider-marked test/sandbox/demo events cannot mutate real points/auction/timer/wheel/winner state. Current 1.0.8 generic normalized-event core has no explicit test-event field/gate. Status: **ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / PROVIDER-CAPABILITY-DEPENDENT / NOT AUTO-AUTHORIZED**. No current supported-provider reproduction was established in this audit.
- **QA-1.0.8-03 — B3 `Требует привязки` workflow missing:** accepted behavior for an event without usable target text is manual binding to game/lot without auto-credit; current 1.0.8 marks `missing_target` inapplicable and exposes no bind path. Status: **ACCEPTED WORKFLOW OMISSION / NOT FIXED / NOT AUTO-AUTHORIZED**.
- DonationAlerts accepted built-in public OAuth Client ID **20915** and Rules opacity/padding control UX were restored to durable documentation.
- **B3 provenance correction:** direct user acceptance was recovered for outside-auction unknown-title auto-creation of a normal persistent game. Current 1.0.8 already implements this; it is documentation/provenance correction, not a runtime defect.
- Runtime/version/schema/migrations remain **1.0.8 / 19 / 15**; the repeated reconciliation changed documentation only.
- **Repeated audit final status:** seventh–ninth passes recovered/corrected QA-1.0.8-02, QA-1.0.8-03 and multiple compressed historical/future contract details; the subsequent **tenth orphan-only control was CLEAN / zero additional delta after corrections**. This does not mean the whole repeated audit found nothing; it means no further orphan remained after the recorded corrections.
- **Eleventh recheck documentation delta:** recovered the historical 2026-08-21 reference-image archive gap and the durable `QA-<version>-NN` defect-numbering rule. Both are documentation/process findings only; no new product scope was selected and no runtime bytes changed.
- **Twelfth recheck documentation delta:** restored exact Timer-viewer idle/default-duration behavior, W1 input/re-entrancy guards, W2 external-reference safety, advanced History identity/comparability rules and deferred A8 compensation invariants. These are preserved accepted contracts; no new implementation scope was selected and runtime/version/schema/migrations remain unchanged.
- **Thirteenth recheck documentation delta:** restored exact S2 collision/threshold semantics, standalone-widget architecture boundary, B6 protected-secret/common-backend rule, Winner Verification public-hosting boundary and Product A7 card/hover semantics. Documentation only; no runtime code, version, schema or migrations changed.
- **Fourteenth recheck documentation/source-hygiene delta:** restored the full B1 plaintext-secret exclusion and disabled-integration/no-background-validation lifecycle. Source review also found an unreachable shipped-path DonationAlerts manual-Client-ID fallback after the built-in 20915 gate; classified as source-hygiene/compatibility residue, not a runtime defect and not auto-authorized for cleanup. Runtime/version/schema/migrations unchanged.
- **Fifteenth post-correction orphan-only control: CLEAN.** After all eleventh–fourteenth corrections were written, no additional durable direct-user requirement or hidden GitHub/source scope was found. D1–D43 remain fully accounted for, there is no actual D44 item, and no implementation scope is auto-selected. Runtime remains **1.0.8 / 19 / 15**.
- **Sixteenth recheck: NOT CLEAN / documentation correction.** A later direct-chat/source pass found that the exhaustive inventory still retained the superseded early B4 reward-availability coupling. Authoritative B4/I1 behavior is manual reward enable/disable in Settings, independent of auction start/resume/pause/finish; current 1.0.8 already implements this. The same pass restored direct implemented decisions for RANDOM.ORG key location (`Настройки → Интеграции`), removal of the date from the lower-right OBS info block, and Restore rejection of the current working `data\streaming.db` as its own source. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. Another post-correction control pass is required before claiming a new clean stop.
- **Seventeenth recheck: NOT CLEAN / process+public-doc correction.** Recovered the direct workflow rule that manual Windows/PowerShell checks are requested only when they add real verification and preferably one focused check/command at a time; also restored the accepted public install wording `Запустить установщик`. A direct-chat provenance recheck confirmed Games `Всего` including archive was already correctly recorded as historical `0.2.22`; only the previous provenance assessment was wrong. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. Another post-correction control is required.
- **Seventeenth recheck: NOT CLEAN / documentation correction.** Restored the full permanent engineering invariant (`reuse first -> minimal diff -> no parallel logic -> no new persistence unless unavoidable`; stability/reliability over optimization) and expanded accepted D43/D26 audio lifecycle/backup/collision behavior. Current 1.0.8 already matches these released audio contracts; no new runtime defect, feature identifier, schema or migration was found. Another post-correction control pass is required.
- **D22 / Issue #5** — остаётся approved post-completion, но был явно отложен пользователем 2026-09-29 и не является автоматическим следующим пунктом.
- Восстановленная retained dependency/complexity chain после D26: **D40 → D34 → D41 → older YouTube integration candidate → D38 → Public Web → D27 → D7**.
- Отдельно сохранены approved/parked **D23, D24, D25, D42**, а также deferred **D16, D17, D18, D20, D22, W1, Saved Auctions/New Auction, A8, B6** и provider-specific follow-ups.
- Более старый PASS13 не используется без поздних corrections: Games/List Autoscroll позже был прямо отклонён как ненужное добавление; Compact presentation отложен; D15 не подтверждён как InOneLine item; D39 не actionable без нового прямого решения пользователя.

Полный текущий inventory и статусы: `docs/ROADMAP.md`.

Полная история пользовательских идей, включая уже реализованные/отложенные/отклонённые: `docs/IDEA_INVENTORY.md`.

Повторная сверка чатов/Drive/GitHub: `docs/history/ROADMAP_RECONCILIATION_2026-10-02.md`.

Выбор следующего scope требует отдельного решения пользователя и fresh exact-CURRENT review.

## Release cadence

В счёт cadence входят только версии, которые прошли финальную пользовательскую приёмку и стали CURRENT/released. Candidate/FIX версии не считаются.

Последняя явно зафиксированная отметка после 1.0.3 была 16/25; с принятыми 1.0.4–1.0.8 текущая арифметическая отметка — **21/25**. Перед фактическим C1 gate счётчик нужно сверить с release history, а не с candidate APP_VERSION.
