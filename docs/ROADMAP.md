# InOneLine Roadmap

Обновлено: **2026-10-02**

Этот файл — короткий канонический inventory будущей работы. Он восстановлен после повторной сверки чатов «Программа для стрима» 1–31, исторических Drive-roadmap/reconciliation-файлов, GitHub Issues, release notes и exact current source.

## CURRENT

- Released product version: **1.0.8 / Global Conditional UI Visibility**.
- Latest accepted 1.0.8 maintenance baseline includes the filesystem/codebase maintenance accepted through **A9**.
- SQLite schema: **19**.
- Named migrations: **15**.
- Все A1–A10 findings контрольного codebase audit 2026-10-01 закрыты.
- Новый product implementation scope после maintenance-аудита **не выбран автоматически**.
- **QA-1.0.8-01 — Conduct integration last-event visibility** — новый reconciliation/QA finding: ранее принятый B1 contract требует показывать время последнего принятого integration event в компактном `Аукцион → Проведение` status UI. Current 1.0.8 сохраняет `last_event_at` и показывает последнюю активность в Settings, но не в Conduct status/dialog. Статус: **ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT FIXED / NOT AUTO-AUTHORIZED**.
- GitHub Issues используются для отдельных tracking-задач, но **не являются исчерпывающим backlog**; полный survivable future inventory находится в этом файле. Полная история пользовательских идей и их статусов — `docs/IDEA_INVENTORY.md`.

## Известный accepted-requirement QA finding

- **QA-1.0.8-01 — Conduct integration last-event visibility**. Это не новая feature idea и не меняет retained future dependency order. Перед runtime fix нужен fresh exact-CURRENT review и отдельное approval; исправление должно переиспользовать существующий `integration_connections.last_event_at`/B1 status infrastructure, без второго event/history backend.

## Ближайшие scope для fresh review

Это **не pre-authorized implementation queue**. Каждый пункт перед кодом требует fresh exact-CURRENT review и отдельного решения пользователя.

1. **Global Multi-File Import** — текущий post-D26 candidate, tracking **#4**. Распространить стандартный Windows Ctrl/Shift multi-select на применимые потоки «Добавить файл…», переиспользуя уже работающий D26 multi-select и существующие managed/external/duplicate rules.
2. **D40 — ручной порядок soundtrack/music library** — сохранённая future-идея, не реализована D26. Должна переиспользовать D43/D26 audio/media/playback state, а не создавать второй player/library backend. Это **не восстановление** superseded pre-D26 Auction playlist/Loop-One модели: с D26 текущий Auction soundtrack — один выбранный зацикленный файл из shared soundtrack library.
3. **D34 — Tourniquet donation adapter** — possible/deferred integration; перед реализацией требуется свежая проверка официального API/event delivery/auth/currencies/security.
4. **D41 — кроссплатформенная агрегация чатов + отдельный OBS chat overlay** — user-requested post-completion idea; обычные сообщения чата сами по себе не меняют auction/SM-points/timer/wheel state.
5. **Older YouTube platform/integration candidate** — сохранённая отдельная integration-direction с неуточнённым scope. Не путать с историческим W3 YouTube soundtrack-source wording и не путать с закрытым «Трейлер (YouTube)».
6. **D38 — optional LAN access to standalone OBS widgets** — post-completion only; localhost остаётся default, Internet exposure по умолчанию запрещён.
7. **Public Web / ordinary site presentation** — сохранённое future/publication direction; exact hosting/security/update/UI scope не определён и не auto-authorized.
8. **D27 — «Честное колесо»** — optional physics/final-stop winner mode; default RNG-first wheel не меняется.
9. **D7 — whole-snapshot cryptographic verification hardening** — security hardening поверх уже реализованной verification model.

Порядок 2–9 восстановлен из ранее принятого complexity/dependency planning. Он нужен, чтобы не потерять зависимости, но **не означает автоматического выбора следующей реализации**.

## Явно отложенные / пропущенные пользователем

Эти пункты живы, но не должны автоматически возвращаться в текущую очередь:

- **D16 — local-wheel hover highlight** — explicitly deferred.
- **D17 — random spin duration** — explicitly skipped for now.
- **D18 — wheel visual style selector** — explicitly skipped for now.
- **D20 — visual sector split** — explicitly deferred.
- **D22 — Battle Royale** — approved post-completion, explicitly deferred 2026-09-29; tracking **#5**.
- **W1 — Space -> existing «Крутить»** — ранее реализовывался, затем сознательно снят из MAIN и оставлен post-completion.
- **Сохранённые аукционы** + зависимый полный **«Новый аукцион...»** — deferred reusable-auction workflow.
- **A8 compensating Undo** — только possible post-completion; прежний whitelist не считается pre-approved, fresh safety review обязателен.
- **B6 Pointauc API adapter contract** — deferred; fresh source-of-truth/conflict/ID/dedup/write-policy review обязателен.
- Дополнительные provider adapters: **iHAQ Donate v2.0, ODA Digital/OpenDonationAssistant, DonateX, VK Video Live rewards/points, Kick Channel Points/Custom Rewards, Donate Helper, DonatePay** — deferred; Kick/VK остаются feasibility-conditional до подтверждения официального/надёжного provider contract, ODA contract-blocked до безопасного официального auth/event/history contract.
- Реальная Twitch Channel Points/Custom Rewards verification — eligibility-dependent, не потерянная feature-задача.

## Approved/retained post-completion wheel items, пока не выбранные

- **D23 — import custom participants**: destination «в текущий аукцион» через existing add/increment path либо temporary wheel-only participants; preview/confirmation и duplicate merge остаются частью сохранённого design.
- **D24 — отдельный OBS Browser Source со списком участников колеса**: независим от operator list и Wheel Overlay; должен использовать authoritative wheel state.
- **D25 — cumulative probability лотов с суммой <= сумме победителя**: approved only as post-completion / **не нужно сейчас**; считать по resolved weighted-wheel snapshot.
- **D42 — текущий лот/сектор под стрелкой во время вращения**: approved post-completion; local + OBS, включаемое/выключаемое отображение, без изменения RNG/weights/winner.

## Принятые/сохранённые future ideas, не выбранные в реализацию

Наличие здесь означает сохранённое пользовательское решение/идею, а не разрешение начать код.

- **D1** double timer / elapsed count-up — user-accepted as possible / deferred.
- **D2** pin/unpin lot — user-accepted as possible / deferred.
- **D5 advanced History analytics** — **USER-ACCEPTED POST-COMPLETION / POST-INTEGRATION**, а не assistant-only possibility: activity heatmap, weekdays distribution, participant rankings, separate points/donations analytics, record cards и «Самый дорогой победивший лот». Core History уже реализован.
- **D9** localization/languages — user-accepted / deferred post-completion; централизованная UI-localization, без автоматического перевода пользовательских данных, названий игр и History/Journal content.
- **D10** GitHub link — conditional future item; prerequisite public repo теперь существует, но fresh review required.
- **D11** Telegram link — conditional on official project Telegram resource.
- **D12** support/Boosty link — conditional on official support resource.
- **D13** optional Pending/manual-processing queue — user-accepted as possible post-completion; MAIN automatic acceptance не меняется.
- **D28** artificial/fixed probability mode — user-accepted as possible post-completion, only explicit artificial-chance mode.
- **D29** viewer names in viewer-facing table — user-accepted as possible / integration-dependent.
- **D30** blind/hidden viewer amounts — user-accepted as possible post-completion; authoritative values/RNG unchanged.
- **D31** Never/Match/Always auto-processing selector — user-accepted as possible extension of future D13.
- **D32** viewer name as order text — user-accepted, later narrowed to a separate future participant/viewer-based mode.
- **D33** alternative display sorts old/new/cheap/expensive — user-accepted as possible; default amount-desc stays.
- **D35** per-bet fortune multiplier — user-accepted as possible post-completion.
- **D36** viewer chooses lot — user-accepted as possible, dependent on D35 and fresh interaction review.
- **D37** presets export/import — user-accepted / deferred post-completion.
- **Games/List Compact presentation** — earlier accepted, 2026-09-28 explicitly postponed until a real future need appears.
- **Auction Lots Normal/Compact applicability** — only specification-reconciliation territory; not a confirmed defect.

## Неутверждённые / review-later только

- **D3** universal inline editing in all tables — possible post-completion; no current approval to implement.
- **Auction Lots Normal/Compact** remains specification-reconciliation territory unless separately selected.

## Важные status corrections

- Games/List shared persisted **Autoscroll** из старого PASS13 **не является живой задачей**: 2026-09-28 пользователь прямо решил не добавлять её, потому что автопрокрутка уже реализована там, где нужна.
- **D15 Twitch AI-bot/neural-network** — не подтверждён как InOneLine roadmap item; historical identifier only.
- **D39 per-scene widget style profiles** — historical assistant-proposed possibility; **NOT ACTIONABLE** без нового прямого решения пользователя.
- Historical W3 **YouTube URL/video-ID soundtrack source** — reference-only possibility, не direct-user-approved roadmap scope.
- Historical **«Трейлер (YouTube)»** — resolved/closed; не возвращать.
- **D4** separate top-level Wheel page, **D6** generic Widgets umbrella, **D8** video requests, **D14** old umbrella item — rejected/superseded; не возвращать автоматически.
- F-series rejected/superseded items не являются backlog.
- H-series — existing behavior to preserve, а не новые задачи.

## Недавние закрытые roadmap items

- **QA-1.0.2-01 / unified OBS onboarding** — CLOSED in 1.0.2.
- **QA-1.0.2-02 / external donation auto-extension completion** — CLOSED in 1.0.3.
- **D19 — custom center image + remote Twitch/7TV/BTTV/FFZ sources + quick picker** — RELEASED in 1.0.4.
- **D43 — OBS Browser Audio Transport** — RELEASED in 1.0.5.
- **D21 — Elimination wheel** — RELEASED in 1.0.6.
- **D26 — Music Player + shared soundtrack library + OBS overlay** — RELEASED in 1.0.7.
- **Global Conditional UI Visibility / #3** — RELEASED in 1.0.8.
- Старый deferred stale-OBS-page reload/version-handshake уже закрыт реализованным overlay handshake; отдельной roadmap-задачей больше не является.
- Старый wheel-overlay infinite RAF optimization также не является открытой задачей: current wheel overlay запускает animation RAF только во время реального wheel animation.
- Старые release-hygiene/unused-file cleanup темы закрыты maintenance-аудитом 2026-10-01/02.

## Process gate

Release cadence считает **только принятые CURRENT/released версии**; rejected candidate/FIX не считаются.

После принятых 1.0.4–1.0.8 текущая арифметическая отметка — **21/25**. Перед фактическим C1 gate счётчик всё равно сверяется с release history.

## Roadmap safety rule

Наличие идеи в этом файле не означает разрешения на реализацию. Перед product change:

1. сверить latest exact CURRENT code/data/UI;
2. проверить, не была ли идея позже реализована, отложена, отклонена или superseded;
3. выбрать ровно один scope;
4. определить минимальный reuse-first diff;
5. получить явное approval;
6. automated QA -> native Windows/manual gate -> explicit acceptance -> promotion exact tested bytes.

Подробный повторный reconciliation от 2026-10-02: docs/history/ROADMAP_RECONCILIATION_2026-10-02.md.
