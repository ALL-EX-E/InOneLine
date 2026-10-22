# InOneLine — единый реестр будущих работ и правил

**Статус:** единый рабочий документ для будущих идей, отложенных улучшений, проверочных ворот и правил реализации.
**Создан по прямой команде пользователя 2026-10-22.**
**Назначение:** все последующие решения о том, *что делать дальше*, фиксировать **здесь**, не заводить вторую активную дорожную карту, не выбирать задачи по устаревшему фрагменту истории. GitHub history, исходные файлы и исторический `ACTIVE_REVIEW_LEDGER` используются **только для сверки доказательств**, а не как конкурирующие очереди.

> **Важнейшее:** этот документ собирает идеи и принятые ограничения, но НЕ даёт разрешения автоматически их реализовывать. Каждая функциональная задача проходит отдельный fresh exact-CURRENT review и явное решение пользователя. Изменение документа / повторная сверка допускаются по текущему прямому поручению пользователя; изменение программного runtime — нет.

## 0. Быстрый ответ: текущая очередь и последнее решение

- **Этап `ACTIVE_REVIEW_LEDGER` и его FINAL GATE завершены.** Отдельный Global Multi-File Import / Issue #4 реализован, Windows A 8/8, B 10/10, C 9/9 приняты; GitHub main regression 70/70 PASS. Не возвращать эти задачи в незавершённые из-за старых historical status.
- **D40 — ручной порядок музыкальной библиотеки: ОТЛОЖЕНО пользователем 2026-10-22.** Остаётся идеей, не реализовано; не запускать без нового выбора.
- **D34 — Tourniquet: ОТЛОЖЕНО пользователем 2026-10-22.** Исследование/адаптер не продолжать автоматически; не считать Tourniquet обязательным донат-сервисом.
- **NEXT FOR DISCUSSION: D41 — мультичат и отдельный OBS-виджет.** Это **следующий пункт для уточнения требований**, а не согласованная команда писать код. Пользователь ещё не одобрил список источников, поля сообщений, модерирование и оформление.
- Дальнейшая сохранённая ветка после D41: **older YouTube integration candidate → D38 LAN widgets → Public Web → D27 физическое колесо → D7 криптографическое усиление**. Очерёдность может изменить **только новое решение пользователя**; отложенные D40/D34 сохраняются вне активной очереди.
- Остальные идеи в разделах 2–7 не включены автоматически в текущую последовательность; их сохранение означает лишь, что они не потеряны.
- Текущий официальный публичный релиз: [1.0.8 FINAL GATE](https://github.com/ALL-EX-E/InOneLine/releases/tag/v1.0.8-final-gate-2026-10-22); SQLite schema 19 / 15 named migrations. Поздняя реализация Issue #4 уже в `main`, но **не** перепубликовала неизменяемый FINAL GATE release.

## 1. Источники, приоритет решений, достоверность

**Проверенные современные источники (GitHub, main на 2026-10-22):**
- [ACTIVE_REVIEW_LEDGER.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/ACTIVE_REVIEW_LEDGER.md) — источник исходных правил накопления, реализации, ручной приёмки и окончательного закрытия очереди P00–P23/FINAL GATE.
- [IDEA_INVENTORY.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/IDEA_INVENTORY.md) — подробный реестр пользовательских идей, статусов, отмен, зависимостей (основная база разделов 2–7 ниже).
- [ROADMAP.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/ROADMAP.md) — историческая зависимостная очередность, реализованные этапы, пострелизные изменения; устаревшие записи внутри большого cumulative-файла не превосходят позднее прямое решение пользователя.
- [PROJECT_STATE.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/PROJECT_STATE.md) — статус актуального приложения и ретроспективные уточнения.
- [DECISIONS.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/DECISIONS.md) — долговременные принятия и архитектурные границы.
- [WORKFLOW.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/WORKFLOW.md) — полный процесс разработки и релизов.
- [FUTURE_GENERAL_AUCTIONS.md](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/FUTURE_GENERAL_AUCTIONS.md) — отдельное возможное расширение предметной области без реализации.
- [Issue #4](https://github.com/ALL-EX-E/InOneLine/issues/4) — завершённый multi-file import; [Issue #5](https://github.com/ALL-EX-E/InOneLine/issues/5) — отложенный D22.
- [Исторический Wheel review](https://drive.google.com/file/d/1Vj3vVySwxzd0QHg3LWur5AEbvKwnPmdZ/view), [History review](https://docs.google.com/document/d/1acCouFybLmGU87_ZmdhqHVcEWLZVPSYlCkAFDcK3L-4/edit), [Widgets review](https://docs.google.com/document/d/1lykjF5ZpY5dRhQbkTSJM-nCSMUENtEgt0IdKszCcc7s/edit), [Settings/integrations review](https://docs.google.com/document/d/1Xo_5ybRmAz28P2luFX4OK5Rl4gmRhK0ZcLdNdtbPtPI/edit) — исторические карточки первоначальных решений; не переопределяют последующий D26/FINAL GATE.
- Проектный исторический Drive-архив [«Программа для стриминга»](https://drive.google.com/drive/folders/1iBqDmg_HegoGpb7USrCU95QJmXyfX6KO), включая [путеводитель](https://docs.google.com/document/d/1kOFeUp1pDN-V8XkUEu424wwU-DAiFa0lAIg-6UoY5dM/edit), [реестр исторических объектов](https://docs.google.com/document/d/1636eBj2_k78mk7ySNjYp3_a5OoDRm5pPZVzgUO71oz0/edit), [старый IDEA_INVENTORY](https://docs.google.com/document/d/1RvtF2vfvJj8B2eiqdV2_Bw9uo3NEku_227e6he86F5Q/edit) и [ROADMAP_RECONCILIATION](https://docs.google.com/document/d/1N_d_DrigEKQ2xOM44uJJ407JX1xFJOR5DTaPISfji3M/edit). Архивные версии **не** являются параллельными CURRENT.

**Разрешение противоречий:** (1) более позднее прямое решение пользователя; (2) принятый фактический runtime и exact source/CI/manual QA; (3) свежая каноническая документация; (4) исторические версии/скриншоты/референсы как доказательства происхождения. Прежнее `READY` в разделах до FINAL GATE не означает новую неисполненную задачу. Не уверены — писать `NEEDS REVIEW`, не выдумывать факт. Равные/похожие записи объединять **с сохранением всех исходных идентификаторов**.

**Проверяемость полноты:** первичные крупные документы и каталоги Drive сверены на первом проходе; оригиналы всех пронумерованных разговоров 1–64 и каждого байта каждого ZIP здесь **не удостоверены**. Этот пробел не следует скрывать фразой «абсолютно все исходники проверены»; дальнейшие повторные аудиты могут дополнять документ найденными подтверждёнными пунктами.

## 2. Основная сохранённая цепочка после текущего этапа

| Позиция | Код | Что сохранено | Текущее решение | Следующий gate |
|---|---|---|---|---|
| вне очереди | D40 | Ручной порядок музыки/саундтреков внутри существующего D26, без восстановления отменённого старого Auction playlist | **ОТЛОЖЕНО** прямым решением пользователя | Только новое прямое открытие |
| вне очереди | D34 | Tourniquet donations adapter с реальной API-интеграцией | **ОТЛОЖЕНО** прямым решением пользователя | Только новое открытие; до кода официальный API/auth/event contract |
| 1 | D41 | Сбор сообщений из нескольких платформ + отдельный OBS Browser Source чата | **СЛЕДУЮЩЕЕ НА ОБСУЖДЕНИЕ**, не implementation-approved | Определить точные провайдеры/поля/порядок/фильтрацию/UI |
| 2 | YouTube (историческая идея) | Отдельное интеграционное направление с пока не определённым объёмом | Сохранено, scope unclear | Не путать с D41-чатиками и старым YouTube soundtrack |
| 3 | D38 | Опциональный LAN-доступ к standalone OBS widget с другого ПК | Отложено ранее | Security/bind/firewall/discovery, localhost default |
| 4 | Public Web | Обычный публичный сайт/веб-представление списка | Только будущее направление | Хостинг, доступ, модель обновления, защита и UX |
| 5 | D27 | Дополнительный физический/«честный» вариант колеса, где результат определяется остановкой | Только будущее направление | Физика, вероятности, подтверждение RNG/аудит |
| 6 | D7 | Криптографическая защита всего подтверждённого snapshot | Только future-hardening | Независимое доказательство/ключи/verification |

Последующие строки документа перечисляют **все сохранённые категории**, включая те, которые не были включены в эту короткую зависимостную цепочку.

## 3. Каталог D-серии: подробные исходные формулировки незавершённых идей

Перенесено из `IDEA_INVENTORY.md` с сохранением первоначальных D-идентификаторов и условий; статусы D34/D40 уточнены последним решением выше. Некоторые записи **ACCEPTED AS POSSIBLE** означают только признание идеи возможной, а не разрешение на код.

- **D1 — double timer / elapsed count-up** — **ACCEPTED AS POSSIBLE / DEFERRED**; текущий single timer сохраняется.

- **D2 — закрепить/открепить лот** — **ACCEPTED AS POSSIBLE / DEFERRED**.

- **D3 — universal inline editing во всех таблицах** — **POSSIBLE POST-COMPLETION**; основной edit остаётся через Games.

- **D5 — History umbrella** — **PARTIALLY SUPERSEDED**: core реализован; advanced analytics из раздела VII **USER-ACCEPTED / DEFERRED**.

- **D7 — Winner Verification umbrella** — MAIN verification **IMPLEMENTED**; whole-snapshot cryptographic tamper-resistance **ACCEPTED AS POST-COMPLETION HARDENING**.

- **D9 — Localization/languages** — **ACCEPTED / DEFERRED POST-COMPLETION**; русский остаётся primary. Accepted boundary: локализация должна быть централизованной на уровне UI/программных строк; пользовательские данные, названия игр и исторические записи не переводятся автоматически. Конкретный набор будущих языков не зафиксирован.

- **D10 — GitHub link** — **CONDITIONAL FUTURE ITEM**; link may point only to the official InOneLine repository. Public-repo prerequisite now exists, but placement/UX still requires fresh review and is not auto-authorized.

- **D11 — Telegram link** — **CONDITIONAL FUTURE ITEM** only after an official project channel/group exists; use only the official project URL, never a placeholder/unofficial community link.

- **D12 — Support/Boosty link** — **CONDITIONAL FUTURE ITEM** only after program completion/publication and an official support page exists. Accepted placement intent is informational/project/support UI, **not Auction business UI**; use only the official support URL.

- **D13 — Pending/manual-processing queue** — **ACCEPTED AS POSSIBLE POST-COMPLETION**, не MAIN.

- **D16 — local-wheel hover highlight** — **USER-APPROVED / EXPLICITLY DEFERRED**. Accepted preserved contract: local operator wheel only; use existing `game_id`; hovered logical lot keeps its color while the others may gray temporarily; leaving restores normal colors; hover is cleared/ignored during spin; no OBS hover propagation; RNG, weights and authoritative data remain unchanged.

- **D17 — random spin duration** — **USER-APPROVED / SKIPPED FOR NOW**. Fixed duration remains default; optional min/max range; actual duration is sampled once per spin and shared by local+OBS; this is animation-duration randomness only and must not affect winner RNG/Random.org; soundtrack follows the actual resolved duration.

- **D18 — wheel visual style selector** — **USER-APPROVED / SKIPPED FOR NOW**. Current wheel remains `Обычный`/default; additional original themes are presentation-only; one persisted style applies to local+OBS; weights, probability, RNG and logical geometry semantics do not change.

- **D20 — visual sector split without changing logical probability** — **USER-APPROVED / DEFERRED**. One logical lot/game_id/weight may render as multiple visual fragments whose combined angular share equals the original lot share; authoritative RNG selects the logical lot first, fragment choice is only visual landing; local+OBS use one resolved layout.

- **D22 — Battle Royale** — **USER-APPROVED / EXPLICITLY DEFERRED**; Issue #5. Pairwise weighted duels use real RNG over temporary tournament weights; duel winner absorbs only the loser's temporary tournament weight; persistent game/auction points do not change; one selected RNG method applies consistently through the tournament; bracket/byes/extreme-weight behavior, multi-round presentation and verification storage require fresh review before implementation.

- **D23 — import custom participants** — **APPROVED POST-COMPLETION / NOT SELECTED**. Destination `В текущий аукцион` reuses existing add/increment; `Только в колесо` creates temporary wheel-only participants without normal Games/Public/status/auction-amount semantics. Preserved import design accepts `Название,вес` and `Название|вес`; omitted weight=1; empty lines ignored; invalid numeric values produce line-specific errors; duplicates within import merge by summed weight; preview+confirmation occurs before apply. Wheel-only restart lifetime remains for fresh design review; do not create a second permanent Games importer.

- **D24 — separate OBS participant list** — **APPROVED POST-COMPLETION / NOT SELECTED**. Independent Browser Source from both operator lot list and Wheel Overlay; reuse authoritative wheel state and existing standalone-list architecture; own viewer presentation settings; D20 fragments do not inflate logical participant count; operator search/filter must not filter the viewer list; future multi-round formats may show progression such as remaining N of M from authoritative run state.

- **D25 — cumulative probability of lots <= winner amount** — **APPROVED POST-COMPLETION / EXPLICITLY «НЕ НУЖНО СЕЙЧАС»**. If revisited, compute only from the immutable snapshot of a completed **ordinary weighted-wheel** run; do not recalculate from later mutable game state and do not automatically inject the metric into the core post-result/viewer UI without a separate display decision.

- **D27 — «Честное колесо» / final-stop physics winner** — **USER IDEA / POST-COMPLETION / NOT IMPLEMENTED**. Optional alternative only; default RNG-first wheel stays unchanged. Fresh design must separately settle randomness/initial conditions, physics/deceleration, weighted geometry/boundaries, timing independence, local+OBS synchronization, reproducibility and verification/audit model.

- **D28 — artificial/fixed probability mode** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. A locked percentage may be maintained only inside a separate explicit artificial-chance mode; it must never silently alter ordinary auction amounts/chances in the normal flow. Exact balancing algorithm/UI requires future design.

- **D29 — viewer names in viewer-facing table** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / INTEGRATION-DEPENDENT**. Reuse common integration participant identity/event data, not a second viewer-name store; visibility is persisted presentation state; disabling display never deletes participant data.

- **D30 — blind/hidden amounts for viewers** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. Conceal individual lot/bid amounts only on viewer-facing presentation; operator sees real values and authoritative storage/sorting/leader/weighted-wheel/RNG logic always use real values. Independent from A6 total-sum visibility.

- **D31 — `Никогда / При совпадении / Всегда` auto-processing selector** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / D13-DEPENDENT**. `Всегда` routes every eligible event automatically; `При совпадении` auto-routes only a full existing-title match; `Никогда` routes into manual processing. This must not change current B3 automatic-acceptance semantics unless future D13 Pending/manual queue is explicitly implemented.

- **D32 — viewer name as order text** — **USER-ACCEPTED, LATER NARROWED** to a separate future participant/viewer-based mode. Ordinary game auction always uses message/order text for lot/game matching and keeps sender identity separate; do not add this selector to the ordinary game-auction path.

- **D33 — alternative display sorts old/new/cheap/expensive** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; default remains expensive/amount-desc. Any alternative is display-order only and cannot alter amounts, leader/winner, wheel weights/probabilities or DB semantics. `Old/New` time criterion must be explicitly defined later and must not silently mean game release date.

- **D34 — Tourniquet donation adapter** — **USER-RETAINED / DEFERRED POST-COMPLETION**. Before any implementation re-check then-current service reliability, payment architecture, security model, official/reliable API, realtime/event-delivery contract, supported currencies/crypto assets and operational risks; do not treat it as a sole/mandatory donation channel.

- **D35 — per-bet Fortune Wheel multiplier** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. Separate from weighted winner wheel: after common integration/dedup + source-unit conversion, it may multiply/reduce/lose the resulting SM points for one bet before final lot credit. Future design must define multipliers/probabilities/trigger/controls/RNG/proof/OBS. History must retain pre-fortune SM points, result/multiplier and final credited points.

- **D36 — Viewer chooses lot** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / DEPENDS ON D35**. Treat as a dependent submode of the future per-bet mechanic, not an independent core mode; before coding, re-investigate exact viewer interaction, lot selection, payload/validation, B2/B3 conversion integration, OBS/public UI, history and failure handling.

- **D37 — presets export/import** — **USER-ACCEPTED / DEFERRED POST-COMPLETION**. Future design must explicitly define which settings/state belong to a preset, schema/version compatibility, import conflicts and security. Integration secrets/tokens are never silently exported as ordinary preset data.

- **D38 — optional LAN access for standalone OBS widgets from second PC** — **USER-ACCEPTED / EXPLICITLY DEFERRED POST-COMPLETION**. MAIN remains bound to `127.0.0.1`/localhost; do not silently expose LAN/Internet or add firewall/network setup to current backlog. If explicitly reopened, review security, bind-address selection, Windows Firewall, discovery and URL UX before implementation.

- **D40 — manual custom soundtrack/music library order** — **RETAINED POST-COMPLETION / NOT IMPLEMENTED**; D26 currently has Alphabetical/Shuffle, no manual playlist-order editor. Это отдельный future scope поверх current D26 media/audio state и **не означает восстановление superseded pre-D26 Auction playlist/Loop-One contract**.

- **D41 — cross-platform chat aggregation + separate OBS chat overlay** — **USER IDEA / POST-COMPLETION**. Twitch/YouTube/VK/other supported chat providers; ordinary chat does not mutate auction/points/lots/leader/timer/wheel/winner and is distinct from D15 AI-bot. Reuse B1/B2 auth/service adapters rather than a second connection manager; verify each platform's chat capability/API immediately before implementation. Exact cross-chat ordering, author fields, badges/emotes, moderation/filtering, history/persistence, styling and OBS presentation contract are **NOT YET APPROVED** and must be designed only when D41 is explicitly reopened.

**Выведены из будущей очереди как уже исполненные:** D19 (части center-image/UI-079 проверены в закрытом P15), D21, D26, D42 (прошёл закрытый UI-review), D43. **Нельзя восстанавливать как новую задачу:** D4, D6, D8, D14, D15, D39. D5 обозначает только ещё не выполненную advanced analytics, а не повторение core History. Названия D44 в инвентаре нет: не придумывать его.

## 4. Внешние сервисы, дополнительные адаптеры и интеграционные идеи

Текущая авторитетная интеграционная основа: существующие B1/B2/B3, защищённые credentials DPAPI, ingest + idempotent `source + external_event_id`, единая conversion/pending/History, а не второй backend. По каждому сервису заново проверять действующие official API, условия auth, event IDs, валюты/единицы, доставку/повтор, security. Не использовать web/OBS scraping как замену корректного интерфейса. Тестовые/sandbox события не могут менять реальные баллы.

## Принятые, но отложенные service targets

Каждый требует fresh current official API/auth/event review:

- **Kick Channel Points / Custom Rewards** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; это сохранённый provider capability scope, а не generic «любая интеграция Kick». Перед реализацией заново подтвердить официальный/надёжный API/auth/event contract.
- **VK Video Live rewards/points** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; сохранённый scope относится к viewer/channel reward/points capability и требует свежего official API/auth/event feasibility review.
- **Common deferred donation-adapter contract** — **USER-ACCEPTED / PRESERVE**: reuse one B2/B3 ingestion path; deduplicate by source + external event ID; convert source currency/unit through common S1/POINT 5.4 rules; donation message/order text is the ordinary game/lot text while sender identity remains separate metadata; preserve original amount/unit/message/sender/event ID/time, applied conversion rate and resulting SM points in immutable history so later rate changes do not rewrite old donations; reuse common timer rules rather than provider-specific auction logic; use official/confirmed reliable programmatic APIs only, never page scraping/OBS-widget parsing/browser automation.
- **iHAQ Donate v2.0** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Preserve source/user/amount/currency/message/event identifiers; special interactive/super-donation mechanics are not automatically auction bets without a later explicit rule.
- **Donate Helper** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Official API/reliable transport/payload must be freshly verified; if no reliable programmatic interface exists, defer. Common history/conversion/matching rules remain authoritative.
- **DonatePay** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Realtime API path using Centrifugo was considered technically plausible, but exact current endpoint/auth/channel/payload/currency/event-ID contract must be reverified; REST recovery/reconciliation only where current API supports it.
- **DonateX** — **ACCEPTED / DEFERRED / OFFICIAL-API PATH PREVIOUSLY CONFIRMED, DELIVERY CONTRACT TO REVERIFY**. Preserve its provider test flag when present and apply the general B2 test-event safety rule; exact current live-delivery/auth/cursor/payload/identifier contract must be rechecked before implementation.
- **ODA/OpenDonationAssistant** — **DEFERRED / CONTRACT-BLOCKED** до безопасного official auth/event/history contract.
- **B6 external auction-service API adapter** — **ACCEPTED / DEFERRED**. Поздняя refinement: normal direction — InOneLine source of truth -> external mirror; emergency recovery только явно подтверждённым оператором. Перед кодом заново определить conflicts, IDs, dedup, writes/recovery. The provider token is a secret and must reuse B1 protected credential storage rather than plaintext main-SQLite storage. The adapter must wrap the common integration/auction business paths rather than become a second auction backend; source-of-truth direction, conflict handling, lot-ID mapping, bid deduplication, temporary-lot behavior and allowed provider write operations all require fresh explicit design before coding.
- **Older YouTube platform/integration candidate** — **RETAINED / SCOPE UNDEFINED**. Не путать с D41 chat provider и не путать с historical soundtrack-source wording.

---

**D34 Tourniquet уже указан в §3 и помечен ОТЛОЖЕНО;** его не запускать по присутствию в этом перечне. B6 — внешний auction-mirror adapter, а не общий локальный write API; реконсиляция только явно и безопасно по разрешению оператора.

## 5. Не-D идеи: рабочие аукционы, история, media/UI, website

### 5.1 Saved/New Auction

# III. Saved/New Auction

- **«Сохранённые аукционы»** — несколько именованных reusable working auction configurations без второй Games database, с быстрым выбором/переключением и безопасными rename/delete flows — **ACCEPTED / DEFERRED TO POST-COMPLETION**. Обычный Save обновляет уже связанную saved-конфигурацию; отдельная копия создаётся только через явный Save-As-like путь.
- **Полный «Новый аукцион…»** с именем, `Начать без сохранения` / `Сохранить предыдущий и начать`, безопасной обработкой активной сессии и immutable historical name snapshot — **ACCEPTED / DEFERRED**, зависит от Saved Auctions. Создание нового working auction не очищает Games, global Journal, completed History, Saved Auctions, integration settings, Rules templates или global/widget OBS settings; сбрасывается только runtime новой рабочей сессии.
- Completed History и Saved Auctions — разные системы; переименование/удаление saved configuration не переписывает историю — **DURABLE ACCEPTED RULE**.

---

### 5.2 Операторские функции

- **Product A8 — safe compensating Undo для обратимых действий** — **ACCEPTED / DEFERRED**. 2026-09-01 пользователь решил не включать в MAIN; нужен новый safety/design review, прежний whitelist не pre-approved. Durable safety invariants from the original acceptance still survive: Undo must create a new auditable compensating event rather than delete/rewrite the original history record; it must be unavailable once later dependent changes make reversal unsafe; and Undo is operator-only inside InOneLine, never exposed to viewer OBS outputs. Exact reversible-action whitelist remains intentionally unapproved until fresh review.

- **W1 — Space вызывает существующий путь «Крутить»** — **ACCEPTED / DEFERRED**. Был реализован, но 2026-09-01 пользователь отменил включение в MAIN и попросил оставить улучшением готовой программы; current runtime этого shortcut не содержит. Accepted guard contract for any future reintroduction: Space must call the existing Spin action rather than a second start/RNG path; it must be ignored while focus is in text/numeric/other controls where Space has normal meaning, and it must not cause duplicate/re-entrant spin while spinning or when Spin is otherwise unavailable.

### 5.3 Отложенная продвинутая статистика Истории

Текущий core History уже реализован. Следующие блоки были **прямо приняты пользователем** как будущая аналитика, а не просто assistant suggestions:

- **Activity calendar / heatmap аукционов** — **ACCEPTED / POST-COMPLETION**. Derive only from authoritative completed-auction/session history; no parallel analytics backend and no guessed copy of an external intensity formula. Period/color-scale details stay for future design.
- **Распределение по дням недели** — **ACCEPTED / POST-COMPLETION**. Reuse the same inclusion rule for which sessions count as completed/conducted across History analytics; do not invent a second session-eligibility rule.
- **Лучшие участники / rankings** — **ACCEPTED / POST-INTEGRATION + POST-COMPLETION**. Requires stable participant identity based at minimum on provider/source + stable external user ID; display nickname is mutable presentation metadata, not the primary key. Accounts from different services must not be auto-merged merely because visible nicknames match; future cross-service account linking requires an explicit separate design.
- **Отдельная статистика Points и Donations** — **ACCEPTED / POST-INTEGRATION + POST-COMPLETION**. Raw source units/currencies are preserved separately and must not be naively combined without a defined comparable basis; normalized historical SM-point totals may be used where the metric is explicitly about accumulated InOneLine value.
- **Record card «Самый большой аукцион»** — **ACCEPTED / POST-COMPLETION**: use final historical session/lot snapshot values, not current mutable Games values.
- **Record card «Самый популярный»** — **ACCEPTED / POST-INTEGRATION**: greatest count of unique real participants after stable identity exists.
- **Record card «Больше всего баллов»** — **ACCEPTED / POST-INTEGRATION**: only within a comparable points system/source unless a later explicit normalization rule is designed.
- **Record card «Больше всего донатов»** — **ACCEPTED / POST-INTEGRATION**: monetary values/currencies require an explicitly defined comparable/base-currency rule; do not naively add unlike currencies.
- **«Самый дорогой победивший лот»** — **ACCEPTED / POST-COMPLETION**; считать по historical snapshot, не по текущей mutable сумме игры.

Ранний D5 umbrella поэтому **PARTIALLY SUPERSEDED**: core History реализован, а перечисленная advanced analytics остаётся принятой future work.

### 5.4 Публичная публикация, вид списка и невыбранные варианты отображения

# X. Public Web / list presentation residuals

- **Ordinary Public Web/site representation of the public game list** — **RETAINED FUTURE DIRECTION / SCOPE UNDEFINED / NOT AUTO-AUTHORIZED**. Distinct from local JSON API, OBS list overlay and XLSX mirrors.
- **Games/List `Обычный / Компактный` presentation** — earlier accepted, later **EXPLICITLY POSTPONED** until a real need appears.
- **Дополнительный общий persisted Games/List Autoscroll control** — **NO LONGER A LIVE TASK**. Более позднее решение пользователя: не добавлять отдельную новую функцию, потому что нужная автопрокрутка уже есть.
- **Auction Lots Normal/Compact** — **SPECIFICATION-RECONCILIATION ONLY**, не подтверждённый defect.

---

### 5.5 Возможное расширение на любые категории аукционов

**Статус: ACCEPTED AS POSSIBLE. Не реализовано; программные изменения не разрешены этим пунктом.**

Решение пользователя от 2026-10-22: использовать в новых публичных описаниях предметно-нейтральную терминологию, не ограничивать позиционирование одной тематикой, подготовить документационную основу для возможного расширения аукционов.

Предварительные понятия: **сессия аукциона**, **лот**, **ставка или вес**, **источник события**, **результат и история**. Это только концепция — не подтверждение универсальной модели текущего программного кода.

Для будущей реализации нужны отдельные согласования категорий лотов, статусов, интеграций, отображения в OBS, импорта/экспорта CSV/JSON/XLSX, миграций существующих записей, совместимости резервных копий, правил начислений и RNG. Каждая доработка — отдельный scope с Windows CI и ручной приёмкой.

**Что НЕ меняется в 1.0.8:** пользовательский интерфейс, схема SQLite 19, 15 миграций, таблицы и поля, API и технические идентификаторы, алгоритмы колеса и аукциона, версии, музыка, интеграции и существующие данные. Исторические QA, release notes и решения нельзя переписывать задним числом.

**Статус: ACCEPTED AS POSSIBLE / NOT IMPLEMENTED.** Нейтральные слова «аукцион/лот/запись» в публичных описаниях **не доказывают** поддержку произвольных категорий лотов текущим runtime. Нужны отдельные решения по типам, статусам, импортам, OBS, интеграциям, сохранению старых данных и миграциям.

### 5.6 Дополнительная зафиксированная UX-идея

## GLOBAL-FOCUS-001 — единое снятие focus/selection во всей программе — DEFERRED / RECORDED — 2026-10-07

- Пользователь выявил общий UX-дефект после ручной проверки P04-C: если таблица полностью заполнена строками, для снятия selection может не существовать видимой пустой области; пользователь не должен прокручивать список до самого низа только ради deselect.
- Та же проблема шире таблиц: после клика в поле ввода focus визуально/логически остаётся на нём, пока пользователь не выберет другой focusable control.
- Это не дефект только Games/Public и не должен решаться набором локальных hacks по каждой вкладке.
- Целевое продуктовое правило: должен существовать единый естественный способ убрать focus с поля и снять selection с таблицы независимо от наличия видимой пустой строки/области. Пользователь не должен искать другое поле или прокручивать длинный список вниз.
- Предпочтительно сначала исследовать один общий механизм на уровне shared UI/MainWindow/event handling; не ломать обычный click/double-click, Enter-search, keyboard navigation, dialog validation, caret/selection semantics, buttons, combo/spin boxes и explicit programmatic focus/selection.
- Конкретный жест/реализацию (например neutral-background click и/или универсальный keyboard escape fallback) утвердить при отдельном global UI review после проверки влияния на существующие widgets.
- Не расширять текущий P04-C до глобального mouse/focus subsystem. Реализовывать отдельным изолированным шагом после сортировки зависимостей.

## 6. Проверочные долги / технические ограничения, не приравниваемые к новым продуктовым идеям

- **QA-1.0.8-01** — отображение времени последней принятой интеграционной активности в `Проведение` (описано как пропуск accepted-контракта в ранней сверке). Перепроверить фактическое состояние после P18/P22 и FINAL GATE, прежде чем объявлять его текущим дефектом. Нет автоматического права на исправление.
- **QA-1.0.8-02** — гарантировать, что явно помеченные тестовые/sandbox/demo события провайдера не создают реальные начисления, лоты и изменения таймера/победителя. Требуется сверить адаптеры и current normalized-event pipeline; без подтверждённого сценария не заявлять уязвимость действующих сервисов.
- **QA-1.0.8-03 / UI-087** — историческое замечание по пустому тексту внешнего события и временным `Без текста N`. Этот пункт вошёл в пройденную очередь P21 и FINAL GATE; **не открывать повторно как новую задачу без обнаруженной регрессии**.
- **GLOBAL-FOCUS-001** — сохранённая отдельная глобальная идея единообразного снятия фокуса/выделения, со специальным status DEFERRED / RECORDED (см. фрагмент ниже).

**Важное различие:** QA-finding, возможная фича, user-deferred задача, текущая реально незакрытая регрессия и успешно реализованная задача — разные статусы. Не превращать QA-примечания в автоматический implementation scope.

**Условия мониторинга D42/UI-079 и полного UI-review:** старые `READY AFTER BATCH APPROVAL` в ранних разделах `IDEA_INVENTORY` не доказывают их незавершённость после FINAL GATE. Перед назначением пункта проверить поздний append-only журнал закрытий и настоящий `main`.

## 7. Список исключений: то, что НЕ должно самопроизвольно возвращаться в разработку

| Идентификатор / тема | Окончательная трактовка |
|---|---|
| D4 | Отдельная top-level Wheel page отклонена/заменена колесом внутри Auction |
| D6 | Универсальный composite/named Widgets builder отвергнут; standalone widgets |
| D8 | Video Requests не нужны |
| D14 | Старый umbrella superseded конкретными решениями |
| D15 | AI Twitch-bot не подтверждён как утверждённая пользователем идея InOneLine |
| D39 | Per-scene widget profiles — только historical assistant possibility, не actionable |
| F1–F9 | Исторические reject/superseded из `IDEA_INVENTORY` §XI, не таски |
| Дополнительный Games/List Autoscroll | Более поздним решением признан ненужным; уже существующей прокрутки достаточно |
| Ранний Auction playlist/Loop One | Заменён D26, D40 не восстановление старого backend |
| Автоматический перевод SM points → деньги | Отменён, S1 только source→SM points |
| Произвольная универсализация аукционов | Возможное направление, НЕ реализовано, без approval |
| FINAL GATE / Issue #4 | Принято и закрыто; старые кандидаты не новая очередь |

## 8. Обязательные правила работы — перенесены из ACTIVE_REVIEW_LEDGER

**Применимость:** изложенные ниже *организационные, инженерные и QA-правила продолжают действовать*. Историческое ограничение «новые функции приостановлены до завершения UI-review», а также требование сначала копить скриншоты до фразы `«всё делаем»`, описывали конкретный **уже завершённый** review-этап. Оно не отменяет позднюю команду пользователя вернуться к будущим идеям. При работе с любыми новыми идеями **сначала обсудить и утвердить точный scope, не писать код по одному факту присутствия пункта в реестре**.

###### 8.1 Оригинальный порядок фиксации, сортировки и приёмки из ACTIVE_REVIEW_LEDGER (§§1–3)

#### Active Review Ledger

**ПЕРВОЕ И ОБЯЗАТЕЛЬНОЕ ПРАВИЛО:** перед каждым ответом по текущей работе над InOneLine сначала сверяться с этим документом. Этот файл является рабочим журналом текущего этапа: поиск багов, доработка интерфейса и улучшение уже существующих функций. Он не разрешает автоматически менять программу.

##### 1. Текущий режим работы

Разработка новых функций **приостановлена**. Работаем только с уже готовой программой:

- ищем баги и регрессии;
- проверяем интерфейс;
- дорабатываем удобство и понятность существующего UI;
- исправляем уже существующие функции, если они работают неправильно или неполно;
- не расширяем продукт новым функционалом без отдельного решения пользователя.

Рабочий цикл для скриншотов:

1. Пользователь присылает скриншот текущей программы.
2. Сначала проверяется, какие уже существующие функции и элементы интерфейса видны на скриншоте и к каким текущим механизмам они относятся.
3. Пользователь указывает, что нужно исправить, изменить или доработать.
4. Ассистент **ничего не меняет в коде сразу**.
5. Каждое замечание сначала записывается в этот документ как отдельная задача с привязкой к существующей функции/экрану.
6. Задачи накапливаются до прямой команды пользователя **«всё делаем»**.
7. После команды «всё делаем» весь накопленный список сначала пересматривается, проверяется на дубли и зависимости и сортируется по сложности/безопасности реализации так, чтобы более простые и базовые исправления выполнялись раньше, а последующие по возможности переиспользовали уже сделанное.
8. Затем задачи выполняются **по одной**. Параллельная реализация нескольких накопленных пунктов без отдельной необходимости запрещена.
9. После каждого исправления пользователь вручную проверяет программу.
10. Следующая задача начинается только после результата ручной проверки текущей задачи и явного принятия/указания на дальнейший фикс.

**Формат ручной проверки — последнее решение пользователя:** весь чек-лист текущего candidate-пакета выдавать сразу целиком, с действиями и ожидаемыми результатами. Прежнее предпочтение выдавать по одному сценарию отменено. Уже подтверждённые сценарии отмечать PASS и не повторять без причины. Реализация по одному согласованному пакету, переиспользование существующего, стабильность, запись результатов и приёмка перед следующим пакетом сохраняются.

##### 2. Постоянное инженерное правило этого этапа

Для любого исправления действует прежний принцип проекта:

**reuse first -> minimal diff -> no parallel logic -> no new persistence unless unavoidable**

То есть:

- сначала использовать уже существующий механизм, UI-компонент, данные, setting, calculation, API, storage path, helper или backend;
- новое создавать только если существующее объективно нельзя безопасно применить;
- не создавать вторую параллельную реализацию уже существующей логики;
- не добавлять новое хранилище/состояние без крайней необходимости;
- не делать крупный рефакторинг ради удобства самого рефакторинга;
- производительность нельзя улучшать ценой стабильности, надёжности, корректности данных или отзывчивости UI;
- стабильность и сохранность пользовательских данных важнее уменьшения кода, размера или количества объектов;
- RNG, verification, auction/business semantics, schema/migrations и ownership persistence не меняются вне явно утверждённого scope;
- если проблема может быть исправлена в существующем UI/механизме локально, именно это является предпочтительным решением.

##### 3. Правила накопления задач

Статусы рабочих пунктов:

- **CAPTURED** — замечание записано, код не менялся.
- **NEEDS REVIEW** — перед реализацией требуется дополнительная сверка с текущим кодом/поведением.
- **READY AFTER BATCH APPROVAL** — задача понятна и ждёт команды «всё делаем».
- **IN PROGRESS** — выбран ровно один пункт и идёт реализация.
- **AWAITING MANUAL QA** — исправление собрано, пользователь должен проверить его вручную.
- **ACCEPTED** — пользователь подтвердил, что исправление работает как нужно.
- **REOPENED** — ручная проверка выявила проблему; исправляется тот же пункт.
- **REJECTED / CANCELLED** — пользователь отказался от изменения.

Ни один CAPTURED/READY пункт не является автоматическим разрешением изменять runtime.

##### 3.0 Правило порядка текущего UI-review

- **REVIEW-RULE-002 — следующий элемент подробного разбора всегда выбирает пользователь.**
  - После фиксации текущего пункта ассистент не переводит review на следующий UI-элемент по собственной инициативе.
  - Можно перечислять замечания только внутри выбранного пользователем экрана/элемента.
  - Следующий объект review открывается только после прямого указания пользователя.

###### 8.2 Универсальный процесс создания, QA и релиза — WORKFLOW.md (с исходными формулировками)

Ниже сохранён текст `WORKFLOW.md`; его абзац `Active Review Ledger — текущий режим` описывает закончившуюся историческую фазу и теперь читается с оговоркой §8 настоящего документа. **Текущий главный журнал будущих работ — этот файл**.

#### Development and Release Workflow

##### Основной цикл

1. Выбрать ровно один scope.
2. Выполнить fresh review против exact CURRENT.
3. Зафиксировать точный scope и получить явное одобрение пользователя.
4. Реализовать изменение в candidate-ветке, reuse-first.
5. Прогнать automated gates.
6. Собрать Windows candidate.
7. Провести сфокусированную ручную Windows-проверку.
8. При дефекте исправлять только candidate, выпускать новый FIX и повторять только нужные проверки плюс regression gates.
9. После полного PASS получить явную пользовательскую приёмку.
10. Продвигать **точно проверенные bytes**, не пересобирая installer/source после ручной приёмки.
11. Source ZIP собирать только из Git-tracked файлов через `tools/create_source_snapshot.py`; запрещено архивировать post-build workspace копированием каталога.
12. Для публикации создать новый immutable request в `.github/release/requests/` с exact artifact ID, target commit, именами файлов и SHA-256; единый `publish-accepted-release.yml` проверяет bytes, запрещает overwrite существующего tag/release, публикует без пересборки и повторно проверяет опубликованные SHA-256.
13. Обновлять `docs/PROJECT_STATE.md`, `docs/ROADMAP.md`, QA и решения.
14. Только после этого считать версию CURRENT/released.

##### Active Review Ledger — текущий режим

Пока пользователь не отменит этот режим, разработка новых product features приостановлена. Работа по багам, UI и уже существующим функциям ведётся через `docs/ACTIVE_REVIEW_LEDGER.md`.

Перед ответом по текущей работе InOneLine сначала сверяться с `ACTIVE_REVIEW_LEDGER.md`. Замечания со скриншотов сначала только фиксируются в ledger; runtime не меняется до прямой команды пользователя **«всё делаем»**. После этой команды накопленные пункты сначала проверяются на дубли/зависимости и сортируются по сложности/безопасности, затем выполняются строго по одному с обязательной ручной проверкой пользователя после каждого исправления.

##### Инженерные инварианты

Эти правила действуют для любых future feature, maintenance, optimization и cleanup scope:

- **Reuse first → minimal diff → no parallel logic → no new persistence unless unavoidable.** Существующие механизмы, данные, UI, settings, calculations, APIs и storage paths переиспользуются прежде, чем вводить новую сущность/ветку/backend.
- Новый механизм/сущность допустим только если существующий объективно непригоден для **корректности, надёжности или требуемой производительности**; удобство рефакторинга само по себе недостаточно.
- **Стабильность и работоспособность важнее ускорения/уменьшения размера.** Оптимизация не должна повышать риск зависаний, вылетов, потери данных, нарушения RNG/verification/business semantics или чрезмерного RAM/package growth.
- Любой performance/size/RAM cleanup должен быть измеримым и локальным; удаление кода/зависимостей/файлов без доказательства безопасности запрещено.
- Перед рискованным cleanup/refactor должна существовать постоянная regression/Windows QA foundation. Если проблема находится в QA/build harness, сначала исправляется QA/build слой, а runtime не меняется без отдельного approved scope.
- Вне утверждённого scope запрещено менять runtime behavior, schema/migrations, RNG/weights/probabilities, persistence ownership или пользовательские данные.

##### Версии

- Candidate/FIX не считаются релизами.
- Candidate/build staging проверяется **до** замены/продвижения безопасного артефакта; failed build/validation не должен уничтожать или перезаписывать последний принятый/безопасный archive/artifact. Historical A1 использовал temporary `.building` + fail-closed validation; current GitHub publication uses immutable accepted artifacts/requests, but safety invariant remains the same.
- Номинальный APP_VERSION candidate не увеличивает release cadence.
- Rollback — предыдущий реально принятый CURRENT.
- При release-финализации допустим отдельный metadata-only commit; он не должен менять принятые runtime/source bytes.

##### QA

Автоматические тесты не заменяют ручную Windows-проверку там, где поведение зависит от Qt, браузера, OBS, Windows media stack или реального UI.

Если пользователь сообщает `Работает`, закрывается только явно проверенный сценарий; уже пройденные сценарии не повторяются без причины.

Ручные Windows/PowerShell проверки пользователю даются **только когда они реально добавляют проверку**. По последнему решению пользователя весь чек-лист текущего candidate-пакета выдаётся **сразу целиком**, с действиями и ожидаемыми результатами. Прежнее предпочтение выдавать по одной проверке/команде отменено. Уже подтверждённые сценарии не повторяются без причины; реализация сохраняет один согласованный scope за раз и приёмку перед следующим пакетом.

###### Идентификаторы QA

- Release/reconciliation defects and accepted-scope omissions use **`QA-<version>-NN`** identifiers.
- Permanent roadmap/product identifiers such as D/A/W/B/E/R must not be reused for temporary release defects or QA findings.
- A QA finding can point to an older accepted roadmap contract, but it remains a QA finding until the user explicitly approves and accepts the runtime correction.

##### Документация

После каждого долговременного решения:

- текущее состояние → `PROJECT_STATE.md`;
- очередь/идея/статус → `ROADMAP.md`;
- долговременное правило → `DECISIONS.md`;
- release QA → `docs/qa/`;
- публичное пользовательское изменение → release notes/README при необходимости.

Нельзя полагаться на единственный старый cumulative-файл, в который бесконечно дописывались предыдущие версии. Git history теперь выполняет роль истории изменений документа.

Исторические audit/reference/release материалы при очистке активного дерева **не уничтожаются как единственный экземпляр**: retire/cleanup допустим только когда соответствующая история уже сохранена в Git history, canonical history docs или архиве Drive. Нельзя заявлять, что утраченный исходный артефакт архивирован, если доступна только поздняя текстовая реконструкция.

##### Публичная документация

Сторонние продукты нельзя использовать как публичные design/UX references. Название стороннего продукта допустимо только когда оно объективно необходимо для фактической интеграции, API/протокола, зависимости, лицензии/атрибуции или legacy-совместимости.

Перед публикацией действует `publication-wording` gate.


##### Publication requests

- Publication requests после создания не редактируются и не переиспользуются.
- Изменение старого `RELEASE_NOTES_*.md` само по себе никогда не должно запускать публикацию.
- Исторические release-specific workflows хранятся только в Git history; active CI использует единый publisher.
- Для уже существующего tag или GitHub Release publisher обязан завершаться отказом до загрузки/публикации новых assets.


### 8.3 Правило терминологии, сохранности, источников и UI

- **Conditional UI:** когда контрол логически неприменим — скрывать; когда применим, но временно недоступен — оставлять visible + disabled. Переиспользовать существующий механизм, не добавлять дубли.
- **Нейтральные названия:** текущие пользовательские подписи там, где допускает контекст, используют «список», «запись», «название», «лот». Не переписывать DB/API/schema/parser/legacy IDs, и не переименовывать автоматически принятые `ИГРАЛ / НЕ ИГРАЛ`.
- **Безопасность:** токены/пароли/API secrets не сохранять открытым текстом в SQLite/обычных настройках/логах/экспорте. В backup допускается только уже защищённый DPAPI ciphertext. Не публиковать приватные данные/metadata в GitHub.
- **Доказательства QA:** GitHub хранит канонические код/состояния/решения; Google Drive остаётся архивом текстовых логов/скриншотов QA по ранее принятому правилу. Exact artifact bytes/SHA-256 и ссылки сохранять, исторические QA не переписывать задним числом.
- **Публичные reference-названия:** названия чужих продуктов не использовать как публичные UI/design references; разрешены только фактические названия интеграций/протоколов/лицензий/совместимости.
- **C1 аудит:** после каждых 25 **принятых** выпусков/версий проводить накопительный аудит с предварительной сверкой точного счётчика. Candidate/FIX не являются выпущенными релизами.

### 8.4 Упрощённый исполнимый чек-лист для ЛЮБОГО нового пункта

1. Сначала прочитать именно **этот** документ, последнее прямое решение пользователя и exact CURRENT программного кода. Проверить ID/статус/дубликаты/зависимости.
2. Выбрать только **один** пункт, совместно проверить требования, реальные API/ограничения/совместимость, согласовать конечный scope. Если необходим дополнительный незапланированный fix, **сначала объяснить и получить одобрение**, не делать отсебятину.
3. **До одобрения не менять runtime**, migrations, RNG, данные, business logic. Разрешена документальная сверка/исправление реестра по текущему поручению.
4. После explicit approval: отдельная ветка, минимальный diff, reuse first. Строгие инварианты `no parallel logic`, `no new persistence unless unavoidable`, correctness/stability/data safety и nonblocking GUI.
5. Автоматические тесты и native Windows CI, package installer + QA ZIP; пользователю **целиком одним сообщением** чек-лист текущего пакета (действия и ожидаемый результат), не дробить без причины.
6. При ошибке открыть тот же пакет `REOPENED`, подготовить FIX, повторить релевантные QA и regression gates.
7. Только после явного Windows PASS пользователя записать **ACCEPTED**, затем продвинуть exact unchanged tested Git blobs/bytes и проверить независимую postmerge Windows CI; не пересобирать accepted installer/source.
8. Обновить **этот** документ, записать evidence/CI/QA/release status; никакого молчаливого перехода к следующему без прямой команды пользователя.
9. Публикация отдельным релизным решением с immutable manifest, verified SHA256, nonoverwrite, Git-tracked source ZIP. Не подменять уже опубликованные версии.

### 8.5 Статусы этого единого документа

- `CAPTURED` — зафиксировано, ещё не пересмотрено;
- `NEEDS REVIEW` — требуется свежая сверка с кодом/провайдером;
- `RETAINED / FUTURE` — сохранено как идея, implementation не согласован;
- `DEFERRED BY USER` — прямо отложено пользователем; не продвигать до нового прямого выбора;
- `CONDITIONAL` — требует внешней предпосылки, условий API или ещё отсутствующего ресурса;
- `READY FOR APPROVAL` — полностью уточнено, но всё ещё не разрешено менять код;
- `APPROVED FOR IMPLEMENTATION` — пользователь прямо одобрил точный scope;
- `IN PROGRESS` — выполняется один согласованный пункт;
- `AWAITING MANUAL QA` — отдельный кандидат собран и ждёт проверки пользователя;
- `REOPENED` — текущая проверка выявила дефект того же пункта;
- `ACCEPTED / VERIFIED / MERGED` — есть явно подтверждённая пользовательская приёмка и подтверждённая technical closure;
- `CANCELLED / REJECTED / SUPERSEDED` — отменено или заменено более поздним решением, не инициировать по исторической записи.

## 9. Проверка полноты и протокол повторной сверки

### 9.1 Матрица сверки

| Контроль | Проверяемый результат |
|---|---|
| Всего D-кодов | Исходный inventory D1–D43 сохранён как history, незавершённые вынесены выше; D44 не подтверждён |
| Отложенные пользователем D40/D34 | Дважды ясно зафиксирован статус DEFERRED BY USER, не следующий код |
| D41 | Первый в текущей retained review-цепочке; scope ещё не утверждён |
| Other future | Saved/New Auction, A8, W1, providers/B6, History analytics, Public Web, произвольные категории, компактный список, GLOBAL-FOCUS |
| Conditional | D10/D11/D12, Twitch eligibility, Kick/VK/OGA API, D35→D36, D13→D31 |
| Negative register | Отменённые F/D направления и автоматизация, от которой пользователь отказался |
| QA findings | Отдельно от новых функций, no auto-approval; проверять против latest main перед пометкой «current bug» |
| Правила | Основной review loop + full checklist + one scope + exact promotion + engineering & security invariants |
| Provenance | GitHub CURRENT, Drive historical, source paths, dated explicit decisions |

### 9.2 Журнал аудита

- **2026-10-22 / проход №1:** сопоставлены GitHub `ACTIVE_REVIEW_LEDGER`, `IDEA_INVENTORY`, `ROADMAP`, `PROJECT_STATE`, `WORKFLOW`, `DECISIONS`, `FUTURE_GENERAL_AUCTIONS`; Drive source-guide, file-registry, исторические IDEA/ROADMAP snapshot и каталог дополнительных архивов. Принятые FINAL GATE и Global Multi-File Import отделены от исторических unimplemented labels. Пользовательские «D40 откладываем», «D34 тоже откладываем» учтены. Сформирован единый документ. Незавершённые проверки original chat transcripts и содержимого вложенных архивов **не выдаются за выполненные**.
- **Следующие проходы:** читать именно эту версию перед каждым обновлением, искать дополнительную подтверждённую будущую идею/противоречие, сверять конкретную дату последнего user decision, дополнять **только этот** реестр, фиксировать «новых подтверждённых пунктов нет», если так и оказалось. Нельзя искусственно создавать новое задание ради активности.

- **2026-10-22 / проход №2:** сопоставлены архивные Drive ROADMAP_ADDENDUM по D17/D22/D26, а также первоначальные review колеса, истории, виджетов и настроек/интеграций. Указанные в них retained идеи D16–D25, D28–D33, D40, advanced History, provider dependencies учтены; newer supersession D26/FINAL GATE соблюдён. Из D-секции удалены два дублировавшихся исторических bullet (D1/D7), сохранилось **ровно 32 уникальных future-D кода**; иерархия заголовков цитируемых правил исправлена. Новых одобренных implementation scopes не обнаружено.

## 10. Как вести документ дальше (обязательное правило)

Любое будущее обсуждение InOneLine начинается с этого документа. Новую идею/отложенный пункт **добавлять сюда** с ID, дословной сущностью решения, источником, статусом, зависимостями, рисками, текущим Next Gate и отметкой user approval. После реализации обновлять здесь status/QA evidence/ссылку и не удалять старое решение без причины. Другие файлы GitHub остаются историческими/техническими источниками для чтения и точной сверки кода; **не вести в них альтернативную живую очередь будущих задач**. Пользователь определяет, какая идея рассматривается следующей. Работа над реализацией всегда требует нового согласованного scope.
