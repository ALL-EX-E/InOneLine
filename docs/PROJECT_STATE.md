# InOneLine — Current Project State

Обновлено: **2026-10-07**

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
- **QA-1.0.8-03 — B3 missing-target current-runtime gap — SUPERSEDED PRODUCT TARGET / STILL NOT FIXED IN 1.0.8:** the earlier manual `Требует привязки` workflow is no longer the product target for an ordinary accepted external event received during a running auction with empty message. UI-087 now requires automatic temporary lots `Без текста N`; known-rate events credit that placeholder, unknown-rate events remain pending but already target it. Current 1.0.8 still marks `missing_target` as `inapplicable`, so the runtime gap remains until batch implementation. Provider-specific events that cannot safely map to a normal lot-targeted credit remain separate edge cases.
- DonationAlerts accepted built-in public OAuth Client ID **20915** and Rules opacity/padding control UX were restored to durable documentation.
- **B3 provenance correction:** direct user acceptance was recovered for outside-auction unknown-title auto-creation of a normal persistent game. Current 1.0.8 already implements this; it is documentation/provenance correction, not a runtime defect.
- Runtime/version/schema/migrations remain **1.0.8 / 19 / 15**; the repeated reconciliation changed documentation only.
- **Repeated audit final status:** seventh–ninth passes recovered/corrected QA-1.0.8-02, QA-1.0.8-03 and multiple compressed historical/future contract details; the subsequent **tenth orphan-only control was CLEAN / zero additional delta after corrections**. This does not mean the whole repeated audit found nothing; it means no further orphan remained after the recorded corrections.
- **Twenty-third reconciliation documentation delta:** direct user S1 decisions were recovered explicitly: unknown-rate external events remain pending and require manual `Применить` after the rate is saved; service-specific conversion rows are shown only while the corresponding service is connected/available. Current 1.0.8 already implements both. Documentation-only, no new product scope or runtime change.
- **Eleventh recheck documentation delta:** recovered the historical 2026-08-21 reference-image archive gap and the durable `QA-<version>-NN` defect-numbering rule. Both are documentation/process findings only; no new product scope was selected and no runtime bytes changed.
- **Twelfth recheck documentation delta:** restored exact Timer-viewer idle/default-duration behavior, W1 input/re-entrancy guards, W2 external-reference safety, advanced History identity/comparability rules and deferred A8 compensation invariants. These are preserved accepted contracts; no new implementation scope was selected and runtime/version/schema/migrations remain unchanged.
- **Thirteenth recheck documentation delta:** restored exact S2 collision/threshold semantics, standalone-widget architecture boundary, B6 protected-secret/common-backend rule, Winner Verification public-hosting boundary and Product A7 card/hover semantics. Documentation only; no runtime code, version, schema or migrations changed.
- **Fourteenth recheck documentation/source-hygiene delta:** restored the full B1 plaintext-secret exclusion and disabled-integration/no-background-validation lifecycle. Source review also found an unreachable shipped-path DonationAlerts manual-Client-ID fallback after the built-in 20915 gate; classified as source-hygiene/compatibility residue, not a runtime defect and not auto-authorized for cleanup. Runtime/version/schema/migrations unchanged.
- **Fifteenth post-correction orphan-only control: CLEAN.** After all eleventh–fourteenth corrections were written, no additional durable direct-user requirement or hidden GitHub/source scope was found. D1–D43 remain fully accounted for, there is no actual D44 item, and no implementation scope is auto-selected. Runtime remains **1.0.8 / 19 / 15**.
- **Sixteenth recheck: NOT CLEAN / documentation correction.** A later direct-chat/source pass found that the exhaustive inventory still retained the superseded early B4 reward-availability coupling. Authoritative B4/I1 behavior is manual reward enable/disable in Settings, independent of auction start/resume/pause/finish; current 1.0.8 already implements this. The same pass restored direct implemented decisions for RANDOM.ORG key location (`Настройки → Интеграции`), removal of the date from the lower-right OBS info block, and Restore rejection of the current working `data\streaming.db` as its own source. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. Another post-correction control pass is required before claiming a new clean stop.
- **Seventeenth recheck: NOT CLEAN / process+public-doc correction.** Recovered the direct workflow rule that manual Windows/PowerShell checks are requested only when they add real verification and preferably one focused check/command at a time; also restored the accepted public install wording `Запустить установщик`. A direct-chat provenance recheck confirmed Games `Всего` including archive was already correctly recorded as historical `0.2.22`; only the previous provenance assessment was wrong. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. Another post-correction control is required.
- **Eighteenth recheck: NOT CLEAN / documentation correction.** Restored the full permanent engineering invariant (`reuse first -> minimal diff -> no parallel logic -> no new persistence unless unavoidable`; stability/reliability over optimization) and expanded accepted D43/D26 audio lifecycle/backup/collision behavior. Current 1.0.8 already matches these released audio contracts; no new runtime defect, feature identifier, schema or migration was found. Another post-correction control pass is required.
- **Nineteenth recheck: NOT CLEAN / documentation precision.** Restored exact D10/D11/D12 official-link boundaries and the historical-artifact retention rule. No runtime defect or new product identifier was found; another post-correction control pass is required.
- **Twentieth recheck: NOT CLEAN / documentation precision.** Restored exact historical A1 safe-update QA details and B2 restart-persistence details. No new runtime defect or product identifier was found; another control pass is required.
- **D22 / Issue #5** — остаётся approved post-completion, но был явно отложен пользователем 2026-09-29 и не является автоматическим следующим пунктом.
- Восстановленная retained dependency/complexity chain после D26: **D40 → D34 → D41 → older YouTube integration candidate → D38 → Public Web → D27 → D7**.
- Отдельно сохранены approved/parked **D23, D24, D25, D42**, а также deferred **D16, D17, D18, D20, D22, W1, Saved Auctions/New Auction, A8, B6** и provider-specific follow-ups.
- Более старый PASS13 не используется без поздних corrections: Games/List Autoscroll позже был прямо отклонён как ненужное добавление; Compact presentation отложен; D15 не подтверждён как InOneLine item; D39 не actionable без нового прямого решения пользователя.

- **Twenty-fourth reconciliation documentation delta:** restored accepted D26 media-identity behavior: case-insensitive filename dedup across managed/external Music Player rows, external→managed promotion preserving media ID/queue, and context-local external soundtrack selections that clear safely without D26 recovery UI. Current 1.0.8 already implements this; documentation only, no new scope/runtime change.
- **Twenty-fifth reconciliation/public-doc delta:** restored exact S1 legacy-money migration boundary (1 RUB = 1 SM point, positive fractional RUB rounds upward, historical change_log JSON untouched) and identified the accepted SmartScreen/Unknown Publisher step-by-step guidance gap. The README guidance has now been corrected; no runtime change.
- **Twenty-sixth recheck: NOT CLEAN / documentation+public-guidance correction.** Recovered the Drive audit log/screenshot archive rule, R1.0.4 uninstall backup recommendation, D19 animated-center runtime boundary, D21 no-final-winner elimination terminal semantics, S1 user-facing `Баллы` naming, R1/S3 Windows-input details, Auction session-only autoscroll boundary, A11.1 1-minute/24-hour local+OBS motion acceptance, A12 real-operator smoke path, and the historical public-Git privacy/history-cleanup process. Current runtime already implements applicable runtime behavior; README SmartScreen guidance was corrected. No new product identifier, future implementation candidate or runtime QA omission was found. A post-correction clean control is still required before declaring this latest repeated audit closed.
- **Twenty-seventh post-correction control: CLEAN.** After all pass-26 corrections were written, a new direct-chat orphan search, Drive current/history/review/policy check, GitHub source TODO/FIXME/future scan, open Issue/PR check and identifier/QA mechanical reconciliation found **0 additional durable delta**. Current runtime stays **1.0.8 / 19 / 15**; no implementation scope is auto-selected.
- Current known runtime accepted-scope gaps remain exactly **QA-1.0.8-01 / QA-1.0.8-02 / QA-1.0.8-03**; none is auto-authorized for runtime implementation.

Полный текущий inventory и статусы: `docs/ROADMAP.md`.

Полная история пользовательских идей, включая уже реализованные/отложенные/отклонённые: `docs/IDEA_INVENTORY.md`.

Повторная сверка чатов/Drive/GitHub: `docs/history/ROADMAP_RECONCILIATION_2026-10-02.md`.

Выбор следующего scope требует отдельного решения пользователя и fresh exact-CURRENT review.

## Release cadence

В счёт cadence входят только версии, которые прошли финальную пользовательскую приёмку и стали CURRENT/released. Candidate/FIX версии не считаются.

Последняя явно зафиксированная отметка после 1.0.3 была 16/25; с принятыми 1.0.4–1.0.8 текущая арифметическая отметка — **21/25**. Перед фактическим C1 gate счётчик нужно сверить с release history, а не с candidate APP_VERSION.

### Reconciliation pass 28 — 2026-10-03

- Same-scenario recheck was **NOT CLEAN** because additional already-implemented/accepted detail had to be restored to the exhaustive inventory: exact Games/Public status-group ordering, Product A7 hover/autoscroll semantics, D21 between-round format switching, and the historical timer/B1 visual provenance notes.
- These are documentation precision/provenance corrections, not new feature identifiers and not new auto-authorized runtime work.
- Current known accepted-scope runtime gaps remain **QA-1.0.8-01 / QA-1.0.8-02 / QA-1.0.8-03**.
- Current runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**.
- A new post-correction control pass is required before claiming a clean stop for this iteration.
### Reconciliation pass 29 — 2026-10-03

- Post-pass-28 direct-chat, Drive and GitHub/source control is **CLEAN**.
- No additional durable user requirement, future idea, rejected/superseded item, runtime QA omission or hidden source scope was found after the pass-28 corrections.
- Current runtime QA findings remain exactly **QA-1.0.8-01 / QA-1.0.8-02 / QA-1.0.8-03**.
- Open tracking remains Issues **#4 / #5** and stale PR **#9** repository hygiene.
- No product implementation scope is selected automatically.
- Runtime/version/schema/migrations remain **1.0.8 / 19 / 15**.


## Completed UI review reconciliation — 2026-10-07

- Подробный визуальный/функциональный разбор всех вкладок завершён. Рабочий target текущего review находится в `docs/ACTIVE_REVIEW_LEDGER.md`.
- Runtime/source остаётся exact CURRENT **1.0.8 / schema 19 / 15 named migrations**. До команды пользователя `«всё делаем»` принятые UI/BUG-решения не реализуются.
- Текущий review **не возвращает старую roadmap-очередь как автоматический следующий scope**: сначала должен быть завершён reconciliation текущего review, затем dependency sorting, и только потом — реализация по одному пункту после отдельной команды пользователя.
- Ключевые поздние supersession, которые нельзя смешивать с released 1.0.8 baseline:
  - **UI-074** заменяет future-target старой auction-autoscroll модели: локальная auction table больше не автопрокручивается; persisted switch управляет только `/auction-lots-overlay`.
  - **UI-087** заменяет manual `Требует привязки` для обычного empty-message event во время running auction на отдельный временный `Без текста N`.
  - **UI-088/UI-090** заменяют retained R1.0.9 UI organization как future target: file exports CSV/JSON/Excel возвращаются на `Публичный список`, legacy `Совместимый экспорт` удаляется, внутренняя `Настройки → Экспорт` удаляется целиком.
  - **UI-044** в прежнем виде superseded: `Публичный API` не создаётся внутри удаляемой `Настройки → Экспорт`; endpoint `/api/public` сохраняется.
- QA status после review:
  - **QA-1.0.8-01** — остаётся documented finding без отдельного implementation approval;
  - **QA-1.0.8-02** — остаётся documented safety finding без отдельного implementation approval;
  - **QA-1.0.8-03** — target уже определён UI-087 и ждёт общей batch-команды, runtime 1.0.8 пока не соответствует этому target.
- После сверки прошлых решений исправлены stale statuses UI-018/TEST-001/BUG-007/UI-055; UI-053 закрыт решением 2026-10-07: на странице `Аукцион` рядом с `Копировать URL таймера` добавить `Открыть предпросмотр таймера`, доступный и для Max Amount, и для wheel context через существующий `/timer-overlay?preview=1`.
- AUCTION-TIMER-REVIEW-002 закрыт прямым решением пользователя 2026-10-07: tie overtime Max Amount должен использовать saved Max Amount duration default; current 1.0.8 пока ошибочно использует wheel-duration default. Отдельный overtime setting не создаётся; pending-overtime `Сбросить` также возвращает Max Amount default; ручное изменение времени до `Старт` сохраняется.
- AUCTION-TIMER-REVIEW-003 закрыт решением пользователя 2026-10-07: ~1.2 s остаётся отдельным technical preparation lead-in после `Старт`/`Крутить`; пользовательская длительность до его окончания не расходуется. После lead-in timer + applicable wheel animation + soundtrack стартуют от одной общей authoritative boundary. Повторный action во время подготовки должен быть re-entry protected. Неразрешённых timer-review вопросов не осталось.

## Dependency reconciliation complete — 2026-10-07

- Point 2 of the post-review plan is complete: all accepted UI/BUG/GLOBAL/timer decisions were cross-checked for shared backend dependencies, supersession and ordering hazards.
- Final precedence corrections include: UI-025 over old hidden-list Enter behavior; UI-043 over stale `Локальный API` undecided text; UI-060 over the old Rules separate-style/save model; GLOBAL-OBS-VISIBILITY-001 over the earlier Rules no-program-visibility rule; AUCTION-TIMER-REVIEW-003 over the old unresolved short-spin lead-in note.
- Rules final boundary: one composite rules template for text/appearance, no duplicate Rules settings in Stream/OBS, common widget show-mode remains a separate widget-level persisted policy, preview stays override.
- Timer final boundary: ~1.2 s preparation is outside configured duration; actual timer/wheel/audio start is synchronized; source-time auction membership begins at the actual Max Amount/overtime start boundary; re-entry is blocked during preparation.
- Max Amount/Conversion final dependency: pre-close pending gates irreversible result; post-close new events use persistent path; Stop remains no-winner emergency exit and does not implicitly discard pending events.
- UI-088/UI-090 final export boundary: public file exports move to Public List; Settings Export and legacy compatible-export UI disappear; `/api/public` remains but has no new visible access point in this batch.
- QA-1.0.8-01/02 remain outside the implementation batch unless separately approved.
- No unresolved logical conflict remains inside the accepted current-review target. Point 3 can now sort implementation by shared foundations/dependencies.
## P01 candidate progress — A/B/C/D complete — 2026-10-07

- Candidate branch: `candidate/p01-mainwindow-shell-cleanup`; CURRENT/main runtime remains unchanged.
- P01-A `8d50ef21f5e05cebce1ba70866e71369f93b893c`: removed duplicate `Файл` menu/actions only.
- P01-B `183c6accb3f974058ac3abbd1949da558f7f6c9f`: removed `Вид` menu and retained one direct MainWindow `F5 → refresh_all()` action.
- P01-C `0845c3c624edd907acd68a0f7e5f669f5b96a0f4`: added non-clickable `F5 — обновить данные во всех разделах` label in the existing menu-bar area.
- P01-D `4dfd487f700ab1c1cd456df9ee9d34dcf582397c`: added focused shell assertions to the existing GUI regression smoke for no menus, exact/noninteractive hint, exactly one F5 action and real `refresh_all()` dispatch.
- Candidate source diff now contains `streaming_manager/views/main_window.py` plus `tools/gui_regression_smoke.py`; product/runtime behavior is still changed only in `main_window.py`.
- P01-E QA trigger: draft PR #19 opened only to run existing PR-gated automation against candidate SHA `4dfd487f700ab1c1cd456df9ee9d34dcf582397c`; no merge/publication authorized.
- Main Windows regression run `37582729729`, job `112665869659` — **SUCCESS**.
- PASS includes compile, Actions/publication regressions, A9 UI-state/installer checks, backup/restore/media regressions, source snapshot, fresh DB integrity, the P01-focused Native GUI regression, frozen application build/startup/browser-source checks, Inno Setup, installer build and silent-install startup/filesystem regression.
- Automatic `Publication wording gate` run `37582729787` failed only on pre-existing documentation wording in `ACTIVE_REVIEW_LEDGER.md`, `IDEA_INVENTORY.md` and `PROJECT_STATE.md`; no P01 runtime/new-regression file was cited, so it remains a separate documentation finding outside P01.
- P01 manual-QA artifact attempt: temporary QA branch `qa/p01-windows-artifact` and draft PR #20 were created from exact tested runtime commit `4dfd487f700ab1c1cd456df9ee9d34dcf582397c`; the newly introduced artifact workflow did not trigger from the API-created QA event. PR #20 was closed **without merge**. Candidate runtime remained unchanged.
- Manual QA artifact was subsequently produced by permanent Windows regression run `37583488177` — **SUCCESS** after adding artifact preservation to the existing regression workflow. GitHub artifact: `11465802252` / `InOneLine_1.0.8_WINDOWS_QA`.
- Google Drive handoff completed: `InOneLine_P01_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive file ID `1VvMjue9GOFet2XSN8PpttBkX1nyB03Gk`, verified size `46756638` bytes, stored in folder `Программа для стриминга`; ZIP contains `InOneLine_Setup_1.0.8.exe`.
- Extracted installer: `InOneLine_P01_CANDIDATE_Setup_1.0.8.exe`, 47,616,617 bytes, SHA-256 `c931ae5d7abba8ac8ae3d0f43e61fcacb1dc4344e746c028551c3eafec32ce82`.
- Product runtime remained the P01 candidate; the later branch commit only synchronized CI artifact-preservation infrastructure.
- P01 automated candidate gate — **PASS**. Manual QA accepted by user on 2026-10-07: top `Файл`/`Вид` menus absent; F5 produced no error and its non-visual refresh behavior was accepted.
- PR #19 merged into `main`: `d40c0dc7798aae3c9d7a8d7b8faab97756e06512`.
- Post-merge verification: QA-only PR #21 from the exact merge commit; regression run `37586507639` — **SUCCESS**. PR #21 closed without merge.
- Separate Publication wording gate `37586507550` failed on the already-known documentation wording issue; it did not invalidate the Windows runtime regression.
- **P01 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- P02 is now unblocked.

## P02 candidate progress — A/B/C/D/E complete — 2026-10-07
- Branch: `candidate/p02-list-public-labels`.
- **P02-A / UI-010** implementation commit `f6481b6668019b45af3d9d11040117baf2868f4c`: visible main tab label `Игры` -> `Список` only; internal `GamesTab/games_tab`, DB/API semantics and behavior unchanged.
- P02-A regression expectation commit `cc1bad8b3e6a0d882dec429f043997b64fcb11cf`: existing GUI smoke expects `Список`.
- **P02-B / UI-011** implementation commit `1ccc1ad65ad6a050380ce469f99ae307976b2dbd`: only the main-list button label `Добавить игру` -> `Добавить`; existing `GamesTab.add_game` action unchanged.
- P02-B regression commit `772af23741caa81ddc8ad8f8562dad0ec65d6b9e`: GUI smoke asserts the button text is exactly `Добавить`.
- **P02-C / UI-012** implementation commit `dc4197fc05f9eec7885705f77eda1ed7053962b3`: common GameDialog window title is exactly `Добавить` or `Изменить`; internal headings `Новая игра` and `Редактирование записи` removed.
- P02-C regression commit `57789c7dbbc1202f000cf8c74f04239f8772c4d9`: GUI smoke instantiates both dialog modes and checks titles/headings.
- **P02-D / UI-013** implementation commit `e62c0b08de7bd358e85eaf3d6354816dbb3d7063`: visible field labels only: `Название игры:` -> `Название:`; `Дата выхода:` -> `Дата:`. Widgets, payload keys, parsing, DB and storage semantics unchanged.
- P02-D regression commit `e7b90528e3b17ac3b16a4e846a5dec98ba8c4915`: both add/edit GameDialog modes assert new labels and absence of legacy labels.
- **P02-E / UI-015** implementation commit `635e4405ffd12ed35f8c0385616ff1f1193a689f`: visible labels only: `Дата (необязательно):`, `Баллы (необязательно):`, `Отзыв (необязательно):`. `Название` remains required; `Кооператив` and `Статус` keep their current default selections and are not marked optional.
- P02-E regression commit `1f73618165e5e3f1cd3acad833209cc4cef58f45`: add/edit dialogs assert the optional labels, absence of incorrect optional markers on `Кооператив/Статус`, and preserved default `Баллы = 0`.
- Focused P02-E diff versus P02-D: `games.py` 3 additions / 3 deletions; remaining changes are regression-only.
- **P02-F / UI-022** implementation commits `8781b4bafbfdfdafcbfd960f6d667924ca08f822` + `6a7746c956460ca9464951551f5b7242af174958`: main button `Очистить список`; dialog title `Очистить список`; heading `Будут удалены все записи: N`; warning uses `обычные, архивные и временные записи`; exact confirm text `УДАЛИТЬ ЗАПИСИ`; destructive button `Удалить записи`; worker completion also restores `Очистить список` instead of the legacy label.
- P02-F regression commits `7ac2eb591a9af5c93aa5a542d07f3c049dcac3ab` + `00abccc2301d72076ad4caa1a36f32440c23bd73`: verify exact texts, inexact/exact confirmation enablement, Enter acceptance, and post-worker label persistence.
- Existing open-auction guard, isolated safety-backup, background worker, completed-auction history/Journal preservation and destructive workflow logic are unchanged.
- Focused P02-F diff versus P02-E: `games.py` 7 additions / 7 deletions; remaining changes are regression-only.
- **P02-G / UI-024** implementation commit `99ecc55ef2556957f0957c61098a4ae6df03c2d6`: sorting-rules wording only — heading `Автоматическая сортировка списка`; intro `Сначала список распределяется по статусу:`; archive wording `В режиме «Всего» сначала идут все записи вне архива` and `Архивные записи располагаются отдельным блоком в самом низу`. Sorting semantics and order are unchanged.
- P02-G regression commit `7b03ca8786ec81b507a0ad4c265dcf07928cc4bd`: GUI smoke captures the actual QMessageBox and asserts exact new wording plus absence of legacy wording.
- Focused P02-G diff versus P02-F: `games.py` 4 additions / 4 deletions; remaining changes are regression-only.
- **P02-H / UI-029** implementation commit `282ca506ad6376c5ee165009bff8bfa1c9969f44`: on `Публичный список` only, the top explanatory text and read-only table title header change `НАЗВАНИЕ ИГРЫ` -> `НАЗВАНИЕ`. Data field `title`, API/JSON keys, public XLSX headers/mapping, CSV/XLSX exporters and sorting remain unchanged.
- P02-H regression commit `6566370f056feaa2063f0bed5f6164877d62b34a`: GUI smoke asserts the explanatory text uses `НАЗВАНИЕ`, contains no legacy `НАЗВАНИЕ ИГРЫ`, and table column 3 is exactly `НАЗВАНИЕ`.
- Focused P02-H diff versus P02-G: `public.py` 2 additions / 2 deletions; remaining changes are regression-only.
- **P02-I / UI-030** implementation commit `a82154e53ad61a25c7026de64592ad1ba422a802`: removed only the visible `Открыть локальный JSON` button and its click connection from `Публичный список`; dead imports `QDesktopServices` / `QUrl` removed after reference check.
- `/api/public` remains unchanged in `api_server.py`; Public List data model, read-only table, XLSX mirror, API payload and exports are untouched.
- P02-I regression commit `655dc42510cd726eaa3098ab00ded28e49958bb5`: GUI smoke asserts the legacy Public List JSON button is absent.
- Focused P02-I diff versus P02-H: only `public.py` and regression smoke; `api_server.py` is not in the diff.
- **P02 implementation scope UI-010..013, UI-015, UI-022, UI-024, UI-029, UI-030 is complete as candidate.**
- Draft PR #22 opened for QA only; candidate SHA `655dc42510cd726eaa3098ab00ded28e49958bb5`, 20 small commits, 4 changed files (`games.py`, `main_window.py`, `public.py`, existing `gui_regression_smoke.py`).
- Candidate-wide Windows regression run `37590831341` — **SUCCESS**. Passed compile, Actions-version, publication CI consolidation, A9 UI-state/installer checks, backup/restore/media, clean source snapshot, fresh DB integrity, **Native GUI regression core with all P02 focused assertions**, frozen build/startup/browser-source, Inno Setup, installer build, silent-install startup and installer artifact preservation.
- Separate Publication wording gate `37590831319` failed only on pre-existing documentation wording in `docs/ACTIVE_REVIEW_LEDGER.md`, `docs/IDEA_INVENTORY.md`, `docs/PROJECT_STATE.md`; P02 runtime/new GUI regression files were not cited.
- Manual-QA artifact: GitHub artifact `11469195381` / `InOneLine_1.0.8_WINDOWS_QA`; ZIP SHA-256 `4602b57a8547075fe9362f0ffa970cd7a170c8082b6755da3846c9adad95301c`.
- ZIP contains exactly `InOneLine_Setup_1.0.8.exe`, 47,609,680 bytes, SHA-256 `8aaf388bb20b59b0c039f4a529b3298f7d3258002890498ee60dac7a74920647`.
- Google Drive handoff complete: `InOneLine_P02_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1bRyJ2SJMvRIBadjwgSCOY12JjBp1Ajpp`, verified size 46,749,709 bytes in folder `Программа для стриминга`.
- Manual QA 2026-10-07: user confirmed the rest of P02 looks/works as intended, but found remaining user-facing game terminology in screenshots. **P02 = REOPENED / MANUAL QA FAIL ON TERMINOLOGY ONLY.**
- New global rule: **GLOBAL-TERMINOLOGY-001** — user-facing object terminology must be neutral (`список / запись / название / лот` by context); internal `Game/GamesTab/game_id` and legacy compatibility remain technical contracts.
- **P02-J1** fixes the screenshot-visible List/Public terminology: commits `a49e7a41134479675fb558df6960319f45129d3f` + `1748a31d8606a513cbcb67d9ba1035e5861d98b7`; regression `f2b9e9218d81aea5a0b533a2e8b629a4894e6b92`.
- **P02-J2** fixes remaining safe current-package wording in list-toggle, restore counts, duplicate fallback and clear-list failure messages: commits `a0ee0a764da4360cd93869295df67dc7cb9e4530`, `404919075f3b54e840a0cb277739abfeea318201`, `e75af0d0195a41665d5839ab6039314e46a33230`, `eba81eb4934984fd2ca1f85da0be3106f51b765b`; regression `4bf4c7e2a4b15837e172073098dcf5595c227e8c`.
- CSV/import wording is intentionally deferred to P03 so preferred neutral headers/messages and backward-compatible aliases are changed together. Remaining terminology is routed to P05/P07, P09, P12/P20, P18/P19 and P22.
- Previous Drive artifact `1bRyJ2SJMvRIBadjwgSCOY12JjBp1Ajpp` is superseded for acceptance.
- Fresh P02-J candidate head: `4bf4c7e2a4b15837e172073098dcf5595c227e8c`.
- Fresh candidate-wide Windows regression run `37594380334` — **SUCCESS**. Native GUI regression, frozen build/startup, Browser Source, installer build, silent-install and artifact preservation all passed.
- New manual-QA artifact: GitHub artifact `11470436517`; ZIP SHA-256 `6105bcfc17c93eabbf1cf4aa6ace35dd520bad38fe1f6b76a6e2f3e2a7e41085`.
- ZIP contains exactly `InOneLine_Setup_1.0.8.exe`, 47,627,996 bytes, SHA-256 `39dc8bb825ff6d6b58cf880668d0fa687fc37708802c0a424357b76337dc42d6`.
- Google Drive V2 handoff: `InOneLine_P02_CANDIDATE_V2_1.0.8_WINDOWS_QA.zip`, Drive ID `1fGGNR1_2FZl1mgKwFAPexmE1HFzXKygt`, verified size 46,767,800 bytes.
- Repeat manual QA 2026-10-07: user confirmed **everything is correct and works**. P02 terminology fixes J1/J2 accepted.
- Safety clarification accepted: **do not change `ИГРАЛ / НЕ ИГРАЛ`**; they are coupled to sorting/status mechanics. Terminology changes must be targeted user-facing substitutions only, never bulk renames that may alter parsers, persisted/API keys, status values or business logic.
- Clean promotion PR #23 merged into `main`: merge commit `e89b178f4816b30e3a54e59ea5407eab2e782e6d`.
- Pre-merge clean-promotion regression `37596838501` — **SUCCESS**.
- Post-merge QA-only PR #24 from the exact merge commit completed Regression Foundation run `37597234911` — **SUCCESS** and was closed without merge. Historical candidate PR #22 also closed without merge.
- **P02 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- **P03 is now unblocked.** GLOBAL-TERMINOLOGY-001 remains active, with `ИГРАЛ / НЕ ИГРАЛ` explicitly protected.

## P03 candidate progress — A/B/C complete — 2026-10-07
- Branch: `candidate/p03-csv-date-caret`.
- **P03-A / UI-021** implementation `d6b8b30a1336f5b7864b1ca3f19c41c4473815f2`: CSV importer accepts canonical headers `НАЗВАНИЕ` and `ДАТА`; legacy aliases `НАЗВАНИЕ ИГРЫ` and `ДАТА ВЫХОДА` remain accepted. Existing points/coop/status/review semantics are unchanged and `ИГРАЛ / НЕ ИГРАЛ` values are untouched.
- P03-A regression `2ac0f44deaa3f6234af194d88b755e36fc729c72`: isolated DB verifies new and legacy title/date headers map correctly.
- **P03-B / UI-020** implementation `a70f00688650638ff2173ba942b418db26ba8201`: rewrites only `Правила импорта CSV` using canonical `НАЗВАНИЕ / ДАТА`, explicit optional fields, `0` guidance, neutral `запись` wording, compatibility aliases, and atomic-import/backup explanation.
- P03-B regression `ec74bed827edaa675f6360dd703326e442f38ee9`: captures the actual help QMessageBox and checks canonical wording, compatibility aliases and preserved `НЕ ИГРАЛ / ИГРАЛ` status labels.
- **P03-C / UI-019** implementation `0f7f8b24b3b702607b9c1ef4b167745f714230c7`: CSV validation errors now follow `что не так -> строка/значение -> как исправить` for duplicate title, status, coop, date, points, missing headers and legacy `Название|Баллы`. Duplicate tracking now remembers the first source line only to improve the error message; parsed data and transaction semantics are unchanged.
- P03-C regression `2230c10a06a986389bff3ab546afbe011368730c` + cleanup `e7a32323fbe3f951f966b8a2d538961ed34f6fa6`: existing GUI smoke verifies the TEST-001 error set, preserves explicit `ИГРАЛ / НЕ ИГРАЛ` allowed statuses, checks `0` guidance, confirms safety-backup path survives wrapper errors, and confirms full-file atomicity.
- Focused P03-C runtime diff versus P03-B is limited to `streaming_manager/db/services.py`; regression changes remain in existing `gui_regression_smoke.py`.
- **P03 is not accepted yet.** Next small step: BUG-002 date-field caret preservation.
## P00 exact baseline verification — PASS — 2026-10-07

- Runtime remains exact CURRENT **1.0.8 / schema 19 / 15 named migrations**.
- No runtime/source change occurred during P00.
- Accepted A9 runtime anchor is `74ad16c5772d5cc191f7e307203b6a574af7815c`; post-A9 changes before this gate were documentation/README only.
- Permanent Windows regression was freshly rerun: run `36972339831`, fresh job `112658659175`, conclusion **success**.
- Key green areas: compile, fresh DB integrity, native GUI, frozen startup/Browser Source, full backup/restore and rollback, A9 UI-state migration/single-instance, media/filesystem, Inno Setup and silent-install startup/filesystem.
- CURRENT 1.0.8 is therefore the verified rollback/reference baseline for the first implementation candidate P01.
## Implementation planning complete — 2026-10-07

- Point 3 is complete: the accepted review batch is sorted into P00–P22 + FINAL GATE in dependency order.
- Detailed queue and package membership are canonical in `docs/ACTIVE_REVIEW_LEDGER.md` §4.7; `docs/ROADMAP.md` contains the compact sequence.
- Mechanical coverage verified: UI-001…UI-090 all accounted for, no missing IDs and no duplicate package assignment.
- Ordering principle: low-risk UI first; then shared list/state/position/media foundations; then OBS/Rules/Auction structure; then timing; then Settings/integrations/conversion; then auction business/accounting cross-links; History/Journal last.
- Every package is a separate candidate with automated checks and mandatory user manual acceptance before the next package.
- Runtime remains exact CURRENT **1.0.8 / schema 19 / 15 named migrations**. No implementation package has started yet.
## Active review / bugfix phase

Новые product features временно приостановлены по прямому решению пользователя. Текущий рабочий протокол и накопительная очередь замечаний находятся в `docs/ACTIVE_REVIEW_LEDGER.md`.

Правило этапа: сначала разбор скриншота и запись замечаний без изменения runtime; реализация начинается только после команды пользователя **«всё делаем»**. После неё задачи сортируются по сложности/зависимостям и выполняются по одной; после каждого исправления обязательна отдельная ручная проверка пользователя. Existing-first/minimal-diff/stability-first invariant сохраняется.
