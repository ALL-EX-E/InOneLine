# InOneLine — Current Project State

Обновлено: **2026-10-10**

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
- Final precedence corrections include: UI-025 over old hidden-list Enter behavior; UI-043 over stale `Локальный API` undecided text; UI-060 over the old Rules model with separate formatting and save actions; GLOBAL-OBS-VISIBILITY-001 over the earlier Rules no-program-visibility rule; AUCTION-TIMER-REVIEW-003 over the old unresolved short-spin lead-in note.
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
- **P03-D / BUG-002** implementation `7872121a09c740e99073053d9b1ee9e776296202`: `_format_date_while_typing()` keeps the existing auto-dot formatter but restores caret using the formatted prefix left of the current caret instead of forcing `len(formatted)`. No new widget; `normalize_date_text()` and accepted date formats are unchanged.
- P03-D regression `2fd76ae1260738fdf289b36de084ac2b15234e19`: both Add/Edit GameDialog modes verify middle-of-field formatting, Backspace, Delete, selection replacement and sequential compact input; caret no longer jumps to the end.
- Focused P03-D diff versus P03-C: `games.py` caret-preservation logic + regression-only changes in existing `gui_regression_smoke.py`.
- **P03 implementation scope is complete as candidate.**
- Clean review branch: `candidate/p03-review`, head `9fb64bc0d0867f439b0866f82826b406c22ef012`; draft PR #25. Diff from current `main`: exactly 3 files — `streaming_manager/db/services.py`, `streaming_manager/views/games.py`, existing `tools/gui_regression_smoke.py`.
- Candidate-wide Windows regression run `37633288322` — **SUCCESS**. Passed compile, current dependency/toolchain gates, backup/restore/media, fresh DB, Native GUI regression with P03 header/help/error/atomicity/caret checks, frozen build/startup/Browser Source, installer build, silent-install startup and artifact preservation.
- Separate Publication wording gate `37633288273` failed only on the already-known documentation wording in `docs/ACTIVE_REVIEW_LEDGER.md`, `docs/IDEA_INVENTORY.md`, and `docs/PROJECT_STATE.md`; P03 runtime/regression files were not cited.
- Manual-QA artifact: GitHub artifact `11487761077`; ZIP SHA-256 `b3dd8056d15430ad407472ff27951c760fffec34149cbcf24d0ff778d7bdb8be`.
- ZIP contains exactly `InOneLine_Setup_1.0.8.exe`, 47,615,165 bytes, SHA-256 `5f82f276e36ab316b2f2bc9f130036791e2b3f0c7de2d9c7d067690e9a57086d`.
- Google Drive handoff: `InOneLine_P03_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1Fpk09-w7nq22ao8qdgDMLyJBSJIwD9tu`, verified ZIP size 46,755,018 bytes.
- **P03 automated candidate gate = PASS; user manual QA = PASS / ACCEPTED.** Merge and post-merge regression passed.
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

## P03 manual acceptance and current handoff

- User manual acceptance: **«Работает. Идём дальше.»** in reply to the complete P03 checklist. CSV headers/help/errors, compatibility aliases, merge without clearing empty values, atomicity/backup path and date editing in both Add/Edit modes are **PASS / MANUALLY ACCEPTED**.
- Exact manually checked candidate head: `9fb64bc0d0867f439b0866f82826b406c22ef012`; Windows regression `37633288322` was successful. Accepted installer/ZIP bytes remain unchanged.
- Manual checklist: `InOneLine_P03_MANUAL_QA.zip`, 15 CSV files + README; Drive ID `1eJG2u16e6xpLgJadVp0ugju04WSVn_FB`.
- **P03 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS. P04-A / UI-025 is CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS. P04-B / BUG-003 is next.**

- Current manual-QA format: issue the complete current-package checklist in one message; do not repeat already accepted scenarios without a reason. Other latest workflow and terminology rules remain active.

## P03 technical closure and P04-A start

- User accepted the complete P03 manual checklist: «Работает. Идём дальше.»
- Clean promotion PR #26 merged as `8a0ac384f2df7b2cbf526c14e62ae89b86586932`; all three accepted file blobs match candidate `9fb64bc0d0867f439b0866f82826b406c22ef012`.
- Pre-merge Windows regression `37647359158` and wording gate `37647358838` — **SUCCESS**.
- Exact merge-commit Windows regression `37647803098` and wording gate `37647803210` — **SUCCESS**. Historical QA PR #25 closed without merge. Accepted installer bytes were not replaced.
- **P03 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- **P04-A / UI-025 = MANUALLY ACCEPTED / AWAITING CLEAN PROMOTION.** Accepted scope removes obsolete hide/show-list buttons, spacers, MainWindow/Enter visibility hooks and `lists/visible`, `games/list_visible`, `public/list_visible` UI-state keys while preserving the existing tables, `ui_state.ini` geometry/tab restoration, data, filters and explicit search navigation. Selection/search/total-points follow-up scopes remain separate later steps.
- P04 remains open. Do not start the next implementation step until P04-A is clean-promoted, merged and exact post-merge regression passes.

## P04-A / UI-025 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS

- Branch `candidate/p04-a-list-visibility`, head `3cdff95129d012729d1cfc8c7a74f4050f3231d0`, draft PR #27. Exactly four changed files: MainWindow, Games, Public and existing GUI regression smoke; 53 additions / 195 deletions. Published blobs match the locally tested files.
- Removed only obsolete hide/show controls, empty spacers and MainWindow/search visibility hooks. `_restore_ui_state()` removes `lists/visible`, `games/list_visible`, `public/list_visible`; save no longer recreates them. Window geometry/maximized/tab state and the native-QSettings migration backup remain intact. Existing tables, data, filters, explicit selection synchronization, statuses, schema and accepted P03 CSV/date behavior are preserved.
- Local compile, publication wording and full existing GUI smoke — **PASS**. New GUI cases cover upgrade from false visibility preferences, both tables visible, no hide/show buttons, Enter navigation and synchronized selection, unchanged window size and saved-tab/geometry persistence.
- Exact candidate Windows regression `37648861189` — **SUCCESS**, including Native GUI, frozen startup/Browser Source, installer build, silent install and artifact preservation. Publication wording gate `37648861211` — **SUCCESS**.
- Artifact `11495357287`, ZIP size 46,751,606 bytes, GitHub SHA-256 digest `1eb7e5f9589f71fae4cf778d6da90f06e5d08badea0fd67035fd8d3f900bfcee`. Installer CI SHA-256 `086ed75bf046036a0d7d74efff677626f460d6346c5a849249d3fd53d229bdc0`.
- Drive handoff: `InOneLine_P04_A_CANDIDATE_1.0.8_WINDOWS_QA.zip`, file ID `13AHiI075GQtGE5stmsQFUhUrnuDA9KRR`; uploaded directly from the GitHub artifact reference, verified Drive size 46,751,606 bytes.
- Complete manual checklist issued together: (1) both lists and existing records visible, hide/show buttons absent; (2) repeated tab switches do not resize the window or hide either table; (3) Enter search on both tabs selects/navigates to an active existing record and synchronizes selection; (4) F5 keeps both tables visible and data accessible; (5) restart restores window position/size and selected tab, both tables remain visible.
- **P04-A = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS. P04 remains open.** User accepted the complete checklist with «Работает. Записывай. Пока дальше не идём.» Clean promotion PR #28 (`7fe09b7543b666ae6657377a9d782bac9442ec77`) passed regression `37652474014` + wording `37652474280`, merged as `fddf49014ffb34ff48c6871027a817f1453edb9e`, and exact post-merge regression `37653013085` + wording `37653013097` succeeded. Candidate PR #27 closed without merge. **Next: P04-B / BUG-003 only.**


## P04-B / BUG-003 start

- Scope is intentionally small: ordinary refresh/filter must preserve selection only when the same row remains visible; otherwise leave no row selected. If nothing was selected before refresh, keep no selection.
- Add a lightweight empty-area click deselect behavior for the main list.
- Existing explicit actions that intentionally select a row remain unchanged: Enter search and `focus_game()`.
- Search-across-filters, removal of search/reset buttons, Public search changes, and total-points counter remain later P04 scopes.


## P04-B / BUG-003 candidate gate — PASS / AWAITING MANUAL QA

- Implementation `b059d9dc997b1df6af2b75a7f73de2db9d852694`; regression head `f3740181a9f161c3c56965d075a2d3c2ae3d0762`; draft PR #29.
- Ordinary refresh/filter no longer auto-selects a replacement first row. Selection is restored only for the same still-visible game; otherwise selection/current cell are cleared.
- Left click on empty main-list table space clears selection/current cell through the existing viewport and action-state logic.
- Explicit Enter search and `focus_game()` selection are preserved.
- Windows regression `37654068727` = SUCCESS; wording gate `37654069253` = SUCCESS.
- Artifact `11497079107`: ZIP SHA-256 `8bd07c0e3a38d568afede9591a340d7ae93de8b34d5451f99482c7fbf0716d8b`; installer SHA-256 `c4156a66265d77d12a7359f6dbfbd42b0e38c34e98923d40bd8df582810522f8`.
- Drive: `InOneLine_P04_B_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1eRIdxzl8ny6svzrZlgKeS-3nsDJI9IOu`, 46,766,270 bytes.
- **P04-B = AUTOMATED PASS / AWAITING USER MANUAL QA / NOT ACCEPTED / NOT MERGED.**

## P04-B CLOSED / P04-C automated candidate — 2026-10-07

- P04-B / BUG-003 is fully closed: user manual PASS, merge `f2cc6e9f0968eac1be75f7d5b91ead7afe7e76df`, post-merge regression `37655810706` SUCCESS and wording `37655810503` SUCCESS.
- P04-C / BUG-004 is implemented only on candidate head `68f11b92fe2dd5ebb91752cf8723a9d5c66a0e09` / PR #31.
- Candidate changes only Public empty-area deselection and its existing GUI-smoke coverage; search/data/sort/Public XLSX and other P04 scopes remain unchanged.
- Regression Foundation `37656101654` = SUCCESS; wording checks = SUCCESS.
- Artifact `11498364307`: ZIP SHA-256 `a8aae91a3edcef92e8ed95f5b9152182dd58b2d123da5730f7c3c1a348df4bf8`; installer SHA-256 `c5c64e75a53434d75de068d51747ab8c1175b8facc465fcbecd2d12f0bc628b1`.
- Drive file ID `1M0ooksHuIEa0_50oJEcICJtkzzWCxK5L`, 46,761,453 bytes.
- **P04-C = AWAITING USER MANUAL QA / NOT MERGED.**

## GLOBAL-FOCUS-001 — единое снятие focus/selection во всей программе — DEFERRED / RECORDED — 2026-10-07

- Пользователь выявил общий UX-дефект после ручной проверки P04-C: если таблица полностью заполнена строками, для снятия selection может не существовать видимой пустой области; пользователь не должен прокручивать список до самого низа только ради deselect.
- Та же проблема шире таблиц: после клика в поле ввода focus визуально/логически остаётся на нём, пока пользователь не выберет другой focusable control.
- Это не дефект только Games/Public и не должен решаться набором локальных hacks по каждой вкладке.
- Целевое продуктовое правило: должен существовать единый естественный способ убрать focus с поля и снять selection с таблицы независимо от наличия видимой пустой строки/области. Пользователь не должен искать другое поле или прокручивать длинный список вниз.
- Предпочтительно сначала исследовать один общий механизм на уровне shared UI/MainWindow/event handling; не ломать обычный click/double-click, Enter-search, keyboard navigation, dialog validation, caret/selection semantics, buttons, combo/spin boxes и explicit programmatic focus/selection.
- Конкретный жест/реализацию (например neutral-background click и/или универсальный keyboard escape fallback) утвердить при отдельном global UI review после проверки влияния на существующие widgets.
- Не расширять текущий P04-C до глобального mouse/focus subsystem. Реализовывать отдельным изолированным шагом после сортировки зависимостей.

## P04-C / BUG-004 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-07

- User manual result: `Работает`. Separate cross-app focus/selection limitation was recorded as GLOBAL-FOCUS-001 and intentionally excluded from P04-C.
- Exact accepted candidate head: `68f11b92fe2dd5ebb91752cf8723a9d5c66a0e09`.
- Clean promotion PR #32 passed regression and wording gates, then merged as `7df4071088e8ef3f89b5f6d20caeab745a958d39`.
- Exact post-merge Regression Foundation `37658841462` = SUCCESS; wording gate `37658841402` = SUCCESS.
- P04-C remains limited to Public empty-area deselection and existing GUI regression. GLOBAL-FOCUS-001 remains DEFERRED / RECORDED as a later global UI task.

## P04-D / UI-007 candidate — AUTOMATED PASS / AWAITING MANUAL QA — 2026-10-07

- Branch `candidate/p04-d-search-scope`, head `943a26d76bbaf0784b9e38fed84076d9597e82e3`, draft PR #33; base at implementation start `948a577e558ac37d36a10679d12afc9dde3a4b79`.
- Scope is UI-007 only. A non-empty main-list search reuses `games_refresh_snapshot/_list_games_conn` with effective `status_filter="all"` + `include_archived=True`, while `active_filter` itself remains unchanged.
- Clearing search therefore immediately restores the currently selected statistic filter. Existing Unicode normalization and title/review matching are preserved; `auction_only=1` temporary lots remain excluded by the existing normal-list query.
- UI-008/UI-009/UI-028/UI-076 and GLOBAL-FOCUS-001 are not included.
- Exact diff: `streaming_manager/views/games.py` + existing `tools/gui_regression_smoke.py` only; 64 additions / 3 deletions.
- Regression Foundation `37660389855` = SUCCESS; wording gate `37660389867` = SUCCESS.
- Artifact `11501485064`, ZIP 46,756,657 bytes, SHA-256 `6e8d3d5d320c60fc75e882a7c53e00fefea6388fadae7081f3d97e29f812dad9`; contains exactly `InOneLine_Setup_1.0.8.exe`, 47,616,617 bytes, SHA-256 `2a6fa43681b535f14a4092693c975033863fe969b756e78cc994943fc6e682d7`.
- Drive handoff: `InOneLine_P04_D_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1o1BEOnoJqFCwkgTJVQoBgahGiVWYslSC`, verified 46,756,657 bytes.
- **P04-D = AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED.** Do not start UI-008/UI-009 or later P04 scopes before manual acceptance and technical closure.

## P04-D / UI-007 — ПРИНЯТ И ТЕХНИЧЕСКИ ЗАКРЫТ — 2026-10-08

- Пользователь подтвердил **ручной PASS всех шести проверок** поиска и сохранения фильтра на `InOneLine_P04_D_CANDIDATE_1.0.8_WINDOWS_QA.zip`.
- Original QA candidate `943a26d76bbaf0784b9e38fed84076d9597e82e3`; исторический PR #33 закрыт без merge после принятия.
- Чистый перенос через PR #35, два файла с теми же SHA Git blob, что и у вручную проверенного кандидата; merge commit `e9e22d27d0f0101773c7016367f867e2bb61e7c8`.
- До merge Windows Regression `37748280816` = SUCCESS и wording `37748280794` = SUCCESS; **точный post-merge** Regression `37748751586` = SUCCESS и wording `37748751519` = SUCCESS.
- **P04-D = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** В `main` теперь действуют независимый от статистического фильтра поиск по всем обычным записям с архивом и возврат выбранного фильтра после очистки строки. Следующая отдельная задача P04 — **UI-008**.
- Публичный maintenance installer не заменён; текущий исходный код и официальный опубликованный установщик могут отличаться при одинаковом `APP_VERSION=1.0.8`. Не объявлять новый релиз.
- PR #34 (полный аудит и отдельные исправления) остаётся самостоятельным не принятым пакетом; после этого merge его изменения в общем `tools/gui_regression_smoke.py` требуют повторной совместной проверки, прежде чем объединять #34.

## UI-008 — отдельный кандидат ожидает ручной QA — 2026-10-08

- После принятого/закрытого P04-D подготовлен только UI-008: убрать кнопку `Найти` на основном списке, сохранив live-search/Enter, публичный список и отдельный UI-009.
- Exact head `f8f03430d0ed77fddde18ba58e2db7b8030cead4`, draft PR #37. Windows regression `37749509764` = SUCCESS, wording `37749509711` = SUCCESS.
- QA artifact `11537451402`, ZIP SHA-256 `44ef8a29606af13c7af3f4a9343a2c890e25a90bf43f67649a7499de21e0029d`; Drive ZIP ID `1ME2RkaJSUpME4PQE3-mIXZHjpaUP9XMQ`. ZIP CRC PASS, единственный installer SHA-256 `f96bc5804d3f19de8fbe18587f612cc57fcd4a17723eb95b4c40a1a9d4902815`.
- **UI-008 = AUTOMATED PASS / AWAITING MANUAL QA / NOT MERGED.** CURRENT main остаётся принятым P04-D. Следующий UI-009 запрещён до ручной приёмки и отдельной технической финализации UI-008.

## UI-008 — MANUAL FAIL / REOPENED (2026-10-08)

- Пользователь прислал скриншот: в основном `Список` остаётся кнопка `Найти`. Остальные четыре ручные проверки пройдены. Итог: **FAIL 1/5, PASS 4/5**. Текущий кандидат НЕ принят, PR #37 открыт/draft, код UI-008 не в `main`.
- Удаление `self.search_btn` подтверждено в исходном коде candidate, но текущий Windows CI не проверяет визуальный интерфейс установленного бинарника (только source GUI smoke плюс installed EXE startup/API), а каталог/хэш фактически запущенного пользователем `InOneLine.exe` пока неизвестны.
- Требуется сопоставить исполняемый путь и SHA-256 процесса с установщиком из exact QA ZIP; не делать новый runtime patch до идентификации сбоя упаковки/установки/запуска. Существующий accepted P04-D в `main` остаётся неизменным. UI-009 НЕ начинать.

## UI-008 / P04 — закрытие после повторной установки — 2026-10-08

- Первоначальная ручная QA: 4/5 PASS, 1/5 FAIL (кнопка `Найти` оставалась). После переустановки пользователь прислал скриншот без `Найти` на `Список`; совместно с ранее подтверждёнными четырьмя пунктами — **ручной PASS 5/5**. Точная причина старого экрана неизвестна: путь и SHA запущенного EXE первой попытки не получены. Не считать это доказанным дефектом обновления.
- Проверенный кандидат `f8f03430d0ed77fddde18ba58e2db7b8030cead4` / historical PR #37 закрыт без merge. Принятые Git blobs перенесены через PR #40, head `fa831a05d6e474337e1012752003be639d6ce9c6`; `main` merge commit `f5e244d04db63ddb421213d3ee1272ed77aee55c`.
- Pre-merge Windows regression `37771721603` = SUCCESS, wording `37771721591` = SUCCESS; точный post-merge regression `37772054443` = SUCCESS, wording `37772054420` = SUCCESS. Два Git blob в `main` соответствуют ручному кандидату, без изменений иных файлов.
- **UI-008 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**. APP_VERSION 1.0.8, schema 19, 15 migrations, published installer и rollback не менялись. Следующий UI-009 только в отдельном candidate; проверка same-version reinstallation/frozen UI оставлена как QA-наблюдение, без неподтверждённого fix.

## UI-009 — подготовлен кандидат, ожидается ручной PASS — 2026-10-08

- Пакет после закрытого UI-008: только убрать `Сбросить фильтры` в основном `Список`; native clear X сохраняет выбранный filter `Не играл`/`Архив`. Не затрагивать Public/OBS/БД и другие P04 scope.
- Exact code: `candidate/p04-f-ui009-clear-search` head `2fd8fa5c31b94469e681aaf0d8b1f3699f0c354e`, [draft PR #42](https://github.com/ALL-EX-E/InOneLine/pull/42). Only `games.py` + existing GUI smoke; sole unreferenced `reset_filters()` removed after repo-wide reference check.
- Automated Windows regression `37772947602` = SUCCESS; wording `37772947662` = SUCCESS. Artifact `11547684618`, ZIP SHA-256 `d0d4c0b4cf5a96d428c829e27b19d5c77cc7c58d78d9c7b9e78e509447c24bb7`, one setup EXE SHA-256 `8d326e0386b536dd3403331897cf2c357e52fddcf29be78588c1b37d5f86441b`. ZIP CRC PASS.
- Google Drive QA ZIP `1I6wRbxVqhXPmG_wI4bm4NaY3ujK1f-C9` size confirmed 46 756 918 bytes.
- **UI-009 = AWAITING USER MANUAL QA / NOT MERGED.** Official published release/installer unchanged. Do not advance before manual QA + clean promotion + post-merge.

## UI-009 — технически закрыт 2026-10-08

- Ручная приёмка 5/5 PASS, original candidate `2fd8fa5c31b94469e681aaf0d8b1f3699f0c354e` (PR #42 closed without merge). PR #44 перенёс два exact candidate Git blobs в `main` merge `464136d144e054efcf38a10da8e075ed5fec8281`.
- Pre-merge Windows CI `37778466982` + wording `37778467039` SUCCESS; post-merge Windows `37778963533` + wording `37778963540` SUCCESS. UI-009 = **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**.
- Удалены `Сбросить фильтры` и неиспользуемый `reset_filters()`, существующий крестик поиска/фильтры/Enter и Public List сохранены. 1.0.8/schema 19/15 migrations/accepted installer/rollback unchanged. Следующий scope — **UI-028** (Public `Найти`), только отдельным кандидатом.

## UI-028 — isolated candidate, Windows PASS, ожидает ручной QA — 2026-10-08

- После UI-009 CLOSED подготовлен UI-028 только для Public: удалить кнопку `Найти`; сохранить live-search, Enter selection/focus/sync/no-match, native X. Вне scope Main Games/OBS/DB/медиа/UI-076/GLOBAL-FOCUS-001.
- Code head `e23e4d2fea50cdc6f962c3486244d4a018279c77`, draft PR #46, ровно два файла Public view + existing GUI smoke.
- Windows regression `37779716348` SUCCESS; wording `37779716372` SUCCESS. GitHub artifact `11550914358`: ZIP SHA-256 `67e41ad6777bdea66b0f460998ad6014970d4c3b0e0e243bbcc93de3b43f1502`, CRC PASS; installer SHA-256 `fd9a9d70c74434c6f45b28e63cb6e0239dfe90b986802627701c92f685b5e967`. Drive ZIP ID `1INEdrDa7vnmkioU4C_DWswix-JVXJqfh`, verified 46 763 712 bytes.
- **UI-028 = AWAITING USER MANUAL QA / NOT MERGED**. `main` по-прежнему принят до UI-009, VERSION 1.0.8/schema19/15 migrations и официальный релиз unchanged.

## UI-028 — техническое закрытие — 2026-10-08

- Ручная приёмка 5/5 PASS. Candidate `e23e4d2fea50cdc6f962c3486244d4a018279c77`, historic PR #46 CLOSED without merge. Clean PR #48 merged `974515f8065c8aa11e9b244d9b4841d346259a64`, два blob exact-match.
- Pre-merge Windows `37795531310`, wording `37795531399`; exact post-merge Windows `37796011497`, wording `37796011272` — все **SUCCESS**. UI-028 **CLOSED / ACCEPTED / POST-MERGE PASS**.
- Все текущие P04 удаления кнопок (`UI-008`, `UI-009`, `UI-028`) приняты; следующая отдельная задача `UI-076` — общий счётчик баллов только внутри основного «Список». Version/schema/migrations/accepted installer/rollback без изменений.

## UI-076 — candidate готов, ожидает ручной приёмки — 2026-10-08

- Exact branch `candidate/p04-h-ui076-total-points` head `ad6a913dceaa3ea05584211845a1c9755e5fdebf` / draft PR #50; isolated 3 files: existing aggregate `_game_stats_conn` adds `COALESCE(SUM(sm_points),0) AS total_points` with `auction_only=0`, stat snapshot unchanged, non-clickable `QLabel` `Всего баллов: N` at right of existing stats buttons, current GUI smoke expanded.
- Scope: normal entries all statuses + archived included; temporary auction-only excluded before materialization; no new DB connection, Public/OBS/API, filters, migration.
- Windows CI `37797159783` **SUCCESS**; wording `37797159654` **SUCCESS**. GitHub QA artifact `11559571188`, ZIP 46 774 807 bytes, repository SHA-256 `5796783f2b563c4348174c9e5bed4dc0d7f34b5b957432fbc645c0fe7628297d`. Local CRC/hash verification unavailable; no independent checksum claim. QA Drive ID `1sRuOo4CX5ANiLBfnUMDSvCcWIvrlmKq5`; file size verified 46 774 807 bytes.
- **UI-076 = AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED**; `main` retains accepted UI-028. Version 1.0.8, schema 19, 15 migrations and published release unchanged.

## UI-076 — MANUAL FAIL на 1100 px, исправлен; повторная QA ожидается — 2026-10-08

- Ручная QA исходного UI-076: 5/6 PASS, шестой пункт FAIL по двум скриншотам: QLabel `Всего баллов: 500` и статистические фильтры обрезались на минимальной ширине 1100 px. Не считать UI-076 принятым.
- В том же `candidate/p04-h-ui076-total-points`, PR #50 (draft), head `cbc0056daba456e9c5bf3792f979ca6e9b6877c7`, добавлен адаптивный перенос ТОЛЬКО QLabel на правую вторую строку при нехватке места; на широкой форме он возвращается справа первой строки. Десять фильтров, сумма `sm_points`, запрос/схема БД и обработчики без изменений.
- GUI smoke теперь измеряет геометрию и полноту подписей при `1100 → 1600 → 1100`; Windows CI `37803969976` SUCCESS; wording SUCCESS. Новый артефакт GitHub `11562825039`, ZIP SHA-256 `c86caa20d0c7939997e15bd1d04bcbc741da34a92b8014238327a45139a63041`, CRC PASS, Drive ID `1XQ83iShKwVZapAxyhlp5neDIP5_Flu6I`. Старый Drive QA ZIP `1sRuOo4CX5ANiLBfnUMDSvCcWIvrlmKq5` оставлен как failed/superseded.
- **Status = AUTOMATED PASS / AWAITING USER MANUAL RETEST / NOT MERGED.** Current main остаётся принятым UI-028, официальный релиз, версия 1.0.8, 15 миграций и схема 19 без изменений. Следующий пункт дорожной карты заблокирован до отдельного пользовательского PASS и технического закрытия.

## UI-076 — новый макет по замечаниям пользователя, ждёт ручного подтверждения — 2026-10-08

- Пользователь показал два скриншота узкого/широкого окна: второй фикс устранил усечение, но QLabel `Всего баллов: N` уезжал на отдельную промежуточную строку при сужении. Утверждён целевой макет: счётчик в строке трёх кнопок сортировки/URL/предпросмотра, правый край точно под правым краем `Не кооп`, без изменения расположения десяти фильтров.
- Actual code branch `candidate/p04-h-ui076-total-points`, head `9608b6c557953797779e95dfb0a08806600f5330`, draft PR #50. Новый `sorting_actions` QLabel + геометрический Qt anchor, не меняет SQL/DB schema, данные или UI-state. Скриншоты повторной ручной приёмки ожидаются.
- Windows CI `37808003241` SUCCESS, wording exact head SUCCESS. Новый QA ZIP `1DMqTUTMv4slMcFiXMnx7sdAYFNDi38h8`, GitHub artifact `11564056115`, SHA-256 `30ba79754efc53feafac86412184daea4f796f8d8735fff9ddf4a712a82a42bf`, 46 785 061 bytes, CRC PASS. Предыдущие 2 UI-076 ZIP superseded. UI-076 **NOT MERGED / AWAITING USER MANUAL QA**.
- **P06 future** уменьшение минимального размера и горизонтальная прокрутка подтверждено пользователем, при выполнении отдельно проверить выравнивание счётчика на ширинах ниже 1100. Сейчас не менять размер окна, масштабирование, таблицу и существующую прокрутку.

## UI-076 — stable placement candidate (место 2), ручная QA ожидается — 2026-10-08

- По новым скриншотам прошлое выравнивание относительно «Не кооп» дрожало при resize из-за QHBox spacer mutation. Пользователь предложил места 1 или 2, указал на скрытые action-кнопки и уезжающее `Очистить список` при выборе места 1. Для минимального стабильного scope выбран вариант **2**: QLabel в существующей сортировочной строке сразу после `Открыть предпросмотр списка`, обычный Qt spacing; удалены `QSpacerItem`, собственный `resizeEvent/showEvent` и геометрические пересчёты. Скрытые кнопки/очистка списка не изменены.
- Code candidate `candidate/p04-h-ui076-total-points` head `220adcc78778a43265a855045bf694a5e5d75d03`, PR #50 OPEN/DRAFT. GUI Windows test 7 последовательных ширин и отсутствие горизонтального jitter; Windows run `37810486613` SUCCESS, wording SUCCESS. БД/агрегат и фильтры без изменений.
- Новый QA ZIP `1Ohsul5NaTtGP7J_TCKMytBuY-E8N22dA`, GitHub artifact `11564293733`, 46 769 147 bytes, SHA-256 `18ae42c5e2544c62dfbd646d22828150823623d88ed49bb35ee6d4600b50189b`; local ZIP CRC PASS, one installer. Три предыдущих UI-076 кандидата superseded, не заменяются/не удаляются.
- **UI-076 AWAITING USER QA / NOT MERGED.** Main retains accepted UI-028, App version 1.0.8, schema 19, 15 migrations, installed accepted release unchanged. Future P06 (smaller minimum + horizontal scroll) separate.


## UI-076 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-08

- Пользователь вручную принял стабильное размещение счётчика после «Открыть предпросмотр списка»: «Всё работает. Идём дальше».
- QA package: `InOneLine_UI_076_STABLE_POSITION_2_CANDIDATE_1.0.8_WINDOWS_QA.zip`, artifact `11564293733`, 46 769 147 bytes, SHA-256 `18ae42c5e2544c62dfbd646d22828150823623d88ed49bb35ee6d4600b50189b`; Drive file `1Ohsul5NaTtGP7J_TCKMytBuY-E8N22dA`.
- Clean promotion PR [#55](https://github.com/ALL-EX-E/InOneLine/pull/55), merge commit `5d8ee1e2d7fb7be57246ff332cf603dc970b54fc); original candidate PR #50 закрыт без merge. Candidate QA bytes не пересобирались и не заменялись после ручной проверки.
- Точные runtime blobs в `main`: `streaming_manager/db/games.py` `3d14e9df676dbefbad80e4942d8e8d267eb7f0dc`; `streaming_manager/views/games.py` `f6ca072489e30b99ac7f28859669910a0edc94ce`; `tools/gui_regression_smoke.py` `669e32f4961b865550aafa9f35fbf71dbca92f5c`.
- Pre-merge Windows regression `37814527293` and wording gates `37814527185` / `37814518804` — **SUCCESS**. Exact post-merge Windows regression `37814970241` and wording gate `37814970284` — **SUCCESS**.
- UI-076 **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**. App/release version `1.0.8`, SQLite schema `19`, migrations `15`, official release and rollback remain unchanged.
- Следующий пункт утверждённой очереди — **P05: Public file export + removal Настройки → Экспорт**. Сначала fresh scope review exact CURRENT; runtime changes ждут отдельного явного пользовательского одобрения.


## P05 — свежий review exact CURRENT завершён; ожидает batch approval — 2026-10-08

- Exact CURRENT: `main` at `eb123eb99d9913db2d6ee2694471dc99f8b9d569`; app 1.0.8, SQLite schema 19, 15 migrations. Runtime/UI P05 не менялись.
- P05 объединяет ранее одобренные решения UI-088/UI-089/UI-090: перенести единственные файловые кнопки CSV/JSON/Excel на `Публичный список` в отдельный блок `Экспорт списка`; объяснить, что это одноразовый снимок, в отличие от продолжающегося XLSX-зеркала; удалить совместимый pipe-export UI и вкладку `Настройки → Экспорт`.
- Уже существуют `PublicTab.export_csv/export_json/export_xlsx` и общий backend `streaming_manager.exporters`; они используют полный `db.public_games()` dataset (без archived и `auction_only=1`, в каноническом порядке) и не добавляют `СТАРТ/ТЕКУЩАЯ`. Эти семантики и отдельный auto-update workflow `Публичная таблица` сохраняются. `/api/public` остаётся без нового UI-входа.
- В `SettingsTab` сейчас пять внутренних вкладок, включая `Экспорт`; там же находятся три Public file actions и legacy `Экспорт CSV` / `Копировать список`. `tools/gui_regression_smoke.py` жёстко проверяет старые пять вкладок и пока не проверяет перемещённый блок: gate следует обновить, проверить единственные кнопки на Public, отсутствие legacy controls/Export tab, сохранность XLSX mirror и импорта старого headerless `Название|Баллы`.
- Review note: текущий Settings save helper автоматически нормализует расширение файла; существующий Public helper этого не делает. При переносе сохранить корректный суффикс CSV/JSON/XLSX, одновременно переиспользуя существующие `PublicTab.export_*` и exporters.
- `AuctionTab.legacy_export_page` в `streaming_manager/views/auction.py` создаётся, но не добавляется в `auction_tabs` (там остаются только `Лоты` и `Проведение`). Его callbacks используют legacy pipe helpers; после удаления Settings Export провести exact caller audit и удалять эту недоступную страницу/helper только если tests, imports и другие callers не требуют их. Импортёр в `streaming_manager/db/services.py::import_csv` сохраняет pipe import compatibility.
- **Статус: FRESH REVIEW COMPLETE / READY AFTER BATCH APPROVAL / NOT IMPLEMENTED.** Требуется отдельное прямое пользовательское одобрение начала P05; до него runtime не менять.

## P05 status — 2026-10-09

- Пользователь подтвердил: «Работает. Записывай и идём дальше». Initial manual PASS относится к Public CSV/JSON/Excel actions, обоим XLSX mirror flows, удалённому Settings Export UI и исчезновению пустого прямоугольника на `Аукцион`.
- Проверенный кандидат: `9eb8aae28a2d85709e4090dce4cb12badc4b6607`; QA ZIP `InOneLine_P05_AUCTION_HOST_FIX_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1TV2hvEz4-uVpk3ax07r9kCfnsmKQcz_y`, 46,762,701 bytes, SHA-256 `1d6df043f106d9656d4476d3cac77376d485cc4a87230a2c2ac076d48909060e`.
- Clean promotion PR #59 merged as `45bb317751e688054d201ee3d77d5bbe5199c82b`; original candidate PR #58 closed without merge. Promotion Regression Foundation `37883637947` and wording gate `37883637998` succeeded. No release/version/schema/migration changes.
- При сверке UI-088 обнаружено, что первый promotion изменил файловый заголовок `НАЗВАНИЕ ИГРЫ` на `НАЗВАНИЕ`; утверждённый формат CSV/XLSX и JSON `columns` требует сохранить старый заголовок. Follow-up PR #60 (`886eaa2d96dc1b9576f2e292e2a1af6e6ed2ccee`) восстанавливает его и проверяет все три экспорта. Windows regression `37883971211` и wording `37883971209` succeeded.
- Follow-up QA ZIP: `InOneLine_P05_HEADER_FIX_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1O6PmpJMW8Qqf3ST06YlwTkYZ-1zXfsy-`, 46,764,368 bytes; GitHub artifact SHA-256 `86d03f964c57de19c5fea0da2262d99cb9313709a06eab6c886009c52e57f7ad`.
- Follow-up manual retest: **PASS** for CSV, Excel and JSON headers; the user replied `PASS` on 2026-10-09 using the exact QA ZIP listed above.
- Clean promotion PR #62 reused both exact tested file blobs from candidate PR #60 and merged as `777ce8caed26ba05af97adebd0f6c56dd3c48886`. Promotion Regression Foundation `37886832208` and wording gate `37886832239`: **SUCCESS**.
- Candidate PR #60 and QA-only post-merge PR #63 were closed without merge. Exact post-merge Regression Foundation `37887212648` and wording gate `37887212487`: **SUCCESS**.
- **P05 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** App 1.0.8, schema 19, migrations 15, published release and rollback are unchanged.


## P06 — fresh review exact CURRENT complete — 2026-10-09

- Reviewed exact `main` `777ce8caed26ba05af97adebd0f6c56dd3c48886`; app 1.0.8 / schema 19 / migrations 15.
- P05 is closed with manual PASS, clean merge PR #62, and successful post-merge Regression Foundation `37887212648` plus wording gate `37887212487`. Candidate PR #60 and QA-only PR #63 are closed without merge.
- The next package is P06: responsive main-window sizing/scrolling, stable selected-tab restoration after the approved tab reorder, and inclusion/restoration of `data/ui_state.ini` in new full backups while preserving legacy archives and ordinary `.db` backups.
- User authorized continuation with `«Работает. Записывай и идём дальше»`; candidate implementation proceeds within the already accepted P06 scope. Manual QA and clean promotion remain pending.


## P06 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-09

- Пользователь подтвердил полный manual PASS: обычный и минимальный размеры окна; все вкладки и прокрутка только таблиц; перестройка основного списка и отступы кнопок; цветные иконки/подсказки; страницы «Лоты» и «Проведение»; строка «Изображение» в настройках «Аукциона»; сохранение выбранной вкладки после обновления/перезапуска; резервное копирование `.db`, новая полная `.iolbackup` с состоянием UI и legacy `.iolbackup` без `data/ui_state.ini`. Отдельно приняты шрифты/пипетки OBS и первый показ компактных кнопок «Музыки».
- Tested candidate `0901fb2d864190cb2954909302217be0457699cb`; QA archive `InOneLine_P06_RESPONSIVE_TAB_STATE_BACKUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1YfwqW1SF85QUaxZafI1bgwSozV6LLv-U`, 46,766,667 bytes, SHA-256 `166ffe31981a1f88510245bc64361c6dd5d50a41d129e8d6de55b9c68ad6a14c`.
- Clean promotion PR #66 reused the exact 15 candidate blobs from main `aae15c30ebd69b79d87bf3aeaf5a58a701e27884`; merged as `e9a8919357eeb4cb182e847ef115058e6c253f58`. Candidate PR #65 closed without merge.
- Pre-merge Regression Foundation `37936833848` and publication wording gate `37936833837`: **SUCCESS**. Exact post-merge Regression Foundation `37937370459` and wording gate `37937370714`: **SUCCESS**.
- **P06 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** App 1.0.8, schema 19, migrations 15, published release and rollback remain unchanged. Next roadmap package: **P07 — position policy + XLSX derived position**.


## P07 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-09

- User confirmed manual candidate PASS: «Работает. Идём дальше» after focused Shared XLSX and position-policy QA. Original functional, 2560×1440/compact layouts and both Auction presentation scenarios were accepted earlier.
- Exact accepted artifact: GitHub Windows QA `11627206204`, 46,789,798 bytes, SHA-256 `0556c9d5a1bd00cb11f9bd1190243f17570e7622a18875133a6841198e5c4de9`; same ZIP at [Drive](https://drive.google.com/file/d/1CMX8uX5BNsMYxG8DKf5cAoQDlv573_12/view). Candidate runtime validated on Windows `37952905531` and documentation-only follow-up `37953728981`, both **SUCCESS**.
- Clean promotion PR [#70](https://github.com/ALL-EX-E/InOneLine/pull/70) copied **exactly 13 Git source/test blob SHAs** from the user-tested candidate without recompilation or code changes. Premerge Windows run `37954975909` and wording `37954975953`: **SUCCESS**. Merge commit `f3d78a5b78862e78807c09694a3655fab800ee52`. Independent postmerge Git blob verification: **13/13 identical** to candidate. Exact postmerge Windows `37955458936` and wording `37955458951`: **SUCCESS**. Superseded candidate PR #68 closed **without merge**; rejected PR #69 also remains closed without merge.
- P07 behavior delivered: main/public one calculated current position; Auction/Auction Lots overlay adapt one vs start/current columns and preserve elimination progress between rounds; Shared and Public XLSX calculated position projection, legacy Shared read compatibility and safe external edit preservation; wide/narrow header/filter polish. P05 one-off exports unchanged. No runtime version/schema/migration/RNG/auction business semantics change.
- **P07 CLOSED. P08 (BUG-005/UI-039) is next for fresh exact-CURRENT source review**, then one isolated candidate and manual QA. No P08 runtime change included in P07 clean promotion. APP_VERSION 1.0.8; SQLite schema 19 / 15 migrations; published installer/rollback remain unchanged.


## P08 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-09

- User's exact manual PASS: «Всё работает. Записывай и продолжаем делать дальше» for P08 candidate. Source QA ZIP `InOneLine_P08_MEDIA_DEDUP_AVAILABILITY_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Drive](https://drive.google.com/file/d/1Bs7VyDhOkazRVXiaqOdxFZ0YiE8R3UZg/view), artifact `11628691932`, 46,781,334 bytes, SHA-256 `05a7fd822c6f2f145e150948cd18088c9d92988e8d65ccc2a09e7479a6a1fd9d`.
- Clean promotion PR [#72](https://github.com/ALL-EX-E/InOneLine/pull/72) copied **exactly four tested Git source/test blob SHAs**, excluding draft documentation, from P08 candidate PR #71 without source edits or artifact rebuild. Premerge Windows `37958764542` = SUCCESS; publication wording `37958764547` = SUCCESS. Merged as `4f92b80d33b1220835896d662a12224d99f91af2`. Independent `main` comparison = **4/4 exact blobs**. Postmerge Windows `37959168279` = SUCCESS; wording `37959168295` = SUCCESS. Draft PR #71 closed without merge.
- Delivered BUG-005/UI-039: shared case-insensitive media identity in both main/Auction Lots background selectors, no duplicate managed/external file rows, external→managed promotion preserving media ID, coordinated available-only selectors, removal of obsolete manual repair action, safe missing-file selection reset. Existing D26 media sync extended to managed overlay backgrounds; missing external references remain registered. Video-copy race guarded. All media/user state outside this approved category unchanged.
- **P08 CLOSED.** APP_VERSION 1.0.8; SQLite schema 19 / 15 migrations, published release and rollback unchanged. Next: **P09 Stream/OBS structural cleanup**, starting as isolated UI-033 OBS help text, then UI-034–UI-043 according to existing ledger; each scoped substep needs its own Windows/manual gate.


## P09 / UI-033 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-09

- User manually tested and confirmed «Всё работает. Идём дальше». Accepted exact Windows QA ZIP: `InOneLine_P09_UI033_OBS_HELP_CANDIDATE_1.0.8_WINDOWS_QA.zip`; [Drive](https://drive.google.com/file/d/1m47jnKVKcV5SUTJlWhk5KjgvG7gDDL8L/view), artifact `11630113395`, 46,790,077 bytes, SHA-256 `9d6239a8915bd5e30e62e24eefa918a4773dad1dc9f41b45a321b4c20d4741bb`.
- Clean accepted two-blob promotion PR [#74](https://github.com/ALL-EX-E/InOneLine/pull/74), using exact Git blobs from tested code candidate PR #73. Premerge Windows `37965769207` + wording `37965769301`: **SUCCESS**; merge `b580b7067000df035944d68889405e5c0cdcb18a`; `main` blob verification **2/2 identical**; postmerge Windows `37966164330` + wording `37966164142`: **SUCCESS**. Draft PR #73 closed without merge.
- UI-033 improved Russian-language help and audio/OBS Browser Source advice only. No audio engine, overlay, settings, code navigation, app version or schema changes. **UI-033 CLOSED. P09 package remains IN PROGRESS**; next isolated substep UI-034 moves existing title typography controls immediately below Current Game while retaining the same three keys and shared save action.


## P09 / UI-034 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- User manual PASS for tested UI-034 package: «Работает. Записывай и идём дальше». Exact Windows QA ZIP `InOneLine_P09_UI034_TITLE_FONT_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Drive](https://drive.google.com/file/d/11AiWZcBq6xgJ4UNdfGawuWnja1noUblE/view), GitHub artifact `11633138736`, 46,795,736 bytes, SHA-256 `8e824d53e2f5b4d2734299fc360c65f5f3589cab155e6666d24f7dd6113d282d`.
- Clean exact two-source/test-blob promotion [PR #76](https://github.com/ALL-EX-E/InOneLine/pull/76) from draft candidate PR #75 without source code changes. Premerge Windows `38026996499` SUCCESS, wording `38026996429` SUCCESS. Merge `030e95c1c6255c598be177b01eb389ed46d27aa1`; 2/2 Git blob SHAs verified identical in main to manually tested candidate. Postmerge Windows `38027189063` SUCCESS; wording `38027189010` SUCCESS. Candidate PR #75 closed without merge.
- UI-034 delivered the *existing* `title` font controls directly below current game selection, preserving all six typography registries and `overlay_font_title_*` keys, color picker/pipette and existing StreamTab.save bulk persistence, no new handlers or runtime overlay/data changes.
- **P09/UI-034 CLOSED. P09 package IN PROGRESS.** Next isolated accepted task UI-035: place all informational block UI controls together, preserve live overlay layout rules and existing settings keys. APP_VERSION 1.0.8, schema 19 / 15 migrations unchanged.


## P09 / UI-035 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- User reported manual Windows acceptance: «Работает. Записывай и идём дальше.» Exact accepted QA ZIP `InOneLine_P09_UI035_INFO_PANEL_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Drive](https://drive.google.com/file/d/1t1ITj_MnODe5tGFZy9VcYd7NgFCeTEl3/view), GitHub artifact `11660757645` (46,781,067 bytes), SHA-256 `0c4314e71438dfe5ed014da70a87125e0ffe45190811dbe3d022498dd64958d6`.
- Clean exact-two-blob promotion via [PR #78](https://github.com/ALL-EX-E/InOneLine/pull/78), from PR #77 without source edits or candidate docs; premerge Windows `38028691707` SUCCESS and wording `38028691712` SUCCESS. Merge `601959832ff7cfce524cd5a469e32cb9e20418dc`; 2/2 source/test Git blobs verified identical in `main`; postmerge Windows `38028878671` SUCCESS and wording `38028878636` SUCCESS. Draft candidate PR #77 closed without merge.
- Delivered one thematic `Информационный блок` with existing text, show checkbox, position, glow frame color and original info typography grouped together. Disabled info preserves text and hides dependent controls; exact keys and `StreamTab.save()` unchanged; OBS browser geometry/audio unchanged. App 1.0.8, schema 19 / 15 migrations unchanged.
- **P09/UI-035 CLOSED / P09 IN PROGRESS.** Next approved isolated substep **UI-036**: local Save buttons after each currently independent main-overlay settings group, all calling the same existing `StreamTab.save()` and preserving single bulk save. Specialized timer/music/player saves remain untouched.


## P09 / UI-036 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- User manually accepted tested UI-036 QA: «Работает. Записывай и идём дальше». Exact ZIP `InOneLine_P09_UI036_LOCAL_SAVE_CANDIDATE_1.0.8_WINDOWS_QA.zip` in [Google Drive](https://drive.google.com/file/d/1g0Wsr8-6--Dm-bWMUCq6Ny0cA8iqnHSL/view), artifact `11661550875`, 46,790,281 bytes, SHA-256 `dc9949033e7556fbd0791bce8702cb7549e7f10dc275eec4aae28332447b4403`.
- Clean exact two-blob promotion [PR #80](https://github.com/ALL-EX-E/InOneLine/pull/80), approved candidate draft PR #79 closed unmerged. Premerge Windows `38030015962` SUCCESS; wording `38030015938` SUCCESS. Merge `131d9d61b03acf71d537de8ccd99c082e913b743`; both Git blobs verified identical in `main` to tested candidate. Postmerge Windows `38030194087` SUCCESS and wording `38030194086` SUCCESS.
- Six identical primary `Сохранить` actions after existing main-overlay settings groups (current game, info, format, background, appearance, typography) use existing single `StreamTab.save()` atomic/bulk settings writes. Old duplicate bottom Save removed. Specialized widget save handlers unchanged, no new settings, audio or geometry changes.
- **UI-036 CLOSED / P09 still IN PROGRESS.** Next isolated UI-037: place existing Format and game-frame glow/color+pipette within thematic `Игровое окно` group; reuse existing widgets, `stream_format` and `overlay_frame_game_color` keys, existing local save, preserve game-frame layout and transparency. No migration or app version change.


## P09 / UI-037 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- User manual Windows PASS on accepted candidate: «Работает. Записывай и идём дальше». Exact QA ZIP `InOneLine_P09_UI037_GAME_WINDOW_CANDIDATE_1.0.8_WINDOWS_QA.zip` on [Google Drive](https://drive.google.com/file/d/1kWhib640aahnxYxdEWgINS7b-_iot8FV/view); artifact `11661672998`, 46,785,146 bytes, SHA256 `17415f51867984b78cc8f093f97b645882f6d5458aaaa3f5bb9cd0ac54e430da`.
- Exact two-Git-blob promotion [PR #82](https://github.com/ALL-EX-E/InOneLine/pull/82), candidate PR #81 closed unmerged. Windows premerge `38031399579` SUCCESS, publication wording `38031399548` SUCCESS. Main merge `5e7fac15977480e846aba544b47064f99f4b1a8f`; 2/2 exact Git blobs verified. Windows postmerge `38031591029` SUCCESS, wording `38031591043` SUCCESS.
- Existing Game Window format and frame color/pipette now grouped under `Игровое окно`. Previous geometry, opacity, browser output and persistence unchanged, shared section Save unchanged, version 1.0.8/schema 19/migrations 15 unchanged. **UI-037 CLOSED**.

## P09 / UI-038 — CLOSED / ALREADY DELIVERED, VERIFIED / NO REDUNDANT PATCH — 2026-10-10

- Ledger requested preserving `Фон оверлея` elements and adding its local Save. Source inspection on the **manually accepted and merged UI-037 main** verifies original asset selector, add-background action including managed/external mode, source, status, stretch/contain/cover/center and help text all live together in one unchanged `Фон оверлея` block.
- `add_main_save("background")` was already delivered and manually accepted with UI-036, all six main-overlay save buttons sharing the existing `StreamTab.save()` atomic/bulk persistence. P08 completed shared media-dedup and availability semantics (BUG-005/UI-039), including removed `Восстановить ссылку` button and safe missing-file fallback; P08 was manually accepted and postmerge Windows passed.
- Thus **UI-038 fulfilled without new code, new installer or additional user QA**: it is already covered by existing user-accepted builds and regressions. **UI-039 and BUG-005 were CLOSED in P08**. Next genuinely unimplemented substep **UI-040** groups Webcam settings and retains the approved relative order Webcam → List → Info; not to change overlay runtime geometry/placement.

## P09 / UI-040 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- Пользователь подтвердил весь manual checklist: «Всё работает. Принимаю, записываем и идём дальше.» (2026-10-10 15:48:50 +07 / 08:48:50 UTC). Проверены общий порядок Веб-камера → Список → Информационный блок, положение и цвет рамки веб-камеры, пипетка, скрытие зависимых настроек, сохранение/перезапуск и OBS-предпросмотр.
- Exact accepted QA ZIP: `InOneLine_P09_UI040_WEBCAM_ORDER_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1fCc3LRnLtbiy8INBT1o0ysSs4V8KmOjc/view); GitHub artifact `11663095396`, 46,784,637 bytes, SHA-256 `ac221638e017f46e2afea4454c1dcfebdd19ee3cfd5e87466576d67ef4ec7433`. Tested source/test commit `7460dd9fb5d2de10cb3d6fbf833ac864681f714b`; accepted Windows run `38031932881` SUCCESS. Manual acceptance recorded on candidate as `5e1cb8c4bfb48e1b7b69741ebf6db8f859635475`.
- Clean promotion [PR #84](https://github.com/ALL-EX-E/InOneLine/pull/84) copied only the exact two accepted Git blobs, without source changes or replacing the user-tested installer: `streaming_manager/views/stream.py` = `5c557a91f80a6c75818ee2dcf34d6e911152561b`; `tools/gui_regression_smoke.py` = `dbd512c5830ce1745106808c6092f73994b244c5`. Promotion head `590022e5128ed81a7c5da484b73446fc1cf80bfd`; premerge Windows `38039319109` and wording `38039319011` / `38039316918` SUCCESS.
- Main merge `1d9a906aefc9984cd36439798c200a722c9581b6`: independent Git-tree readback confirms **2/2 exact accepted blobs**. Exact postmerge Windows [38039495072](https://github.com/ALL-EX-E/InOneLine/actions/runs/38039495072) and wording `38039495077`: **SUCCESS**. Original draft candidate PR #83 is superseded by #84 and closed without merge.
- Existing webcam checkbox, position selector, frame color/pipette and shared local Save now form one `Веб-камера` block. Conditional visibility and stored values preserved; sidebar settings order Webcam → List → Information accepted. Overlay runtime geometry, data, routes, settings keys and specialized saves unchanged.
- **UI-040 CLOSED; P09 IN PROGRESS.** Next approved isolated step **UI-041**: consolidate existing List show/position/frame, Top-1/2/3/list typography, standalone list URL/preview actions and shared local Save into one `Список` group. App 1.0.8 / SQLite schema 19 / 15 migrations; published release and rollback unchanged.

## P09 / UI-041 — WINDOWS CANDIDATE PASS / AWAITING MANUAL QA / NOT MERGED — 2026-10-10

- After user acceptance and exact postmerge closure of UI-040, implemented the already approved UI-041 scope in isolated `candidate/p09-ui041-list-group` from canonical `main` `241aa29acd887e24fdff6149740238b20efcf644`. Draft [PR #85](https://github.com/ALL-EX-E/InOneLine/pull/85); code/test head `eedb5c60b467515a7e542df6ad6b59fdc3f25b88`. Only two source/test files changed: `streaming_manager/views/stream.py` blob `e3ef5d3b81d573fd48021af4702edaf9813e54aa`; `tools/gui_regression_smoke.py` blob `a2b17c0fe8dca378250b97448b54108623b8d3c6`. Local vs GitHub hashes identical.
- Existing List show/position/frame color+pipette, four typography rows, standalone copy/preview actions and one shared bulk Save are grouped together under `Список`. Checkbox `Показывать на оверлее` and labelled `Положение списка`; obsolete generic typography block/save removed. Current six main-overlay thematic Save buttons retain the original bulk handler. Webcam → List → Information order preserved. Embedded-list disable hides position/frame/typography without discarding values or disabling separate `/list-overlay` actions; handlers, keys and browser routes reused.
- Real Qt/SQLite TDD: new helper failed on exact base (old switch label), then PASS on candidate. All distinct list font sizes/colors, frame/side/show values persist through shared Save and refresh; standalone clipboard/preview callbacks work while embedded list is disabled. Existing P09 regression checks PASS locally. Native main-window visual probes at widths 520/1100/2560 confirm accessible moved actions and adaptive typography rows. Compileall/diff check PASS; AST scope audit: only constructor and existing conditional-visibility helper changed, all 55 other StreamTab methods unchanged.
- Independent read-only Superpowers code review: no Critical/Important/actionable Minor findings; independent fresh-DB helper PASS and exact-base expected failure confirmed. Linux offscreen full suite hits the same unrelated P06 compact-tab font-fitting baseline failure on accepted UI-040 and candidate; this does not replace the canonical Windows gate.
- Full Windows [Regression Foundation 38040034301](https://github.com/ALL-EX-E/InOneLine/actions/runs/38040034301) **SUCCESS**, exact head `eedb5c60b467515a7e542df6ad6b59fdc3f25b88`: native GUI including `P09_UI041_LIST_GROUP_SHARED_SETTINGS_AND_STANDALONE_ACTIONS=PASS`, DB/backup/legacy/media/source/integrity, frozen startup/browser sources, installer build and silent installed startup all PASS. Wording runs `38040034325` (PR) and `38040032265` (push) SUCCESS.
- Manual QA archive: `InOneLine_P09_UI041_LIST_GROUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1XrswFhp9s0bVE_NOhiwWcse2QUPD_dTR/view), folder `Обзор_UI_1.0.8`. GitHub artifact `11665466642`; **46,790,609 bytes**, SHA-256 **`7e1938624027ffbff97d7769b62759c1887cc780ee6f56879da84fddae3402c4`**. Downloaded bytes independently match GitHub size/digest; ZIP CRC PASS; exactly one `InOneLine_Setup_1.0.8.exe`. Drive readback confirms name, same size and expected QA folder. This exact ZIP is the manual-test package.
- **UI-041 AWAITING USER MANUAL QA / NOT MERGED.** Main runtime remains accepted UI-040; P09 IN PROGRESS. Next isolated step after UI-041 acceptance/clean promotion/postmerge PASS: **UI-042**, distribute actual OBS URLs/actions and server status into their appropriate sections. App 1.0.8 / schema 19 / 15 migrations, official release and rollback unchanged.

Полный ручной checklist UI-041 (весь список проверяется одной сборкой):
1. Закрыть программу, установить проверенный QA installer и открыть Стрим / OBS; пользовательские данные сохранены.
2. Порядок Веб-камера → Список → Информационный блок; в Список находятся переключатель, положение, рамка, Top-1/2/3/прокручиваемая часть, две list-only кнопки и одна Сохранить. Отдельного Шрифты оверлея больше нет.
3. Авто/Справа/Слева после Сохранить управляют встроенным списком главного оверлея; авто продолжает следовать за стороной веб-камеры.
4. Цвет рамки через диалог и пипетку сохраняется; рамка корректна в главном и отдельном списке.
5. Для Top-1, Top-2, Top-3 и Прокручиваемого списка проверить семейство, размер/шаговые кнопки, цвет/пипетку; после Сохранить изменения видны в обоих OBS-вариантах. Для прокручиваемой части нужен список минимум из четырёх игр.
6. Выключить Показывать на оверлее и сохранить: положение/рамка/шрифты скрываются, встроенный список исчезает; две кнопки отдельного списка продолжают работать, копируется /list-overlay и открывается отдельный список.
7. Снова включить переключатель: выбранные положение, рамка и все шрифты возвращаются. После сохранения и перезапуска значения и состояние переключателя сохраняются.
8. Обычный, минимальный и широкий размеры: все controls и обе list-only кнопки доступны через существующую прокрутку; порядок и соседние блоки не нарушены.


## P09 / UI-041 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- Пользователь принял весь UI-041 checklist: «Всё работает. Принимаю, записываем и идём дальше.» (2026-10-10 16:16:13 +07 / 09:16:13 UTC). Проверены порядок Веб-камера → Список → Информационный блок, положение и рамка списка, четыре группы шрифтов, независимые copy/preview действия при выключенном встроенном списке, сохранение/перезапуск и доступность при изменении размера окна.
- Exact accepted Windows QA ZIP: `InOneLine_P09_UI041_LIST_GROUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1XrswFhp9s0bVE_NOhiwWcse2QUPD_dTR/view); artifact `11665466642`, 46,790,609 bytes, SHA-256 `7e1938624027ffbff97d7769b62759c1887cc780ee6f56879da84fddae3402c4`. Tested code/test head `eedb5c60b467515a7e542df6ad6b59fdc3f25b88`, Windows `38040034301` SUCCESS; candidate acceptance recorded as `2cedf8fabd752495cb7035aa33537f37de214a48`.
- Clean promotion [PR #86](https://github.com/ALL-EX-E/InOneLine/pull/86), head `646fe570db95087b12c703b8a99e173958a87edd`, copied only the exact two accepted blobs: `streaming_manager/views/stream.py` = `e3ef5d3b81d573fd48021af4702edaf9813e54aa`; `tools/gui_regression_smoke.py` = `a2b17c0fe8dca378250b97448b54108623b8d3c6`. Premerge Windows `38040932080` and wording `38040932034` / `38040930233`: SUCCESS.
- Main merge `6703b123a45be432f30cdb52c7c05c632cfdc47d`: independent recursive Git-tree readback confirms **2/2 identical accepted blobs**. Exact postmerge Windows [38041134372](https://github.com/ALL-EX-E/InOneLine/actions/runs/38041134372) and wording `38041134425`: **SUCCESS**. Original draft PR #85 closed without merge; user-tested installer remains the acceptance reference.
- **UI-041 CLOSED; P09 IN PROGRESS.** Next approved isolated step **UI-042**: move server status to the top and actual OBS URLs plus existing copy/preview actions before the settings of their corresponding sections; preserve existing saves. Wheel access reuses Auction callbacks; its future UI-078 show-mode/settings scope remains queued. Rules editor relocation remains UI-048/UI-060. App 1.0.8 / schema 19 / 15 migrations unchanged.


## P09 / UI-042 — WINDOWS CANDIDATE PASS / AWAITING MANUAL QA / NOT MERGED — 2026-10-10

- After exact accepted UI-041 closure, implemented the already approved UI-042 in isolated `candidate/p09-ui042-obs-access-layout` from canonical main `20539e7afbbf5a2638e2ac7345bd4d7414282d2f`. Draft [PR #87](https://github.com/ALL-EX-E/InOneLine/pull/87), exact source/test head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`.
- One server status at the top; seven actual local URL labels plus copy/preview actions before their corresponding settings. Specialized Saves remain after the original settings forms; all six shared main-overlay Saves unchanged. List URL/actions remain visible with the embedded list disabled. Wheel access uses existing Auction callbacks through MainWindow wiring; both entry points share one URL/preview implementation.
- Only three source/test files: `streaming_manager/views/stream.py` = `035347ddce9fffb332a4150057a7c79924f64170`; `streaming_manager/views/main_window.py` = `1e045d66be0b30c4b74d9a091cb043f5e605e684`; `tools/gui_regression_smoke.py` = `14ee930ee783d607f2aff825c57295453d5dcd3e`. Independent Git tree readback confirms 3/3 local and GitHub blobs identical. AST audit: StreamTab constructor/status-label refresh and MainWindow constructor only; all other 55 StreamTab / 30 MainWindow methods unchanged.
- Real Qt/SQLite TDD: new helper fails on accepted UI-041 base (status below main settings), then passes seven actual copy/preview routes, changed server URL/error state, four specialized Save/refresh checks and previous UI-041 persistence/disabled-list behavior. All P09 helpers PASS; visual/geometry checks at 520/1100/2560 and repeated narrow resize show selectable readable URLs, full action captions and no horizontal overflow. Compile/diff checks and pinned dependency consistency PASS.
- Full local Linux/offscreen suite reaches the previously characterized P06 compact-tab font-metrics failure on accepted baseline; native Windows is the canonical full gate.
- Scope sequencing: UI-042 adds wheel heading/URL/access only; future UI-078 full wheel presentation/show-mode/settings/save remains queued. Existing Rules controls/save are preserved in their current location until UI-048/UI-060 editor relocation; no duplicate editor/settings were added. Remaining Local API health/JSON controls stay until next UI-043. Routes, settings keys, backend, audio and browser rendering unchanged. App 1.0.8 / schema 19 / 15 migrations; official release and rollback unchanged.
- Review follow-up: explicit keyboard order makes the moved copy/preview pairs precede their section settings; real Tab traversal is tested, including OBS Help → main Copy → preview → Current Game. QA helper restores the complete pre-test settings snapshot and deletes initially absent fixture rows, preventing repeated runs from inheriting test values. Keyboard test reproduced the old order before the correction, then PASS.

- Independent read-only Superpowers review on exact final head: no remaining Critical/Important/Minor findings. Reviewer independently passed repeated fresh-DB settings/page/focus restoration, working endpoints, keyboard traversal, existing UI-041 behavior and width geometry; all initial minor findings corrected.
- Full native Windows [Regression Foundation 38045525292](https://github.com/ALL-EX-E/InOneLine/actions/runs/38045525292) **SUCCESS**, exact head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`: compile, DB/backup/legacy/media/source/integrity, native full GUI with `P09_UI042_SECTION_URL_ACTIONS_STATUS_AND_EXISTING_SAVES=PASS` plus prior P09 checks, frozen startup/browser-source, installer build, silent installed startup and clean filesystem all PASS. Wording PR `38045525324` and push `38045522126`: SUCCESS. This final run supersedes earlier candidate validation.
- Manual QA archive: `InOneLine_P09_UI042_OBS_ACCESS_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1jVnnC99nP9Z7s9SUK1ZSQlrjU4EsuNZc/view), folder `Обзор_UI_1.0.8`. GitHub artifact `11666982770`; **46,790,489 bytes**, SHA-256 **`2995e3b138a58d0b93a5401c829af1cc409b081f0e1cbb60cd41ba931e0eef89`**. Downloaded bytes independently match GitHub size/digest; ZIP CRC PASS; exactly one `InOneLine_Setup_1.0.8.exe`. Drive readback confirms name, identical byte size and expected QA folder. This exact archive is the manual-test package.
- **UI-042 AWAITING USER MANUAL QA / NOT MERGED.** Main runtime remains accepted UI-041; P09 IN PROGRESS. Next after UI-042 manual acceptance, clean exact-blob promotion and postmerge PASS: **UI-043**, remove the remaining Local API health/JSON controls from the ordinary Stream/OBS UI while retaining endpoints.

Полный ручной checklist UI-042 (весь список проверяется одной сборкой):
1. Закрыть программу, установить QA installer и открыть Стрим / OBS; данные и сохранённые настройки сохраняются.
2. Состояние: РАБОТАЕТ находится сверху перед Главный оверлей. Под заголовком — фактический /overlay и обе кнопки перед текущей игрой/шрифтами.
3. Во всех семи разделах проверить Копировать URL и Открыть предпросмотр: главный /overlay, Список /list-overlay, таймер /timer-overlay, музыкальный плеер /music-player-overlay, колесо /wheel-overlay, список лотов /auction-lots-overlay, правила /rules-overlay. Копируется полный адрес с фактическим портом; предпросмотр открывает соответствующий виджет. Для списка сохраняется существующий URL без ?preview=1; остальные существующие preview URL имеют ?preview=1.
4. В блоке колеса пока только заголовок, URL и две кнопки; его настройки — отдельный UI-078. Порядок в разделах с существующими настройками: заголовок → URL → copy/preview → настройки → существующая Сохранить. В Список адрес/кнопки перед переключателем; общий порядок Веб-камера → Список → Информационный блок сохранён.
5. Выключить Показывать на оверлее в Список и сохранить: настройки скрываются, а URL и обе кнопки отдельного списка остаются доступны; отдельный список открывается. Снова включить — прежние настройки возвращаются.
6. Изменить размер/цвет таймера, плеера и списка лотов, фон/прозрачность правил; нажать соответствующую Сохранить после настроек. Проверить соответствующие OBS-предпросмотры и сохранение после перезапуска. Локальные Сохранить главного оверлея работают как прежде.
7. Проверить кнопки колеса и в Стрим / OBS, и в Аукцион: копируется один /wheel-overlay с тем же портом, предпросмотр открывается по одному прежнему адресу. Запуск/проведение аукциона и колесо работают как прежде.
8. Проверить Tab: Копировать URL → Открыть предпросмотр → настройки соответствующего раздела. Сузить окно до минимального размера, расширить и снова сузить: все адреса, кнопки и Сохранить доступны через прокрутку, длинные строки/кнопки не обрезаются и не перекрываются.
9. В нижнем Локальный API больше нет общего каталога overlay URL. Оставшиеся Проверить API, Открыть JSON OBS и две JSON-строки удаляются следующим UI-043. Настройки правил пока в прежнем месте; их перенос в редактор выполняется отдельно UI-048/UI-060.


## P09 / UI-042 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- Пользователь принял весь девятипунктный checklist UI-042: «Всё работает. Принимаю, записываем и идём дальше.» (2026-10-10 18:41:30 +07 / 11:41:30 UTC). Проверены сохранение данных при установке, верхний статус, семь OBS URL/actions, порядок разделов и Save, отдельный список при выключенном встроенном списке, специализированные сохранения/перезапуск, общие действия колеса, Tab и узкое/широкое окно.
- Exact accepted Windows QA ZIP: `InOneLine_P09_UI042_OBS_ACCESS_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1jVnnC99nP9Z7s9SUK1ZSQlrjU4EsuNZc/view); artifact `11666982770`, 46,790,489 bytes, SHA-256 `2995e3b138a58d0b93a5401c829af1cc409b081f0e1cbb60cd41ba931e0eef89`. Tested source/test head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`, Windows `38045525292` SUCCESS. Candidate acceptance recorded as `949593fd61044c653dc82d4beefc26c136362304`.
- Clean promotion [PR #88](https://github.com/ALL-EX-E/InOneLine/pull/88), head `0e5121a2a3e479955868967d598675202a938dbb`, copied only three exact accepted blobs: `streaming_manager/views/stream.py` = `035347ddce9fffb332a4150057a7c79924f64170`; `streaming_manager/views/main_window.py` = `1e045d66be0b30c4b74d9a091cb043f5e605e684`; `tools/gui_regression_smoke.py` = `14ee930ee783d607f2aff825c57295453d5dcd3e`. Fresh premerge Windows `38049491911` and wording `38049491923` / `38049489084`: SUCCESS.
- Main merge `d50a337c699aec84a175b8b82abad2bae2f4cee3`: independent recursive Git-tree readback confirms **3/3 identical accepted blobs**. Exact postmerge Windows [38049666677](https://github.com/ALL-EX-E/InOneLine/actions/runs/38049666677) and wording `38049666701`: **SUCCESS**. Original draft PR #87 superseded by #88 and closed without merge; the user-tested installer remains the acceptance reference.
- Seven actual OBS URL/copy/preview sections and top server status accepted; existing saves and routes retained. Wheel access shares Auction callbacks; full wheel settings/show-mode remain UI-078. Rules settings remain in the current location until UI-048/UI-060.
- **UI-042 CLOSED; P09 IN PROGRESS.** Next approved isolated step **UI-043**: remove the old lower Local API block, health/JSON buttons and JSON URL rows from ordinary Stream/OBS UI, retaining all diagnostic/data/public endpoints and normal shared background-availability refresh. After UI-043 acceptance/closure, next package P10 begins with GLOBAL-OBS-VISIBILITY-001. App 1.0.8 / schema 19 / 15 migrations unchanged.


## P09 / UI-043 — WINDOWS CANDIDATE PASS / AWAITING MANUAL QA / NOT MERGED — 2026-10-10

- After user acceptance and exact postmerge UI-042 closure, implemented the already approved UI-043 scope in isolated `candidate/p09-ui043-api-diagnostics-cleanup` from canonical main `66461bfae7f3db36127141c62ffbc732360deb53`. Draft [PR #89](https://github.com/ALL-EX-E/InOneLine/pull/89), exact code/test head `36a31040d3c8e0656265a5e4a4c865a11a74c87a`.
- Removed the obsolete lower `Локальный API` block, `Проверить API` / `Открыть JSON OBS` buttons and `OBS JSON` / `Публичный JSON` URL rows. Top server status, seven OBS URL/copy/preview sections, existing specialized/shared Saves and real Tab order preserved. Existing main-overlay callbacks now constructed directly in their accepted top section; dead `_open_obs_json` handler and diagnostic counter removed after caller audit.
- Exactly two source/test blobs, independently identical locally and on GitHub: `streaming_manager/views/stream.py` = `66ef1428bab8a547b05655d5b8b800d6bf7cd5dd`; `tools/gui_regression_smoke.py` = `0aa8b98217f21d079b56053000ebe45b9a93dcd7`. AST: constructor/refresh changed, obsolete JSON method deleted; 54 other StreamTab methods identical. API server, browser templates, MainWindow, database, settings keys, schema and media logic unchanged.
- Real Qt/SQLite TDD: new contract fails on exact accepted base (old Local API heading), then PASS. Real HTTP /health, /api/health, /api/data, /api/public retain contracts; both main/list Browser Sources still consume /api/data. UI-042 seven copy/preview pairs, native Tab, four specialized Saves and UI-041 List behavior PASS. P08 dedup/missing/restored media PASS with ordinary tab-return availability; full refresh retains existing missing saved-selection cleanup. Visual/geometry at 520/1100/2560/repeated520: 14 actions accessible, no horizontal overflow or leftover service-block gap. Compileall/diff checks and exact pinned dependencies PASS.
- Independent read-only Superpowers reviewer on exact head: no Critical/Important/Minor findings. Independently checked real endpoints, UI-043/UI-042/UI-041/P08, full fixture settings/page/focus/clipboard restoration, missing/restored media, unchanged unsaved text and persisted settings on ordinary tab return, HTTP no-store, width geometry, AST54 and compile/diff checks. Local Linux full GUI reaches the known accepted P06 compact-tab font-metrics baseline after all P09 checks PASS; the native Windows full gate is canonical.
- Full native Windows [Regression Foundation 38050184969](https://github.com/ALL-EX-E/InOneLine/actions/runs/38050184969) **SUCCESS**, exact head `36a31040d3c8e0656265a5e4a4c865a11a74c87a`: compile, DB/backup/legacy/media/source/integrity, full GUI including `P09_UI043_DIAGNOSTIC_UI_REMOVED_AND_LIVE_API_RETAINED=PASS`, `P09_UI043_BACKGROUND_AVAILABILITY_ON_TAB_RETURN=PASS`, prior P09/P08, frozen startup/browser source, installer build, silent installed startup and clean filesystem all PASS. Wording PR `38050184948` and push `38050183666`: SUCCESS.
- Manual QA archive: `InOneLine_P09_UI043_API_UI_CLEANUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1O8Y1d6Lc55vbdNlnhbdJBy7DC4me6QFa/view?usp=drivesdk), folder `Обзор_UI_1.0.8`. GitHub artifact `11668633936`; **46,798,871 bytes**, SHA-256 **`9e1fbada3371fe712775eac25f45e1eee32770d5da1aa159b1d7100f5a92dad6`**. Downloaded bytes independently match GitHub size/digest; ZIP CRC PASS; exactly one `InOneLine_Setup_1.0.8.exe`. Drive readback confirms name, identical size and expected QA folder. This exact ZIP is the user manual-test package.
- **UI-043 AWAITING USER MANUAL QA / NOT MERGED; P09 IN PROGRESS.** Main runtime remains accepted UI-042. After UI-043 acceptance, exact clean promotion and postmerge PASS close P09; next package **P10** starts with **GLOBAL-OBS-VISIBILITY-001**, then approved timer/music presentation. UI-044 is superseded by UI-090 and must not be implemented as written. App 1.0.8 / schema19 / 15 migrations; official release and rollback unchanged.

Полный ручной checklist UI-043 (весь список проверяется одной сборкой):
1. Закрыть In one line, распаковать QA ZIP и установить InOneLine_Setup_1.0.8.exe; открыть программу и проверить сохранение данных/настроек.
2. В Стрим / OBS сверху остаётся Состояние: РАБОТАЕТ. Нижнего Локальный API, кнопок Проверить API/Открыть JSON OBS и строк OBS JSON/Публичный JSON больше нет; после Информационного блока идут настройки таймера без пустого служебного блока.
3. Проверить Копировать URL и Открыть предпросмотр всех семи разделов: главный оверлей, отдельный список, таймер, плеер, колесо, список лотов, правила. Адреса имеют фактический порт; встроенный список можно выключить — доступ отдельного списка остаётся.
4. Проверить обычное сохранение главного оверлея и специализированные Сохранить таймера/плеера/списка лотов/правил; изменения видны в предпросмотрах и сохраняются после перезапуска.
5. Для медиа-фона главного оверлея или списка лотов проверить режим Использовать исходный файл: временно переместить выбранный файл, уйти на другую вкладку и вернуться в Стрим / OBS — недоступный файл не предлагается как доступный фон, предпросмотр продолжает работать. Вернуть файл на прежнее место, обновить F5 — фон снова доступен для выбора.
6. Сузить окно до минимального размера, расширить и снова сузить. URL, copy/preview и Сохранить доступны через прокрутку; Tab по-прежнему проходит Копировать URL → предпросмотр → настройки раздела. После перезапуска статус сервера и все OBS-входы работают.


## P09 / UI-043 — MANUALLY ACCEPTED / EXACT PROMOTION CLOSED / P09 CLOSED — 2026-10-10

- User accepted the full six-item Windows manual checklist: **«Всё работает. Принимаю, записываем и идём дальше.»** at **2026-10-10 19:13:02 Asia/Novosibirsk / 12:13:02 UTC**. Acceptance recorded on candidate branch in `f8969b9dcfbd646bfea1b386e24532a4b2579c72`; user-tested source/test head remains `36a31040d3c8e0656265a5e4a4c865a11a74c87a`.
- Accepted installer archive: `InOneLine_P09_UI043_API_UI_CLEANUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Drive](https://drive.google.com/file/d/1O8Y1d6Lc55vbdNlnhbdJBy7DC4me6QFa/view). **46,798,871 bytes**, SHA-256 `9e1fbada3371fe712775eac25f45e1eee32770d5da1aa159b1d7100f5a92dad6`. Install/data persistence, removed diagnostic UI/top server status, all seven OBS accesses, existing Saves/restart, missing/restored external backgrounds, narrow/wide/Tab checks all accepted.
- Clean [promotion PR #90](https://github.com/ALL-EX-E/InOneLine/pull/90), exact head `352219aa58afb02ee400509b4b9b2fa6e1e3f64f`, contains only the two accepted source/test files, excluding candidate ledger docs. Accepted blobs: `streaming_manager/views/stream.py` = `66ef1428bab8a547b05655d5b8b800d6bf7cd5dd`; `tools/gui_regression_smoke.py` = `0aa8b98217f21d079b56053000ebe45b9a93dcd7`.
- Fresh premerge Windows [38051210141](https://github.com/ALL-EX-E/InOneLine/actions/runs/38051210141) and wording `38051210131` / `38051208436`: **SUCCESS**. Main merge `48fdfebe43cc43b154519d9f8c91997a9cdd4260`: independent recursive Git-tree readback confirms **2/2 identical accepted blobs**.
- Exact postmerge Windows [38051402379](https://github.com/ALL-EX-E/InOneLine/actions/runs/38051402379) and wording `38051402350`: **SUCCESS**. Logs confirm UI-043 live API/background-tab-return, prior P09/P08, complete native GUI, compile/DB/media/backup/source, frozen browser startup, installer/silent startup and clean filesystem PASS. Original draft #89 superseded by #90 and closed without merge.
- **UI-043 CLOSED; P09 CLOSED.** UI-033–UI-043 accepted and closed, including UI-038 satisfied by UI-036/P08. Next already approved isolated step **P10 / GLOBAL-OBS-VISIBILITY-001**: common persisted show-mode and preview override for all seven existing standalone Browser Sources; retain Music's accepted event behavior, use the approved wheel-context predicate, and preserve local operator/business/audio state. Subsequent UI-045/UI-046/UI-049/UI-055 presentation/audio-help work follows separate candidate acceptance. UI-044 remains superseded by UI-090. App **1.0.8 / schema19 / 15 migrations**; official release/rollback unchanged.


## P10 / GLOBAL-OBS-VISIBILITY-001 — USER ACCEPTED / EXACT PROMOTION — 2026-10-10

- **Manual Windows acceptance 2026-10-10 13:57:26 UTC / 20:57:26 Asia/Novosibirsk:** user confirmed **«Работает. Записывай и идём дальше.»** for the revised candidate after screenshots and explicit requested adjustments; all manual checks accepted.
- **Exactly accepted and user-tested source/test head:** `02aeebdadac862581662f732387f1837e7924d53` on `candidate/p10-obs-show-mode`; accepted and packaged [Windows QA run 38056008059](https://github.com/ALL-EX-E/InOneLine/actions/runs/38056008059) SUCCESS and [wording 38056008057](https://github.com/ALL-EX-E/InOneLine/actions/runs/38056008057) SUCCESS. Uploaded artifact `11671656777`, ZIP **46,788,284 bytes**, SHA-256 `c2fa8ff8a43965919637ade3c84885295259d374ae27bf25b75affd413c7a6f8`; [accepted installer ZIP on Google Drive](https://drive.google.com/file/d/1yMQAammU_qDYzhh64ULZgAGxk3fbNh0N/view?usp=drivesdk).
- **Accepted behavior:** seven OBS URL destinations, six visible show-mode controls. Primary `/overlay` always visible, its Qt show selector removed but dormant policy/code retained for possible future reactivation. One List `Показ виджета` controls both `/list-overlay` and the list embedded into the primary canvas; old embedded checkbox removed, saved `overlay_list_enabled` retained only as a compatibility fallback and mirrored on Save. Other timer, Music, wheel, auction lots and Rules modes and their existing audio/event/auction behavior remain intact. Persistent saves, preview override, missing-media and responsive UI tests all accepted.
- **Promotion discipline:** branch `promotion/p10-obs-visibility-accepted-20261010` begins at the exact user-tested source/test commit. Bring over only the current canonical main documentation plus this closure record; preserve every accepted code/test blob byte-for-byte. The promotion PR requires fresh native Windows and publication-gate success before merge; run independent postmerge gates and verify the main file blobs. Product **1.0.8**, schema **19**, **15** migrations, official release/rollback remain unchanged.
- **Next approved isolated P10 item:** **UI-045** — common OBS styling of Timer widget and custom background through existing shared media library, including copy vs original file semantics and audio-context help. Then UI-046 (music widget UI), UI-049 (music OBS audio help) and UI-055 (auction OBS audio help). Keep each change as a separate candidate/manual acceptance and do not jump to P11.


## P10 / GLOBAL-OBS-VISIBILITY-001 — MANUALLY ACCEPTED / EXACT SOURCE PROMOTED — 2026-10-10

- Manual QA accepted by user **2026-10-10 13:57:26 UTC** («Работает. Записывай и идём дальше.»). Accepted QA ZIP: [InOneLine_P10_LINKED_LIST_WINDOWS_QA_1.0.8.zip on Drive](https://drive.google.com/file/d/1yMQAammU_qDYzhh64ULZgAGxk3fbNh0N/view?usp=drivesdk), **46,788,284 bytes**, SHA-256 `c2fa8ff8a43965919637ade3c84885295259d374ae27bf25b75affd413c7a6f8`.
- **Clean final [PR #93](https://github.com/ALL-EX-E/InOneLine/pull/93) MERGED** with squash commit [`2a047837663aed23f8745f298d60910a2ad6ece0`](https://github.com/ALL-EX-E/InOneLine/commit/2a047837663aed23f8745f298d60910a2ad6ece0). Fresh exact promotion-head native Windows [38058186340](https://github.com/ALL-EX-E/InOneLine/actions/runs/38058186340) **SUCCESS**; publication wording [38058186294](https://github.com/ALL-EX-E/InOneLine/actions/runs/38058186294) **SUCCESS**. Native test flow included GUI/Qt, SQLite/API, real seven Chromium OBS pages with live Save, frozen startup and installer checks.
- Independently re-fetched and compared all **19 of 19** accepted source/test/Windows workflow Git blobs on **`main`** versus exact user-tested commit `02aeebdadac862581662f732387f1837e7924d53`: **100% identical**, no unaccepted source edits. Only three canonical doc files were additionally changed at promotion. Old draft [#91](https://github.com/ALL-EX-E/InOneLine/pull/91) and conflicted preliminary promotion [#92](https://github.com/ALL-EX-E/InOneLine/pull/92) **CLOSED WITHOUT MERGE**.
- The standalone GLOBAL-OBS-VISIBILITY-001 step is **CLOSED / ACCEPTED**, not the entire P10 package. Main /overlay always visible with dormant show policy retained; one List mode governs both embedded and standalone surfaces with legacy mirror; five other widget modes preserved. Product **1.0.8**, DB schema **19**, migrations **15**, official release/rollback unchanged.
- The next approved isolated candidate is **P10/UI-045**, standard Timer OBS appearance plus custom image/GIF/video background via the existing shared media asset library (managed/external, dedup, missing-file recovery), label clarity and auction audio-output help note. UI-046/UI-049/UI-055 remain separate later candidates.
- Postmerge source SHA verification PASS. This **docs-only** closure PR triggers the wording gate but not Windows Regression Foundation (that workflow deliberately filters out docs-only diffs). The **exact accepted production code** passed the full native Windows gate on clean promotion PR #93 immediately before merge, and every production/test file was independently verified on `main` after merge; do not misreport docs-only CI as native Windows.


## WORKFLOW — ChatGPT FIRST / CODEX ONLY WHEN REQUIRED — 2026-10-11

User-approved permanent workflow rule (2026-10-11): **Use regular ChatGPT as the default for absolutely everything that can be done without Codex. Reserve Codex for work that genuinely requires its local desktop, repository, terminal, or GUI access.** This minimizes Codex usage limits and ensures development continues in regular ChatGPT if Codex is unavailable.

- **Default in regular ChatGPT:** task analysis, roadmap/idea and acceptance documentation, source inspection and targeted GitHub code commits/PRs, GitHub Actions Windows CI and log analysis, artifact validation and uploads to the Google Drive project folder, manual QA instructions and recording user acceptance, and clean promotion to `main` only after acceptance. Also perform available static/code and CI checks here first; do not invoke Codex merely because a task involves programming.
- **Invoke Codex only when strictly necessary:** inspection of local unuploaded files, Windows-only local reproduction, interacting with the actual installed InOneLine or OBS UI, local terminals/build/debuggers/performance tools, or problems that GitHub CI, connectors and user QA cannot resolve. Before each handoff, explain why regular ChatGPT is insufficient and provide the user a precise, limited Codex instruction. **Regular ChatGPT cannot automatically take control of or launch the user's local Codex session; the user opens/authorizes it explicitly.** Codex output should be reviewed and results recorded in GitHub before further decisions.
- **Local arrangement:** installed user application in `A:\InOneLine` (do not modify its data without explicit approval); separately cloned source repository in `A:\InOneLine-Dev`, with candidate branch `candidate/p10-ui045-timer-media-background` for pending UI-045. Never use installed binaries as a Git source checkout, and never assume ChatGPT cloud sessions can directly read the user's `A:` drive.
- **Safety and acceptance:** no uncontrolled pushes/merges/installs; preserve user-approved step-by-step QA. Build candidates in isolated branches; require Windows CI, deliver all user-downloadable installers/archives to Google Drive with uploaded-file verification; manually accept each change before promotion. Codex being available does not itself authorize actions on local files or user data.
- **Current development status:** GLOBAL-OBS-VISIBILITY-001 accepted/merged; next UI-045 Timer OBS media background is technically Windows-CI-passed in unmerged draft PR #95, with first manual UI/install check confirmed; image/GIF/video/OBS and missing-source behavior still require user acceptance. Do not mark UI-045 fully accepted yet.


## P10/UI-045 — USER ACCEPTED, EXACT CLEAN PROMOTION — 2026-10-11

- **User final manual QA:** 2026-10-11 11:31:13 UTC («все настройки сохраняются. Идём дальше.»). Previous independent checks: UI labels/mode/appearance; GIF playback; MP4 muted loop with timer/audio unaffected; fixed single-Save MP4 copy race; external original-file first Save; disappearing/restored external file while browser remains open; saved background/font modes/other widgets preserved after app restart. **UI-045 ACCEPTED**.
- Accepted candidate source/test head `8b5a524e0e32a927153a46c0c711c86956f7b82e`, draft [PR #95](https://github.com/ALL-EX-E/InOneLine/pull/95). User-tested [Google Drive QA ZIP](https://drive.google.com/file/d/1O0GgZtr8Kb3p7wpqimlbUrop21qG5am6/view?usp=drivesdk), 46,802,794 bytes, SHA256 `8543e858860521a5eed0fd484e5efc0841087020fa944af782894572c00e7893`. Native Windows [38124993767](https://github.com/ALL-EX-E/InOneLine/actions/runs/38124993767) **SUCCESS**, wording [38124993764](https://github.com/ALL-EX-E/InOneLine/actions/runs/38124993764) **SUCCESS**.
- Exact clean promotion branch `promotion/p10-ui045-accepted-clean-20261011` starts from current accepted `main`, preserving all later unrelated docs. Only **six user-tested source/test/workflow blobs**, plus these three canonical docs, may change. No version/schema/migration or music/timer business/audio logic changes. Require fresh premerge native Windows and wording gate success; compare all six accepted blobs before and after merge. Do not promote original draft with stale base.
- **Next isolated item: P10/UI-046** (music-player overlay OBS section layout, renamed labels, and shared visual grouping). Preserve existing music playback/spectrum/cover-color logic, no new controller. UI-049 and UI-055 follow separately. Codex only if GitHub/GitHub Actions cannot resolve task; all user-downloadable builds go to Google Drive with verification.


## P10/UI-046 — USER ACCEPTED, EXACT CLEAN PROMOTION — 2026-10-11

- Final manual acceptance: 2026-10-11 12:45:52 UTC («Всё работает») after three independent QA stages: (1) Music/OBS heading, copy/preview and settings/button layout with labels `Размер шрифта`, `Цвет шрифта`, `Цвет визуализатора`, font size persisted after app restart; (2) playback/title/reactive spectrum/separate manual spectrum color/automatic cover-based frame/background unchanged; (3) music widget Always, Hidden, Track Change, preview, duration, animation, style persistence and existing OBS source unaffected. **UI-046 ACCEPTED**.
- Accepted candidate [draft PR #97](https://github.com/ALL-EX-E/InOneLine/pull/97) exact HEAD `4fcb26d45acb39fdffd13e90e60bb626534284de`. [Google Drive verified QA ZIP](https://drive.google.com/file/d/1QkvHIzRuDNvED-rJvBSZsIaHpkmjslO-/view?usp=drivesdk), 46,781,501 bytes SHA256 `40a51ae7fcc4a099b86da2a1b2e8f226ecae57c2452d5c708fd5ef2de0c2d3d7`. Native Windows [38136840360](https://github.com/ALL-EX-E/InOneLine/actions/runs/38136840360) PASS, wording [38136840421](https://github.com/ALL-EX-E/InOneLine/actions/runs/38136840421) PASS.
- Exact clean promotion branch `promotion/p10-ui046-accepted-clean-20261011` from up-to-date `main`; only two exact accepted blobs `streaming_manager/views/stream.py` + `tools/gui_regression_smoke.py`, plus three canonical project documents; **no audio routing, API, database, schema, migrations, or OBS web runtime modifications**. Fresh native Windows + wording gate required before main merge. Verify both accepted blobs after merge. Close draft #97 without merging stale history.
- Next isolated accepted roadmap candidate **P10/UI-049**: short context-sensitive Music tab `Как выводится звук в OBS?` help button only when mode `Через OBS`; simple existing dialog style; route/audio unchanged; no permanent large explanatory text. Codex reserved for local-only work.

## P10/UI-049 — USER ACCEPTED; exact clean promotion — 2026-10-11

- Manual acceptance: 2026-10-11 14:46:25 UTC, user: «Теперь всё понятно. Продолжаем.» after installing the final revised help-copy candidate. Earlier manual checks confirmed correct context-sensitive button/modal visibility; two previous wording variants were rejected as unclear. This final wording is explicitly accepted.
- Candidate source/test exact HEAD: `b7f3f8c1ffd4f17a5a55059f0789fa7c34134c4a`; original unmerged draft [PR #99](https://github.com/ALL-EX-E/InOneLine/pull/99). Exactly two approved runtime/test files: `streaming_manager/views/music.py` and `tools/gui_regression_smoke.py`. Do not merge the full candidate branch/history; clean promotion copies the two exact blob SHAs from the tested commit.
- Tested ZIP: [InOneLine_P10_UI049_AUDIO_HELP_CLEAR_FLOW_1.0.8_WINDOWS_QA.zip](https://drive.google.com/file/d/1q-C7mBtgy-Rdt4fnarJ32r3T6RgFf7rZ/view?usp=drivesdk), SHA256 `440aa9526ccb3ddbfcdd98a58491c889d3f3e045a3bc5b0619ada6fe8b00a16d`. Native Windows [38147021385](https://github.com/ALL-EX-E/InOneLine/actions/runs/38147021385) SUCCESS and publication wording [38147021357](https://github.com/ALL-EX-E/InOneLine/actions/runs/38147021357) SUCCESS.
- The accepted help explains in order: InOneLine Music output via OBS Browser Source; where the OBS Browser Source's `Управление аудио через OBS` checkbox is; OFF routes to OBS Browser Page/Windows mixer; ON exposes separate OBS mixer source for recording/streaming; local audio requires `Мониторинг и вывод`. Show the help button only for OBS output. No changes to audio routing, controller, music playback, OBS web sources, database/version/schema/migrations.
- Clean exact-file promotion from accepted main is staged separately and requires fresh Windows/wording premerge checks and postmerge accepted-blob readback. The user-approved next isolated item after verified promotion is **P10/UI-055**, matching contextual OBS audio help on the Auction tab using existing dialog/policy; no new audio/backend.

## P10/UI-055 — FINAL USER ACCEPTANCE; exact source promotion — 2026-10-11

- User manual acceptance **2026-10-11 15:07:19 UTC**, «Принимаю. Идём дальше.» for the installed Auction/Wheel OBS-audio help candidate. Final **UI-055 ACCEPTED**. UI-049 remains independently accepted and already merged as [PR #100](https://github.com/ALL-EX-E/InOneLine/pull/100).
- Candidate [draft PR #101](https://github.com/ALL-EX-E/InOneLine/pull/101), tested exact HEAD `3138aeba94cfcc5d1fb1686cbcefc2a45d3988ae`. Verified QA ZIP [Google Drive](https://drive.google.com/file/d/1_Qy9m4ADeQcOuYJiSk4RvyZSEogi7XkL/view?usp=drivesdk), 46,800,086 bytes, SHA256 `bd23176acce32b7f9072c96531f81cac46643afc2679e413bb50f8d0fcdcc5ed`. Exact candidate native Windows [38149238542](https://github.com/ALL-EX-E/InOneLine/actions/runs/38149238542) SUCCESS; publication wording [38149238539](https://github.com/ALL-EX-E/InOneLine/actions/runs/38149238539) SUCCESS.
- Exact accepted blobs only: `streaming_manager/views/auction.py` = `928a25e6161f6a839b93b8668989df43e6dbbd2b`; `tools/gui_regression_smoke.py` = `7c824b46a187b925db8d4fa8d8c77fe7b5198c2f`. User-approved UI: contextual help visible only for Auction/Wheel Timer Browser Source; accepted ordered OBS-checkbox/mixer/monitoring explanation; original warning about disabling invisible Browser Sources preserved inside dialog; no permanent long hint. No modification to audio routing, timer, settings/db, version 1.0.8, schema 19 or 15 migrations.
- Promote those exact blobs on latest accepted main in a **clean new PR**, plus three canonical documentation files only; fresh native Windows + wording SUCCESS required before merge. Verify 2/2 source/test blobs on main afterward; close unmerged draft #101. Following roadmap package **P11 — composite Rules editor/overlay** (`UI-048`/`UI-060`); break into small independently QA-verified increments, preserve current Rules runtime while designing.

## P10 COMPLETE — UI-055 merged and verified; P11-A candidate — 2026-10-11

- Final user-accepted UI-055 [PR #102](https://github.com/ALL-EX-E/InOneLine/pull/102) **MERGED** into main as `7ae552135af67bd42922590c71b03910aa48742a`. On exact promotion head `6318405b213f9596a892e11328392c3f3f03dee8`, native Windows [38150150271](https://github.com/ALL-EX-E/InOneLine/actions/runs/38150150271) and wording [38150150233](https://github.com/ALL-EX-E/InOneLine/actions/runs/38150150233) **SUCCESS**. After merge, fetched source `streaming_manager/views/auction.py` and regression `tools/gui_regression_smoke.py`; **2/2 exact Git blob SHA** match user-installed Windows candidate. Original unmerged draft [#101](https://github.com/ALL-EX-E/InOneLine/pull/101) CLOSED WITHOUT MERGE.
- P10 package (GLOBAL-OBS-VISIBILITY-001, UI-045, UI-046, UI-049, UI-055) is **CLOSED, manually accepted, merged**. App remains **1.0.8 / schema 19 / 15 migrations**.
- Next P11, step **P11-A/UI-060 Rules text-format toolbar removal**, is in isolated [draft PR #103](https://github.com/ALL-EX-E/InOneLine/pull/103). Remove obsolete Undo/Redo/Highlight/highlight pipette only, preserve legacy highlight formatting in stored HTML; no template/back-end/schema changes. **NOT USER ACCEPTED; DO NOT MERGE** until Windows CI, user QA and clean promotion.

## P11-A/UI-060 — USER ACCEPTED; clean promotion — 2026-10-11

- User manual acceptance 2026-10-11 16:51:15 UTC: «Всё работает. Идём дальше.» after installing the FIX1 candidate. Earlier review 15:35:28 UTC accepted functional toolbar but requested compact color picker as in Stream/OBS. **P11-A accepted with FIX1 only**.
- Exact tested candidate SHA: 7bd153c7723f28493593f8c3eeb1e48ff1b923fc, [draft PR #103](https://github.com/ALL-EX-E/InOneLine/pull/103). Native Windows [38155498542](https://github.com/ALL-EX-E/InOneLine/actions/runs/38155498542) and wording [38155498539](https://github.com/ALL-EX-E/InOneLine/actions/runs/38155498539) SUCCESS. Windows artifact 11708412957, InOneLine_P11A_RULES_EYEDROPPER_FIX1_1.0.8_WINDOWS_QA.zip, 46,794,376 bytes, SHA256 ed6cb4b7de1cff8f187085e580de9997f23c39e62361da915ab2930841eb5e6a; ZIP integrity and exact enclosed installer verified.
- Accepted blobs: streaming_manager/views/rules_editor.py = 296eb93b0fee6b21216a2a9bad83b04c1d674641; tools/gui_regression_smoke.py = 90011b91411909fe2cff1e4e4c3543c07dbbfff0. Removed obsolete Undo/Redo/Highlight/highlight-pipette, preserved stored legacy highlight HTML, and reused shared make_screen_color_picker_button() for foreground picker; no changes to Rules storage, OBS routes, DB schema/version, playback or auction state.
- Clean promotion copies exactly two tested blobs atop current accepted main, updates only three canonical docs, and requires fresh Windows/wording CI plus exact 2/2 postmerge SHA verification. Close original draft PR #103 without merging. Next isolated P11-B: relocate existing rules URL/copy and OBS preview actions from Auction page into Rules editor with zero new routes or duplicated backend; composite settings remain later.

## P11-B/UI-060 — USER ACCEPTED; exact clean promotion — 2026-10-12

- User 2026-10-11 17:17:20 UTC confirmed functional Rules URL/copy/OBS preview after installing P11-B; screenshot flagged template-selection row collision at minimum size. Fixed in same candidate FIX1 by separating template combo from original Active badge and action buttons. Final explicit manual acceptance 2026-10-12 04:47:04 UTC: «Всё работает. Идём дальше.»
- Exact user-accepted FIX1 candidate head f009c575370ad1a4bc1ebf855f86676f1bd83a6f in [draft PR #106](https://github.com/ALL-EX-E/InOneLine/pull/106). Native Windows [38159132258](https://github.com/ALL-EX-E/InOneLine/actions/runs/38159132258) SUCCESS; wording [38159132287](https://github.com/ALL-EX-E/InOneLine/actions/runs/38159132287) SUCCESS. Tested QA ZIP [Drive](https://drive.google.com/file/d/1GjhljLeS0EzTIEppN63oXGV9Vl51BjpE/view?usp=drivesdk), 46,801,670 bytes, SHA256 68ad4cc84e0aa60bf35a1cd7478c9389aeec0752943af827d01c4c0f03e63980.
- Exactly THREE accepted blob SHAs: streaming_manager/views/auction.py = bfd24ca8f6105343b6a1f251840bb22929d67d03; streaming_manager/views/rules_editor.py = 2e82c4dd78e9c4b3e926524c934221877291c74f; tools/gui_regression_smoke.py = f650a2a0301349051f042f56fab1a0fde54cac1e. Removes duplicate Rules URL and OBS Preview buttons from Auction page and shows/selects/copies original OBS Rules URL inside editor, retains /rules-overlay?preview=1. Selector moved to separate row above existing template actions; geometric regression at 760x560, 1050x760, 760x560. Saved templates, old Show Rules action, audio/OBS route, schema 19, migrations 15, app 1.0.8 unchanged.
- Manual acceptance recorded. Promote exact three source/test blobs on current main with canonical docs through a new PR; require native Windows + wording SUCCESS for promotion HEAD and 3/3 postmerge Git blob re-read. Close original draft PR #106 without merging its history. Next P11-C: remove legacy Auction page Show Rules button from agreed redesign only after audit of its preview/dependencies; composite Rules editor work remains separate.

## P11-C — user accepted removal of old Rules text preview — 2026-10-12

- Manual acceptance at 2026-10-12 05:03:36 UTC: «Всё работает. Идём дальше.» Exact candidate head 143f3429e4f5234fa2ee9dd2f1ec72f90fae8f5f in [draft PR #108](https://github.com/ALL-EX-E/InOneLine/pull/108). Native Windows [38205668098](https://github.com/ALL-EX-E/InOneLine/actions/runs/38205668098) SUCCESS; wording [38205668019](https://github.com/ALL-EX-E/InOneLine/actions/runs/38205668019) SUCCESS. Final [Drive QA ZIP](https://drive.google.com/file/d/14BkDWt_lQ3IoAwazTmcQQDZTNZ_t-WoW/view?usp=drivesdk), 46,804,540 bytes, SHA256 51db4676f11f56760c969c12464c964acef74a6880b7afdaf2bd2d70c9ae465c.
- Removed duplicated Auction page Show Rules button and obsolete preview callback and read-only popup; retained the full editable WYSIWYG Rules text and true browser rules overlay /rules-overlay?preview=1. No changes to audio, DB, schema 19, 15 migrations, app version 1.0.8 or Rules template/session state.
- Three exact accepted blobs: streaming_manager/views/auction.py = 908404b5ae24e5116a1b80e7f1cf4f65cfccac40; streaming_manager/views/rules_editor.py = 952b12ad713cced84d5809a71f4e4887d41abd92; tools/gui_regression_smoke.py = d615f6e5b5f231223f21c7cd2d75d61e2c0fce30.
- Clean exact-file promotion of these three blobs plus three canonical documents to latest accepted main requires fresh Windows CI, wording and 3/3 blob postmerge verification. Close candidate draft #108 unmerged. Next P11-D: audit the existing composite Rules template and OBS appearance/snapshot renderer before a small independently verifiable next UI step.

## P11-C MERGED; P11-D candidate in review — 2026-10-12

- User-accepted [P11-C clean promotion PR #109](https://github.com/ALL-EX-E/InOneLine/pull/109) was merged into main as c352ad1b27612354bd7b05f3dcf3aaaebade5c4f. Native Windows promotion [38206473290](https://github.com/ALL-EX-E/InOneLine/actions/runs/38206473290) and wording [38206473275](https://github.com/ALL-EX-E/InOneLine/actions/runs/38206473275) SUCCESS. Verified postmerge exact Git blobs for auction.py, rules_editor.py, gui_regression_smoke.py, 3/3 match the user-tested candidate. Original draft [#108](https://github.com/ALL-EX-E/InOneLine/pull/108) CLOSED WITHOUT MERGE. P11-C is DONE.
- Next separately gated [draft PR #110](https://github.com/ALL-EX-E/InOneLine/pull/110), P11-D: visually mark active Rules template green, remove redundant star and status badge, hide Make Active when active and Delete when the last template, reuse original state callbacks. No template persistence, creation/activation, WYSIWYG, OBS runtime, DB schema or app version changes. P11-D is NOT USER ACCEPTED and must not be merged before Windows and manual QA.

## P11-D/UI-060 — manual PASS; clean promotion gate — 2026-10-12

- User 2026-10-12 05:23:24 UTC: «Всё работает. Идём дальше.» This explicitly accepts the installed P11-D active-template visual candidate. Exact user-tested HEAD 14c12b8c6f5367f00f3e3cf2e6c35204617a1be7 in [draft PR #110](https://github.com/ALL-EX-E/InOneLine/pull/110). Windows native [38206882328](https://github.com/ALL-EX-E/InOneLine/actions/runs/38206882328) SUCCESS and wording [38206882336](https://github.com/ALL-EX-E/InOneLine/actions/runs/38206882336) SUCCESS. Verified installer [Drive ZIP](https://drive.google.com/file/d/1Z7sri4UYTC8uyYaRQkI5dLoIx528GIV9/view?usp=drivesdk), 46,801,211 bytes, SHA256 0708044632d523eae51bf692ea9f7bcb1307b9306bff4c1874ca898149b6be74.
- Exact accepted Git blobs: streaming_manager/views/rules_editor.py = 954138d6bcb489f280f499b5d22dc62ac636b655; tools/gui_regression_smoke.py = 2b94c49933b0a20c4fe0f2036f6e8315519de8ab. Active Rules template is marked green in selector and selected field; star and badge removed; existing Make Active hidden when active, Delete hidden when last. No changes to create/save/activate mechanism, session rules snapshot, OBS rendering, storage, app 1.0.8, schema 19 or migrations 15.
- Clean promote exactly these two blobs plus three canonical docs onto accepted main, fresh native Windows and wording gates then 2/2 postmerge blob check; close the superseded draft #110 WITHOUT MERGE. Next isolated P11-E: new template should be created inactive; verify DB creation API and live auction behavior before modifying the sole call site.

## P11-D CLOSED; P11-E Windows QA available — 2026-10-12

- User-accepted P11-D was clean-promoted via [PR #112](https://github.com/ALL-EX-E/InOneLine/pull/112) to main SHA 792845b98597de1dda977eee2dd1788b7a3dc370. Fresh native Windows promotion 38207833716 SUCCESS, wording 38207833690 SUCCESS; 2/2 accepted runtime/test Git blobs exactly match installed candidate. Superseded draft PR #110 CLOSED WITHOUT MERGE. P11-D DONE.
- Next P11-E candidate [draft PR #113](https://github.com/ALL-EX-E/InOneLine/pull/113), exact HEAD ccff76a175b838fda4b30b03637d8269942dd2ea, full native Windows [38208259058](https://github.com/ALL-EX-E/InOneLine/actions/runs/38208259058) SUCCESS and wording [38208259062](https://github.com/ALL-EX-E/InOneLine/actions/runs/38208259062) SUCCESS. [Verified Drive QA ZIP](https://drive.google.com/file/d/1TwN91I4824oHoAXrMqrrFbLQsbmVwEak/view?usp=drivesdk) 46,789,610 bytes, SHA256 23a00bdfe9a2995efac65def103bc52d194659ee0c543fd88f53cf16edbf7339.
- P11-E only changes the existing Rules create-template handler argument to make_active=False. Separate temporary DB GUI regression verifies that inactive draft is editable/savable, active template and content unchanged, and explicit activation still works. NO schema, audio, OBS, runtime session or Save/Close semantics change. P11-E **AWAITING USER MANUAL QA; DO NOT MERGE**.

## P11-E — user accepted; exact promotion gate — 2026-10-12

- User manual PASS at 2026-10-12 06:07:44 UTC: «Всё работает. Идём дальше.» Accepted candidate [draft PR #113](https://github.com/ALL-EX-E/InOneLine/pull/113), HEAD ccff76a175b838fda4b30b03637d8269942dd2ea; native Windows run 38208259058 and publication wording 38208259062 SUCCESS. [User-tested ZIP](https://drive.google.com/file/d/1TwN91I4824oHoAXrMqrrFbLQsbmVwEak/view?usp=drivesdk), 46,789,610 bytes, SHA256 23a00bdfe9a2995efac65def103bc52d194659ee0c543fd88f53cf16edbf7339.
- Exactly accepted source/test Git blobs: streaming_manager/views/rules_editor.py 8fa790e0db60138640dc78f277f5c4c128853cb3; tools/gui_regression_smoke.py ca22851b165810dce24c64d4f8859cd75600cc15. The Rules editor calls existing DB create method with make_active=False, maintaining active Rules and session snapshots, while new template can be edited/saved and explicitly activated. No DB schema, OBS/audio, Save/Close or version change.
- Clean promotion includes only these two exact blobs and three canonical docs, requiring fresh native Windows and wording CI, plus exact 2/2 Git blob readback on main; close old draft #113 without merging. Next P11-F is Save rules without closing the editor, leveraging existing _save_current without duplicating storage.

## P11-E verified closure and P11-F QA — 2026-10-12

- Accepted P11-E was promoted via [PR #115](https://github.com/ALL-EX-E/InOneLine/pull/115), merged as `a9de5694269cb34ce7537f4c52bed3e14567ec05`. Fresh Windows [38211201717](https://github.com/ALL-EX-E/InOneLine/actions/runs/38211201717) and wording 38211201786 SUCCESS; exact accepted source/test blob identities 2/2 VERIFIED on main. Draft PR #113 CLOSED UNMERGED. P11-E DONE.
- Next isolated P11-F [draft PR #116](https://github.com/ALL-EX-E/InOneLine/pull/116) saves Rules without closing; full Windows [38211698235](https://github.com/ALL-EX-E/InOneLine/actions/runs/38211698235), wording 38211698257 SUCCESS. [QA ZIP](https://drive.google.com/file/d/1cI94I7yt7tHBZMZwtE2AGrrYq9etIxMT/view?usp=drivesdk) validated, checksum 7658eb2306ad35c277f3dcbe8122ac0bdff64b57fd2cfa9d9235904f10b3bd60. **Manual user acceptance pending; no merge**.

## P11-F — USER ACCEPTED; exact clean promotion gate — 2026-10-12

- User manually confirmed installed P11-F: «Всё работает. Идём дальше.» at 2026-10-12 06:50:32 UTC. Source candidate [draft PR #116](https://github.com/ALL-EX-E/InOneLine/pull/116), exact tested HEAD 753862c25c648ba22602e574a355d4560ba6ce8c; Windows native 38211698235 SUCCESS, wording 38211698257 SUCCESS. [Verified Drive ZIP](https://drive.google.com/file/d/1cI94I7yt7tHBZMZwtE2AGrrYq9etIxMT/view), 46,786,164 bytes, SHA256 7658eb2306ad35c277f3dcbe8122ac0bdff64b57fd2cfa9d9235904f10b3bd60.
- Exact tested blobs: `streaming_manager/views/rules_editor.py` = `7695fd7a4be491a3fe38588fad03cba4e1b2f4cd`; `tools/gui_regression_smoke.py` = `ab2348791ce938c713c7bd4bb535cd7a27ebc2fb`. Save persists current Rules text without closing existing editor, keeps dirty/Close confirmation, inactive draft state, OBS and auction/session logic. No new DB/schema, version or audio changes.
- **USER ACCEPTED**; clean promotion of exact 2 blobs plus these three canonical docs onto latest main with fresh native Windows Regression Foundation and wording gates is pending. After both PASS, merge with head SHA lease, independently verify exact 2/2 blobs on main and close superseded draft #116 WITHOUT MERGE. Next P11 substep must be isolated and approved independently; composite Rules OBS appearance/template consolidation remains outstanding.

## P11-F VERIFIED CLOSED; next P11-G save-as choice — 2026-10-12

- User manual PASS 06:50:32 UTC, exact clean [PR #118](https://github.com/ALL-EX-E/InOneLine/pull/118) merged via squash main `e8a2820d37b3e02ac2ff6e6d66d24e4a1e1604d6`. Native Windows 38214717462 SUCCESS and wording 38214717445 SUCCESS on promotion head 75915acc40166e96615f221677b957d384dd35bb. Postmerge exact blob verification **2/2**: `rules_editor.py=7695fd7a4be491a3fe38588fad03cba4e1b2f4cd`; `gui_regression_smoke.py=ab2348791ce938c713c7bd4bb535cd7a27ebc2fb`. Original draft #116 CLOSED WITHOUT MERGE. P11-F COMPLETE.
- Next isolated approved UI-060 unit **P11-G**: implement the existing documented Save choice for editing a previously saved Rules template: `Заменить текущий` / `Сохранить как новый` / `Отмена`. Reuse `Database.save_rule_template` and `Database.create_rule_template(..., content_html=..., make_active=False)`; no schema/OBS/session mutation in save-as-new, preserve active and original template. Do not combine with composite OBS styling or other template policy changes. Candidate separate, full Windows regression then user manual QA.

## P11-G native Windows candidate ready; awaiting manual QA — 2026-10-12

- Based on fully accepted P11-F main `dceded6d6c9e07d4851eb43ae41ef13d59e14e70`, separate [draft PR #120](https://github.com/ALL-EX-E/InOneLine/pull/120), exact candidate HEAD `2a727fe580b2712c47e388d16bd9f3cfd4914879`, limited to `streaming_manager/views/rules_editor.py` and `tools/gui_regression_smoke.py`.
- P11-G isolated approved existing-template Save choice `Заменить текущий / Сохранить как новый / Отмена`; first save of freshly created inactive template stays direct, independent copy uses existing `Database.create_rule_template(name, content_html=html, make_active=False)` API, original and active/on-air untouched. Existing dirty and Close prompt retained; no schema/migrations/OBS/routing changes.
- [Native Windows Regression Foundation 38215560993](https://github.com/ALL-EX-E/InOneLine/actions/runs/38215560993) SUCCESS; [wording 38215560921](https://github.com/ALL-EX-E/InOneLine/actions/runs/38215560921) SUCCESS. Exact [verified QA ZIP on Google Drive](https://drive.google.com/file/d/14_7DsQkoVNh-i1T0fOOgx2rRM4-jZsdD/view?usp=drivesdk), 46,783,580 bytes, SHA256 `1de9cb6053756f03d5dc028d20200c59787d51bbc41871f3d41ad7c2731b385f`, full ZIP CRC PASS, one `InOneLine_Setup_1.0.8.exe`; parent QA folder readback confirmed.
- **AWAITING USER MANUAL QA — NOT ACCEPTED / DO NOT MERGE.** Manual scenarios: Replace keeps editor open and persists, Save-as makes inactive new copy while original/active unchanged, Cancel retains dirty, duplicate-name error safe, freshly created template Save direct, existing Close dirty guard unchanged. Only after explicit PASS clean-promote tested source/test blobs and verify CI/postmerge identity.

## P11-G — USER MANUAL PASS, exact clean promotion gate — 2026-10-12

- User explicitly accepted P11-G Windows QA at 2026-10-12 07:15:09 UTC: «Всё работает. Идём дальше.» Exact manually tested draft [PR #120](https://github.com/ALL-EX-E/InOneLine/pull/120), HEAD `2a727fe580b2712c47e388d16bd9f3cfd4914879`, native [Windows regression 38215560993](https://github.com/ALL-EX-E/InOneLine/actions/runs/38215560993) SUCCESS and publication [wording 38215560921](https://github.com/ALL-EX-E/InOneLine/actions/runs/38215560921) SUCCESS. [Verified Google Drive QA ZIP](https://drive.google.com/file/d/14_7DsQkoVNh-i1T0fOOgx2rRM4-jZsdD/view?usp=drivesdk), 46,783,580 bytes, SHA256 `1de9cb6053756f03d5dc028d20200c59787d51bbc41871f3d41ad7c2731b385f` and ZIP CRC PASS.
- Exactly accepted runtime/test Git blobs: `streaming_manager/views/rules_editor.py=df0e97056e995205ce28dead2df29aa68be1ee84`; `tools/gui_regression_smoke.py=18d1262a33ce1544144b2832e6406082ddf10e35`. Save choice Replace/Save-as/Cancel, inactive copy retains existing source and active/on-air Rules; new template first Save direct, old Close dirty guard retained. No DB/schema, OBS/audio or version change.
- **USER ACCEPTED.** Clean-promote exactly these two tested blobs plus three canonical docs on currently accepted main. Fresh full native Windows Regression Foundation and wording PASS on promotion HEAD, then merge with SHA lease, verify 2/2 exact source/test blobs on main, close original draft PR #120 WITHOUT MERGE. Next isolated P11-H: safeguard activating a dirty template (no silent saving before activation). User approved UI-060 prerequisite: prompt to save or cancel before activation; do not silently save; preserve current active/on-air Rules on cancel. Implement and manually QA separately.

## P11-G verified closure; P11-H FIX1 QA candidate — 2026-10-12

- P11-G user manual PASS 07:15:09 UTC; clean accepted [PR #122](https://github.com/ALL-EX-E/InOneLine/pull/122) merged to main SHA `54b96592894c698087d306f5ebee4de10c67a79f` after fresh Windows [38216854293](https://github.com/ALL-EX-E/InOneLine/actions/runs/38216854293) and wording [38216854271](https://github.com/ALL-EX-E/InOneLine/actions/runs/38216854271) SUCCESS. Independently fetched two source/test blobs on `main`: `rules_editor.py=df0e97056e995205ce28dead2df29aa68be1ee84`, `gui_regression_smoke.py=18d1262a33ce1544144b2832e6406082ddf10e35` — exact accepted 2/2. Original draft #120 CLOSED WITHOUT MERGE. **P11-G COMPLETE**.
- P11-H separate UI-060/dirty activation guard in [draft PR #123](https://github.com/ALL-EX-E/InOneLine/pull/123): before `Сделать активным` on a dirty template, present explicit `Сохранить и активировать` / `Отмена` with Cancel default; no silent write, cancel preserves current active/on-air and unsaved draft, failure preserves both, clean activation unchanged. No storage, DB schema, OBS, audio, version, auction business changes. First Windows run 38217570629 failed **test-only** due to incorrect PySide6 mocked exec signature, corrected test-only in FIX1 (runtime unchanged).
- Exact P11-H FIX1 HEAD `917ff991d040142bdbbc90c6363e2a4625320ac9` native [Windows Regression Foundation 38217851436](https://github.com/ALL-EX-E/InOneLine/actions/runs/38217851436) SUCCESS and wording 38217851437 SUCCESS; new and all prior P11 Qt tests PASS. [Verified Google Drive QA ZIP](https://drive.google.com/file/d/12YmMw4R8YItPZOQI2ThDnaWDk7iOUW4d/view?usp=drivesdk), 46,790,726 bytes, SHA256 `a5d8ddb91cdb8e7420d09ae0f726f9daf60c53868bf242bd97fe6578fb103f7d`, ZIP CRC PASS; one InOneLine_Setup_1.0.8.exe, Drive folder/name/size/MIME verified. Candidate exact runtime/test Git blobs `rules_editor.py=7ed11782930f4bdb10050dda062604d31ca7b417`, `gui_regression_smoke.py=41a292237b8f10969605d2ca53616e984f939ac8`.
- **P11-H AWAITING USER MANUAL QA / DRAFT UNMERGED.** After explicit user PASS do a fresh exact-file clean promotion, native Windows and wording SUCCESS, 2/2 Git blob postmerge check, close candidate draft without merging. Composite Rules appearance/OBS template work remains later isolated P11 units.

## P11-H — USER ACCEPTED; exact clean promotion gate — 2026-10-12

- User manually accepted the P11-H FIX1 installed Windows QA archive at **2026-10-12 07:37:00 UTC**: «Всё работает. Идём дальше.» Exact tested draft [PR #123](https://github.com/ALL-EX-E/InOneLine/pull/123) HEAD `917ff991d040142bdbbc90c6363e2a4625320ac9`; native [Windows Regression Foundation 38217851436](https://github.com/ALL-EX-E/InOneLine/actions/runs/38217851436) **SUCCESS** and [publication wording 38217851437](https://github.com/ALL-EX-E/InOneLine/actions/runs/38217851437) **SUCCESS**. [Verified Drive installer ZIP](https://drive.google.com/file/d/12YmMw4R8YItPZOQI2ThDnaWDk7iOUW4d/view?usp=drivesdk), 46,790,726 bytes, SHA256 `a5d8ddb91cdb8e7420d09ae0f726f9daf60c53868bf242bd97fe6578fb103f7d`, full ZIP CRC PASS.
- Copy **exact two tested Git blobs**: `streaming_manager/views/rules_editor.py=7ed11782930f4bdb10050dda062604d31ca7b417`, `tools/gui_regression_smoke.py=41a292237b8f10969605d2ca53616e984f939ac8` unchanged. Rules dirty-activation guard asks `Сохранить и активировать / Отмена`, Cancel default; no silent save, current on-air/active not changed when cancelled or failed save. Clean activation unchanged. No DB/schema, OBS, audio or version changes.
- **USER PASS; clean promotion pending**. On accepted main `34ee82c3bafc18b8015b9d603bf99ccd552526f9`, promote only these two blobs and canonical 3 docs. Require fresh native Windows + wording SUCCESS on exact clean promotion HEAD, merge with SHA lease, verify 2/2 blobs read back on main, close superseded draft #123 **WITHOUT MERGE**. Next P11-I composite Rules editor OBS appearance work: review exact persisted settings and identify smallest compatible UI step; no redundant settings/library/storage subsystem and separate QA gate.

## P11-H CLOSED; P11-I source-awareness candidate — 2026-10-12

- User explicitly accepted installed P11-H FIX1 at 2026-10-12 07:37:00 UTC. Exact clean [PR #125](https://github.com/ALL-EX-E/InOneLine/pull/125) merged to main `6ad1a005f6ca8b4137c270998b134f5f27ab4f34` after native [Windows Regression Foundation 38218911398](https://github.com/ALL-EX-E/InOneLine/actions/runs/38218911398) **SUCCESS** and wording 38218911699 **SUCCESS** on exact promotion SHA `25d2a87ad14e8b73daa29c1b96a1b898d15d51d2`. Postmerge Git blobs readback **2/2 accepted**: `rules_editor.py=7ed11782930f4bdb10050dda062604d31ca7b417` and `gui_regression_smoke.py=41a292237b8f10969605d2ca53616e984f939ac8`. Candidate draft PR #123 CLOSED WITHOUT MERGE. **P11-H DONE**.
- Next isolated approved UI-060 portion **P11-I**: read-only source-awareness note in Rules editor showing whether selected template belongs to the currently open local auction. Uses authoritative existing `Database.get_open_auction_session()` and `rules_template_id` when switching templates, **not** on every keystroke; no session/data/OBS/storage changes. Different or null source templates must never be falsely described as live. No open auction hides the note. Editable text, Save/Activate/Close mechanics unchanged.
- Draft [PR #126](https://github.com/ALL-EX-E/InOneLine/pull/126) candidate HEAD `2390dc25679eb1c0d72a6c00f8a59c7c21dc323c` changes exactly `streaming_manager/views/rules_editor.py` and `tools/gui_regression_smoke.py`. Native Windows [38219653021](https://github.com/ALL-EX-E/InOneLine/actions/runs/38219653021) and wording 38219653034 are the gates; candidate **NOT USER ACCEPTED / NOT MERGED**. Do not proceed to promotion without verified final Windows installer + explicit user manual PASS. Existing composite OBS appearance settings are future separate substeps.

## P11-I Windows QA VERIFIED; await manual acceptance — 2026-10-12

- P11-I draft [PR #126](https://github.com/ALL-EX-E/InOneLine/pull/126) exact source/test HEAD `2390dc25679eb1c0d72a6c00f8a59c7c21dc323c`; isolated Rules editor note when selected template is / isn't the open local auction's source template. No DB/schema/OBS/session behaviors changed, no extra DB polling per keystroke; existing Save/Activate/Close mechanics unchanged.
- [Native Windows Regression Foundation 38219653021](https://github.com/ALL-EX-E/InOneLine/actions/runs/38219653021) SUCCESS, [publication wording 38219653034](https://github.com/ALL-EX-E/InOneLine/actions/runs/38219653034) SUCCESS. Exact source/test Git blobs: `rules_editor.py=b2bef8bb592e566bbe418b913f217f94c71a6ff3`, `gui_regression_smoke.py=7bd54c766cfa0b571d47fba91da8287a319e0be0`.
- [Verified Google Drive P11-I Windows QA ZIP](https://drive.google.com/file/d/1cRveplRPp_ySisLH3YqM7ONr_WA1pfS8/view?usp=drivesdk): `InOneLine_P11I_RULES_CURRENT_AUCTION_NOTICE_1.0.8_WINDOWS_QA.zip`, 46,797,458 bytes, SHA256 `c8a1b01ba1c804c4eda8a83383c0754259d37a8e33aeebccc6a58282eb22b7b4`; exact GitHub artifact digest matched; ZIP CRC PASS; one `InOneLine_Setup_1.0.8.exe` 47,657,433 bytes. Google Drive readback exact name/size/MIME/QA parent.
- **P11-I NOT YET MANUALLY ACCEPTED; CANDIDATE DRAFT UNMERGED.** User to test Rules editor no-auction (note hidden), current auction source template (notice: Save updates live session/OBS), different template (notice Save doesn't affect live session), switching, normal saves/OBS preview. If user confirms, clean promote only exact two blobs on latest main with fresh native Windows and wording PASS; postmerge 2/2 exact blob verify; close draft PR #126 unmerged. Later UI-060 composite OBS appearance editor remains outstanding.

## P11-I manual QA found two defects — 2026-10-12 08:17:27 UTC

- User submitted screenshot evidence: (1) at minimal-width `Аукцион → Проведение`, `Способ определения победителя:` label is clipped and `О методах`/`Данные проверки` overlap method combo. **SEPARATE RESPONSIVE-AUCTION-SETUP BUG P11-UI-MINWIDTH-001**, queued for **isolated** layout change and separate user QA after fixing current Rules live bug. Code inspection: `streaming_manager/views/auction.py` uses a 6-column `QGridLayout` row with nonflexible label, `mode_combo` minimum 180 px, `rng_combo` minimum 170 px and two buttons; its combined minimum width exceeds narrow content viewport. Must preserve method/rng/wheel behavior, avoid hiding controls, prefer responsive layout/safe horizontal scroll, test min-width and wide.
- (2) When a different Rules template is activated during an open auction, the current Rules notice stays stale and real browser OBS preview/widget retain pre-auction content. This is a genuine **P11-I QA blocker**. Root cause: `Database.set_active_rule_template` changed only global `is_active`, whereas `current_rules_payload` correctly reads immutable-before-switch `auction_sessions.rules_template_id/name/html` while open.
- P11-I **NOT MANUALLY ACCEPTED**; initial Windows package superseded by candidate **P11-I FIX1** in draft [PR #126](https://github.com/ALL-EX-E/InOneLine/pull/126), HEAD `d97d7ba62be5cb5e4b9c9357dc976d3d12362790`. Fix: reuse existing single DB transaction to switch active template and currently open local session source/template-name/rules HTML together, journal `switch_rules_template` via existing change log; existing session-source Save sync and closed historical snapshots untouched, no extra backend or schema. Native Qt/SQLite test starts real auction and checks source note, on-air Rules API payload, activation back and forth, inactive Save independence, historical snapshots.
- FIX1 fresh Windows [38223053610](https://github.com/ALL-EX-E/InOneLine/actions/runs/38223053610) and wording 38223053627 pending as of this record; no new installer should be offered until full PASS, artifact digest/CRC verified, Drive readback and explicit user retest. On QA PASS clean-promote exact blobs with fresh gates and SHA verification. **Do not mix min-width layout changes into FIX1**, or mark P11-I accepted before confirmed test.

## P11-I FIX1 native Windows QA READY; manual recheck required — 2026-10-12

- User screenshots/feedback 2026-10-12 08:17:27 UTC: during open auction, activating another Rules template left old session source note, OBS preview and OBS widget; also minimum-width Auction → Проведение label/buttons overlap. Both recorded in accepted main doc record from PR #129. **Initial P11-I installer is superseded and NOT ACCEPTED**.
- Root cause: global `auction_rule_templates.is_active` changed but active `auction_sessions.rules_template_id/name/html` remained old, so `current_rules_payload()` correctly kept serving original snapshot. New FIX1 reuses existing SQLite transaction in `Database.set_active_rule_template` to change current template and open session Rules source together, audit switch with existing log; no parallel state or schema/OBS endpoint. Inactive template Save still independent; closed snapshots preserved; P11-I source note updates as a side effect of reloading current session. Narrow method-selector UI bug is **separately queued** and not bundled.
- Exact P11-I FIX1 candidate [draft PR #126](https://github.com/ALL-EX-E/InOneLine/pull/126), HEAD `4aedfb6d247f24f6f2344587d3b1d8041d7e0623`, three tested Git blobs: `streaming_manager/db/rules.py=388a8802d025f3bd63d1612a9c1d37910c628468`; `streaming_manager/views/rules_editor.py=b2bef8bb592e566bbe418b913f217f94c71a6ff3`; `tools/gui_regression_smoke.py=e46e82cbd5fff0349ad7ba0e7d17a5eb6d588c94`. Prior P11-I FIX1 test fixture needed clean-state patch for Qt raw-HTML dirty confirmation; runtime patch unchanged.
- Full native [Windows Regression Foundation 38223508418](https://github.com/ALL-EX-E/InOneLine/actions/runs/38223508418) **SUCCESS**, [wording 38223508532](https://github.com/ALL-EX-E/InOneLine/actions/runs/38223508532) **SUCCESS**. [Verified ZIP on Google Drive](https://drive.google.com/file/d/19h_8nleRlrefuo4ulTCYnG48gEQNkgV_/view?usp=drivesdk), `InOneLine_P11I_FIX1_LIVE_RULES_SWITCH_1.0.8_WINDOWS_QA.zip`, 46,802,029 bytes SHA256 `57cf192ebd97612cd479276ba8e7c96a0eaa724b24fbf2f3661f724ba12f6566`, full ZIP CRC PASS, single `InOneLine_Setup_1.0.8.exe` 47,662,008 bytes, uploaded Drive metadata readback exact size/name/MIME/QA folder.
- **AWAIT USER MANUAL QA, NOT MERGED.** User to test running auction swap between different rules templates, observe notice and actual OBS browser/widget immediately switch, inactive save remains isolated, active save mirrors; dirty Cancel and no-auction guards. If accepted, clean-promote only exact three tested blobs with native Windows/wording gates and 3/3 blob postmerge verification, close old draft unmerged; then separately fix Conduct minimum-width layout.

## P11-I FIX1 USER MANUAL ACCEPTED — clean promotion gate (2026-10-12)

- At **2026-10-12 08:40:13 UTC** user confirmed the installed [P11-I FIX1 QA ZIP](https://drive.google.com/file/d/19h_8nleRlrefuo4ulTCYnG48gEQNkgV_/view?usp=drivesdk) works: «Всё работает. Идём дальше.» This supersedes rejected P11-I initial package. Exact accepted candidate [draft PR #126](https://github.com/ALL-EX-E/InOneLine/pull/126) HEAD `4aedfb6d247f24f6f2344587d3b1d8041d7e0623`; native [Windows 38223508418](https://github.com/ALL-EX-E/InOneLine/actions/runs/38223508418) SUCCESS, wording 38223508532 SUCCESS. Verified ZIP 46,802,029 bytes, SHA256 `57cf192ebd97612cd479276ba8e7c96a0eaa724b24fbf2f3661f724ba12f6566`, CRC PASS, Google Drive name/size/parent verified.
- User-tested **three exact Git blobs**: `streaming_manager/db/rules.py=388a8802d025f3bd63d1612a9c1d37910c628468`, `streaming_manager/views/rules_editor.py=b2bef8bb592e566bbe418b913f217f94c71a6ff3`, `tools/gui_regression_smoke.py=e46e82cbd5fff0349ad7ba0e7d17a5eb6d588c94`. Reuses one transaction, one existing open-session rules snapshot, existing API and audit; no schema/parallel state. Current auction active Rules switch, OBS, notice and inactive draft isolation confirmed manually.
- **USER PASS; clean source/test promotion pending.** Copy only these 3 blobs plus three canonical docs onto latest accepted main `94312f7354a93e94722ca05a3e8efea145dbc9a9`; fresh Windows Regression Foundation and wording gates on exact promotion SHA must PASS, then squash merge with SHA lease, verify 3/3 exact blobs postmerge and close original draft PR #126 unmerged. Next separately fix `Аукцион → Проведение` method label and buttons overlapping at smallest window width, previously recorded as P11-UI-MINWIDTH-001 from 08:17:27 UTC user screenshot. Do not combine layout with this promotion.

## P11-I FIX1 accepted; Auction Conduct min-width candidate awaiting Windows QA — 2026-10-12

- User explicitly accepted P11-I FIX1 2026-10-12 08:40:13 UTC «Всё работает. Идём дальше.» [PR #131](https://github.com/ALL-EX-E/InOneLine/pull/131) clean exact promotion merged to main f2bd56a74dbacf0b0b2c51522acebacb66b7566f after fresh [native Windows 38225194344](https://github.com/ALL-EX-E/InOneLine/actions/runs/38225194344) SUCCESS and wording 38225194343 SUCCESS on HEAD 2cdf3d937ee72e6cdb61d7ac919a5cc1e8193f5d. Postmerge accepted Git blobs readback PASS 3/3: db/rules.py 388a8802d025f3bd63d1612a9c1d37910c628468, views/rules_editor.py b2bef8bb592e566bbe418b913f217f94c71a6ff3, tools/gui_regression_smoke.py e46e82cbd5fff0349ad7ba0e7d17a5eb6d588c94. Superseded draft #126 CLOSED UNMERGED. **P11-I FIX1 COMPLETED.**
- Next separate **P11-UI-MINWIDTH-001** from user screenshot at 08:17:27 UTC: Auction / Проведение minimum-width method label clipped and adjacent buttons overlap selector. [Draft PR #132](https://github.com/ALL-EX-E/InOneLine/pull/132) changes only views/auction.py and tools/gui_regression_smoke.py, retaining selectors/methods/wheel/rng choices/handlers; replaces overloaded six-column setup with two-column rows, buttons on separate row; Qt geometry regression 520 → 1100 → 520 asserts full method label, no overlap, unchanged data. Candidate HEAD 432852e77390d01b59bda7f34f4eae5d1935a117; full [Windows CI 38226244054](https://github.com/ALL-EX-E/InOneLine/actions/runs/38226244054) and wording gate pending.
- **P11-UI-MINWIDTH-001 UNACCEPTED / DRAFT UNMERGED** pending full Windows PASS, exact verified QA installer ZIP uploaded to existing Google Drive QA folder and explicit user manual QA. Later clean promote only tested source/test blobs on latest main with fresh Windows+wording CI and SHA postmerge verification; no business/audio/DB/OBS changes.

## UI-MINWIDTH-001 compact Auction Conduct: candidate Windows QA READY — 2026-10-12

- User-reported screenshot clipping/overlap on minimum-width Аукцион → Проведение handled separately from manually accepted P11-I FIX1. Source: six-column crowded QGridLayout; no method/auction behavior changes.
- [Draft PR #132](https://github.com/ALL-EX-E/InOneLine/pull/132) exact tested HEAD **432852e77390d01b59bda7f34f4eae5d1935a117**; two tested Git blobs: streaming_manager/views/auction.py=df0322b67eb071ed13d81f98f363abd68c174f48 and tools/gui_regression_smoke.py=a5e90d6cb99c462661994ef2fa0701fa181ae8cb. Layout now stable two-column with full method label and separate methods/verification action row; retains all values/signals and visibility, no data/OBS/audio/session migration. Native 520→1100→520 Qt geometry test checks non-overlap, full label, preserved selection.
- Full [Windows Regression Foundation 38226244054](https://github.com/ALL-EX-E/InOneLine/actions/runs/38226244054) **SUCCESS**, [publication wording 38226243853](https://github.com/ALL-EX-E/InOneLine/actions/runs/38226243853) **SUCCESS** on exact tested candidate SHA. [Verified Windows QA ZIP](https://drive.google.com/file/d/1Qt7HeG5TJ-1NgI2t5f02MMsuziwYpzXI/view?usp=drivesdk), InOneLine_AUCTION_CONDUCT_MINWIDTH_FIX_1.0.8_WINDOWS_QA.zip, 46,797,508 bytes, SHA256 **285d284380e8ed853059cab3af804c72eefb5ef9dde1f05739bacf249bf59b6c** matching GitHub artifact 11736187845. Independent zip CRC PASS and one InOneLine_Setup_1.0.8.exe (47,657,464 bytes). Google Drive readback verified file name/size/MIME/QA folder.
- **AWAIT USER MANUAL QA; do not merge PR #132.** Test min width Аукцион → Проведение label uncut, method selection unoverlapped, method help/verification visible; resize wide and back; wheel/rng choices unaffected; check previous P11-I live Rules switch remains functional. After explicit PASS clean-promote exact 2 blobs + canonical doc acceptance notes on latest main, run fresh native Windows+wording CI, verify 2/2 Git blob identity postmerge, close draft without merging.

## UI-MINWIDTH-001 user accepted: clean exact promotion — 2026-10-12

- User manual PASS at **2026-10-12 13:59:17 UTC**: «Всё работает. Идём дальше.» for installed [Auction Conduct Minwidth FIX 1.0.8 Windows QA](https://drive.google.com/file/d/1Qt7HeG5TJ-1NgI2t5f02MMsuziwYpzXI/view?usp=drivesdk). 46,797,508-byte ZIP, SHA256 285d284380e8ed853059cab3af804c72eefb5ef9dde1f05739bacf249bf59b6c, ZIP CRC PASS and Drive metadata exact filename/size/MIME/QA parent verified. Exact user-tested draft [PR #132](https://github.com/ALL-EX-E/InOneLine/pull/132) HEAD 432852e77390d01b59bda7f34f4eae5d1935a117, native [Windows Regression Foundation 38226244054](https://github.com/ALL-EX-E/InOneLine/actions/runs/38226244054) SUCCESS, publication wording 38226243853 SUCCESS.
- Exact two accepted Git blobs: streaming_manager/views/auction.py=df0322b67eb071ed13d81f98f363abd68c174f48; tools/gui_regression_smoke.py=a5e90d6cb99c462661994ef2fa0701fa181ae8cb. Compact Auction→Проведение method form makes full label visible and action buttons non-overlapping in minimum width, preserves RNG/wheel/method data, handlers, auction/OBS behavior, and existing user settings. No DB/schema/audio/version changes.
- **USER ACCEPTED; clean promotion pending** on latest main 5b189ef168fc550b2a6f172c19b0c66ef9e5a143. Copy EXACT two Git blobs + only three canonical docs; fresh full native Windows+wording SUCCESS on clean promotion SHA, SHA-leased merge and independent 2/2 blob identity verification on main. Close original draft PR #132 WITHOUT MERGE. Then continue next approved P11 (UI-048/UI-060 combined Rules editor/OBS appearance) in isolated small scope after reviewing remaining requirements/code; no parallel settings/state or non-approved features.

## UI-MINWIDTH-001 CLOSED; P11-J Windows QA READY — 2026-10-12

- User manual Windows QA PASS at 2026-10-12 13:59:17 UTC: «Всё работает. Идём дальше.» for Auction→Проведение min-width label/button layout. Clean [PR #135](https://github.com/ALL-EX-E/InOneLine/pull/135) merged via squash main **9c21b2b5f7f56c7d40c93897858cf63823c3b6f1** after fresh [native Windows 38259905933](https://github.com/ALL-EX-E/InOneLine/actions/runs/38259905933) SUCCESS and wording 38259905955 SUCCESS on exact promotion SHA e069d6f05f5b4117c41ab081dd831a8b65a9da59. Postmerge independently read both accepted Git blobs **2/2**: streaming_manager/views/auction.py=df0322b67eb071ed13d81f98f363abd68c174f48; tools/gui_regression_smoke.py=a5e90d6cb99c462661994ef2fa0701fa181ae8cb. Superseded draft PR #132 CLOSED WITHOUT MERGE. **UI-MINWIDTH-001 ACCEPTED / COMPLETED.**
- Next isolated **P11-J/UI-060**: one existing Rules template selector and one shared Save/Activate/Close; add two editor sections `Текст правил` (original QTextEdit+rich-text toolbar) and `Оформление OBS` (reuse exact existing Rules URL/copy/browser preview in own section). No appearance settings have been migrated yet; this is the UI skeleton needed before separate composite template/appearance migration. No duplicate route, handler, save, template or DB/OBS state. Candidate [draft PR #136](https://github.com/ALL-EX-E/InOneLine/pull/136) exact tested HEAD **a41daa569254af507911b8ef386f7371551307e7**; only two tested files: streaming_manager/views/rules_editor.py=d2ec8caeb545a7f400be97fdb12a9fe9af6c8ead; tools/gui_regression_smoke.py=138df9aff263bf5f0a235c4acc1f1e1e76433dfd.
- P11-J [native Windows Regression Foundation 38261010704](https://github.com/ALL-EX-E/InOneLine/actions/runs/38261010704) **SUCCESS**, wording 38261010731 **SUCCESS**; new Qt regression P11_J_RULES_TEXT_OBS_TABS_SHARED_TEMPLATE_SAVE_PREVIEW PASS plus all previous P11/OBS/timer/installer gates. GitHub artifact 11752766380 verified: [Google Drive P11-J Windows QA ZIP](https://drive.google.com/file/d/1wRtqkeAZvpHd8wjjmIB18QyzTbWsj8g8/view?usp=drivesdk), InOneLine_P11J_RULES_EDITOR_TEXT_OBS_TABS_1.0.8_WINDOWS_QA.zip, **46,800,420 bytes**, SHA256 **991fcb8ef85032f1e798c86dc1a3931406950c6df203b9c5b5fdc5da4c4a2192** (matches GitHub), CRC PASS, exactly one InOneLine_Setup_1.0.8.exe (47,660,349 bytes). Drive metadata readback confirms exact file name, size, ZIP MIME and existing QA folder.
- **P11-J AWAIT USER MANUAL QA / NOT MERGED.** Test both editor tabs, unsaved text persists switching to OBS, same shared Save/Activate/Close, URL copy & true browser preview, no changes to on-air Rules, existing Stream/OBS appearance unaffected. After explicit manual PASS clean-promote exact two blobs with fresh native Windows+wording CI and 2/2 postmerge verification; close draft PR #136 without merge. Only then advance to OBS appearance controls and composite per-template persistence, no second style system.

## P11-J USER MANUAL ACCEPTED — clean promotion gate (2026-10-12)

- At **2026-10-12 14:55:22 UTC** user explicitly accepted the installed P11-J Windows QA: «Принимаю. Всё работает. Идём дальше.» This closes the P11-J user manual QA gate, **not** the merge/CI gate. Exact tested candidate [draft PR #136](https://github.com/ALL-EX-E/InOneLine/pull/136) HEAD **a41daa569254af507911b8ef386f7371551307e7**; verified [Windows Regression Foundation 38261010704](https://github.com/ALL-EX-E/InOneLine/actions/runs/38261010704) SUCCESS and publication wording 38261010731 SUCCESS. [Exact user-tested QA ZIP](https://drive.google.com/file/d/1wRtqkeAZvpHd8wjjmIB18QyzTbWsj8g8/view?usp=drivesdk) is 46,800,420 bytes, SHA256 `991fcb8ef85032f1e798c86dc1a3931406950c6df203b9c5b5fdc5da4c4a2192`, CRC PASS and Drive metadata verified.
- **Exactly two accepted Git blobs:** `streaming_manager/views/rules_editor.py=d2ec8caeb545a7f400be97fdb12a9fe9af6c8ead`; `tools/gui_regression_smoke.py=138df9aff263bf5f0a235c4acc1f1e1e76433dfd`. P11-J separates existing Rules rich-text editor and its original OBS URL/copy/real-preview actions into `Текст правил` and `Оформление OBS`, preserving a single template selection, Save, Activate, Close, dirty guard, source/OBS semantics. OBS appearance styling is **not yet migrated**; no additional style database or runtime handlers.
- Clean promotion is limited to these **exact two source/test blobs** plus **three canonical docs** onto previous main `a4c54ef600852779108b2fc66d4429c9e5a51b2f`. Promotion CI requires **fresh native Windows Regression Foundation and publication-wording SUCCESS on exact PR promotion HEAD**, SHA-leased squash merge, independent **2/2 exact Git blob verification on main**, then close original candidate draft PR #136 **WITHOUT merging it**. Do not claim P11-J fully closed before these checks.
- **NEXT P11-K (UI-060 / UI-048) scoped review:** after P11-J clean closure, inspect actual existing Stream/OBS rules-overlay appearance controls and existing rules-template persistence, then plan the smallest reusable editor migration increment. Composite text+appearance templates remain a later isolated user-QA step; do not create parallel style/settings/OBS paths or move all settings at once. Respect one scope, full Windows QA, explicit user acceptance.

## P11-J CLOSED; P11-K UI-060 ownership audit — 2026-10-12

- User manual acceptance at **2026-10-12 14:55:22 UTC**: «Принимаю. Всё работает. Идём дальше.» Tested [P11-J ZIP](https://drive.google.com/file/d/1wRtqkeAZvpHd8wjjmIB18QyzTbWsj8g8/view?usp=drivesdk), original draft [#136](https://github.com/ALL-EX-E/InOneLine/pull/136) SHA `a41daa569254af507911b8ef386f7371551307e7`. Clean exact promotion [PR #138](https://github.com/ALL-EX-E/InOneLine/pull/138) merged via squash to main **e744276bbc71ec12b982ec8e42a54d2aa2791652** after **fresh native Windows 38266824423 SUCCESS** and **publication wording 38266824380 SUCCESS** on promotion HEAD `aab1ca3c4573ae2a51079d253e7e271fe366dab4`. Git blobs independently checked **2/2 exact** on main: `streaming_manager/views/rules_editor.py=d2ec8caeb545a7f400be97fdb12a9fe9af6c8ead`, `tools/gui_regression_smoke.py=138df9aff263bf5f0a235c4acc1f1e1e76433dfd`. Original PR #136 CLOSED **WITHOUT MERGE**. **P11-J USER ACCEPTED AND COMPLETED.**
- **P11-K technical ownership audit:** current `streaming_manager/views/stream.py` holds the old Rules OBS appearance controls and a separate `_save_rules_overlay_settings` handler; `streaming_manager/db/rules.py:current_rules_payload()` combines session/active-template HTML with global `settings` values for `rules_overlay_autoscroll`, `rules_overlay_background`, `rules_overlay_background_color`, `rules_overlay_background_opacity`, and `rules_overlay_padding`. Template storage currently contains only HTML/name/activity, not per-template presentation. The existing `rules` visibility/show-mode remains a **global widget concern** (GLOBAL-OBS-VISIBILITY-001), not part of template appearance.
- **NEXT ISOLATED P11-K / UI-060:** design and implement a backward-compatible, template-owned Rules presentation snapshot in a small, separately reviewed persistence/QA increment **before moving styling controls**. Preserve legacy global appearance as a safe fallback/migration source and unchanged current OBS rendering until a separately tested switch; preserve existing open-auction template source sync and historical snapshots; do not create a second settings/save/route system or bundle UI moves or unrelated features. Only after standalone data-compatibility testing and explicit manual Windows QA proceed to editor UI transfer and one shared text+appearance Save in later increments.

## P11-K1/UI-060 — compatible Rules presentation schema, Windows QA READY (2026-10-12)

- P11-J confirmed accepted and closed; [PR #138](https://github.com/ALL-EX-E/InOneLine/pull/138) clean source/test SHA promotion and [PR #139](https://github.com/ALL-EX-E/InOneLine/pull/139) canonical closure merged to main `08f69f274e543c128fa8e03ae649f5a043500868`. Next P11-K split into small independently verified increments; this is **P11-K1 STORAGE ONLY, NOT OBS/UI CUTOVER**.
- Isolated [draft PR #140](https://github.com/ALL-EX-E/InOneLine/pull/140) exact tested HEAD **5e2cd9e89e4bbe6426d9445ef54fa9acf092478e** changes five paths only: `streaming_manager/constants.py`, `streaming_manager/db/schema.py`, `.github/workflows/regression-foundation-1.0.8.yml`, `tools/rules_presentation_schema_smoke.py`, and `tools/legacy_full_backup_restore_smoke.py` (legacy test fixture correctness only). App remains 1.0.8; database schema **19→20**, named migrations **15→16**. A single idempotent migration adds nullable `auction_rule_templates.presentation_json` and `auction_sessions.rules_presentation_json`. NULL deliberately means **legacy global Rules appearance**, left dynamic and unmodified until a later explicitly tested ownership/UI switch. Existing templates/session rows are untouched. Existing Stream/OBS Rules save/preview/UI, `current_rules_payload()`, visibility policy, auction session rules source/text, historic snapshots and user data are unchanged; no second style system or renderer switch.
- Initial CI failed due test-only missing direct-run project root and a historical restore smoke fixture mislabeling current-schema bytes as schema 19; **fixed in candidate without runtime behavior changes**. FIX1 exact tested head above: full native [Windows Regression Foundation 38269885957](https://github.com/ALL-EX-E/InOneLine/actions/runs/38269885957) **SUCCESS**; [publication wording 38269885953](https://github.com/ALL-EX-E/InOneLine/actions/runs/38269885953) **SUCCESS**. Job logs explicitly contain `P11_K_RULES_SCHEMA19_COMPATIBLE_PRESENTATION_STORAGE=PASS` and `LEGACY_1_0_6_FULL_BACKUP_RESTORE=PASS`, plus existing GUI/OBS/installer PASS. The compatibility test checks fresh/legacy-19 migration, NULL fallback, no text/session/global styling change, idempotent relaunch and preservation of future stored values.
- GitHub artifact **11757205250** exactly verified as [Google Drive Windows QA ZIP](https://drive.google.com/file/d/1UdQYy9axRZQQxY1LdETwf8w_ijYWLCyx/view?usp=drivesdk): `InOneLine_P11K1_RULES_PRESENTATION_SCHEMA20_1.0.8_WINDOWS_QA.zip`, **46,790,328 bytes**, SHA256 **2994337e933e30f05d847d3163efa77052b2c0dfea915c6052aef11178c11bef** matching source GitHub Actions digest; ZIP CRC PASS, exactly one `InOneLine_Setup_1.0.8.exe` 47,650,277 bytes. Drive metadata verified exact title, size, application/zip MIME and original QA folder.
- **P11-K1 AWAIT EXPLICIT USER MANUAL WINDOWS QA; KEEP DRAFT UNMERGED.** User checks app starts after upgrading an existing database, existing rule text/templates remain, Stream/OBS rules styling values are unchanged, live rule-template switch/OBS works, and same after restart. This infrastructure increment intentionally does not expose per-template style controls. On explicit PASS, clean promote exactly five tested files (plus canonical acceptance docs) onto latest main, fresh full Windows+wording gates, SHA-leased merge, verify all five exact Git blobs on main, close draft #140 **without merging**. После принятия этого этапа P11-K2 отдельно добавит чтение, запись и синхронизацию оформления шаблонов; перенос UI и изменение отображения OBS не входят в текущую проверку.

## P11-K1 принят пользователем — перенос точно проверенной схемы (2026-10-12)

- **Ручная приёмка: PASS, 2026-10-12 15:53:14 UTC.** Ответ пользователя после установки и проверки: «Всё работает. Идём дальше.» Проверенная сборка [P11-K1 Windows QA](https://drive.google.com/file/d/1UdQYy9axRZQQxY1LdETwf8w_ijYWLCyx/view?usp=drivesdk): архив 46 790 328 байт, SHA-256 `2994337e933e30f05d847d3163efa77052b2c0dfea915c6052aef11178c11bef`, CRC PASS. Исходный черновик [PR #140](https://github.com/ALL-EX-E/InOneLine/pull/140), проверенный HEAD `5e2cd9e89e4bbe6426d9445ef54fa9acf092478e`; Windows Regression Foundation `38269885957` SUCCESS и publication wording `38269885953` SUCCESS.
- **Точное повышение в main:** ровно пять проверенных файлов без переписывания исходников: `.github/workflows/regression-foundation-1.0.8.yml=0e3aafa38d0c184ea778df5a6c4babc5832aceb1`, `streaming_manager/constants.py=922495d48a4580a08af66ed71585a9d6e6da8da2`, `streaming_manager/db/schema.py=a6be77336e0730dee76556732bcd6f9f46354611`, `tools/legacy_full_backup_restore_smoke.py=ab8e3e5e958438fdff1e6ea604823f313ee801c6`, `tools/rules_presentation_schema_smoke.py=9eefa9ecfafba9f5de7ff229db2953048729820d`. Прежняя версия приложения 1.0.8, новая SQLite schema 20 и 16 миграций, миграция добавляет nullable-поля оформления; работа OBS/UI остаётся прежней. Результаты приёмки зафиксированы отдельно от разработки следующего шага.
- Перед объединением в `main` обязательны новые полные проверки Windows и publication wording на точном HEAD ветки повышения, merge с контролем SHA, чтение 5/5 хешей из `main`, закрытие исходного PR #140 без объединения.
- **Следующий отдельный шаг P11-K2 / UI-060:** совместимые методы чтения/записи оформления по шаблону с повторным использованием полей schema 20, без переноса элементов интерфейса или переключения текущего OBS-рендера. Сохранить NULL как наследование старых общих параметров; предусмотреть корректную обработку недопустимого JSON, строго определить владение снимком для активного аукциона. Новая проверка и отдельная ручная приёмка пользователя обязательны.

## P11-K1 завершён; P11-K2 Windows QA готова — 12 октября 2026

- **P11-K1 принят вручную** в 15:53:14 UTC: «Всё работает. Идём дальше.» Точная чистая приёмка [PR #142](https://github.com/ALL-EX-E/InOneLine/pull/142), Windows Regression Foundation [38273850754](https://github.com/ALL-EX-E/InOneLine/actions/runs/38273850754) SUCCESS и publication wording 38273850763 SUCCESS. Перенос завершён в main коммитом `72820cca1843fce96f98c42de51192ca90a641a2`, все пять исходных Git-блобов сверены после объединения, исходный черновик [#140](https://github.com/ALL-EX-E/InOneLine/pull/140) закрыт без объединения. **Этап P11-K1 принят и закрыт.**
- **P11-K2 — следующий отдельный кандидат** [draft PR #143](https://github.com/ALL-EX-E/InOneLine/pull/143), проверенный HEAD `00a4bc59e46734d0be1ec7f5c5a2fa7be5d1b8a4`; изменены строго четыре файла: `.github/workflows/regression-foundation-1.0.8.yml=ed25c79fa7a74da8067ef3b968b23e22220261f7`, `streaming_manager/db/auction_session.py=df73d8edc5469dd7c915358fadb7658da03255f4`, `streaming_manager/db/rules.py=a0aafadf8588475e6da67449a3db6ab8d532beb7`, `tools/rules_presentation_access_smoke.py=7a15e1d2c7bf4bf1b7da9ca64f73c7c1796c4e96`. Схема 20 и версия приложения 1.0.8 без изменения.
- Повторно используются два новых nullable-поля schema 20. Отдельные методы читают, проверяют и сохраняют пять свойств оформления шаблона, в том числе поддерживают наследование глобального оформления при NULL или повреждённом JSON. Старт аукциона делает снимок оформления активного шаблона; изменение исходного шаблона и переключение активного источника синхронизируют оформление текущей локальной сессии в транзакции; закрытая история неизменна. Повторное сохранение не создаёт лишних изменений. **Пользовательский редактор, глобальная видимость и отображение OBS остаются прежними** до следующего отдельного шага.
- Полный [Windows Regression Foundation 38275387587](https://github.com/ALL-EX-E/InOneLine/actions/runs/38275387587) **SUCCESS**, publication wording 38275387586 **SUCCESS** для точного HEAD; новый тест `P11_K2_RULES_PRESENTATION_TEMPLATE_SESSION_SYNC_NO_OBS_SWITCH=PASS` и прежние проверки базы, интерфейса, браузера, OBS и установщика успешно завершены.
- Проверенный оригинальный GitHub Actions artifact `11759008010` опубликован в прежней папке QA: [InOneLine P11-K2 Windows QA ZIP](https://drive.google.com/file/d/1_xtAGTszqKi6q2fiFQH1kac1FT3YpCiq/view?usp=drivesdk), имя `InOneLine_P11K2_RULES_PRESENTATION_SYNC_1.0.8_WINDOWS_QA.zip`, 46 797 210 байт, SHA-256 `12d36dc0888b68805fbee0354a40d208984d4cb23b30def3fa86222b23a5900a`, CRC PASS, один установщик `InOneLine_Setup_1.0.8.exe` размером 47 657 694 байта. Проверены имя, объём, тип ZIP и папка Google Drive.
- **P11-K2 ожидает ручной Windows-проверки и отдельного подтверждения пользователя.** Черновик не объединять до приёмки. Ручная проверка: запуск после установки, все тексты и выбор шаблонов остаются, активное переключение во время аукциона меняет текст виджета OBS как прежде, глобальные настройки оформления OBS не меняются, после закрытия и повторного открытия данные сохраняются. Из-за отсутствия новых элементов UI внешне новых настроек ожидать не нужно. После подтверждения пользователя — чистый перенос четырёх точных Git-блобов со свежими тестами и сверкой на main. Дальнейший перенос элементов OBS в редактор правил будет отдельным шагом.

## P11-K2: ручная приёмка, чистое повышение — 2026-10-12

- Пользователь подтвердил P11-K2 в 16:48:56 UTC: «Всё работает. Идём дальше.» Это положительная ручная Windows-проверка ранее выданного установщика. Проверенный черновик [PR #143](https://github.com/ALL-EX-E/InOneLine/pull/143), HEAD `00a4bc59e46734d0be1ec7f5c5a2fa7be5d1b8a4`, проверка Windows 38275387587 SUCCESS, проверка текста публикации 38275387586 SUCCESS. Архив в Google Drive: [P11-K2 QA](https://drive.google.com/file/d/1_xtAGTszqKi6q2fiFQH1kac1FT3YpCiq/view?usp=drivesdk), 46 797 210 байт, SHA-256 `12d36dc0888b68805fbee0354a40d208984d4cb23b30def3fa86222b23a5900a`.
- Для безопасного повышения взяты ровно четыре исходных проверенных Git-блоба: `.github/workflows/regression-foundation-1.0.8.yml=ed25c79fa7a74da8067ef3b968b23e22220261f7`; `streaming_manager/db/auction_session.py=df73d8edc5469dd7c915358fadb7658da03255f4`; `streaming_manager/db/rules.py=a0aafadf8588475e6da67449a3db6ab8d532beb7`; `tools/rules_presentation_access_smoke.py=7a15e1d2c7bf4bf1b7da9ca64f73c7c1796c4e96`. Дополнительно изменяются только три основных документа. До объединения необходимы свежие успешные Windows и publication wording на точном HEAD ветки повышения; после него — сверка четырёх SHA в main и закрытие исходного черновика #143 без объединения.
- Смысл P11-K2: безопасные методы работы с оформлением по шаблону и синхронизация его снимка при живом аукционе. Вывод OBS по-прежнему использует общие параметры, UI оформления ещё расположен в «Стрим / OBS». Версия приложения 1.0.8, схема данных 20.
- Следующая самостоятельная задача **P11-K3**: перенос существующих средств настройки оформления правил в окно редактора, вкладку «Оформление OBS», с исключением дублирования настроек и сохранения. Использовать готовые методы P11-K2, соблюдать совместимость с прежними глобальными параметрами; не совмещать перенос интерфейса с переходом OBS на новый формат без отдельной проверки. Изменения маленькими проверяемыми порциями.

## P11-K2 завершён; P11-K3 проверочная Windows-сборка — 12 октября 2026

- **P11-K2 полностью принят и перенесён.** Пользователь сообщил «Всё работает. Идём дальше.» в 16:48:56 UTC. [Чистое повышение PR #145](https://github.com/ALL-EX-E/InOneLine/pull/145) объединено с main коммитом `1f4d6c1806e7a39ec574b35bbfd99074072b969f`; новая Windows Regression Foundation и проверка публикации успешны; сверены все четыре проверенных Git-блоба 4/4. Исходный [черновик PR #143](https://github.com/ALL-EX-E/InOneLine/pull/143) закрыт без объединения.
- **P11-K3/UI-060: КАНДИДАТ, ручная приёмка ещё не получена.** [Черновик PR #146](https://github.com/ALL-EX-E/InOneLine/pull/146), полный проверенный HEAD `0e68eac9f468f73ff444fd74311dafabe22312de`. Семь изменённых файлов: `.github/workflows/regression-foundation-1.0.8.yml=cc07b7947c9b5857e3d965c0f7da9169437c4418`, `streaming_manager/db/rules.py=fbcc63061eabf09732873948f2240ca550bc3d07`, `streaming_manager/views/rules_editor.py=4d9b29d2227ef8ec29654e2400fd0be577a32308`, `streaming_manager/views/stream.py=e535ed98ebd666655e2035cb4161e15aa2eb6431`, `tools/gui_regression_smoke.py=1d03ab8b932222a0b6a6eaff1a087df04ca909e6`, `tools/rules_editor_appearance_smoke.py=04b5c169c04c681f66d46f59bc530fbed7210b59`, `tools/rules_presentation_access_smoke.py=2634bf6ef325402fecd3eeb4a56dd1979f9319f7`.
- В существующем редакторе правил, раздел «Оформление OBS», теперь настраиваются автопрокрутка, тип/цвет фона, непрозрачность и отступ. Те же данные сохраняются через общую кнопку «Сохранить», с защитой несохранённых изменений, выбором «Заменить текущий» или «Сохранить как новый» и переключением активного шаблона. Дублирующие поля оформления удалены из «Стрим / OBS», но глобальный режим показа там остался отдельным. Виджет правил /rules-overlay использует оформление снимка текущего аукциона либо активного шаблона; при пустом/повреждённом значении использует прежние глобальные параметры. Существующие ключи, версия приложения 1.0.8, схема 20, аукционные суммы, звуковые схемы, маршруты и общая видимость не меняются.
- Нативная [Windows Regression Foundation 38281866081](https://github.com/ALL-EX-E/InOneLine/actions/runs/38281866081) **SUCCESS**, проверка публикации `38281866030` **SUCCESS** на точном HEAD. В журнале: `P11_K3_RULES_PRESENTATION_TEMPLATE_SESSION_OBS_CUTOVER=PASS`, `P11_K3_RULES_EDITOR_COMPOSITE_STYLE_SAVE_FALLBACK_QT=PASS`, прежние GUI и OBS тесты PASS. Ранние два прогона выявили несовпадение формата HTML в новом тесте и устаревшую ссылку на перемещённое поле в старом тесте; исправлены только тесты, финальный прогон успешен.
- Проверенный исходный artifact GitHub Actions `11761214458`: [InOneLine P11-K3 Windows QA ZIP](https://drive.google.com/file/d/1C1yOhC-zoSKH296YAVpEu9-8R4eQuOrh/view?usp=drivesdk), `InOneLine_P11K3_RULES_EDITOR_APPEARANCE_1.0.8_WINDOWS_QA.zip`, **46 795 474 байта**, SHA-256 `f0c70e162d26dd1e74972f7e3536528e862ada202ff198d8a8012f520c4ad2e1`, ZIP CRC PASS, ровно один `InOneLine_Setup_1.0.8.exe`, 47 655 977 байт. Метаданные Google Drive (размер, имя, тип и папка проверочных версий) подтверждены.
- **Ожидается отдельная ручная Windows-приёмка P11-K3.** Проверить: старые шаблоны/оформление после установки, пять настроек во вкладке «Оформление OBS», один общий Save, независимые оформления двух шаблонов, замена или сохранение как нового, переключение активного шаблона в текущем аукционе с немедленным изменением фона в браузере OBS, предпросмотр, отмену несохранённого, прежний глобальный режим показа и сохранение после перезапуска. При положительной приёмке выполнить чистое повышение семи проверенных Git-блобов с новыми Windows+wording тестами и сверкой на main. До приёмки PR #146 оставить черновиком и не объединять.

## P11-K3 — ручная приёмка и чистое повышение, 13 октября 2026

- Пользователь подтвердил «Всё работает. Принимаю Идём дальше.» в **2026-10-13 05:52:55 UTC**. **P11-K3 принят по ручной проверке на Windows**: единый редактор текста+оформления виджета правил, независимые параметры оформления каждого шаблона, смена во время аукциона, сохранение и старые параметры. Проверенный кандидат — [PR #146](https://github.com/ALL-EX-E/InOneLine/pull/146), точный HEAD `0e68eac9f468f73ff444fd74311dafabe22312de`. Полный native Windows Regression Foundation [38281866081](https://github.com/ALL-EX-E/InOneLine/actions/runs/38281866081) **SUCCESS** и Publication Wording `38281866030` **SUCCESS**.
- Ручная сборка: [InOneLine P11-K3 Windows QA](https://drive.google.com/file/d/1C1yOhC-zoSKH296YAVpEu9-8R4eQuOrh/view?usp=drivesdk), ZIP **46 795 474 байта**, SHA-256 `f0c70e162d26dd1e74972f7e3536528e862ada202ff198d8a8012f520c4ad2e1`, CRC PASS, каталог проверочных версий Google Drive подтверждён.
- Чистый перенос предусматривает **семь строго совпадающих исходных Git-блобов**: `.github/workflows/regression-foundation-1.0.8.yml=cc07b7947c9b5857e3d965c0f7da9169437c4418`, `streaming_manager/db/rules.py=fbcc63061eabf09732873948f2240ca550bc3d07`, `streaming_manager/views/rules_editor.py=4d9b29d2227ef8ec29654e2400fd0be577a32308`, `streaming_manager/views/stream.py=e535ed98ebd666655e2035cb4161e15aa2eb6431`, `tools/gui_regression_smoke.py=1d03ab8b932222a0b6a6eaff1a087df04ca909e6`, `tools/rules_editor_appearance_smoke.py=04b5c169c04c681f66d46f59bc530fbed7210b59`, `tools/rules_presentation_access_smoke.py=2634bf6ef325402fecd3eeb4a56dd1979f9319f7`. Три основных документа отдельно фиксируют приёмку. Перед объединением необходимы свежие успешные нативные Windows Regression Foundation и Publication Wording на точном HEAD повышения; затем squash с проверкой SHA, независимая сверка 7/7 blobs в main, закрытие исходного черновика #146 **без объединения**.
- **Следующий пункт после закрытия P11-K3:** проверить согласованную дорожную карту UI-060 на предмет незаконченных задач редактора правил и реального предпросмотра OBS. Не создавать параллельные источники и данные, не трогать незапрошенные механики аукциона. Новый шаг — отдельно, по обычному циклу автоматических и ручных проверок.

## P11-K3 закрыт, P11-K4: проверочная сборка — 13 октября 2026

- **P11-K3 принят** пользователем 2026-10-13 в 05:52:55 UTC: «Всё работает. Принимаю Идём дальше.» Чистое повышение [PR #148](https://github.com/ALL-EX-E/InOneLine/pull/148) завершилось в main коммитом `bb17c7bafe5471018da6f486d93a06e542dcf005`. Повторные native Windows Regression Foundation `38354065018` SUCCESS и Publication Wording `38354064988` SUCCESS на точном проверенном HEAD; **7/7** исходных проверенных Git-блобов независимо совпали после merge. Исходный черновик [#146](https://github.com/ALL-EX-E/InOneLine/pull/146) закрыт без объединения. P11-K3 полностью завершён.
- **P11-K4 — отдельный кандидат, вручную ещё не принят.** [Черновик PR #149](https://github.com/ALL-EX-E/InOneLine/pull/149), проверенный HEAD `8504c1ad201e8fb447426520d13a812f655b03af`, ровно семь файлов: `.github/workflows/regression-foundation-1.0.8.yml=ec9731434c672334d63eeca0a817ec4e76d69c02`; `streaming_manager/api_server.py=1e14715047575992d3af5758362105a99b779a53`; `streaming_manager/db/rules.py=e60e3cbd62406ce7c886464388e51c1f8e4e4b13`; `streaming_manager/views/rules_editor.py=77183cfd9ce07761d8f72796518dc4f067ac3cc0`; `streaming_manager/web/rules_overlay.html=d713a0eae93605009a5f74b34cdd58e5d5691b32`; `tools/gui_regression_smoke.py=2d3d446132d4de05b5459ccfc34c53dd903c2eef`; `tools/rules_selected_template_preview_smoke.py=3ce544eb3442ce1ec391952c682afd1729152d04`.
- **Назначение:** кнопка «Открыть предпросмотр OBS» в существующем редакторе показывает *сохранённую* версию **выбранного** шаблона, даже если этот шаблон неактивен и уже идёт аукцион. Передача через существующий `/rules-overlay?preview=1&template_id=N` и тот же HTML/JS-рендерер, без новой таблицы и без отдельного виджета. Только запрос к `/api/rules?preview=1&template_id=N` может читать другой шаблон; обычный `/api/rules` (и `/rules-overlay` в OBS) всегда показывает авторитетный текущий аукцион/активный шаблон. Неправильный ID даёт 400, отсутствующий — 404, формат оформления наследуется по исходным правилам, база/настройки/сессия при просмотре не изменяются. «Копировать URL» в редакторе по-прежнему копирует **обычную рабочую ссылку OBS**; незаписанный текст/цвет появится в предпросмотре после «Сохранить». Встраивание браузерного предпросмотра **внутрь редактора**, а не только открытие внешнего, остаётся отдельной последующей задачей UI-060.
- Для точного P11-K4 HEAD **Windows Regression Foundation 38354914010 SUCCESS**, **Publication Wording 38354914014 SUCCESS**. Новый HTTP тест `P11_K4_SELECTED_RULES_TEMPLATE_READONLY_PREVIEW_NO_ONAIR_CHANGE=PASS`; прошли старые GUI, OBS/Chromium, восстановление базы и запуск установщика.
- Проверенный артефакт GitHub Actions `11792037838` загружен в прежнюю проверочную папку Google Drive: [InOneLine P11-K4 Windows QA](https://drive.google.com/file/d/1u11LBo6JUiU3CQDvi9aikk6oLHgy0Ooe/view?usp=drivesdk); файл `InOneLine_P11K4_RULES_SELECTED_PREVIEW_1.0.8_WINDOWS_QA.zip`, размер **46 797 711 байт**, SHA-256 `e9e46f33b23b8ecc5f57add834af5202fb019643c75d3b488897267181650a64` (совпадает с GitHub Actions); проверка ZIP CRC PASS, **один** `InOneLine_Setup_1.0.8.exe` размером 47 658 226 байт. Google Drive подтвердил точное имя, размер, MIME и исходную папку QA.
- **Ожидается ручная приёмка P11-K4. Черновик #149 НЕ объединять.** Проверка пользователя: два шаблона с разным текстом/оформлением, A активен и показан в OBS при работающем аукционе; выбрать неактивный B без активации и нажать «Открыть предпросмотр OBS» — должен открыться B, а обычный OBS должен остаться на A. Обычная кнопка «Копировать URL» без `template_id`, сохранение/перезапуск, изменение сохранённых значений и отсутствие влияния на рабочий OBS. Только после явной приёмки — чистый перенос семи совпадающих Git-блобов с новыми Windows+wording проверками и SHA-сверкой в main.

## P11-K4 FIX2 — исправление по сообщению пользователя, 13 октября 2026

- Пользователь сообщил в **2026-10-13 06:35:30 UTC**: «При активном шаблоне если выбрать другой шаблон но не активировать его и предпросмотр и оверлей показывают один и тот же шаблон». Первоначальный P11-K4 кандидат и архив по прежней ссылке **не считать принятыми** и **не использовать для новой приёмки**. Исходная подготовка проверяла HTTP и Qt отдельно; отсутствовал сквозной тест двух реально работающих браузерных окон.
- Диагностика: старый кандидат прошёл дополнительный **сквозной Qt+Chromium тест** с А на рабочем OBS и неактивным Б в предпросмотре; ошибок серверного выбора не обнаружено. Выявлена **неоднозначность интерфейса**: предпросмотр на «Стрим / OBS» всегда показывает текущие правила, а кнопка редактора должна показывать выбранный шаблон. Нельзя утверждать, какой именно кнопкой пользовался человек. В FIX2 разделили подписи кнопок и добавили видимую строку «Предпросмотр: «Название» (активный/неактивный шаблон). Рабочий оверлей OBS останется без изменений», подсказку со ссылкой и проверку соответствия ID комбобокса загруженному шаблону, чтобы избежать тихого открытия неверного источника. Рабочий OBS URL и сохранение шаблонов не менялись.
- **Точный проверенный FIX2**: [draft PR #149](https://github.com/ALL-EX-E/InOneLine/pull/149) HEAD `e26e50e4026c99508e07b583b2bb73219ed7221f`; изменены ровно 9 файлов: `.github/workflows/regression-foundation-1.0.8.yml=b5a0b79932967504c53e3d669414fe7167be0426`; `streaming_manager/api_server.py=1e14715047575992d3af5758362105a99b779a53`; `streaming_manager/db/rules.py=e60e3cbd62406ce7c886464388e51c1f8e4e4b13`; `streaming_manager/views/rules_editor.py=13c51885c38f0eb93df4200563199ba1f97bf4e1`; `streaming_manager/views/stream.py=c4b4aa7906a32025f8150740c0edcd0b73c2c6f9`; `streaming_manager/web/rules_overlay.html=d713a0eae93605009a5f74b34cdd58e5d5691b32`; `tools/gui_regression_smoke.py=06e7f6f1c6c5c9cb26d7cb8d5b4c18408c4c46d7`; `tools/rules_selected_template_browser_smoke.py=36310a02af04d405f8d911302748ff83c2850ba1`; `tools/rules_selected_template_preview_smoke.py=3ce544eb3442ce1ec391952c682afd1729152d04`.
- Полный свежий [Windows Regression Foundation 38358877825](https://github.com/ALL-EX-E/InOneLine/actions/runs/38358877825) **SUCCESS**, Publication Wording 38358877874 **SUCCESS**. Проверено в логах: `P11_K4_SELECTED_RULES_TEMPLATE_READONLY_PREVIEW_NO_ONAIR_CHANGE=PASS`, `P11_K4_SELECTED_RULES_QT_CHROMIUM_END_TO_END_ISOLATION=PASS`, прежние P11-J/GUI/OBS/browser/backup и установщик PASS.
- **Актуальный QA архив — только FIX2:** [InOneLine P11-K4 FIX2 Windows QA](https://drive.google.com/file/d/1a2g1FU0xpasb29CD0KrvSzYvjjX3Vohk/view?usp=drivesdk); `InOneLine_P11K4_FIX2_SELECTED_TEMPLATE_PREVIEW_1.0.8_WINDOWS_QA.zip`; **46 803 000 байт**, SHA-256 `de7f04ea72eb7cfccdb9b1c41914945ff8d2938bb5b31cdf2ce806e5afac2353` (сверен и с GitHub Actions, и локально), ZIP CRC PASS, один `InOneLine_Setup_1.0.8.exe` 47 662 976 байт; Google Drive метаданные и папка QA сверены. Прежняя P11-K4 QA ссылка на архив `1u11LBo6JUiU3CQDvi9aikk6oLHgy0Ooe` **УСТАРЕЛА**.
- **ОЖИДАЕТСЯ ПОВТОРНАЯ РУЧНАЯ ПРОВЕРКА P11-K4 FIX2, черновик #149 НЕ объединён с main.** Проверка: полностью выйти из запущенного InOneLine перед установкой, открыть редактор правил, выбрать неактивный шаблон Б; под кнопкой должно отображаться «Предпросмотр: «Б» (неактивный шаблон)»; нажать «Предпросмотр выбранного шаблона» (именно **в редакторе**), в браузере проверить `preview=1&template_id=N` и текст/цвет Б; независимый «Предпросмотр текущих правил» на «Стрим / OBS» и реальный рабочий OBS должны показывать А. Не путать ссылки. При успешном подтверждении сделать clean promotion 9 точно проверенных Git-блобов со свежими Windows+wording CI и SHA-сверкой на main, закрыть исходный draft без merge.

## P11-K4 FIX3: живое следование предпросмотра выбору редактора — 13 октября 2026

- Пользователь 2026-10-13 в 07:32:40 UTC подтвердил частичную работу FIX2 и сообщил новый дефект: после того как ранее неактивный шаблон становится активным, **открытое окно предпросмотра продолжает показывать прежний шаблон**, хотя пользователь выбирает следующий неактивный. Поведение не связано с запуском аукциона. **P11-K4 FIX2 не принят вручную, его QA ZIP по ссылке `1a2g1FU0xpasb29CD0KrvSzYvjjX3Vohk` устарел.**
- **Причина установлена:** браузерный URL был постоянным снимком выбора `?preview=1&template_id=N`; после открытия окна смена шаблона в Qt больше не обновляла его ID. Отдельная кнопка «Предпросмотр выбранного шаблона» исправляла только начальный выбор. **FIX3:** одноразовый непредсказуемый `follow_token` для каждого открытого редактора, процессный словарь выбора с синхронизацией потоков и явным освобождением при закрытии редактора. Браузер по прежнему маршруту `/rules-overlay?preview=1&follow_token=...` раз в 500 мс читает **текущий выбор открытого редактора**, не меняя адрес окна, активный шаблон или снимок аукциона. После закрытия редактора токен удаляется; протухшая ссылка даёт `preview_expired`, не возвращает случайно рабочие правила. Устаревшая статическая ссылка с `template_id` остаётся доступной отдельно для обратной совместимости. Обычный рабочий `/rules-overlay` всегда использует авторитетный текущий источник OBS, никогда не читает временный токен. В database schema и app version нет изменений, только состояние процесса; не создавались таблицы, альтернативные маршруты, дополнительный источник или записи в SQLite.
- **Точный проверенный кандидат FIX3** — [draft PR #149](https://github.com/ALL-EX-E/InOneLine/pull/149), HEAD `3a760e30e6936dc40a29aaf8e1f2dd529b8b6edd`. Изменены ровно 10 файлов: `.github/workflows/regression-foundation-1.0.8.yml=b5a0b79932967504c53e3d669414fe7167be0426`; `streaming_manager/api_server.py=f7515f966231f3035a4369261222a7d3a1c145b8`; `streaming_manager/database.py=a5f78bd71eb6d945ebe642337cf1b091a6002929`; `streaming_manager/db/rules.py=5557f93e5199e97002f5fc9ea7df813186247ac6`; `streaming_manager/views/rules_editor.py=40847ab7e3e7385131e99c2b031777913c28d75e`; `streaming_manager/views/stream.py=c4b4aa7906a32025f8150740c0edcd0b73c2c6f9`; `streaming_manager/web/rules_overlay.html=56a2572e22f5ef5742bc02acc5492aa3f544eb7a`; `tools/gui_regression_smoke.py=015e7bbd3179bed6c6bb3828ad434e97fa0f694e`; `tools/rules_selected_template_browser_smoke.py=d7396da12b45102fe073306cd595d63b7a8fa9d7`; `tools/rules_selected_template_preview_smoke.py=3a7c00aceb84300b11b6abc83a938adf5fdcadd8`.
- Native [Windows Regression Foundation 38365071373](https://github.com/ALL-EX-E/InOneLine/actions/runs/38365071373) **SUCCESS** и Publication Wording 38365071397 **SUCCESS**. Новые проверки: `P11_K4_SELECTED_RULES_TEMPLATE_READONLY_PREVIEW_NO_ONAIR_CHANGE=PASS`, `P11_K4_SELECTED_RULES_QT_CHROMIUM_END_TO_END_ISOLATION=PASS`; тесты реального Chromium подтверждают переключения **Б → А → Б → А в той же вкладке**, в том числе после активации другого шаблона во время аукциона и после завершения аукциона. Существующие GUI/OBS/backup/installer smoke PASS. При первом запуске нового теста исправлен **только сам тест**: при смене активного шаблона закономерно изменяется порядок списка, поэтому тест теперь сравнивает состав ID, а не порядок; повторный полный прогон PASS.
- **Единственный актуальный Windows QA для проверки:** [InOneLine P11-K4 FIX3 Windows QA](https://drive.google.com/file/d/1KwkNonq56dwTvlFe7e3jHYcfVRt7lVHc/view?usp=drivesdk), файл `InOneLine_P11K4_FIX3_LIVE_RULES_PREVIEW_1.0.8_WINDOWS_QA.zip`, **46 811 540 байт**, SHA-256 `f4bd319e8d36f8cbde734a620d2107c48927ea73448be4ba79d900e74ea3b658` (локальная и GitHub SHA совпали), ZIP CRC PASS, один `InOneLine_Setup_1.0.8.exe` 47 671 706 байт, сохранено в исходной папке Google Drive QA, метаданные проверены.
- **ОЖИДАЕТСЯ ручная Windows-приёмка FIX3, PR #149 НЕ объединять.** Полностью выйти из InOneLine, установить FIX3, закрыть ранее открытые вкладки предпросмотра с фиксированным `template_id`, открыть из редактора новое окно «Предпросмотр выбранного шаблона». Затем **не переоткрывая** окно, переключать А ↔ Б в редакторе; предпросмотр автоматически должен следовать. Активировать Б во время аукциона: рабочий OBS станет Б; выбрать неактивный А: открытый предпросмотр должен стать А, а рабочий OBS остаться Б. Повторить без аукциона. Новый URL предпросмотра содержит `preview=1&follow_token=...`; обычная копируемая ссылка рабочего виджета не содержит токена. При успешной отдельной приёмке сделать clean promotion десяти точных Git-блобов с новыми Windows и wording CI и независимой SHA-сверкой в main, закрыть черновик без merge.

## P11-K4 FIX3 — живой предпросмотр следует за выбором, 13 октября 2026

- **Причина исправления:** пользователь сообщил в 2026-10-13 12:47:42 UTC, что уже открытый предпросмотр продолжает показывать ранее выбранный шаблон после активации и выбора другого неактивного шаблона; эффект вероятен также без запущенного аукциона. FIX2 оставлял URL предпросмотра закреплённым за ID, выбранным **на момент открытия**, поэтому поведение было закономерным, а не ошибкой передачи активного шаблона.
- **P11-K4 FIX3 — кандидат, требует новой ручной приёмки.** Код [draft PR #149](https://github.com/ALL-EX-E/InOneLine/pull/149), проверенный HEAD `3a760e30e6936dc40a29aaf8e1f2dd529b8b6edd`, **10 файлов**. Исправление добавляет временный непостоянный токен конкретного редактора с синхронизируемой выбранной записью в памяти единого Database; тот же браузерный Rules-виджет опрашивает текущий выбор по токену и автоматически обновляет существующую вкладку предпросмотра. Обычный OBS URL и текущий аукционный снимок по-прежнему не зависят от токена; после закрытия редактора токен очищается и API явно отвечает 404, не подставляя живой эфир. Прежний режим статического `?preview=1&template_id=N` сохранён.
- **Обязательная проверка реального Chromium+Qt усилена:** A активен и выводится в OBS, открытый предпросмотр показывает неактивный Б; переключение Б→А→Б в том же открытом окне, активация Б с обновлением только живого OBS, выбор неактивного А в ранее открытом окне предпросмотра и повторное переключение после закрытия аукциона — PASS. История и настройки без посторонних изменений. `P11_K4_SELECTED_RULES_QT_CHROMIUM_END_TO_END_ISOLATION=PASS`, `P11_K4_SELECTED_RULES_TEMPLATE_READONLY_PREVIEW_NO_ONAIR_CHANGE=PASS`.
- **На точном HEAD** [Windows Regression Foundation 38365071373](https://github.com/ALL-EX-E/InOneLine/actions/runs/38365071373) **SUCCESS**, Publication wording 38365071397 **SUCCESS**. Полная база, GUI, Chromium, OBS и инсталлятор SUCCESS.
- **Единственная актуальная сборка для нового тестирования:** [InOneLine P11-K4 FIX3 Windows QA](https://drive.google.com/file/d/14nF7-8JHuGoBSdnI_0gHbgwNvD_PueaP/view?usp=drivesdk), файл `InOneLine_P11K4_FIX3_LIVE_RULES_PREVIEW_1.0.8_WINDOWS_QA.zip`, 46 811 540 байт, SHA-256 `f4bd319e8d36f8cbde734a620d2107c48927ea73448be4ba79d900e74ea3b658` совпадает с GitHub Actions artifact `11796358219`, ZIP CRC PASS, ровно один `InOneLine_Setup_1.0.8.exe` размером 47 671 706 байт. Метаданные Google Drive (имя/размер/папка QA) сверены. FIX2 и ранний P11-K4 являются устаревшими кандидатами.
- **Требуется ручная проверка:** закрыть старую программу, установить FIX3, открыть предпросмотр неактивного Б **из редактора**, оставить окно браузера открытым; активировать Б, выбрать А без активации, далее Б и А; рабочий OBS всегда показывает активный, предпросмотр немедленно следует выделению. Повторить без активного аукциона. **PR #149 не объединять в main до отдельного подтверждения пользователя.** После принятия: чистый перенос только точных 10 проверенных Git-блобов, новый полный Windows/wording прогон и сверка main, исходный черновик закрыть без объединения.


## P11-K4 FIX3 — принят и перенесён в main (13 октября 2026)

- Пользователь подтвердил P11-K4 FIX3 ручной Windows-проверкой: «Всё работает. Идём дальше.» (2026-10-13 14:33:32 UTC). Испытанный кандидат draft PR #149, HEAD 3a760e30e6936dc40a29aaf8e1f2dd529b8b6edd; QA ZIP https://drive.google.com/file/d/14nF7-8JHuGoBSdnI_0gHbgwNvD_PueaP/view, SHA-256 f4bd319e8d36f8cbde734a620d2107c48927ea73448be4ba79d900e74ea3b658.
- Чистое повышение: PR #154 https://github.com/ALL-EX-E/InOneLine/pull/154, проверенный HEAD 872b31d8c0619413bb5fac9356cda785eb908dee. Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38414766876 SUCCESS (28 этапов); Publication Wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38414765926 SUCCESS.
- Squash merge в main: 137f72e89141ee66648945293a0c545a4d9dbae1. Независимая сверка итогового Git tree 16e5d587bc24ea6431fb8ba23abab6651c8ae385: все 10/10 blob SHA точно совпадают с принятым FIX3. Исходный draft PR #149 закрыт БЕЗ объединения. После merge запущен Windows run 38415746674; Publication Wording 38415746804 SUCCESS.
- Статус: P11-K4 FIX3 USER PASS / CLEAN MERGED / EXACT 10-of-10. FIX2 устарел. Живой браузерный предпросмотр следует выбранному шаблону, а рабочий OBS независимо показывает активный.
- Следующий участок P11/UI-060: локальный live-preview конечного OBS-оформления непосредственно в большой редактируемой области правил; не путать его с уже готовым независимым браузерным предпросмотром сохранённого шаблона. Перед маленьким кандидатом провести exact-current source review общего renderer/media и QTextEdit; не создавать второй rules/style backend и не начинать P12 до закрытия P11.


## P11-K5 FIX1 — принят и закрыт; P11-K6 следующим (13 октября 2026)

- Пользователь подтвердил ручную проверку объединённого редактора и локального предпросмотра: «Всё работает. Идём дальше.» (2026-10-13 15:48:36 UTC). Принималась только FIX1, а не первая сборка P11-K5.
- Проверочная сборка FIX1: https://drive.google.com/file/d/1eNSERccqNVgEl_9ZRVvCIoLF-XtqSomj/view?usp=drivesdk; GitHub artifact #11827802080, архив 46,803,290 байт, sha256 4c67f957ce2e99620f7e972a52215aa4a6cbee2ab488329c5e768741c68fb56e; exact candidate commit 395826a3aa46fbed36bd7c670a1dbb0e0225a19c (draft PR #156).
- Принятая реализация: ровно одно редактируемое QTextEdit с live color/opacity/inset preview и постоянно доступная панель OBS, горизонтально в широком окне / вертикально при узком; общие Save, Activate и независимый браузерный контроль сохранённого шаблона неизменны.
- Clean promotion PR #157, promotion HEAD 38ee274714337a90c18b62c4e92e6d3f16e0ee34: fresh Windows Regression Foundation 38425433218 SUCCESS (29/29) и Publication Wording 38425433701 SUCCESS. Squash merge в main: f96bce865503872484798a8ad6599f2bca844763; дерево dddf63edd674daa06f738b6a3170a4008df7bbac, 5/5 исходных Git blob SHA совпадают с ручным кандидатом. Исходный draft PR #156 закрыт без merge. После merge запущен Windows 38426216899; wording 38426216870 SUCCESS.
- P11-K5 FIX1 **CLOSED / USER PASS / CLEAN MERGED / 5-of-5 SHA**. Следующий изолированный P11-K6/UI-060: удалить пользовательское поле «Внутренний отступ» и в HTML Browser Source / локальном Qt редакторе использовать единый разумный responsive padding, который меняется при resize. Старое поле padding в persistence можно оставить для совместимости без миграции, но оно не должно управлять видом и появляться в UI. Не объединять этот шаг с glow, round corners, media backgrounds, show-mode или OBS/business mutation. Все регрессии исправить под новую superseding UX-политику; следующий кандидат — только после полного Windows CI и ручной QA.


## P11-K6 / UI-060 — автоматический отступ правил; Windows QA готов, ручная проверка ожидается (2026-10-13)

- Из принятой P11-K5 FIX1 (clean main f96bce865503872484798a8ad6599f2bca844763) начат отдельный P11-K6: UI «Внутренний отступ» удалён, Qt редактор и Browser Source используют одинаковый bounded responsive inset 8–24 px по формуле clamp(8px, 2.2vmin, 24px). Qt реагирует на фактический resize viewport, включая splitter; Chromium CSS реагирует на размер Browser Source; автоперенос и прежняя прокрутка сохранены.
- Сохранённые legacy значения padding в schema20/presentation_json и session snapshots НЕ удалять и не мигрировать; они более не управляют отображением. Сохраняются текущие текст+показ виджета+OBS, общая кнопка Save и независимый browser preview. Ни фон media, ни скругление, ни glow не включены в этот этап.
- QA candidate draft PR #159 https://github.com/ALL-EX-E/InOneLine/pull/159, точный HEAD 8ed0348d3b961ac047b5f12bd81f84e19d630dd7, ровно пять исходных/тестовых файлов.
- Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38427154424 — SUCCESS 29/29, Publication Wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38427154060 — SUCCESS; browser (активный против выбранного), Qt редактор и legacy сохранение проверены.
- Фактический Google Drive QA ZIP: https://drive.google.com/file/d/1RPvYEf7LWXULgXrxkKPJNUf0qu4eaUJG/view?usp=drivesdk, InOneLine_P11K6_RESPONSIVE_RULES_PADDING_1.0.8_WINDOWS_QA.zip, 46,796,214 bytes, GitHub sha256 6ae17411a07dcca2c0749a7f418d6bdb8999b2d50b716b8bbf65310673a01426; имя/размер/папка Drive сверены.
- Статус: NATIVE WINDOWS PASS / USER MANUAL QA PENDING / DRAFT #159 НЕ МЕРДЖИТЬ. После ручной приёмки — clean promotion пяти exact blobs с новым CI. Затем отдельное P11-K7/UI-060 для скругления/glow, затем shared media backgrounds; P12 только после завершения P11.


## P11-K6 закрыт; P11-K7 rounded glow кандидат ожидает ручную QA (2026-10-13)

- Ручное подтверждение пользователя P11-K6: «Всё работает. Идём дальше.» (2026-10-13 16:59:11 UTC). Принят P11-K6 adaptive inset, кандидат 8ed0348d3b961ac047b5f12bd81f84e19d630dd7 и архив https://drive.google.com/file/d/1RPvYEf7LWXULgXrxkKPJNUf0qu4eaUJG/view; не возвращать «Внутренний отступ» в UI.
- Clean promotion PR #161, HEAD 8500f7f8b9d2f8073b0a4844f47f3c5c56eee735, fresh Windows Regression Foundation 38435142366 SUCCESS (29/29), Publication Wording 38435142454 SUCCESS. Объединён squash в main 304575bc21d7e5f2c6e807995972a83eb783f144. Проверено exact 5/5 candidate blobs, дерево bba59757360e9a15349fe3a8c960b244644b928f. Исходный draft #159 закрыт БЕЗ MERGE. Postmain Windows Regression Foundation 38435918062 SUCCESS, Publication wording 38436022629/38435918027 SUCCESS.
- Следующий отдельный P11-K7/UI-060: скруглённый 8px контейнер Rules Overlay и общая трёхслойная подсветка контура с пользовательским переключателем и выбором цвета; одни настройки в composite rules template и редактируемом Qt preview/OBS. Никакой отдельной настройки радиуса/blur, второй style backend, отдельного media background или изменения аукционной логики. Старые пять полей presentation JSON остаются валидны наряду с новыми семью; миграции схемы не нужны.
- P11-K7 кандидат draft PR #162 https://github.com/ALL-EX-E/InOneLine/pull/162, точный HEAD 9f0a36072b723912398756bd369effa9809eb804, семь изменённых файлов. Windows Regression Foundation 38436617029 SUCCESS 29/29; Publication wording 38436616990 SUCCESS. В том числе DB compatibility, Qt WYSIWYG/save/clone, real Chromium active/inactive isolation PASS.
- Актуальный P11-K7 ZIP: https://drive.google.com/file/d/1_iRSmj5E01by35kZPvZwXXHKu1-A4X8J/view?usp=drivesdk, InOneLine_P11K7_RULES_ROUNDED_GLOW_1.0.8_WINDOWS_QA.zip, размер 46,825,981 байт; digest GitHub artifact #11832554504 sha256 215d9652d1fde557e1493df7cf133089007756a8acd22619035f89bbf52d1f9c. Метаданные файла и QA-папка Google Drive проверены.
- **Статус P11-K7: AUTOMATED PASS / USER MANUAL PENDING; PR #162 не объединять до явной приёмки.** После ручного PASS: clean promotion семи exact Git blobs, свежие Windows/wording, сверка на main, исходный draft без merge. Следующий отдельный подэтап P11/UI-060 — custom media background из общей MEDIA_CATEGORY_OVERLAY_BACKGROUNDS; P12 преждевременен.


## P11-K7 принят и закрыт; следующий P11-K8A общий фон правил (14 октября 2026)

- Ручная Windows-приёмка P11-K7 от пользователя 2026-10-14 12:46:34 UTC: «Всё работает. Идём дальше.» Проверен candidate draft #162, HEAD 9f0a36072b723912398756bd369effa9809eb804, ZIP https://drive.google.com/file/d/1_iRSmj5E01by35kZPvZwXXHKu1-A4X8J/view, QA SHA256 215d9652d1fde557e1493df7cf133089007756a8acd22619035f89bbf52d1f9c.
- P11-K7 clean-promotion #164: head 9f7b55b2676d1b92208c5581e0a2dda3b5649607, Windows Regression Foundation 38566600986 SUCCESS (29/29) и Publication Wording 38566601036 SUCCESS; merge main 41e392f13c40630bfdc19c7c132c3f02466e2237; дерево 2fa0dd5acc2cf626bda70a30087b5b61200fc3de, exact семь из семи blob SHA проверены. Исходный draft #162 закрыт без merge. После merge main Windows 38567301048 SUCCESS, wording 38567301415/38567503897 SUCCESS. P11-K7 USER PASS / CLEAN MERGED / CLOSED.
- Следующий P11-K8 (UI-060 custom/shared background) делится для ручной проверки: сначала **K8A**: выбор уже зарегистрированных статических изображений PNG/JPG/JPEG/WEBP из существующей категории MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, локальный Qt still-image и реальный OBS Browser Source через защищённый `/media/<id>` с проверками category/availability, per-template сохранение в той же presentation JSON без новой схемы. Дополнение режима `Свой` не добавляет отдельную библиотеку или дублирующий importer.
- K8A candidate draft PR #165 https://github.com/ALL-EX-E/InOneLine/pull/165, разработка/Windows CI продолжается; до ручного PASS НЕ ОБЪЕДИНЯТЬ. Для K8A добавление файлов пока выполняется существующим importer на `Стрим / OBS → Фон оверлея`, а не в диалоге правил.
- Оставшиеся независимые части P11-K8: подключить штатный managed/external import flow с дедупликацией непосредственно из редактора, затем полноценный live preview GIF/video (без второго backend), Browser Source video muted/autoplay/loop и missing-file semantics. После полного P11/UI-060 перейти к P12; не обгонять ручную QA.


## P11-K8A — общий фон правил: Windows QA готова, ручная приёмка ожидается (2026-10-14)

- Ранее P11-K7 принят пользователем и чисто объединён в main как `41e392f13c40630bfdc19c7c132c3f02466e2237`, проверены 7/7 SHA; после merge Windows regression 38567301048 SUCCESS. Дорожная карта сохраняет P11/UI-060 до полного оформления фонов.
- P11-K8A ограничен статическими PNG/JPG/JPEG/WEBP из существующей `MEDIA_CATEGORY_OVERLAY_BACKGROUNDS`, без второй библиотеки или импортера. Режим «Свой» и выбор имеющегося зарегистрированного изображения в одном редакторе; локальный editable Qt still image и безопасный браузерный `/media/<id>`, availability/category проверки, шаблоны active/preview изолированы. Новые медиа ID сохраняются в существующем composite presentation JSON (поддержка legacy 5/7-key) без схемных изменений.
- Черновик PR #165 https://github.com/ALL-EX-E/InOneLine/pull/165, final QA HEAD `b2bdcbb0da4c041a798b48ccb4c0aa24128385ce`, 7 изменённых исходных/тестовых файлов. Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38568916254 SUCCESS 29/29; Publication Wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38568916646 SUCCESS.
- Актуальная проверочная Windows сборка: https://drive.google.com/file/d/1XtLXQG8LvoElqwAmHT8Ub2b8Q0bBXgov/view?usp=drivesdk, InOneLine_P11K8A_SHARED_RULES_IMAGES_1.0.8_WINDOWS_QA.zip, 46,813,371 bytes, GitHub artifact #11895894953 sha256 de9647f9a79092e3f82631446bfb61abd07ed1fc340bf37d4e6f561ce44d25bc; Drive имя, размер и QA-папка подтверждены.
- Статус: NATIVE WINDOWS PASS / USER MANUAL PENDING / draft #165 НЕ МЕРДЖИТЬ. После явного PASS чисто перенести 7 exact Git blobs с новыми Windows/wording. Отдельные последующие K8 части: подключение существующего managed/external импортера непосредственно в редактор правил и GIF/video с локальным live-preview. P12 не начинать до закрытия P11.


## P11-K8A принят и чисто объединён; P11-K8B общий импорт через редактор (2026-10-14)

- Пользователь подтвердил ручной Windows QA PASS P11-K8A: «Всё работает. Идём дальше.» (14 октября 2026, 13:32:59 UTC). Испытанный кандидат draft #165, exact HEAD b2bdcbb0da4c041a798b48ccb4c0aa24128385ce, проверочный ZIP https://drive.google.com/file/d/1XtLXQG8LvoElqwAmHT8Ub2b8Q0bBXgov/view, SHA256 de9647f9a79092e3f82631446bfb61abd07ed1fc340bf37d4e6f561ce44d25bc; native Windows 38568916254 и wording 38568916646 SUCCESS.
- Clean promotion #168, head 6cec25c6e120c02e27718b1fcd3b5457a12cf024; fresh Windows 38572934048 SUCCESS 29/29, Publication Wording 38572934225 SUCCESS. Squash merge main 301eae825c278c7cf557745996c01e61ff3e1edd; Git tree 19e3fe0eefaffd952a81fda36dc9162fe3c72c5a; independently exact 7/7 source blobs matched accepted candidate. Original draft #165 closed WITHOUT MERGE. Postmerge Windows regression initiated. K8A USER PASS / MERGED / CLOSED.
- K8A limited static registered PNG/JPG/JPEG/WEBP background selector from existing MEDIA_CATEGORY_OVERLAY_BACKGROUNDS with secure /media/<id>, no parallel media import, no schema or auction logic change.
- Next separate P11-K8B draft #169 https://github.com/ALL-EX-E/InOneLine/pull/169: «Добавить фон…» inside modal Rules editor must call the **existing** Stream/OBS managed/external importer through MainWindow/AuctionTab callback. No new file database, importer, directory or settings; preserve dedup, external/managed transition and availability. Changes apply only to current unsaved Rules template, not other OBS widgets or active on-air Rules until Save/Activate. Qt modal picker/storage/duplicate notices must belong to Rules dialog. K8B remains still images only; GIF/MP4/WEBM are deferred to independent K8C.
- Status K8B: CODE CANDIDATE/CI IN PROGRESS, MANUAL QA PENDING, DRAFT #169 MUST NOT MERGE before successful native Windows CI, Google Drive QA ZIP and user's explicit acceptance. P12 starts only after P11/UI-060 closure.


## P11-K8B FIX1 принят; P11-K8B FIX2 — убрать лишнюю кнопку (2026-10-14)

- Пользователь проверил Windows FIX1 с живым изображением в редактируемом поле правил и обновлением браузерного предпросмотра без сохранения: «Всё работает» (14 октября 2026, 15:02 UTC). В той же беседе пользователь уточнил, зачем нужна кнопка «Обновить», и принял предложение её удалить: «Да. Давай. Делаем.» (15:03 UTC).
- Exact accepted P11-K8B FIX1 QA draft PR #169 `db82cfef88b4c5059987e00ce8833caa79f0d5bc`; проверенная сборка `InOneLine_P11K8B_FIX1_LIVE_RULES_MEDIA_PREVIEW_1.0.8_WINDOWS_QA.zip` https://drive.google.com/file/d/1uMKQ2-1cRunCONVsphC45ga2JKcyZYLZ/view?usp=drivesdk, 46,811,380 bytes, artifact SHA256 `186d559b9265cbe84600c3a188829b64a596bcb0e56eb8746c278596962197ee`. Windows CI 38584152282 PASS 30/30, wording 38584151973 PASS.
- Чистое принятие через PR #171, promotion HEAD `de9626785b705ce5f0a6f33703cd8e1510707504`, fresh Windows 38586254201 SUCCESS 30/30 и wording 38586254406 SUCCESS. Squash main `c894b9a1a475dc4c87bed85557c36e987782b645`, tree `8d33b759f1c1e42590137c2666becd43cd8362e4`, все 12/12 blob SHA совпадают с ручной сборкой. Исходный draft #169 закрыт WITHOUT MERGE.
- Следующий узкий P11-K8B FIX2: удалить только кнопку «Обновить» рядом с выбором фонового изображения. Сама синхронизация общей медиабиблиотеки остаётся автоматической при создании редактора, переключении шаблонов и завершении импорта; изменение выбора фона по-прежнему сразу обновляет Qt и браузерный предпросмотр без Save, а OBS использует активный сохранённый шаблон. Без изменений схемы, импорта, аукционной логики или медиафоновой инфраструктуры.
- FIX2 отдельный draft PR #173 https://github.com/ALL-EX-E/InOneLine/pull/173, exact HEAD `1168e8ccfbdc2629da33969e4cd73a67258ed463` (3 changed files: rules_editor.py и два Qt/Chromium smoke); Windows CI и Google Drive QA установщик готовятся, ручная QA пока не проводилась. Временный PR #172 закрыт без merge, потому что был создан до squash предыдущей FIX1 и показывал лишние изменения.
- Статус: P11-K8B FIX1 USER PASS / CLEAN MERGED / CLOSED; P11-K8B FIX2 NATIVE CI IN PROGRESS / USER QA PENDING / DO NOT MERGE. После FIX2 продолжить P11-K8C (GIF/видео в том же общем media реестре), затем P12 строго после полного P11.


## P11-K8B FIX2 принят и закрыт; P11-K8C — отдельный GIF/video кандидат (2026-10-14)

- Пользователь проверил установленную Windows FIX2 сборку и явно подтвердил: «Проверил. Работает. Идём дальше.» (14 октября 2026, 15:48 UTC). Проверенный QA ZIP: https://drive.google.com/file/d/1CT0X0s5Um4u5DRA26cP43392BucXXtpT/view, `InOneLine_P11K8B_FIX2_NO_REFRESH_BUTTON_1.0.8_WINDOWS_QA.zip`, 46,813,351 bytes; исходный draft #173 HEAD `1168e8ccfbdc2629da33969e4cd73a67258ed463`.
- FIX2 clean promotion #175 https://github.com/ALL-EX-E/InOneLine/pull/175, exact promotion HEAD `d67e540734d0e77ebda733b89efaba7b4d3354ec`. Fresh native Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38592835253 SUCCESS (30/30), Publication wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38592835030 SUCCESS. Exactly three expected Git blobs individually verified. Squash merge into main `88ba91677106b580f5bc7db0b4137e54a842931f`. Original draft #173 closed WITHOUT MERGE.
- FIX2 user-visible contract: button `Обновить` no longer exists; shared background catalog automatically synchronizes on Rules editor open, template selection and `Добавить фон…`. Current unsaved template drives ONLY the editor/local/browser preview; live OBS keeps the saved active template until Save/Activate. No schema, media importer or auction state mutation.
- Next independently testable **P11-K8C**: GIF/MP4/WEBM Rules background in that same overlay-background media registry, with true local editable Qt GIF/video frames and muted/looped/autoplay OBS Browser Source. Missing-file fallback and active-versus-selected separation must stay intact. Initial QA-only draft #176 https://github.com/ALL-EX-E/InOneLine/pull/176, head `f8ddc09d4ab6ac7f36d5c545448bbd563c227b54`; five source/test/workflow files. No new schema, duplicate media library, importer or independent Rules renderer. Native Windows CI and manual real-media QA required before promotion.
- Status: **P11-K8B FIX2 USER PASS / CI PASS / CLEAN MERGED / CLOSED**; **P11-K8C CANDIDATE / MANUAL USER QA PENDING / DO NOT MERGE**. P12 remains blocked until P11 full closure.


## P11/UI-060 полностью принят и закрыт; следующий этап P12 (2026-10-16)

- Пользователь подтвердил установленную QA-сборку P11-K8C с GIF/MP4/WEBM и исправлением обрезанной кнопки «Цвет текста»: «Всё работает. Идём дальше.» (16 октября 2026, 14:45:51 UTC). Проверенный ZIP: `InOneLine_P11K8C_UIFIX1_TEXT_COLOR_1.0.8_WINDOWS_QA.zip`, https://drive.google.com/file/d/1Mydk9MZcjrHPaY7so5rIvW6hXT3DREXx/view?usp=drivesdk, Drive size 46 821 393 bytes. Source QA draft [#176](https://github.com/ALL-EX-E/InOneLine/pull/176) HEAD `6c86ad3235168991021eca68ad54247995d227fb`; исходный черновик закрыт **без merge**.
- Чистое продвижение [PR #178](https://github.com/ALL-EX-E/InOneLine/pull/178) из точно семи Git-блобов на прежний main `0bb482df9df947b66631228ea9397c9a243285cd`. Promotion HEAD `bb9a8b8e5704384dacfdc3a56f47a506b4efbb1d`; fresh Windows Regression Foundation [38918602829](https://github.com/ALL-EX-E/InOneLine/actions/runs/38918602829) SUCCESS (31/31); publication wording [38918602965](https://github.com/ALL-EX-E/InOneLine/actions/runs/38918602965) SUCCESS. Squash main `e53b2c330ad9dae7f2decc6eb60393cc96fd4e8a`, independently verified exact 7/7 Git blobs.
- **P11 завершён**: Rules one editable QTextEdit, selected browser preview independent from active OBS, unified shared background library/import, still/GIF/video silent-loop live Qt/Browser, automatic safe transparency when missing, rounded/glow, responsive inset, scrolling, per-template Save/Activate. Qt text-color label has adequate precomputed width even at minimum window.
- **Следующий P12** — UI-051 (одна Auction page/одна таблица лотов без скрытого дубликата), затем UI-052 единая «Как работает аукцион?» и UI-056/UI-059 корректный live-search/Enter/prestart versus active-session scope; UI-057 «Ставки / История» постоянно видны. Выполнять небольшими отдельными кандидатами; никаких изменений аукционного business state/rate/RNG/winner logic. P13 не начинать до P12 QA/приёмки.


## P12-A принят и закрыт; P12-B единая справка ожидает ручную QA (2026-10-16)

- Пользователь явно принял установленную P12-A Windows QA сборку: «Всё работате. Идём дальше.» (16 октября 2026, 16:18:58 UTC). Исходный [черновик #180](https://github.com/ALL-EX-E/InOneLine/pull/180) exact HEAD `2e6df359c653c337927babbb3eb50fd78fb33c0f`, ZIP `InOneLine_P12A_ONE_AUCTION_PAGE_1.0.8_WINDOWS_QA.zip` https://drive.google.com/file/d/1qiTNPi2NCmsFXtpUClXFsnUHLoSdy5N_/view?usp=drivesdk, Drive size 46 814 264 bytes.
- Чистое повышение [PR #181](https://github.com/ALL-EX-E/InOneLine/pull/181), promotion HEAD `6d0a0bf340478a88f22f86009319e050e71ff7f2`, семь точных Git-блобов 7/7. Fresh native Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38931118515 **SUCCESS**, publication wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38931118665 **SUCCESS**. Squash в main `33135aba3f456298987520030ea2046359ba0e16`; после merge повторная сверка 7/7. Исходный #180 закрыт без merge.
- Принято P12-A: одна страница Аукцион и одна физическая QTableWidget вместо Лоты/Проведение, единый счётчик `Лотов: N`, поиск `Поиск по лотам…` и Enter, до аукциона синхронизация с Список/Публичный список, при активной сессии поиск по её составу и временным лотам без изменений других списков; существующий Ставки/История блок и business-состояния сохранены. Не создавать второй table/backend и не возвращать дублирующую вкладку.
- Следующий изолированный P12-B/UI-052: [черновик #182](https://github.com/ALL-EX-E/InOneLine/pull/182), exact QA HEAD `bc85d3f2930e445ad1bf16dd327579f2880669d1`. Объединённая встроенная справка `Как работает аукцион?` / `Скрыть справку`, прежние правила формирования лотов, режимы и ставки, без implementation терминов; прежний редактор `Правила аукциона` сохранён; устаревшие сообщения `на вкладке Проведение` исправлены. Ровно три файла, без изменения схемы и аукционного backend.
- P12-B native Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38932210085 **SUCCESS** (31/31), wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38932210342 **SUCCESS**. ZIP `InOneLine_P12B_AUCTION_HELP_1.0.8_WINDOWS_QA.zip`, https://drive.google.com/file/d/1Qtrt187oYXOn5CP7Z_Eb-RETbtPPjjjq/view?usp=drivesdk, metadata Drive size 46 815 753 bytes. **P12-B MANUAL USER QA PENDING / DRAFT НЕ МЕРДЖИТЬ** до явной приёмки пользователя. UI-074 OBS-only auto-scroll и другие P12 review-пункты остаются в очереди; P13 не начинать до закрытия P12.


## P12 завершён и принят; P13-A quick timer preview ожидает QA (2026-10-16)

- Пользователь 16.10.2026 в 17:42:05 UTC явно подтвердил «Отлично. Тогда продолжаем. Всё текущее принимаю». Это принятие установленной QA-сборки P12-B HELP FIX2 `InOneLine_P12B_FIX2_HELP_WORDING_1.0.8_WINDOWS_QA.zip`, https://drive.google.com/file/d/1-QK-3RKLIGk4HZKh4c5QgYl-HeOfuo0y/view?usp=drivesdk, Drive 46 828 959 bytes. Исходный черновик [#182](https://github.com/ALL-EX-E/InOneLine/pull/182) HEAD `ecfe2cf9a8225acfe29e198b8610c698def7fcb3` закрыт **без merge**.
- Принятая справка «Как работает аукцион?» описывает существующие статусы/лот-состав, текущие ставки, ничью, колесо, таймер и OBS; первая фраза пользовательская, неверная отдельная строка «ДЛЯ АУКА» удалена. Логика ставок, wheel, схема БД и настройки не изменены.
- Clean promotion [#184](https://github.com/ALL-EX-E/InOneLine/pull/184) проверенных 3/3 Git-блобов; fresh native Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38941853907 **SUCCESS (31/31)**, wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38941854066 **SUCCESS**. Squash main `39a1e9b49e55847ab6de17ebea4a4434267603b7`, sha 3/3 повторно сверены после merge.
- **P12/UI-051/UI-052/UI-056/UI-059 закрыты**: одна страница Auction, одна физическая lot-table/одно поле live-search, prestart синхронизированный поиск/Enter, running session-only scope, сохранённый always-visible блок UI-057 `Ставки / История`, встроенная единая справка и старый Rules editor. Не вводить вторые таблицы/backend.
- **P13-A/UI-053** — следующий маленький draft [#185](https://github.com/ALL-EX-E/InOneLine/pull/185), exact HEAD `ddca1c6db600783f234f9a781196b2ee5c735ba7`: добавить на рабочую страницу Auction рядом с копированием URL кнопку `Открыть предпросмотр таймера` с уже существующим `/timer-overlay?preview=1` из Stream/OBS. Два файла, никакой новой логики таймера, OBS маршрута и изменённого winner/audio/RNG. **WINDOWS / MANUAL QA PENDING, NO MERGE** до явной приёмки. Дальнейшая перестановка blocks и contextual soundtrack выполняются отдельно.
- Утверждённое изменение **UI-072/P16**: wheel minimum 1 секунда (верх 24 часа) вместо текущих 3 секунд. Runtime до P16 остаётся с `AuctionSessionMixin.WHEEL_MIN_DURATION_MS = 3000`; подготовка вращения ~1,2 с должна оставаться вне пользовательской длительности. Не изменять одну границу без комплексной P16 synchronization.


## P13-A принят; P13-B/UI-062 перемещение локального колеса — QA ожидается (2026-10-16)

- Пользователь подтвердил установленную P13-A QA-сборку 2026-10-16 в 18:27:59 UTC: «Всё работает. Идём дальше.» Архив `InOneLine_P13A_AUCTION_TIMER_PREVIEW_1.0.8_WINDOWS_QA.zip` https://drive.google.com/file/d/1jI4-A_3BCaLLGytmUZwqOnjt1w0B2IE-/view?usp=drivesdk, Drive размер 46 822 406 байт; исходный draft [#185](https://github.com/ALL-EX-E/InOneLine/pull/185) HEAD `ddca1c6db600783f234f9a781196b2ee5c735ba7` закрыт **без merge**.
- Чистое продвижение [PR #187](https://github.com/ALL-EX-E/InOneLine/pull/187), promotion HEAD `20d4d1e02dc4ad5c273f341a16a1b00ffa9f6fa1`: точно два принятых Git-блоба. Fresh Windows Regression Foundation https://github.com/ALL-EX-E/InOneLine/actions/runs/38947723175 **SUCCESS**, wording https://github.com/ALL-EX-E/InOneLine/actions/runs/38947723147 **SUCCESS**. Squash main `cc196f472fab783c76f2cdbae364dbad427fbcbc`; после merge повторная сверка 2/2 точных blob SHA.
- P13-A/UI-053 **ACCEPTED/CLOSED**: кнопка `Открыть предпросмотр таймера` рядом с `Копировать URL таймера` вызывает штатный `/timer-overlay?preview=1`, работает с единственным общим таймером; никаких новых источников, смены поведения RNG/таймера и сохранённых настроек.
- **P13-B/UI-062 первая часть — draft [#188](https://github.com/ALL-EX-E/InOneLine/pull/188), QA PENDING.** Точно две файлообласти: `auction.py` и `gui_regression_smoke.py`, source candidate `e2a7d04d1c233a10da2543c5aa6072a7674e25a3`. Перемещение единственного имеющегося локального wheel_panel из нижней третьей колонки рядом с lot-table/Ставки/История в верхнюю область рядом со способом победителя; колесо сохраняет текущую conditional visibility. Нижний content layout остаётся ровно `Список лотов + Ставки/История`. Не создавать второй Wheel или OBS renderer, не менять звук, RNG, session, победителя, время. Существующие wheel soundtrack controls остаются при panel до отдельного UI-071.
- UI-062 поднятие общего timer block, UI-071 перенос **существующих** двух наборов soundtrack controls и UI-073 визуальная унификация — следующие отдельные QA steps после принятия текущего; **P16/UI-072** минимум wheel 1 секунда остаётся запланированным, сейчас 3 секунды.

## P13-B FIX1 закрыт; следующий P13-C/UI-071 — 17 октября 2026

- 2026-10-17 05:05:21 UTC: установленный P13-B FIX1 принят пользователем «Всё отлично. Всё работает. Идём дальше.». Исправленная двухколоночная компоновка: method+wheel слева, общий timer справа, compact stack; кнопки ▲/▼ всегда в горизонтальном ряду с объёмом.
- Exact accepted QA HEAD `ec63fbe66d2d8ff3d2a449d4388a439d33ff9773`, QA https://drive.google.com/file/d/1d9jiVbvs5eYhb5_gchaZbN5w3DIHI6G_/view, 46 823 566 bytes; native Windows [39004329318](https://github.com/ALL-EX-E/InOneLine/actions/runs/39004329318) PASS (31/31).
- Clean promotion [#190](https://github.com/ALL-EX-E/InOneLine/pull/190), fresh Windows [39005058988](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005058988) SUCCESS, wording [39005058984](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005058984) SUCCESS; squash main `f8a59ecb242876a02879cc1ca82a4bac786db2c4`; exact 3/3 Git blobs совпали. Исходный QA draft [#188](https://github.com/ALL-EX-E/InOneLine/pull/188) closed WITHOUT MERGE.
- Next P13-C/UI-071 only: move existing wheel soundtrack controls from wheel panel into shared timer and preserve contextual auction/wheel visibility, selections, imports, volume/mute, audio routing and state. No timer-duration/RNG/winner changes; UI-073/P16 separate.

## P13-C/UI-071 Windows QA готова; ручная приёмка ожидается (17 октября 2026)

- Отдельный черновик [PR #191](https://github.com/ALL-EX-E/InOneLine/pull/191), exact source HEAD `8b7515e9fcd87413155015087fe0f9068ac4e0fc`, три файла: `streaming_manager/views/auction.py`, `streaming_manager/views/auction_parts/audio.py`, `tools/gui_regression_smoke.py`. Существующий `wheel_soundtrack_widget` физически перенесён из локального wheel panel в общий `timer_widget`; `auction_soundtrack_widget` остаётся там. Два независимых набора saved selection/volume/mute не дублируются и показываются контекстно по текущему состоянию Max Amount / Wheel. Аудиомаршрут, таймер, OBS, логика аукциона, база и RNG не менялись.
- Exact Windows Regression Foundation [39005511816](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005511816) SUCCESS (31/31), publication wording [39005511761](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005511761) SUCCESS. Проверочная сборка `InOneLine_P13C_UI071_CONTEXTUAL_SOUNDTRACK_1.0.8_WINDOWS_QA.zip`: https://drive.google.com/file/d/1y_G_uwvY9WdGQ5KKMrXm7_-ClmUY43an/view, размер 46 826 173 байта, SHA256 `55ef1765bc1e0d98ce309f601ab7abc1e6b338ebcc432b24702766f19be0e618`; CRC PASS, один `InOneLine_Setup_1.0.8.exe`.
- **P13-C AUTO PASS / USER MANUAL QA PENDING / DRAFT НЕ ОБЪЕДИНЯТЬ до явного подтверждения.** После ручной приёмки выполнить отдельное clean promotion exact blobs с новым Windows CI и проверкой. P13-D/UI-073 визуальная унификация таймера, P16/UI-072 минимум 1 сек и прочие пункты остаются дальше.

## P13-C/UI-071 принят; следующий P13-D/UI-073 — 17 октября 2026

- Пользователь принял установленную P13-C/UI-071 QA-сборку 2026-10-17 05:27:33 UTC: «Всё работает. Идём дальше.» Exact проверочная ветка HEAD `8b7515e9fcd87413155015087fe0f9068ac4e0fc`, Windows Regression Foundation [39005511816](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005511816) SUCCESS (31/31), wording [39005511761](https://github.com/ALL-EX-E/InOneLine/actions/runs/39005511761) SUCCESS. Проверенный ZIP 46 826 173 байта https://drive.google.com/file/d/1y_G_uwvY9WdGQ5KKMrXm7_-ClmUY43an/view.
- Чистое продвижение [PR #192](https://github.com/ALL-EX-E/InOneLine/pull/192) HEAD `0ba14d8ada62f490dcc1432c55ba31a934a3afff`, свежие Windows Regression Foundation [39006381760](https://github.com/ALL-EX-E/InOneLine/actions/runs/39006381760) SUCCESS и wording [39006381758](https://github.com/ALL-EX-E/InOneLine/actions/runs/39006381758) SUCCESS. Squash main `0565538a9f7d942f7a8a9450257c2b9fe6762c3a`, точная сверка Git blobs 3/3 PASS. Исходный draft [#191](https://github.com/ALL-EX-E/InOneLine/pull/191) закрыт **БЕЗ MERGE**.
- P13-C/UI-071 **ACCEPTED/CLOSED**: существующий wheel soundtrack editor перенесён в исходный общий `timer_widget` рядом с существующим auction soundtrack editor. Контекстная видимость при Max Amount / Weighted Wheel и переходе к колесу. Два независимых сохранённых набора выбора / громкости / mute, общий existing audio output route, без изменения логики аукциона, таймера и OBS.
- **Следующий P13-D/UI-073** — только внешняя визуальная унификация общего timer block с принятым стилем Stream/OBS: оформление секции, заголовка, отступов; сохранить оригинальные widgets, порядок управления, контекстные кнопки и те же таймеры, быстрые кнопки, OBS URL и два набора soundtrack. Не смешивать с P16/UI-072 минимум Wheel 1 секунда, BUG-007 или иными функциональными поправками. Новый отдельный QA draft, Windows CI, затем ручная проверка.

## P13-D/UI-073 визуальная унификация таймера: Windows QA готова / MANUAL PENDING (17 октября 2026)

- Изолированный draft [#193](https://github.com/ALL-EX-E/InOneLine/pull/193), exact QA HEAD `28ec28c2b04e55bfda44b3f32903ad04ca4f7264` (3 файла: `auction.py`, `common.py`, `gui_regression_smoke.py`). Оригинальный общий `timer_widget` получил совместимый с приложением нейтральный `sectionCard` (существующая тёмная палитра), заголовок `Таймер` точно с типографикой существующих Stream/OBS headings 13pt/650, расстояние между секциями 8 вместо 6. Старые controls, signal handlers, контекст музыки, положение локального колеса и маршруты OBS сохранены. Новая независимая механика не создавалась.
- Native Windows Regression Foundation [39006907474](https://github.com/ALL-EX-E/InOneLine/actions/runs/39006907474) **SUCCESS 31/31**; publication wording [39006907376](https://github.com/ALL-EX-E/InOneLine/actions/runs/39006907376) SUCCESS. ZIP с установщиком `InOneLine_P13D_UI073_SHARED_TIMER_STYLE_1.0.8_WINDOWS_QA.zip` https://drive.google.com/file/d/13kpk1lkeBeP6lQIeQ27SJrhzIE-DQmC1/view, **46 816 679 байт**, SHA256 `7248f6499ff8bd32b9cf37e644498f96a048243536281739ba7f419540aac0fa`; скачанная копия прошла локальные независимые SHA256 и ZIP CRC.
- **Пока не принято пользователем, не объединять с main.** Проверить широкое и минимальное окно, расположение колеса слева/общего таймера справа, контекстные оба набора soundtrack, кнопки таймера и OBS предпросмотры. После ручной приёмки продвигать точно проверенные blob SHA отдельным clean PR c повторным Windows CI. UI-072/P16 (минимум 1 сек), BUG-007 и tie-overtime semantic fix отдельно.

## P13-D UI-073 принят; P14-A UI-047 первая часть + косметическая правка таймера (17 октября 2026)

- 2026-10-17 05:52:58 UTC пользователь принял установленную P13-D/UI-073 QA-сборку: «Всё работает. Принимаю», при этом на скриншоте отметил более тёмные полосы за заголовком `Таймер` и подписями музыки. По явному решению пользователя дефект оформления **не блокирует приёмку P13-D** и исправляется вместе со следующим этапом.
- Проверенная исходная версия P13-D HEAD `28ec28c2b04e55bfda44b3f32903ad04ca4f7264`, Windows CI [39006907474](https://github.com/ALL-EX-E/InOneLine/actions/runs/39006907474) PASS 31/31, ZIP [Google Drive](https://drive.google.com/file/d/13kpk1lkeBeP6lQIeQ27SJrhzIE-DQmC1/view). Чистое продвижение [PR #194](https://github.com/ALL-EX-E/InOneLine/pull/194), fresh Windows [39007955110](https://github.com/ALL-EX-E/InOneLine/actions/runs/39007955110) SUCCESS и wording [39007955083](https://github.com/ALL-EX-E/InOneLine/actions/runs/39007955083) SUCCESS, squash main `2e3df73c59394014b33f3c06c6116a1b9c106f8f`. Все 3/3 exact source/test blobs повторно совпали в `main`; старый draft [#193](https://github.com/ALL-EX-E/InOneLine/pull/193) закрыт БЕЗ MERGE.
- Следующий пакет по утверждённой очереди — **P14 Auction Lots Overlay (UI-047/UI-074/UI-075)**, затем P15 и P16. Первый ограниченный шаг **P14-A/UI-047**: изменить презентацию `/auction-lots-overlay` с старой HTML-таблицы на отдельные скруглённые плашки под общим rounded/glowing контейнером, сохранить current data/size-to-content column widths, title wrap, show-chance, API polling и auto-scroll, rename `Размер шрифта`/`Цвет шрифта` в Stream/OBS. Одновременно исправить фон вложенных `QLabel`/двух существующих soundtrack `QWidget` только в `sectionCard`, не меняя остальной Qt-стиль и функцию таймера.
- Изолированный проверочный draft [#195](https://github.com/ALL-EX-E/InOneLine/pull/195), ветка `candidate/p14a-ui047-cards-and-timer-stripes-clean-20261017`, base `2e3df73c59394014b33f3c06c6116a1b9c106f8f`; 5 файлов исходников/тестов. **Автоматические тесты и ручная приёмка ожидаются**, не объединять без явного подтверждения пользователя.
- P14-A — первая UI-047 foundation-проверка, а **добавление настраиваемой прозрачности/свечения/цветов и независимых параметров шрифта заголовков** остаётся в следующем отдельном шаге UI-047. UI-074 OBS-only автопрокрутка без локального автоскролла и UI-075 footer итоговых баллов — следующие самостоятельные шаги P14. P16/UI-072 (1 секунда Wheel) не смешивать с P14.
