# Durable Decisions

Этот файл содержит решения, которые должны переживать отдельные чаты и релизы.

## 2026-09-30 — GitHub становится source of truth

- Текущие Project State, Roadmap, Decisions, Workflow и QA ведутся в GitHub.
- Google Drive остаётся резервным/историческим архивом и не определяет CURRENT.
- Существенное решение из чата должно быть перенесено в GitHub-документацию, а не существовать только в истории чата.
- Официальные бинарные релизы хранятся в GitHub Releases.
- Candidate/FIX artifacts могут существовать в Actions/Drive как временные или резервные копии, но не являются CURRENT.

## Release rule

- В release cadence считаются только принятые CURRENT/released версии.
- Candidate/FIX версии не считаются.
- После manual acceptance официальные installer/source bytes не пересобираются.
- Release metadata может быть добавлена отдельным commit, если runtime/source принятых bytes не меняются.

## Accepted release publication

- Исторические per-release publication workflows не являются текущим источником истины и хранятся только в Git history.
- Для будущих принятых релизов используется единый `.github/workflows/publish-accepted-release.yml`.
- Нормальная публикация начинается только с добавления нового immutable request в `.github/release/requests/`.
- Request обязан фиксировать exact accepted Actions artifact ID, exact target commit, release metadata, final asset names и SHA-256.
- После manual acceptance публикация не пересобирает installer/source: она только проверяет, переименовывает/стейджит и публикует exact accepted bytes.
- Существующие tag/GitHub Release никогда не перезаписываются общим publisher.
- Старые release notes сами по себе не запускают публикацию.
- После публикации assets скачиваются повторно и проверяются по exact name/SHA-256.
- Полный контракт: `docs/RELEASE_PUBLICATION.md`.

## Public naming rule

В публичных материалах функции называются по назначению, а не по стороннему продукту, использованному как внутренний референс. Сторонние названия допустимы только для объективно нужной интеграции/API/protocol/dependency/license/legacy compatibility.

## D43 / D26 audio architecture

- InOneLine остаётся авторитетом для playback state.
- Browser Source — renderer/transport, а не второй business-logic engine.
- Auction и wheel soundtrack используют Timer Browser Source.
- Music Player использует отдельный Music Player Browser Source.
- AudioCoordinator определяет слышимого владельца.
- Music Player уступает ownership только активному событию с реально доступным незаглушённым soundtrack.
- После события Music Player возвращается на сохранённую позицию.

## D26 Music Player

- Managed music: `data\music`; supported MP3/WAV/OGG.
- Managed soundtrack: общий `data\soundtrack`; выбор auction/wheel независим.
- После перезапуска текущий трек/позиция восстанавливаются в Pause; autoplay запрещён.
- Search меняет только видимость списка, не очередь.
- Show mode, animation, artwork, colors и Spectrum относятся к OBS Music Player Overlay.
- Preview не создаёт дополнительный слышимый звук.

## D21 Elimination

Released behavior имеет приоритет над ранними draft-описаниями: каждое elimination spin использует настоящий weighted RNG по текущим активным лотам; выбранный лот архивируется только после явного `В архив`; последний лот тоже проходит spin; нулевой список завершает режим без final winner.

## Post-D26 UX rules

Из двух post-D26 UX patch items один уже закрыт:

1. **Conditional UI Visibility** — RELEASED in 1.0.8. Логически неприменимые controls скрываются; временно недоступные, но применимые controls остаются visible + disabled.
2. **Global Multi-File Import** — остаётся eligible for selection. Требование: распространить стандартный Windows Ctrl/Shift multi-file import на все применимые `Добавить файл…` flows, переиспользуя уже реализованный D26 multi-select механизм Music Player.


## 2026-10-02 — Roadmap reconciliation

После повторной сверки чатов 1–31, исторических Drive-roadmap/audit records, GitHub Issues, release notes и current runtime зафиксированы durable rules:

- Короткий post-D26 GitHub roadmap `#4 -> D22` был неполным documentation drift, а не новым решением пользователя удалить остальной backlog.
- GitHub Issues — tracking для выбранных/выделенных задач, а не полный реестр будущих идей; отсутствие Issue не означает удаление пункта из canonical roadmap.
- Global Multi-File Import / #4 остаётся eligible for fresh review, но не выбран автоматически.
- D22 / #5 остаётся explicitly deferred и не является автоматическим следующим scope.
- Retained dependency/complexity chain после released D26 сохраняет D40 -> D34 -> D41 -> older YouTube integration candidate -> D38 -> Public Web -> D27 -> D7.
- D23, D24, D25 и D42 остаются сохранёнными post-completion items.
- D16, D17, D18 и D20 сохраняют более поздние direct-user defer/skip статусы.
- Games/List shared Autoscroll из старого PASS13 не восстанавливается: более позднее прямое решение пользователя — не добавлять его; Compact presentation отложен до реальной необходимости.
- D15 не является подтверждённым InOneLine roadmap item.
- D39 остаётся historical assistant-proposed possibility / NOT ACTIONABLE без нового прямого решения пользователя.
- Historical W3 YouTube soundtrack-source wording не является утверждённым roadmap scope; «Трейлер (YouTube)» закрыт.
- Старые stale-OBS-page reload и wheel infinite-RAF candidates не являются открытыми задачами: их соответствующие runtime concerns уже закрыты текущей реализацией.
- При конфликте более позднее прямое пользовательское решение и released/current behavior имеют приоритет над более ранними assistant-authored cumulative planning blocks.
- Полный survivable inventory хранится в `docs/ROADMAP.md`; подробный reconciliation — `docs/history/ROADMAP_RECONCILIATION_2026-10-02.md`.

Этот reconciliation не выбирает следующий implementation scope.


## 2026-10-02 — Full user-idea inventory

- `docs/IDEA_INVENTORY.md` is the canonical exhaustive historical inventory of user-proposed/accepted/deferred/rejected/superseded ideas.
- `docs/ROADMAP.md` is the shorter current/future selection view and must not be treated as a complete history of everything the user ever proposed.
- GitHub Issues are tracking aids only; they are not the full idea inventory.
- Three historical A-namespaces must always be labelled explicitly: **August Stabilization A1–A12 (including A7.1/A11.1)**, **Product A1–A8/A6.1**, and **Maintenance A1–A10**. The same identifier can mean different work in each namespace.
- Direct user dialogue has priority over later assistant-authored status compression. In particular, advanced History analytics (heatmap, weekdays, participant rankings, points/donations analytics, record cards, most expensive winning lot) remains USER-ACCEPTED post-completion/post-integration work.
- Backup-retention last-N/N-days remains non-roadmap because no direct user proposal/acceptance was recovered; do not promote assistant audit suggestions into the user inventory.
- Before declaring an old idea “missing” or “next”, check IDEA_INVENTORY + later direct decisions + released/current behavior.


## 2026-10-02 — Third-pass recovered product invariants

A third independent comparison of old chats/Drive dedicated reviews against `docs/IDEA_INVENTORY.md` recovered several durable details:

- DonationAlerts/I1 uses the later permanent-source model: enabled connection is intake permission; provider source timestamp routes an event to the auction that was running at source time or to the persistent game list outside auctions. The old auction-only intake toggle/target binding is retired compatibility state, not current product behavior.
- Twitch Channel Points likewise are not gated by an auction-only intake switch; contribution routing may occur both inside and outside auctions according to the accepted B3/B4 rules.
- Integration connection UX should avoid user-managed client secrets where the provider supports public/native application authorization; use browser/device authorization and protected local tokens.
- Auction/game mutations obey a cross-surface synchronization invariant: authoritative DB mutation must propagate to Games/Public/Auction/Journal and relevant OBS/API views without manual F5.
- The default weighted wheel remains RNG-first: the winner is determined before animation, hidden until animation completes, and persisted spin/result state is recovered after restart. D27 remains a separate future alternative.
- Main OBS transparency remains cutout-only for game/webcam interiors; a second whole-overlay transparent mode was explicitly rejected.
- The initial public-GitHub-without-source publication plan was superseded by the later official SOURCE+INSTALLER publication and custom license decision.

These are historical/current invariants, not new implementation scopes.


## 2026-10-02 — Deep-history identifier/provenance corrections

- Rules aliases are two stages, not one: **R1** = reusable Rules templates/WYSIWYG/local preview/session snapshot; **R2** = standalone OBS Rules viewer + viewer settings/live synchronization. The rejected temporary `Изменить текущие правила` live-only workflow is not a separate retained feature.
- The historical assistant proposal for a separate local InOneLine write API (`POST /api/v1/bids`/generic `PUT /lot`) was **not directly user-approved**. User approval was for the dedicated B6 provider adapter using that provider's official API. Do not promote the assistant proposal into roadmap/backlog.
- Early 0.2.x and pre-1.0 stabilization/release-stage user-approved scopes are historical implemented evidence and belong in `IDEA_INVENTORY.md`; they do not create new future roadmap items.
- The accepted outside-auction integration rule is provider-neutral: a valid game-targeted external monetary/service-unit event may update persistent game points without a running auction, but may not create/start/resume an auction or mutate current auction/timer/wheel state; S2 requires an eligible running auction.

## 2026-10-02 — B1/B2 integration contract recovery and QA finding

Повторная сверка прямых решений пользователя, старого `APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT`, current 1.0.8 source и полного inventory подтвердила:

- B1 Conduct integration status contract включает только configured/used services, заметные ошибки даже в compact/collapsed state, переход в `Настройки → Интеграции` и **время последнего принятого integration event**.
- `Отключить` и `Удалить подключение` — разные операции; Remove требует подтверждения и удаляет только локальную connection config/secret, не historical external events, contributions или auction history.
- Provider/network/auth work не должен блокировать GUI; provider capabilities определяют применимые controls.
- B2 Twitch lifecycle сохраняет Public Device Code/native authorization без Client Secret, protected access/refresh credentials, startup/hourly validation, serialized refresh, `Требует входа` для invalid/revoked auth и bounded `Ошибка` для transient failures; Connect/Reconnect/Disconnect/Remove имеют разные принятые semantics.
- Current 1.0.8 сохраняет `integration_connections.last_event_at` и показывает последнюю принятую активность в Settings, но Conduct integration status/dialog не показывает accepted last-event time.
- Это зафиксировано как **QA-1.0.8-01 / ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT FIXED**. Это не новая feature idea и не автоматическое разрешение менять runtime.
- Reconciliation-файл не должен считать B1/B2 детали восстановленными, если exhaustive `IDEA_INVENTORY.md` снова схлопывает их до одной общей строки; durable detail должен храниться в inventory.

## 2026-10-02 — Fifth-pass current-audio/provider-scope corrections

Повторная сверка current 1.0.7/1.0.8 release behavior с ранними accepted Widgets/Settings decisions зафиксировала:

- Historical pre-D26 Auction/Timer Music действительно включал playlist, starting track, Loop One/sequential library order, separate Auction/Wheel profiles и точный Auction track+timestamp при временном Auction → Wheel → Auction handoff.
- **D26 / 1.0.7 supersedes текущие auction-playlist semantics**: current Auction soundtrack — один выбранный зацикленный файл из shared `data\soundtrack`; старый Auction playlist/checkbox `Зациклить выбранный трек` больше не используется. Старую модель нельзя автоматически трактовать как незавершённую current feature.
- **D40 manual library order** остаётся отдельной future-идеей поверх current D26/D43 architecture и не восстанавливает старый Auction playlist без fresh review.
- Retained provider scope уточнён по исходному Settings review: **Kick Channel Points / Custom Rewards** и **VK Video Live rewards/points**, оба feasibility-conditional до свежей проверки официального/надёжного API/auth/event contract.
- Эти уточнения не добавляют новый implementation identifier и не меняют current runtime/version/schema/migrations.

## 2026-10-02 — Seventh-pass B2/B3 provenance and publication corrections

Повторный direct-chat + Drive review исправил две ошибки предыдущего reconciliation:

- **B3 unknown-title outside-auction behavior was directly user-approved on 2026-09-02.** A valid outside-auction event with a usable unknown game title creates a normal persistent game and credits it in the same transaction. It must not create/start/resume an auction, `auction_only`, auction entry, timer or wheel state. Unknown conversion rate stays Pending and does not pre-create the game before credit can actually be applied. Current 1.0.8 source already implements this behavior.
- **Generic B2 test-event safety was directly user-approved on 2026-08-28 through the DonateX review.** Provider events explicitly marked test/sandbox/demo must not credit real points, create/increment games/lots, change leader, trigger timer auto-extension, or affect wheel/winner logic. Diagnostics/history-only storage is allowed. Current 1.0.8 normalized-event core has no explicit test-event field/gate, so this is now tracked as **QA-1.0.8-02 / ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / PROVIDER-CAPABILITY-DEPENDENT / NOT AUTO-AUTHORIZED**.
- Deferred donation adapters preserve one common B2/B3 contract: source+external-event-ID dedup; common source-unit conversion; message/order text as ordinary lot/game text while sender remains separate; immutable historical original source values + applied conversion rate + credited points; common timer path; official/reliable programmatic APIs only; no page/OBS/browser scraping.
- Provider precision preserved: iHAQ/Donate Helper are feasibility-gated; DonatePay realtime path requires exact endpoint/auth/channel/payload/currency/event-ID revalidation; DonateX official API path was previously confirmed but live-delivery contract must be revalidated and its provider test flag must obey the common test-event safety rule.
- Historical E1 native-EXE acceptance required the exact build output to visibly reach `[9/9] BUILD EXE: OK` with console kept open/full output visible; exact binary/manual QA and explicit user acceptance remained separate mandatory gates.
- Public GitHub wording rule is reaffirmed: do not expose development-reference provenance in published files. A provider name may remain only where genuinely necessary as the name of the actual provider/integration/API itself.

## 2026-10-02 — Eighth-pass B3 binding and Rules control recovery

Additional direct-chat comparison after the seventh pass recovered:

- **B3 missing/unusable target text** was directly accepted as a distinct `Требует привязки` state. Such an event must not auto-create or auto-credit and must await manual operator binding to a game/lot; this is separate from `pending_conversions`, which is for unknown conversion rate/unit.
- During a running auction, a usable unknown title follows the ordinary temporary `auction_only` path; outside auction, a usable unknown title creates a normal persistent game.
- Current 1.0.8 handles usable-title paths correctly, but `missing_target` is marked `inapplicable` and there is no manual bind workflow. Track as **QA-1.0.8-03 / ACCEPTED B3 WORKFLOW OMISSION / NOT FIXED / NOT AUTO-AUTHORIZED**.

### 2026-10-06 — UI-087 supersession for ordinary empty-message auction events

- The earlier `Требует привязки` rule is **superseded for an ordinary accepted external event received during a running auction when message/lot text is empty**.
- New accepted behavior: create a distinct temporary lot `Без текста N` (1, 2, 3...) in that auction session; numbering is monotonic per session and dedup happens before assigning the next number.
- If the conversion rate is known, credit that placeholder immediately/exactly-once. If the unit/rate is unknown, create the placeholder immediately but keep the event pending and target that placeholder; UI-085/UI-086 then govern conversion, warning and result-gating.
- User-facing terminology for these reviewed flows is `лот`; legacy/internal `game/games` identifiers remain implementation details only.
- Current 1.0.8 `missing_target -> inapplicable` remains the current runtime behavior until the approved batch is implemented.
- The accepted DonationAlerts built-in public OAuth Client ID is **20915**; the user should authorize, not create their own application or enter a Client Secret.
- Rules viewer controls `Непрозрачность` and `Внутренний отступ` preserve the accepted wide external ▲/▼ + manual entry + hold/repeat UX; mouse wheel must not alter values while scrolling.

## 2026-10-02 — Ninth-pass verification/security and retained-scope preservation

- Winner Verification MAIN contract is the immutable per-run snapshot + deterministic read-only replay + completed-History details + optional pre-spin read-only data view. The snapshot preserves participants/weights or chances, effective range/equal fallback, RNG method/random value, winner, timestamp and algorithm/mapping version; Random.org+ reuses its signed ticket/signature evidence where present.
- A SHA-256 stored only in the same mutable database is **not** considered meaningful protection against intentional tampering. Whole-snapshot signing, protected key management, external hash publication/notarization and independent off-app verification remain separate post-completion security hardening.
- Future D28–D42 scopes must preserve their recorded presentation/business-state boundaries; presence in the inventory is not permission to implement them. In particular viewer-only presentation features cannot mutate authoritative auction/RNG state, D35/D36 remain separate per-bet post-completion mechanics, D38 keeps MAIN localhost-only, and D41 ordinary chat cannot mutate auction business state.
- Directly accepted R1/B1 detailed contracts are durable requirements even when shorter summaries exist elsewhere; do not collapse them back into one-line aliases during future documentation cleanup.

## 2026-10-02 — Eleventh-pass archive/provenance and QA-ID recovery

- Historical reconciliation PASS 12 is still correct that the original **2026-08-21 external-reference screenshot set** is not recoverable from currently accessible Drive image search. Later text/dedup/dedicated review records preserve the product decisions, but the original image bytes must **not** be claimed as archived and must not be reconstructed and presented as originals.
- This is a **REFERENCE ARCHIVE GAP**, not a product feature, runtime defect or reason to reopen already accepted/rejected roadmap decisions.
- Release/reconciliation defects use **`QA-<version>-NN`** identifiers. Permanent roadmap/product identifiers (D/A/W/B/E/R and similar) must not be recycled for temporary QA defects or omissions.
- Recovering one of these process/archive rules does not select a new implementation scope; runtime remains unchanged until a separately reviewed and explicitly approved code change.

## 2026-10-02 — Twelfth-pass History/Wheel/Timer precision recovery

A post-correction control against the dedicated History/Wheel/Widgets reviews recovered additional direct-user detail that had been compressed too far:

- Standalone Timer viewer is read-only and shows only the timer value. With no active auction it shows the configured initial/default duration for the next auction/current pre-start mode; during an auction it mirrors the authoritative timer. It never creates a second timer engine or viewer controls.
- W1 Space hotkey, if ever reintroduced, must call the existing Spin action, be blocked while focus is in controls where Space has a normal meaning, and must never create duplicate/re-entrant spin.
- W2 external media references never authorize modifying/deleting the original external file or exposing arbitrary filesystem access to Browser Sources. Missing/moved/disconnected media degrades safely and can be repaired/reselected through the existing protected media-serving path.
- Advanced History participant identity uses provider/source + stable external user ID; mutable nickname is display metadata. Same-name accounts across services are never auto-merged without a separate explicit linking design.
- Advanced History cross-unit statistics require an explicit comparable basis: unrelated point systems or currencies are not naively summed; record cards are computed from authoritative historical snapshots, not current mutable Games state.
- A8 retained safety invariants survive even though implementation is deferred: reversal is an appended auditable compensating event, original history is never deleted/rewritten, unsafe dependency chains block Undo, and operator-only Undo is never exposed to viewer OBS outputs. Exact reversible-action whitelist remains for fresh review.

## 2026-10-02 — Thirteenth-pass S2/widget/B6 boundary recovery

A further post-correction comparison against the dedicated Settings/Widgets/Winner reviews restored additional accepted boundaries:

- S2 timer auto-extension collision/threshold semantics are durable: only genuine new-lot creation qualifies for the new-lot reason; external events qualify only after common acceptance/dedup; one originating action/event may extend once using the largest matched configured duration rather than summing; equality at threshold is eligible; disabled threshold allows enabled triggers through the running auction; paused/non-running sessions and already-expired timers do not auto-extend/resurrect.
- Standalone viewer architecture keeps Стрим / OBS as the single top-level output center. OBS owns scene composition and Browser Source viewport sizing; no generic named-instance/composite canvas is part of MAIN. Operator-only controls/status do not receive viewer widgets by default.
- B6 uses the common integration/auction backend and B1 protected credential storage. Provider token/plaintext secret storage in the main SQLite DB is prohibited. Source-of-truth direction, conflicts, IDs, dedup, temporary-lot behavior and provider writes remain fresh-review items.
- Winner Verification MAIN does not imply a public Internet verification page. Localhost remains the default service boundary; LAN/public sharing is a separate D38/Public-Web/security decision.
- Product A7 history cards keep explicit affected-lot/object/value context, understandable event icons and exact stored timestamps; hover linkage remains operator UI only.

## 2026-10-02 — Fourteenth-pass B1/B2 secret/lifecycle precision

Direct-chat recheck recovered two B1/B2 details that were still compressed in current documentation:

- **Secret hygiene is broader than “not in SQLite”.** Plaintext tokens/passwords/API secrets must not be stored in main SQLite, ordinary settings/provider config, logs/diagnostics, exports or full-backup manifests/plain content. Full backup may carry protected credential files only as their already-protected DPAPI ciphertext. Secret-bearing errors/diagnostics must be masked/sanitized.
- **Disconnect/disabled lifecycle:** disabling use preserves local configuration, protected credentials, account/capability metadata and history. After restart the integration remains disabled and does not undergo background provider validation until use is re-enabled. A preserved connected grant is represented as `Статус: Подключено · использование отключено`. Remove is distinct: after confirmation it deletes local connection config/credential metadata and returns to `Не настроено`, but never deletes historical events/contributions/auction history.

Current 1.0.8 source already follows these runtime rules: active validation filters to enabled+connected adapters and diagnostic errors pass through secret sanitization.

Source review also found a **production-unreachable DonationAlerts manual-Client-ID fallback UI** after `has_built_in_client_id()`. The shipped path constructs `DonationAlertsAdapter()` with built-in public Client ID 20915 and returns before that fallback. Classification: **SOURCE-HYGIENE / COMPATIBILITY RESIDUE / NOT RUNTIME QA DEFECT / NOT AUTO-AUTHORIZED FOR CLEANUP**. Do not revive manual Client ID management as product scope.

## 2026-10-02 — Sixteenth-pass B4 supersession and direct UI precision

A new direct-chat/current-source recheck after the fifteenth CLEAN pass found a real documentation contradiction plus three compressed implemented decisions:

- **B4 reward availability supersession:** the earlier accepted B4 design allowed app-managed Twitch rewards to follow auction/bid-intake state. The later direct-user I1/permanent-source decision on 2026-09-03 superseded that behavior. Current authoritative rule: Twitch rewards are enabled/disabled explicitly with the manual Settings controls and do **not** automatically follow auction start/resume/pause/finish. Channel Points intake remains a permanent connected source with source-time routing inside/outside auctions. Legacy `twitch_rewards_link_to_auction` and the old local Channel-Points intake toggle are compatibility-only, not current gates. Current 1.0.8 source already implements the later rule, so this is documentation correction rather than a runtime defect.
- **RANDOM.ORG UI location:** the user directly moved the API-key configuration from `Настройки → Общие` to `Настройки → Интеграции`; B1 protected credential storage remains authoritative.
- **OBS info-block date:** the user directly requested removal of the date from the lower-right OBS information block. Current accepted/runtime presentation keeps that date absent.
- **Restore safety UI:** the accepted manual Restore flow rejects selecting the current working `data\streaming.db` as its own source, validates a real backup, creates a safety backup, then applies restore/restarts.

The Games `Всего`/archive-counter behavior was also rechecked. Current code counts ordinary archived records in the Games total and excludes temporary `auction_only` rows until promotion, but the new direct-chat control did not recover a sufficiently clean standalone user wording beyond accepted implementation/history evidence to promote this as a newly recovered direct-user requirement. Existing inventory coverage for archive layout/counters remains unchanged.

No runtime/source/version/schema/migration change is authorized or performed by this documentation correction.

## 2026-10-02 — Seventeenth-pass process/public-wording recovery

The first post-sixteenth orphan-only control found two durable direct-user process/public-documentation rules that were implemented but not yet preserved explicitly in canonical decision docs:

- **Focused manual QA cadence:** Windows/PowerShell checks should be requested only when they add real verification and preferably one focused command/check at a time; do not burden the user with a long manual checklist when automated gates or already-passed Windows scenarios cover the same fact.
- **Public installer instruction wording:** the user explicitly required the install step wording `Запустить установщик`; the current README implements it as `Запустите установщик и следуйте его подсказкам`.

The same control also corrected the sixteenth-pass note about Games `Всего`: direct user provenance does exist for `Всего` including archived ordinary records, active records first and archive as a bottom block. This requirement was already present in the exhaustive historical ledger (`0.2.22`) and current code, so no new inventory item or runtime defect is created; only the provenance note required correction.

No runtime/source/version/schema/migration change is authorized or performed.

## 2026-10-02 — Eighteenth-pass engineering/audio contract recovery

A further same-scenario recheck against direct chats, released 1.0.5/1.0.7 evidence and current 1.0.8 source recovered two durable areas that were still compressed too aggressively.

### Engineering invariants

The user's permanent development rule is stronger than the short `reuse-first` wording:

- **reuse first -> minimal diff -> no parallel logic -> no new persistence unless unavoidable**;
- existing mechanisms/data/UI/settings/calculations/APIs/storage must be reused whenever they remain correct and reliable;
- new entities/backends/persistence are justified only when the old mechanism is objectively unsuitable for correctness, reliability or required performance;
- optimization/speed/size work must never trade away stability, correctness, data safety or predictable resource use;
- the product must avoid hangs/crashes and unnecessary RAM/package growth;
- risky cleanup/refactor follows a permanent regression/Windows QA foundation, and QA/build compatibility problems are fixed in QA/build before changing runtime unless runtime change is separately approved;
- no out-of-scope runtime/schema/RNG/persistence/data-semantics changes.

These rules are now explicit in `docs/WORKFLOW.md`.

### D43 / D26 accepted audio lifecycle

The released/current contract is more specific than the prior short summary:

- merely opening/configuring Auction does **not** interrupt Music Player; audible ownership changes only when an actual auction/wheel phase starts and has an available unmuted soundtrack;
- the Music Player suspension snapshot preserves track, exact position and desired Play/Pause intent. If it was playing, release resumes the same track/position; if it was paused, release leaves it paused;
- max-amount timer end releases Music Player immediately at the phase boundary rather than waiting for winner confirmation;
- tie state retains the auction soundtrack position so additional time can continue the same timeline; changing the selected soundtrack during tie setup intentionally discards the old retained position so the newly selected track starts from its own beginning;
- event soundtrack Mute immediately yields audible ownership back to Music Player; unmuting during the still-active phase can reacquire ownership without restarting the event soundtrack transport;
- between D21 Elimination rounds Music Player is allowed to resume;
- same-name managed soundtrack copy requires an explicit operator choice: **use existing / replace / save separate copy / cancel**;
- full backup/restore preserves managed `data\music`, shared `data\soundtrack`, selections and D26 settings; external referenced file bytes remain external; restored Music Player starts paused and does not autoplay.

These are already accepted/released behaviors, not new feature requests and not new runtime QA findings.

## 2026-10-02 — Nineteenth-pass conditional-link and archive-preservation precision

A post-seventeenth orphan check recovered two small direct-decision areas that were still compressed:

- **D10/D11/D12 link boundary:** GitHub/Telegram/support links are valid only for the corresponding official project resource. D10's repository prerequisite now exists but placement remains fresh-review work; D11 waits for an official project Telegram resource; D12 waits for completion/publication plus an official support page and belongs to informational/project/support UI, not Auction business UI.
- **Historical artifact preservation:** cleanup of active docs/CI/source trees must not destroy the only surviving historical audit/reference/release evidence. Retired material remains recoverable through Git history, canonical history docs or Drive archive. If original bytes/screenshots are gone, a later textual reconstruction must not be represented as the original archive.

These are documentation/process precision corrections only; no runtime/product scope is selected.

## 2026-10-02 — Twentieth-pass A1 isolation and B2 restart precision

The first full control after the nineteenth documentation corrections recovered two accepted details that were still only implicit:

- **August Stabilization A1 exact fail-closed QA/promotion contract:** create the candidate archive in temporary `.building`; validate forbidden runtime/user files before promotion; a failed validation must leave the previous safe archive untouched. Update simulation is performed on a copied installation rather than the main working folder, and the copied `data\streaming.db` hash is checked unchanged before launch. Clean-install simulation verifies that user DB state is absent before first launch.
- **B2 restart persistence contract:** a valid saved Twitch authorization survives application restart with no new OAuth/Device Code popup. Saved account/status remain available; enabled connected integrations are checked automatically after startup and then hourly, updating the stored/visible last-check timestamp. Reauthorization is required only when validation/auth state actually requires login.

Current 1.0.8 source matches the B2 startup/hourly validation and persisted connection-status model. These are documentation/process restorations, not new runtime defects.

## 2026-10-02 — Twenty-second-pass Auction autoscroll / S2 / SOURCE precision

The next Drive+chat+release control recovered three accepted details that were present in historical/release evidence but not explicit enough in the exhaustive inventory:

- **Auction autoscroll boundary:** Auction Lots, Conduct and the dedicated Auction Lots OBS overlay share one current-session autoscroll state. It starts OFF on every application launch, is not persisted, and does not inherit Games/List presentation persistence. This is current/released behavior, not a future Games/List-autoscroll task.
- **1.0.3 service-unit timer-extension UX:** the accepted persisted checkbox `Также учитывать неденежные единицы интеграций` defaults OFF. OFF keeps external auto-extension monetary/currency-only; ON additionally includes provider-neutral service units. Monetary and service-unit audit reasons remain distinct and use the same S2 threshold/collision/24h backend.
- **Official accepted SOURCE asset:** `InOneLine_Source_<version>.zip` is the exact accepted SOURCE snapshot published as a dedicated release asset. GitHub-generated `Source code (zip/tar.gz)` archives come from the tagged repository tree and are not substitutes for, or expected to be byte-identical to, the official accepted SOURCE ZIP.

No runtime defect or new roadmap identifier is created by these documentation restorations.

## 2026-10-02 — Twenty-third pass S1 pending/manual-apply precision

A new direct-chat comparison after the twenty-second pass recovered two accepted S1 details that were implemented in current 1.0.8 but still compressed out of the exhaustive ledger:

- Unknown-rate external events remain pending and **do not auto-credit** when a rate later appears. Saving the rate only moves the item into a manually applicable state; the operator must explicitly press `Применить` and confirm the previewed conversion.
- Service-specific conversion rows are visible only while the corresponding integration capability/service is connected/available; ordinary currency rows follow the persistent registry/rate model. Current implementation keeps the saved service-unit rate while its row is hidden and restores it when visible again, but this persistence is recorded as implementation behavior rather than a separately proven direct-user requirement.
- Late manual application must not retroactively rewrite a closed/paused auction; current `apply_pending_conversion_event()` preserves that historical boundary.

These are documentation-precision findings only. No runtime/source/schema/version/migration change is authorized or required by this pass.

## 2026-10-02 — Twenty-fourth pass D26 media-identity and external-soundtrack contract

Direct-chat + accepted 1.0.7 release evidence confirms the following D26 rules are durable:

- Music Player media identity/dedup is case-insensitive by filename across managed + external rows.
- Importing an external duplicate does not create another row; one match may select the existing track, while multiple matches are informational only and do not auto-navigate/search.
- `Копировать в программу` on an existing external Music Player row promotes that same record to managed while preserving media ID and queue position.
- External Auction/Wheel soundtrack references are context-local selections, not reusable members of the shared managed soundtrack library.
- Missing selected external soundtrack clears safely without a D26 recovery-button flow.
- Managed `data\music` and `data\soundtrack` remain filesystem-synchronized managed sources; full backup includes managed bytes/settings/selections, not bytes of external references.

These details are implemented in current 1.0.8 and do not reopen D26 or alter D40.

## 2026-10-02 — Twenty-fifth pass early-media / S1 migration / public-install precision

Further direct-chat/source comparison recovered:

- Current overlay/media implementation preserves `original_name` during managed registration/copy. **Provenance correction:** a latest exact direct-chat recheck did not recover a direct user sentence making original-filename preservation a separate requirement, so this is retained as implemented historical behavior rather than promoted as a new user-originated product decision.
- S1 legacy-money migration was explicitly accepted as **1 RUB = 1 SM point**, with positive fractional RUB rounded upward. Historical `change_log` JSON remains untouched rather than being retroactively rewritten. Current schema migration implements this exact boundary.
- Public-install documentation had a direct user requirement to explain the Windows unsigned-publisher/SmartScreen warning path to ordinary users and why it appears, without requiring security protection to be disabled. Current README explains the unsigned installer and SHA-256 verification, but the previously requested step-by-step Windows prompt guidance is not fully preserved. Track this as a **PUBLIC-DOCUMENTATION GAP / NO RUNTIME IMPACT** pending a safe current-wording refresh.

The earlier backup-retention `last N / N days` candidate was rechecked against direct chat again: the user confirmed backup creation worked, but did not directly approve/reject that assistant suggestion. It remains intentionally outside the user-approved backlog.

## 2026-10-02 — Archive/process preservation correction

Повторная сверка прямых решений пользователя восстановила два process/detail правила, которые были реализованы/использовались, но недостаточно явно отражались в exhaustive documentation:

- **Drive audit archive rule:** текстовые логи аудитов/проверок и пользовательские скриншоты, используемые как QA/project evidence, должны сохраняться на Google Drive. Решение 2026-09-30 сделать GitHub canonical source of truth не отменяет это правило: GitHub хранит authoritative current docs/code/history, Drive остаётся backup/historical archive для логов, скриншотов и delivery artifacts. Drive не может переопределять более поздний GitHub CURRENT.
- **R1.0.4 uninstall warning detail:** destructive uninstall warning должен не только сообщать об удалении program/user data, но и рекомендовать сначала создать внешнюю полную `.iolbackup` через dedicated full-backup flow и хранить её вне install root. Current installer already implements this; correction is documentation-only.

## 2026-10-02 — Twenty-sixth same-scenario pass: archive/UI/release precision

The user requested another full chats -> Drive -> GitHub -> canonical-docs reconciliation after the previous corrections. This pass recovered additional **direct-user detail**, but no new product identifier or newly authorized implementation scope:

- **Drive audit archive rule:** audit/check text logs and user screenshots used as QA/project evidence are kept on Google Drive. GitHub remains canonical CURRENT; Drive remains backup/history and cannot override later GitHub state.
- **R1.0.4 uninstall guidance:** destructive uninstall warning recommends creating the dedicated full external `.iolbackup` first and storing it outside the InOneLine root. Current installer already implements this.
- **D19 animated center runtime contract:** supported animated center media stays animated locally and in OBS before/during/after spin; the center layer itself stays stationary while sectors rotate; center media cannot alter RNG/sector/probability/target/winner semantics.
- **D21 elimination lifecycle:** each result is `Выбывает: <лот>`; `В архив` replaces ordinary winner confirmation; archive is explicit/non-destructive and removes the lot from later rounds; operator-only archive control is not shown to viewer OBS. The last lot still goes through the same `Крутить -> В архив` path and the mode ends with zero active lots, **without an automatic/final winner concept**.
- **S1 user-facing terminology:** normal UI uses `Баллы`, not `Баллы SM`; legacy `БАЛЛЫ SM` remains only as a compatibility import/header alias.
- **R1/S3 Windows-input precision:** Rules font-size uses a scroll-safe numeric field with native tiny arrows removed and wide external step buttons; the eyedropper confirms on left click, cancels on Escape or right click, and must release temporary mouse/keyboard grabs on every exit.
- **Auction autoscroll boundary:** Lots, Conduct and Auction Lots OBS share one current-session autoscroll state, default OFF at every app launch and intentionally not persisted; it is distinct from Games/List presentation persistence.
- **A11.1/A12 precision:** the accepted local+OBS wheel motion profile scales smoothly across manually checked 1-minute and 24-hour spins without changing RNG/result; A12 smoke must exercise the real operator `start_auction()` path and cannot substitute direct DB/session setup or manual `run_wheel()`.
- **Public SmartScreen guidance:** README was corrected to preserve the accepted ordinary-user warning path: official Releases source/SHA-256 check, `Подробнее -> Выполнить в любом случае` when offered, then UAC confirmation; disabling Windows protection is not required.
- **Public Git privacy/history cleanup:** before public launch, the user explicitly allowed one-time Git-history rewriting to remove personal author e-mail/metadata only after a backup, preserving file content and then synchronizing public refs/tags/releases/docs. The user chose a direct PowerShell workflow rather than a downloadable-script method. This historical privacy exception is not a general license to rewrite accepted published release bytes/tags or reintroduce removed personal data.

Current runtime already implements the relevant runtime behaviors above; the SmartScreen correction is public-documentation-only. No APP_VERSION/schema/migration/runtime change is authorized or made by this pass.

## 2026-10-03 — Pass 28 precision recovery

Another same-scenario cross-source recheck recovered direct accepted detail that pass 27 had not stated precisely enough:

- Games/Public canonical order uses status groups `ПРОХОДИТСЯ` -> `ИГРАЛ + НЕ ИГРАЛ` -> `ПРОЙДЕНО` -> `ЗАБРОШЕНО`; the later grouped middle tier supersedes earlier wording that separated `НЕ ИГРАЛ` and `ИГРАЛ`. Current shared SQL is authoritative for the accepted released behavior.
- Product A7 History hover is a temporary operator interaction: pause Conduct autoscroll, reveal/highlight the linked lot without changing selection, keep it fixed while hovered, then remove highlight and resume scrolling from the revealed position/direction.
- D21/1.0.6 allows `Выбывание -> Обычное` (and later back again) only between completed rounds; switching is blocked during spin and while an elimination result awaits `В архив`; already archived lots stay archived/excluded. Each spin retains its own verification snapshot.
- Historical timer UX explicitly rejected a separate `+2 минуты` shortcut/hotkey layer; later accepted controls standardized `-10/-1/+1/+10` minutes.
- The 2026-08-21 B1 visual concept used a green check/red X square with collapsed-error visibility. Later B1 was manually accepted with the current text-badge presentation and no later direct message re-opened the icon requirement. Preserve the early icon design as historical accepted provenance, not as an automatic current defect.

No runtime/source/schema/migration change and no new implementation scope is authorized by this documentation recovery.


## 2026-10-07 — completed UI review supersession map

The full tab-by-tab UI/function review is complete. Runtime remains exact CURRENT 1.0.8; the items below are accepted future-target decisions for the pending review batch, not implemented behavior yet.

- **Auction autoscroll target supersession:** historical/released 1.0.8 behavior where local Auction lists and Auction Lots OBS share one non-persisted session-only autoscroll state remains valid as CURRENT history, but it is **not the future target**. UI-074 supersedes it for the pending batch: the local auction table no longer autoscrolls; a persisted `Автопрокрутка оверлея` switch controls only `/auction-lots-overlay`.
- **Settings Export target supersession:** retained R1.0.9 organization (`Settings → Export` centralizes public file export + legacy compatible export) remains historical released behavior only. UI-088/UI-090 supersede it for the pending batch: public CSV/JSON/XLSX file-export actions move to `Публичный список`, the legacy compatible-export block is removed, and the inner `Настройки → Экспорт` tab is removed entirely.
- **UI-044 supersession:** the previously accepted plan to add `Публичный API` inside `Настройки → Экспорт` must not be implemented there because UI-090 removes that tab. Existing `/api/public` stays available; a future visible access point, if needed, requires a separate decision.
- **B3 empty-message supersession:** UI-087 remains authoritative for ordinary accepted empty-message events during a running auction: create a distinct `Без текста N` temporary lot, rather than a standard `Требует привязки` workflow.
- **Review-status reconciliation:** UI-018 is closed by UI-019/UI-020/UI-021; TEST-001 manual CSV QA is complete/pass; BUG-007 and UI-055 are ready for the batch; UI-053 is narrowed to the still-undecided local timer-preview action.
- **Still unresolved, do not infer:** no direct user decision was recovered for AUCTION-TIMER-REVIEW-002 (tie-overtime saved default), AUCTION-TIMER-REVIEW-003 (~1200 ms lead-in for 1-second spins), or the remaining UI-053 timer-preview action. Preserve CURRENT behavior until explicitly decided.
- **QA findings:** QA-1.0.8-01 and QA-1.0.8-02 remain documented findings without implementation approval. QA-1.0.8-03 now has an approved target through UI-087 and waits for the future review-batch implementation command.
