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

