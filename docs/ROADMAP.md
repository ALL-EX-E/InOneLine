# InOneLine Roadmap

Обновлено: **2026-10-07**

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
- **QA-1.0.8-02 — accepted B2 test-event safety contract is not represented generically in current normalized-event core**. Direct user acceptance exists: provider events explicitly marked test/sandbox/demo must never credit points, create/increment game/lot, change leader, extend timer or affect wheel/winner; diagnostics/history-only is allowed. Current 1.0.8 has no explicit normalized test-event field/gate. Classification: **ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / PROVIDER-CAPABILITY-DEPENDENT / NOT AUTO-AUTHORIZED**. No current supported-provider reproduction was established; implement only through fresh exact-current review and common B2/B3 reuse.
- **QA-1.0.8-03 — B3 empty-message current-runtime gap — TARGET APPROVED IN UI-087 / AWAITS REVIEW-BATCH IMPLEMENTATION**. The earlier generic manual `Требует привязки` target is superseded for an ordinary accepted external event received during a running auction with empty message. UI-087 requires an automatic temporary lot `Без текста N`: each accepted empty-message event gets its own sequential placeholder within that auction session; a known-rate event credits it immediately, while an unknown-rate event creates the placeholder immediately but keeps the credit in `Ожидают применения` until the rate is saved and the operator presses `Применить`. Current 1.0.8 still marks `missing_target` as `inapplicable`, so runtime remains out of contract until the approved review batch is implemented after the user's future `«всё делаем»` command. A separate `Требует привязки` workflow must not be created just for standard empty-message donations; provider-specific events that cannot safely map to an ordinary lot-targeted credit remain separate edge cases.


## Текущий утверждённый review-batch — не реализован

Полный UI/function review завершён 2026-10-07. Детальный source of truth для накопленных решений — `docs/ACTIVE_REVIEW_LEDGER.md`.

- Runtime/source остаётся **1.0.8 / schema 19 / 15 named migrations**.
- Это уже не fresh-review candidate list: большинство UI/BUG-пунктов имеют принятый target и ждут общей команды пользователя `«всё делаем»`.
- До этой команды **код не менять**.
- Главные cross-cutting supersession текущего batch:
  - UI-074: локальный список аукциона без автопрокрутки; persisted autoscroll только для Auction Lots OBS overlay;
  - UI-087: empty message во время running auction → `Без текста N`;
  - UI-088/UI-090: CSV/JSON/Excel file export переносится на `Публичный список`; legacy compatible export и внутренняя вкладка `Настройки → Экспорт` удаляются;
  - UI-044 в прежнем виде не реализуется, потому что target `Настройки → Экспорт → Публичный API` исчезает вместе с вкладкой; `/api/public` сохраняется.
- Не считать released 1.0.8 layout/behavior в исторических записях более поздним target, если оно явно superseded текущим ledger.
- UI-053 закрыт 2026-10-07: на странице `Аукцион` рядом с `Копировать URL таймера` добавить `Открыть предпросмотр таймера`; действие работает и для Max Amount, и для wheel context и переиспользует существующий `/timer-overlay?preview=1`.
- AUCTION-TIMER-REVIEW-002 закрыт решением пользователя 2026-10-07: tie overtime Max Amount использует saved Max Amount duration default; pending-overtime reset возвращает тот же default; отдельной overtime-настройки нет. Current 1.0.8 требует изменения, потому что сейчас использует wheel default.
- AUCTION-TIMER-REVIEW-003 закрыт решением пользователя 2026-10-07: сохранить ~1.2 s как отдельный preparation lead-in; до его окончания установленная длительность не расходуется, затем timer / применимое wheel motion / soundtrack стартуют одновременно от общей authoritative start boundary; repeated Start/Spin during lead-in must be re-entry protected.
- После этого неразрешённых timer-behavior вопросов перед dependency sorting не осталось.
- QA-1.0.8-01 и QA-1.0.8-02 остаются documented findings и **не включаются автоматически** в batch без отдельного решения пользователя. QA-1.0.8-03 уже покрыт UI-087.

## Dependency reconciliation — point 2 COMPLETE

- All accepted current-review decisions have been cross-checked against each other and exact CURRENT 1.0.8.
- Supersession/precedence is now explicit in `docs/ACTIVE_REVIEW_LEDGER.md`; no unresolved logical conflict remains in the approved review target.
- Critical shared boundaries: one position policy, one media library/availability path, one OBS visibility policy, one auction session state machine, one integration/conversion provenance pipeline, one authoritative timer/wheel start boundary.
- Rules Overlay is the main resolved exception case: UI-060 composite template owns Rules text/appearance; GLOBAL-OBS-VISIBILITY-001 later owns widget-level show-mode; Stream/OBS does not host a second Rules settings/save copy.
- Stop with unresolved source-auction pending does not auto-discard it: Stop closes without winner/materializes lots; later explicit Apply can credit the corresponding persistent target exactly once without reopening session state.
- Next plan step is point 3: sort implementation so shared foundations are changed before dependent UI and each accepted change can be manually verified in isolation.
## P01 progress — A/B/C source changes complete

- Candidate `candidate/p01-mainwindow-shell-cleanup`.
- A: remove `Файл` menu/actions — source check PASS.
- B: remove `Вид` menu; keep one direct F5 → `refresh_all()` — source check PASS.
- C: add exact non-clickable hint `F5 — обновить данные во всех разделах` in existing top menu-bar area — source check PASS.
- Runtime candidate touches only `streaming_manager/views/main_window.py` so far.
- Next: focused regression assertion, automated candidate checks, then manual QA. P01 is not accepted yet.
## P00 baseline gate — PASS — 2026-10-07

- Exact CURRENT reconfirmed: **1.0.8 / schema 19 / 15 named migrations**.
- Accepted A9 runtime anchor `74ad16c5772d5cc191f7e307203b6a574af7815c`; subsequent `main` changes before P00 were docs/README only.
- Fresh rerun of permanent Windows regression: run `36972339831`, fresh job `112658659175` — **SUCCESS**.
- Compile, DB integrity, GUI, frozen Browser Source, backup/restore, A9 migration/single-instance, Inno Setup and silent-install regressions all passed.
- P00 changed no runtime/product behavior. **P01 is the next implementation package.**
## Final implementation queue — point 3 COMPLETE

Detailed source of truth: `docs/ACTIVE_REVIEW_LEDGER.md` §4.7.

Execution rule: each package below is one candidate/review gate. Do not start the next package before automated checks + user manual acceptance of the previous package. Exact CURRENT 1.0.8 remains rollback baseline until a candidate is accepted.

1. **P00** — exact baseline/regression gate.
2. **P01** — MainWindow shell/menu/F5 cleanup.
3. **P02** — low-risk List/Public labels/dialogs.
4. **P03** — CSV/import + date/caret correctness.
5. **P04** — search/filter/selection/hide-list cleanup + total points.
6. **P05** — Public file export relocation + remove Settings Export.
7. **P06** — window sizing/state/tab-order migration + full backup ui_state.
8. **P07** — one position policy + XLSX derived position.
9. **P08** — shared media dedup/availability foundation.
10. **P09** — Stream/OBS structural cleanup and API-control removal.
11. **P10** — common OBS show-mode + timer/music widget presentation/audio help.
12. **P11** — Rules composite editor/overlay.
13. **P12** — single Auction page + lot-search scope.
14. **P13** — Auction layout/timer contextual UI/quick actions.
15. **P14** — Auction Lots Overlay + OBS-only autoscroll/footer.
16. **P15** — Wheel OBS widget + appearance/center-image UX.
17. **P16** — authoritative timer/wheel/audio timing core.
18. **P17** — Auction Settings over final timer/wheel foundations.
19. **P18** — integration connection/state UX + Auction readiness/RNG navigation.
20. **P19** — conversion/pending-rate workflow.
21. **P20** — Max Amount/Wheel business state machine.
22. **P21** — source-time pending gate + `Без текста N`.
23. **P22** — integration transparency + final History/Journal presentation.
24. **FINAL GATE** — complete automated/manual regression and release acceptance.

Mechanical coverage: UI-001…UI-090 = 90/90 accounted for, no missing IDs, no duplicate package assignment. UI-014/016/017/018/023/026/027/031/044/057 are preserve/resolved/superseded validation-only items; QA-1.0.8-01/02 remain outside this batch; QA-1.0.8-03 is handled by P21/UI-087.
## Сохранённые future scope после текущего review-batch

Эти пункты сохранены для будущего и **не являются следующей автоматической очередью**, пока текущий review-batch не сверён по зависимостям и не реализован/закрыт. Для каждого из них позже всё равно требуется fresh exact-CURRENT review и отдельное решение пользователя.

1. **Global Multi-File Import** — текущий post-D26 candidate, tracking **#4**. Распространить стандартный Windows Ctrl/Shift multi-select на применимые потоки «Добавить файл…», переиспользуя уже работающий D26 multi-select и существующие managed/external/duplicate rules.
2. **D40 — ручной порядок soundtrack/music library** — сохранённая future-идея, не реализована D26. Должна переиспользовать D43/D26 audio/media/playback state, а не создавать второй player/library backend. Это **не восстановление** superseded pre-D26 Auction playlist/Loop-One модели: с D26 текущий Auction soundtrack — один выбранный зацикленный файл из shared soundtrack library.
3. **D34 — Tourniquet donation adapter** — possible/deferred integration; перед реализацией требуется свежая проверка официального API/event delivery/auth/currencies/security.
4. **D41 — кроссплатформенная агрегация чатов + отдельный OBS chat overlay** — user-requested post-completion idea; обычные сообщения чата сами по себе не меняют auction/SM-points/timer/wheel state.
5. **Older YouTube platform/integration candidate** — сохранённая отдельная integration-direction с неуточнённым scope. Не путать с историческим W3 YouTube soundtrack-source wording и не путать с закрытым «Трейлер (YouTube)».
6. **D38 — optional LAN access to standalone OBS widgets** — post-completion only; localhost остаётся default, Internet exposure по умолчанию запрещён.
7. **Public Web / ordinary site presentation** — сохранённое future/publication direction; exact hosting/security/update/UI scope не определён и не auto-authorized.
8. **D27 — «Честное колесо»** — optional physics/final-stop winner mode; default RNG-first wheel не меняется.
9. **D7 — whole-snapshot cryptographic verification hardening** — security hardening поверх уже реализованной verification model. Public Internet verification is not implied; any LAN/public viewer endpoint remains a separate D38/Public-Web/security decision.

Порядок 2–9 восстановлен из ранее принятого complexity/dependency planning. Он нужен, чтобы не потерять зависимости, но **не означает автоматического выбора следующей реализации**.

## Явно отложенные / пропущенные пользователем

Эти пункты живы, но не должны автоматически возвращаться в текущую очередь:

- **D16 — local-wheel hover highlight** — explicitly deferred.
- **D17 — random spin duration** — explicitly skipped for now.
- **D18 — wheel visual style selector** — explicitly skipped for now.
- **D20 — visual sector split** — explicitly deferred.
- **D22 — Battle Royale** — approved post-completion, explicitly deferred 2026-09-29; tracking **#5**.
- **W1 — Space -> existing «Крутить»** — ранее реализовывался, затем сознательно снят из MAIN и оставлен post-completion. If reopened, Space must reuse the existing Spin action, stay inactive while focus is in text/numeric/other controls with normal Space behavior, and be blocked during invalid/re-entrant/ongoing spin states.
- **Сохранённые аукционы** + зависимый полный **«Новый аукцион...»** — deferred reusable-auction workflow.
- **A8 compensating Undo** — только possible post-completion; прежний whitelist не считается pre-approved, fresh safety review обязателен. Retained invariants: compensation appends an auditable reversal event instead of deleting original history, is blocked after unsafe dependent changes, and remains operator-only/not viewer-facing.
- **B6 external auction-service API adapter contract** — deferred; fresh source-of-truth/conflict/ID/dedup/write-policy review обязателен. Provider token must use B1 protected credential storage; B6 must wrap the common integration/auction backend rather than create a second auction engine.
- Дополнительные provider adapters: **iHAQ Donate v2.0, ODA Digital/OpenDonationAssistant, DonateX, VK Video Live rewards/points, Kick Channel Points/Custom Rewards, Donate Helper, DonatePay** — deferred. Все используют общий B2/B3 dedup/conversion/history/matching path, official/reliable APIs only, no page/OBS/browser scraping; provider test flags obey QA-1.0.8-02 safety invariant. Kick/VK remain feasibility-conditional; Donate Helper/iHAQ feasibility-gated; DonatePay exact realtime payload/auth contract and DonateX delivery contract require fresh revalidation; ODA remains contract-blocked.
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
- **D5 advanced History analytics** — **USER-ACCEPTED POST-COMPLETION / POST-INTEGRATION**, а не assistant-only possibility: activity heatmap, weekdays distribution, participant rankings, separate points/donations analytics, record cards и «Самый дорогой победивший лот». Core History уже реализован. Fresh review must preserve the accepted identity/comparability rules: participant identity uses provider/source + stable external user ID rather than mutable nickname; cross-service accounts are not auto-merged by matching names; unlike point systems/currencies are not naively combined without an explicit comparable basis/base-currency rule; analytics reuse authoritative completed-history snapshots rather than a second backend.
- **D9** localization/languages — user-accepted / deferred post-completion; централизованная UI-localization, без автоматического перевода пользовательских данных, названий игр и History/Journal content.
- **D10** GitHub link — conditional future item; only the official InOneLine repository is valid. The public repo exists; placement still needs fresh review.
- **D11** Telegram link — conditional on an official project Telegram resource; official project link only.
- **D12** support/Boosty link — conditional on completion/publication and an official support resource; informational/project UI, not Auction business UI.
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
