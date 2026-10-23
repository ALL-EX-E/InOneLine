# InOneLine — единый реестр будущих работ и правил

**Статус:** единый рабочий документ для будущих идей, отложенных улучшений, проверочных ворот и правил реализации.
**Создан по прямой команде пользователя 2026-10-22.**
**Последняя сверка: 2026-10-23.** Получены все **161/161** текстовых источников архивного каталога, повторно проверен состав его восьми разделов; результаты и границы проверки записаны в §9.3–9.5 и приложении А.
**Назначение:** все последующие решения о том, *что делать дальше*, фиксировать **здесь**, не заводить вторую активную дорожную карту, не выбирать задачи по устаревшему фрагменту истории. GitHub history, исходные файлы и исторический `ACTIVE_REVIEW_LEDGER` используются **только для сверки доказательств**, а не как конкурирующие очереди.

> **Важнейшее:** этот документ собирает идеи и принятые ограничения, но НЕ даёт разрешения автоматически их реализовывать. Каждая функциональная задача проходит отдельный fresh exact-CURRENT review и явное решение пользователя. Изменение документа / повторная сверка допускаются по текущему прямому поручению пользователя; изменение программного runtime — нет.

## 0. Быстрый ответ: текущая очередь и последнее решение

- **Этап `ACTIVE_REVIEW_LEDGER` и его FINAL GATE завершены.** Отдельный Global Multi-File Import / Issue #4 реализован, Windows A 8/8, B 10/10, C 9/9 приняты; GitHub main regression 70/70 PASS. Не возвращать эти задачи в незавершённые из-за старых historical status.
- **D40 — ручной порядок музыкальной библиотеки: ОТЛОЖЕНО пользователем 2026-10-22.** Остаётся идеей, не реализовано; не запускать без нового выбора. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L287).
- **D34 — Tourniquet: ОТЛОЖЕНО пользователем 2026-10-22.** Исследование/адаптер не продолжать автоматически; не считать Tourniquet обязательным донат-сервисом. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L281).
- **NEXT FOR DISCUSSION: D41 — мультичат и отдельный OBS-виджет.** Это **следующий пункт для уточнения требований**, а не согласованная команда писать код. Направления Twitch, YouTube, Kick и VK Video Live уже сохранены в истории; точный состав первой версии, доступные возможности каждого адаптера, поля сообщений, модерирование и оформление ещё требуют согласования. Архивный список возможностей для разбора сохранён в §3.1.
- Дальнейшая сохранённая ветка после D41: **older YouTube integration candidate → D38 LAN widgets → Public Web → D27 физическое колесо → D7 криптографическое усиление**. Очерёдность может изменить **только новое решение пользователя**; отложенные D40/D34 сохраняются вне активной очереди.
- Остальные идеи в разделах 2–7 не включены автоматически в текущую последовательность; их сохранение означает лишь, что они не потеряны.
- Текущий официальный публичный релиз: [1.0.8 FINAL GATE](https://github.com/ALL-EX-E/InOneLine/releases/tag/v1.0.8-final-gate-2026-10-22). Поздняя реализация Issue #4 уже в `main`, но **не** перепубликовала неизменяемый FINAL GATE release. Для проверенного `main` приложение имеет версию **1.0.8**, схему SQLite **21** и **17 именованных миграций**: [constants.py](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/streaming_manager/constants.py#L3-L7), [реестр миграций](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/streaming_manager/db/schema.py#L231-L338). Старые `19 / 15` в накопительных журналах не использовать как актуальную характеристику кода. Этот проход не устанавливал схему старых установленных сборок и не менял выпущенные артефакты.

## 1. Источники, приоритет решений, достоверность

**Проверенные современные источники:** `main` на коммите `658fa5e3beb2b98e4e306dd3202ab68b9c463ce8` от 2026-10-23; получен текст **81** Markdown/TXT-документа из `docs/`, README и release notes. Состояние кода и историческая приёмка различаются.
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

**Проверяемость полноты:** к 2026-10-23 получены все 161 текста из каталога §9.3, отдельно прочитаны два документа путеводителя/реестра и исторический performance-log. Текстовые представления содержат много повторяющихся накопительных записей. Получение всего текста, поиск уникальных формулировок и адресная сверка найденных решений **не равны** независимой реконструкции каждой строки всех чатов, каждой ревизии и каждого вложенного ZIP. Оригиналы всех пронумерованных разговоров 1–64 и каждого байта каждого ZIP здесь **не удостоверены**. Для каждого спорного пункта сохранять источник и `NEEDS REVIEW`; не писать «абсолютно всё проверено».

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

- **D1 — double timer / elapsed count-up** — **ACCEPTED AS POSSIBLE / DEFERRED**; текущий single timer сохраняется. Сохранённая рабочая трактовка второго счётчика — общее прошедшее время; форматы, выбор активного таймера и действие ручных поправок нужно определить отдельно. Исторический переключатель «Показывать общее время аукциона» относится к этой же идее, а не образует ещё одну функцию. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L236).

- **D2 — закрепить/открепить лот** — **ACCEPTED AS POSSIBLE / DEFERRED**. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L237).

- **D3 — universal inline editing во всех таблицах** — **POSSIBLE POST-COMPLETION**; основной edit остаётся через Games. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L238).

- **D5 — History umbrella** — **PARTIALLY SUPERSEDED**: core реализован; advanced analytics из раздела VII **USER-ACCEPTED / DEFERRED**. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L240).

- **D7 — Winner Verification umbrella** — MAIN verification **IMPLEMENTED**; whole-snapshot cryptographic tamper-resistance **ACCEPTED AS POST-COMPLETION HARDENING**. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L242).

- **D9 — Localization/languages** — **ACCEPTED / DEFERRED POST-COMPLETION**; русский остаётся primary. Accepted boundary: локализация должна быть централизованной на уровне UI/программных строк; пользовательские данные, названия игр и исторические записи не переводятся автоматически. Конкретный набор будущих языков не зафиксирован. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L244).

- **D10 — GitHub link** — **CONDITIONAL FUTURE ITEM**; link may point only to the official InOneLine repository. Public-repo prerequisite now exists, but placement/UX still requires fresh review and is not auto-authorized. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L245).

- **D11 — Telegram link** — **CONDITIONAL FUTURE ITEM** only after an official project channel/group exists; use only the official project URL, never a placeholder/unofficial community link. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L246).

- **D12 — Support/Boosty link** — **CONDITIONAL FUTURE ITEM** only after program completion/publication and an official support page exists. Accepted placement intent is informational/project/support UI, **not Auction business UI**; use only the official support URL. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L247).

- **D13 — Pending/manual-processing queue** — **ACCEPTED AS POSSIBLE POST-COMPLETION**, не MAIN. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L248).

- **D16 — local-wheel hover highlight** — **USER-APPROVED / EXPLICITLY DEFERRED**. Accepted preserved contract: local operator wheel only; use existing `game_id`; hovered logical lot keeps its color while the others may gray temporarily; leaving restores normal colors; hover is cleared/ignored during spin; no OBS hover propagation; RNG, weights and authoritative data remain unchanged. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L251).

- **D17 — random spin duration** — **USER-APPROVED / SKIPPED FOR NOW**. Fixed duration remains default; optional min/max range; actual duration is sampled once per spin and shared by local+OBS; this is animation-duration randomness only and must not affect winner RNG/Random.org; soundtrack follows the actual resolved duration. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L252).

- **D18 — wheel visual style selector** — **USER-APPROVED / SKIPPED FOR NOW**. Current wheel remains `Обычный`/default; additional original themes are presentation-only; one persisted style applies to local+OBS; weights, probability, RNG and logical geometry semantics do not change. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L253).

- **D20 — visual sector split without changing logical probability** — **USER-APPROVED / DEFERRED**. One logical lot/game_id/weight may render as multiple visual fragments whose combined angular share equals the original lot share; authoritative RNG selects the logical lot first, fragment choice is only visual landing; local+OBS use one resolved layout. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L255).

- **D22 — Battle Royale** — **USER-APPROVED / EXPLICITLY DEFERRED**; Issue #5. Pairwise weighted duels use real RNG over temporary tournament weights; duel winner absorbs only the loser's temporary tournament weight; persistent game/auction points do not change; one selected RNG method applies consistently through the tournament; bracket/byes/extreme-weight behavior, multi-round presentation and verification storage require fresh review before implementation. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L257).

- **D23 — import custom participants** — **APPROVED POST-COMPLETION / NOT SELECTED**. Destination `В текущий аукцион` reuses existing add/increment; `Только в колесо` creates temporary wheel-only participants without normal Games/Public/status/auction-amount semantics. Preserved import design accepts `Название,вес` and `Название|вес`; omitted weight=1; empty lines ignored; invalid numeric values produce line-specific errors; duplicates within import merge by summed weight; preview+confirmation occurs before apply. Wheel-only restart lifetime remains for fresh design review; do not create a second permanent Games importer. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L258).

- **D24 — separate OBS participant list** — **APPROVED POST-COMPLETION / NOT SELECTED**. Independent Browser Source from both operator lot list and Wheel Overlay; reuse authoritative wheel state and existing standalone-list architecture; own viewer presentation settings; D20 fragments do not inflate logical participant count; operator search/filter must not filter the viewer list; future multi-round formats may show progression such as remaining N of M from authoritative run state. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L259).

- **D25 — cumulative probability of lots <= winner amount** — **APPROVED POST-COMPLETION / EXPLICITLY «НЕ НУЖНО СЕЙЧАС»**. If revisited, compute only from the immutable snapshot of a completed **ordinary weighted-wheel** run; do not recalculate from later mutable game state and do not automatically inject the metric into the core post-result/viewer UI without a separate display decision. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L260).

- **D27 — «Честное колесо» / final-stop physics winner** — **USER IDEA / POST-COMPLETION / NOT IMPLEMENTED**. Optional alternative only; default RNG-first wheel stays unchanged. Fresh design must separately settle randomness/initial conditions, physics/deceleration, weighted geometry/boundaries, timing independence, local+OBS synchronization, reproducibility and verification/audit model. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L274).

- **D28 — artificial/fixed probability mode** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. A locked percentage may be maintained only inside a separate explicit artificial-chance mode; it must never silently alter ordinary auction amounts/chances in the normal flow. Exact balancing algorithm/UI requires future design. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L275).

- **D29 — viewer names in viewer-facing table** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / INTEGRATION-DEPENDENT**. Reuse common integration participant identity/event data, not a second viewer-name store; visibility is persisted presentation state; disabling display never deletes participant data. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L276).

- **D30 — blind/hidden amounts for viewers** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. Conceal individual lot/bid amounts only on viewer-facing presentation; operator sees real values and authoritative storage/sorting/leader/weighted-wheel/RNG logic always use real values. Independent from A6 total-sum visibility. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L277).

- **D31 — `Никогда / При совпадении / Всегда` auto-processing selector** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / D13-DEPENDENT**. `Всегда` routes every eligible event automatically; `При совпадении` auto-routes only a full existing-title match; `Никогда` routes into manual processing. This must not change current B3 automatic-acceptance semantics unless future D13 Pending/manual queue is explicitly implemented. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L278).

- **D32 — viewer name as order text** — **USER-ACCEPTED, LATER NARROWED** to a separate future participant/viewer-based mode. Ordinary game auction always uses message/order text for lot/game matching and keeps sender identity separate; do not add this selector to the ordinary game-auction path. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L279).

- **D33 — alternative display sorts old/new/cheap/expensive** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; default remains expensive/amount-desc. Any alternative is display-order only and cannot alter amounts, leader/winner, wheel weights/probabilities or DB semantics. `Old/New` time criterion must be explicitly defined later and must not silently mean game release date. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L280).

- **D34 — Tourniquet donation adapter** — **USER-RETAINED / DEFERRED POST-COMPLETION**. Before any implementation re-check then-current service reliability, payment architecture, security model, official/reliable API, realtime/event-delivery contract, supported currencies/crypto assets and operational risks; do not treat it as a sole/mandatory donation channel. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L281).

- **D35 — per-bet Fortune Wheel multiplier** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**. Separate from weighted winner wheel: after common integration/dedup + source-unit conversion, it may multiply/reduce/lose the resulting SM points for one bet before final lot credit. Future design must define multipliers/probabilities/trigger/controls/RNG/proof/OBS. History must retain pre-fortune SM points, result/multiplier and final credited points. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L282).

- **D36 — Viewer chooses lot** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / DEPENDS ON D35**. Treat as a dependent submode of the future per-bet mechanic, not an independent core mode; before coding, re-investigate exact viewer interaction, lot selection, payload/validation, B2/B3 conversion integration, OBS/public UI, history and failure handling. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L283).

- **D37 — presets export/import** — **USER-ACCEPTED / DEFERRED POST-COMPLETION**. Future design must explicitly define which settings/state belong to a preset, schema/version compatibility, import conflicts and security. Integration secrets/tokens are never silently exported as ordinary preset data. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L284).

- **D38 — optional LAN access for standalone OBS widgets from second PC** — **USER-ACCEPTED / EXPLICITLY DEFERRED POST-COMPLETION**. MAIN remains bound to `127.0.0.1`/localhost; do not silently expose LAN/Internet or add firewall/network setup to current backlog. If explicitly reopened, review security, bind-address selection, Windows Firewall, discovery and URL UX before implementation. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L285).

- **D40 — manual custom soundtrack/music library order** — **RETAINED POST-COMPLETION / NOT IMPLEMENTED**; D26 currently has Alphabetical/Shuffle, no manual playlist-order editor. Это отдельный future scope поверх current D26 media/audio state и **не означает восстановление superseded pre-D26 Auction playlist/Loop-One contract**. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L287).

- **D41 — cross-platform chat aggregation + separate OBS chat overlay** — **USER IDEA / POST-COMPLETION**. Twitch/YouTube/VK/other supported chat providers; ordinary chat does not mutate auction/points/lots/leader/timer/wheel/winner and is distinct from D15 AI-bot. Reuse B1/B2 auth/service adapters rather than a second connection manager; verify each platform's chat capability/API immediately before implementation. Exact cross-chat ordering, author fields, badges/emotes, moderation/filtering, history/persistence, styling and OBS presentation contract are **NOT YET APPROVED** and must be designed only when D41 is explicitly reopened. [Историческая запись](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L288).

**Выведены из будущей очереди как уже исполненные:** D19 (части center-image/UI-079 проверены в закрытом P15), D21, D26, D42 (прошёл закрытый UI-review), D43. **Нельзя восстанавливать как новую задачу:** D4, D6, D8, D14, D15, D39. D5 обозначает только ещё не выполненную advanced analytics, а не повторение core History. Названия D44 в инвентаре нет: не придумывать его.

### 3.1 D41: сохранённые подробности для будущего разбора

Источник: [архивный блок D41 от 2026-08-31](https://drive.google.com/file/d/1olA_2-4TYdsrSQDX-lfzRdQftFm1jxk7/view), источник №114 приложения А. Таблица ниже сохраняет **материал для разбора**, а не утверждённый состав реализации.

| Возможность, которую предлагалось разобрать | Сохранённая граница решения |
|---|---|
| Общий поток сообщений нескольких платформ | Сама идея D41 сохранена; порядок объединения, задержки и возможности первой версии ещё определить |
| Дополнительные источники, включая Telegram/Discord | Встречались в перечне возможностей внешнего референса; отдельного одобрения этих адаптеров нет |
| Собственный OBS-виджет чата | Часть идеи D41; оформление, набор полей и редактор ещё не утверждены |
| Идентичность автора и платформы, аватар, значки и роли | Кандидаты полей; учитывать доступность и ограничения каждого провайдера |
| Общий и отдельные счётчики зрителей | Кандидат для разбора, не обещанная текущая функция |
| TTS | Кандидат для разбора; источник голоса, триггеры и аудиопуть не согласованы |
| Выделение упоминаний | Кандидат для разбора; точное правило выделения не согласовано |
| Команды, реакции и звуковые команды | Отдельно разрешаемый слой; обычное сообщение не вызывает бизнес-действий |
| Сохранение/экспорт сообщений в текстовые файлы | Кандидат; сроки хранения, формат и приватность ещё определить |
| Сторонние emotes BTTV/FFZ/7TV | Кандидат для применимых платформ; API и допустимость проверять при выборе |
| API/WebSocket/взаимодействие через файлы | Материал для разбора, не разрешение создавать публичный write API |
| Оформление и отдельный редактор виджета | Кандидат; не восстанавливает отвергнутый универсальный конструктор виджетов |
| Модерация, фильтрация, история, мобильное/LAN-представление | Точный объём не утверждён; LAN дополнительно подчиняется D38 |

Предварительные архитектурные границы из того же источника: собственные адаптеры и единый нормализованный поток; переиспользование существующих подключения/auth и standalone-widget инфраструктуры; данные источника/канала, native message ID, source timestamp и local received_at для дедупликации и восстановления после reconnect; доступные данные автора, содержимого и удаления/модерации. Это **не утверждение окончательной схемы хранения**. Чат не зависит от установленного внешнего чат-приложения; обычные сообщения не начисляют баллы и не изменяют лоты, таймер или RNG.

Дополнение от 2026-09-03: YouTube прямо сохранён как будущий `ChatProvider` вместе с Twitch, Kick и VK Video Live — [исторический источник №69](https://drive.google.com/file/d/1B3pbjms0Ww6CknPZiwJgcmXBKPgE0DrTZ20IcNEG1R0/view). Super Chat/Super Sticker упоминались только как возможный **отдельный** будущий разбор; это не готовый донат-адаптер и не разрешение принимать такие события в аукцион.

## 4. Внешние сервисы, дополнительные адаптеры и интеграционные идеи

Текущая авторитетная интеграционная основа: существующие B1/B2/B3, защищённые credentials DPAPI, ingest + idempotent `source + external_event_id`, единая conversion/pending/History, а не второй backend. По каждому сервису заново проверять действующие official API, условия auth, event IDs, валюты/единицы, доставку/повтор, security. Не использовать web/OBS scraping как замену корректного интерфейса. Тестовые/sandbox события не могут менять реальные баллы.

### 4.1 Принятые, но отложенные service targets

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

**Граница этого решения:** предметно-нейтральное позиционирование само по себе не меняет пользовательский интерфейс, таблицы и поля, API и технические идентификаторы, алгоритмы колеса и аукциона, версии, музыку, интеграции и существующие данные. Фактические параметры проверенного `main` — схема **21 / 17 именованных миграций** (см. §0); старое `19 / 15` в записях приёмки сохраняется как история, а не как характеристика сегодняшнего исходного кода. Исторические QA, release notes и решения нельзя переписывать задним числом.

**Статус: ACCEPTED AS POSSIBLE / NOT IMPLEMENTED.** Нейтральные слова «аукцион/лот/запись» в публичных описаниях **не доказывают** поддержку произвольных категорий лотов текущим runtime. Нужны отдельные решения по типам, статусам, импортам, OBS, интеграциям, сохранению старых данных и миграциям.

### 5.6 Дополнительная зафиксированная UX-идея

**GLOBAL-FOCUS-001 — единое снятие focus/selection во всей программе — DEFERRED / RECORDED — 2026-10-07.**

- Пользователь выявил общий UX-дефект после ручной проверки P04-C: если таблица полностью заполнена строками, для снятия selection может не существовать видимой пустой области; пользователь не должен прокручивать список до самого низа только ради deselect.
- Та же проблема шире таблиц: после клика в поле ввода focus визуально/логически остаётся на нём, пока пользователь не выберет другой focusable control.
- Это не дефект только Games/Public и не должен решаться набором локальных hacks по каждой вкладке.
- Целевое продуктовое правило: должен существовать единый естественный способ убрать focus с поля и снять selection с таблицы независимо от наличия видимой пустой строки/области. Пользователь не должен искать другое поле или прокручивать длинный список вниз.
- Предпочтительно сначала исследовать один общий механизм на уровне shared UI/MainWindow/event handling; не ломать обычный click/double-click, Enter-search, keyboard navigation, dialog validation, caret/selection semantics, buttons, combo/spin boxes и explicit programmatic focus/selection.
- Конкретный жест/реализацию (например neutral-background click и/или универсальный keyboard escape fallback) утвердить при отдельном global UI review после проверки влияния на существующие widgets.
- Не расширять текущий P04-C до глобального mouse/focus subsystem. Реализовывать отдельным изолированным шагом после сортировки зависимостей.

### 5.7 Архивные примеры возможностей без отдельного утверждения

Эти сведения сохраняются, чтобы не терять происхождение обсуждения. Они **не добавляют утверждённых задач** и не расширяют принятую функциональность.

| Архивная формулировка | Как учитывать сейчас |
|---|---|
| В раннем D26 перечислялись библиотека, плейлисты, очередь, метаданные, обложки, горячие клавиши, история и crossfade | Это был перечень примеров ещё не спроектированного плеера. Позднее согласованный D26 выполнен; нельзя объявлять все ранние примеры обязательным незакрытым остатком. Ручной порядок отдельно сохранён как D40 |
| YouTube URL/video-ID как источник саундтрека | Историческое наблюдение/предложение, отдельное пользовательское утверждение не установлено. Не смешивать с будущим YouTube ChatProvider |
| Оригинальные языки внешнего интерфейса | D9 сохраняет идею локализации; конкретный список языков InOneLine отдельно не утверждён |
| Сохранённые экземпляры виджетов, общий drag/resize/snap canvas | Ранний референс позднее отвергнут самостоятельной standalone/OBS-архитектурой; D39 не является одобренным остатком |
| JSON-импорт участников, замеченный в раннем референс-пакете | Не считать утверждённым форматом D23. Сохранённый конкретный контракт D23 описывает текстовые пары название/вес; дополнительные форматы требуют решения |
| Сортировки и автосохранение в старом «Архиве» | Наблюдения внешнего интерфейса не доказывают утверждения каждой детали. Собственная согласованная идея — Saved Auctions + зависимый New Auction; третью систему «Архив» не создавать |

Источники: архив №114 (D26/D41 и ранние screenshot-решения), №32 (исправление происхождения YouTube-саундтрека), №35 (Saved Auctions/Archive), dedicated Wheel/Widgets/Settings reviews №149–151; точные ссылки — приложение А. Позднее принятое решение всегда важнее раннего списка примеров.

## 6. Проверочные долги / технические ограничения, не приравниваемые к новым продуктовым идеям

- **QA-1.0.8-01** — отображение времени последней принятой интеграционной активности в `Проведение` (описано как пропуск accepted-контракта в ранней сверке). Перепроверить фактическое состояние после P18/P22 и FINAL GATE, прежде чем объявлять его текущим дефектом. Нет автоматического права на исправление.
- **QA-1.0.8-02** — гарантировать, что явно помеченные тестовые/sandbox/demo события провайдера не создают реальные начисления, лоты и изменения таймера/победителя. Требуется сверить адаптеры и current normalized-event pipeline; без подтверждённого сценария не заявлять уязвимость действующих сервисов.
- **QA-1.0.8-03 / UI-087** — историческое замечание по пустому тексту внешнего события и временным `Без текста N`. Этот пункт вошёл в пройденную очередь P21 и FINAL GATE; **не открывать повторно как новую задачу без обнаруженной регрессии**.
- **GLOBAL-FOCUS-001** — сохранённая отдельная глобальная идея единообразного снятия фокуса/выделения, со специальным status DEFERRED / RECORDED (см. фрагмент ниже).

**Важное различие:** QA-finding, возможная фича, user-deferred задача, текущая реально незакрытая регрессия и успешно реализованная задача — разные статусы. Не превращать QA-примечания в автоматический implementation scope.

**Условия мониторинга D42/UI-079 и полного UI-review:** старые `READY AFTER BATCH APPROVAL` в ранних разделах `IDEA_INVENTORY` не доказывают их незавершённость после FINAL GATE. Перед назначением пункта проверить поздний append-only журнал закрытий и настоящий `main`.

### 6.1 Закрытые этапы, которые нельзя переносить в будущие задачи

| Пункт | Проверенный статус и граница |
|---|---|
| **P06 / GLOBAL-UI-002 / UI-032 / UI-082** | **CLOSED / MANUALLY ACCEPTED / POST-MERGE PASS**, 09.10.2026. Компоновка окна, вкладки, состояние UI и резервное копирование приняты. Старая заявка на обязательную внешнюю горизонтальную полосу не отменяет принятую компактную перестройку; актуальный минимум окна по коду — 520×360. [Закрытие](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ACTIVE_REVIEW_LEDGER.md#L3755-L3761) |
| **E1** | Готовность production EXE/сборки уже принята; старый финальный build-gate не является новой функцией |
| **E2** | Version handshake/cache-busting OBS уже реализован; ранние «отложено» перекрыты поздней приёмкой |
| **E3** | Историческая идея отдельного overtime-default перекрыта принятым общим таймером. Дополнительное время использует сохранённый Max Amount default, отдельное новое setting не требуется |
| **E4** | Windows deployment принят в пределах поддерживаемого пути запуска **короче 260 символов**. Произвольный portable-запуск из пути ≥260 не входил в принятый контракт и не является незавершённым E4; возможный bootstrap требует отдельного решения |
| **Issue #3 / conditional visibility** | GitHub issue закрыт; [финальная публикационная запись](https://github.com/ALL-EX-E/InOneLine/issues/3#issuecomment-5915717437). Не открывать по старому тексту его шапки |
| **Issue #4 / multi-file import** | Закрыт после A/B/C, ручной приёмки и независимых main gates. CSV, подключение XLSX и восстановление backup остаются однодокументными операциями; Ctrl/Shift не распространять на них автоматически |
| **Issue #233 / остановка tie-wheel** | GitHub issue закрыт 18.10.2026. Не возвращать исходное предложение как незавершённую задачу; остановка колеса и остановка всего аукциона имеют разные принятые смыслы |
| **Issue #361 / About/Description** | GitHub issue закрыт после фактической проверки нейтрального описания. Изменение слов не доказывает реализации произвольных категорий лотов |
| **Issue #366 / устойчивость P16-F QA** | **Закрыт как QA-only исправление**, а не как доказанный runtime-дефект: PR #367, merge `8e9d3f56dc78a6597f7aad7cf924138b585db932`, independent Windows run `39761374801` 69/69. [Окончательное закрытие](https://github.com/ALL-EX-E/InOneLine/issues/366#issuecomment-6338470174). Старые два красных запуска не являются текущим незакрытым issue |

Источники E1–E4: [исторический реестр](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L357-L366); E3 дополнительно подтверждён [поздним P16-D](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ACTIVE_REVIEW_LEDGER.md#L4598-L4607) и [текущим start_tie_overtime](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/streaming_manager/views/auction_parts/actions.py#L392-L401). Факт старого ручного PASS берётся из датированного журнала — этот документ не выдаёт его за новую проведённую Windows-проверку.

### 6.2 Технические наблюдения и границы аудита

- Несовпадение старых `schema 19 / 15 migrations` с фактическим `main` **21 / 17** — ошибка актуальности документации, а не новая миграция в рамках этой работы. Исправлена характеристика текущего кода здесь; исторические записи не переписаны.
- Упоминания Qt-callback после уничтожения виджетов в закрытом #366 оставлены как отдельное **наблюдение для диагностики**, без доказанного текущего воспроизведения и без разрешения менять runtime. Не смешивать с уже принятой QA-only правкой тайминга.
- Из шести найденных обычных GitHub issues только **#5 / D22** открыт; остальные перечисленные issues закрыты. Открытый #5 остаётся отложенной идеей, а не командой реализации. Состояния прочитаны через GitHub API 23.10.2026.

## 7. Список исключений: то, что НЕ должно самопроизвольно возвращаться в разработку

| Идентификатор / тема | Окончательная трактовка |
|---|---|
| D4 | Отдельная top-level Wheel page отклонена/заменена колесом внутри Auction |
| D6 | Универсальный composite/named Widgets builder отвергнут; standalone widgets |
| D8 | Video Requests не нужны |
| D14 | Старый umbrella superseded конкретными решениями |
| D15 | AI Twitch-bot не подтверждён как утверждённая пользователем идея InOneLine |
| D39 | Per-scene widget profiles — только historical assistant possibility, не actionable |
| F1 | Прямое редактирование суммы в ячейке заменено общим полем и действиями Добавить/Уменьшить |
| F2 | Отдельный быстрый `+` в каждой строке отклонён/заменён общим полем суммы |
| F3 | Обязательная ручная Accept/Reject-очередь для всех интеграций заменена B3 auto-accept; возможный D13 остаётся отдельным будущим расширением |
| F4 | Перенос временных лотов только после подтверждения победителя устарел: отмена аукциона тоже обрабатывает перенос |
| F5 | Утверждение, что connection-status архитектура впервые появилась в позднем референс-разборе, исторически неверно; это не функция |
| F6 | Повторная жеребьёвка того же незавершённого набора участников отклонена/не нужна |
| F7 | Универсальный Delete Lot из панели результата отклонён; не путать с разрешёнными отдельными безопасными операциями |
| F8 | Автоматически заменять ссылки в названии лота текстом — отклонено |
| F9 | «Шаровой аукцион» — отклонён, не держать как post-completion идею |
| Дополнительный Games/List Autoscroll | Более поздним решением признан ненужным; уже существующей прокрутки достаточно |
| Ранний Auction playlist/Loop One | Заменён D26, D40 не восстановление старого backend |
| Автоматический перевод SM points → деньги | Отменён, S1 только source→SM points |
| Произвольная универсализация аукционов | Возможное направление, НЕ реализовано, без approval |
| FINAL GATE / Issue #4 | Принято и закрыто; старые кандидаты не новая очередь |
| «Трейлер (YouTube)» | Промежуточное референс-наблюдение закрыто поздним общим review; не самостоятельная будущая задача |
| Отдельный второй Rules backend или live-only редактор | Архитектурно отвергнуты: один обычный редактор и authoritative состояние; не возвращать отдельный «Изменить текущие правила» |
| Generic local write/control API вне B6 | Не подтверждён пользователем. Одобрение внешнего B6-адаптера не разрешает новый `POST /api/v1/bids`/`PUT /lot` backend |
| Split-install / основной data-root в AppData | Отвергнут в пользу одного выбираемого installation root; не предлагать как потерянную обязательную миграцию |
| Отдельная быстрая кнопка +2 минуты | Раннее предложение отменено; не восстанавливать наряду с принятым набором ручных поправок времени |

Источник отрицательных решений: [IDEA_INVENTORY §XI](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/IDEA_INVENTORY.md#L321-L351) и архив №114. Здесь раскрыта сущность F1–F9, чтобы пользоваться единым документом без догадок по одним кодам.

## 8. Обязательные правила работы — перенесены из ACTIVE_REVIEW_LEDGER

**Применимость:** изложенные ниже *организационные, инженерные и QA-правила продолжают действовать*. Историческое ограничение «новые функции приостановлены до завершения UI-review», а также требование сначала копить скриншоты до фразы `«всё делаем»`, описывали конкретный **уже завершённый** review-этап. Оно не отменяет позднюю команду пользователя вернуться к будущим идеям. При работе с любыми новыми идеями **сначала обсудить и утвердить точный scope, не писать код по одному факту присутствия пункта в реестре**.

### 8.1 Оригинальный порядок фиксации, сортировки и приёмки из ACTIVE_REVIEW_LEDGER (§§1–3)

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

### 8.2 Универсальный процесс создания, QA и релиза — WORKFLOW.md (с исходными формулировками)

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
- **C1 аудит:** после каждых 25 **принятых** версий, реально становившихся CURRENT/released, проводить накопительный аудит. Последняя арифметическая отметка — **21/25** после 1.0.4–1.0.8; перед фактическим gate заново сверить release history. Отклонённые кандидаты, неперенесённые FIX, промежуточные шаги, не становившиеся самостоятельным CURRENT/release, и простая смена APP_VERSION не увеличивают счётчик. P00–P23 и Issue #4 не дают основания молча прибавлять по единице за каждый пакет. [Источник отметки](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ROADMAP.md#L363-L369), архивная политика №7.

#### 8.3.1 Глобальные UI-правила с сохранёнными идентификаторами

| Правило | Обязательное содержание и актуальная трактовка |
|---|---|
| **GLOBAL-UI-001** | Во всех вкладках/диалогах скрывать логически неприменимую строку/группу целиком, включая подпись и вспомогательные элементы. При возвращении применимости показывать её автоматически и сохранять значения. Контрол, нужный для понимания состояния или выбора режима, остаётся видимым; применимый, но временно недоступный — visible + disabled. Переиспользовать принятую общую инфраструктуру |
| **GLOBAL-UI-002** | Поддерживать читаемое компактное окно и достижимость действий; переключения вкладок и conditional controls не меняют самопроизвольно размер верхнего окна. **P06 закрыт и принят**: сохранять принятую адаптивную перестройку и прокрутку таблиц; не восстанавливать старые требования 1100×700/обязательной внешней полосы как новую задачу |
| **GLOBAL-TERMINOLOGY-001** | В пользовательских подписях применять «список», «запись», «название», «лот» по контексту. **ИГРАЛ / НЕ ИГРАЛ не переименовывать** без отдельной задачи; не трогать автоматически `Game`, `game_id`, DB/API keys, persisted values и parser aliases. Исторические формулировки не переписывать. Старые CSV aliases сохраняют совместимость, новые подсказки используют нейтральные названия |
| **OBS-QUICK-URL-001** | Быстрый «Копировать URL…» рядом с соответствующей функцией сохраняется, даже если настройка того же виджета есть в «Стрим / OBS». Это намеренный оперативный доступ; централизация настроек не является основанием его удалить |
| **GLOBAL-OBS-VISIBILITY-001** | Сохранять принятый P10-контракт показа существующих виджетов и preview override. Основной `/overlay` всегда видим; один List show-mode управляет embedded и standalone списком. Dormant compatibility values не удалять как мнимый новый долг; новые виджеты требуют собственного согласованного поведения |

Источники: [Ledger §§3.1–3.3](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ACTIVE_REVIEW_LEDGER.md#L70-L113), [оперативные URL](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ACTIVE_REVIEW_LEDGER.md#L2711-L2718), [закрытие P10 show-mode](https://github.com/ALL-EX-E/InOneLine/blob/658fa5e3beb2b98e4e306dd3202ab68b9c463ce8/docs/ACTIVE_REVIEW_LEDGER.md#L4044-L4053). Старые `READY` в ранних блоках читаются вместе с поздней приёмкой.

#### 8.3.2 Медиа, удалённый доступ и происхождение требований

- **Общая media-инфраструктура, отдельные каталоги по назначению.** Фоны, музыка, джинглы/саундтреки и центр колеса не складываются в один плоский каталог. Новое функциональное назначение получает свой managed-каталог через существующую инфраструктуру. Managed/external ownership, стабильные media IDs, дедупликация и обработка пропавшего исходника переиспользуются; внешний оригинал нельзя удалять как принадлежащую программе копию.
- **Аудио имеет одного владельца воспроизведения.** Новый виджет не создаёт второй независимый звуковой движок и не должен дублировать звук из-за нескольких OBS-сцен, предпросмотра или повторно открытой страницы. Сохраняются действующие AudioCoordinator и принятые маршруты «в программе / через OBS»; раннее «Timer всегда visual-only» перекрыто D43 и поздними решениями.
- **Remote/public viewer tokens — условное ограничение, не текущая отдельная функция.** Если отдельно будет разрешён LAN/public доступ, viewer-доступ должен быть read-only, отделён от service/API credentials, с возможностью отзыва и ротации. Через viewer URL не допускаются write-операции. Это условие будущего D38/Public Web, а не разрешение открыть сеть сейчас.
- **Сторонний референс не равен требованию.** Указание пользователя изучить приложение разрешает разбор; конкретная возможность становится требованием только после отдельного решения. Сохранять и помечать неподтверждённые предложения, не приписывать пользователю автоматического одобрения. Наблюдения из других личных тем пользователя не входят в требования InOneLine.

Источники: архив №83/№89 (media-purpose separation), №35 п.7 (remote viewer guard), №114 D41 (граница референс-разбора), актуальные `WORKFLOW.md`/`IDEA_INVENTORY.md`. Защита от дублирования воспроизведения не отменяет отдельно согласованный OBS-аудиомаршрут.

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

- **2026-10-23 / проход №3:** продолжена существующая сверка с остановки 48/161. Получены оставшиеся 113 текстов, а ранние 48 повторно получены для сопоставления; сверены живые списки всех восьми разделов текстового архива — дополнительных объектов вне каталога не найдено. Обработаны 161 текста, два файла путеводителя/реестра и отдельный исторический performance-log; получены 81 актуальный Markdown/TXT-документ GitHub и состояния шести обычных issues. В единый документ возвращены подробности D41 и его неподтверждённые кандидаты, уточнена будущая роль YouTube, добавлены глобальные UI/OBS-правила, условный viewer-token guard, закрытые P06/E/issue-статусы и C1 21/25. По исходникам исправлена актуальная схема: **21 / 17 именованных миграций**, вместо перенесённого из истории `19 / 15`. **Новых пользовательских разрешений на реализацию не обнаружено.** Код приложения, тесты, данные и релизные артефакты не изменялись.

### 9.3 Проверяемый охват текстового архива

| Раздел | Получено текстов | Роль в сверке |
|---|---:|---|
| Снимки документации GitHub | 6/6 | Исторические исходные правила и inventory; поздний main имеет приоритет |
| Сверки 2026-09-27 | 44/44 | Исправления происхождения, отмен, C1 и ложных «не реализовано» |
| История состояния | 76/76 | Хронология уточнений, будущие D-пункты, прекращённые кандидаты |
| История канонической документации | 13/13 | Ранние очереди и версии правил; не параллельный CURRENT |
| Устаревшие TMP0377 | 5/5 | Старые состояния для отрицательной сверки; не источники текущей очереди |
| Аудиты и требования | 8/8 | Подробные Wheel/History/Widgets/Settings/Verification решения |
| Дополнения дорожной карты | 3/3 | Поздние D17/D21/D22/D26/D43 уточнения |
| Исторические текущие сводки | 6/6 | Накопительные решения и их поздние отмены |
| **Всего каталогизированных текстов** | **161/161** | Точные имена и источники — приложение А |

Способ поиска пропусков: нормализованы переводы строк и повторяющиеся формулировки, выделены **1 575 уникальных строк с маркерами будущего/отложенного/отклонённого решения**; это **не 1 575 функций**. Числа и кодовые обозначения проверялись отдельно от смысловых блоков. Дополнительно адресно разобраны исходные review и ненумерованные уточнения: D41 reference-кандидаты, YouTube ChatProvider, remote viewer guard, Saved/New Auction, media-purpose separation и ложные незакрытые статусы. Одно наличие слова `future` или `deferred` не создаёт пункт: например, `deferred autosize` в Qt — технический термин.

### 9.4 Матрица результатов и отрицательных проверок

| Проверка | Результат для единого рабочего документа |
|---|---|
| D1–D43 | Все исходные коды классифицированы: 32 сохранённых будущих D-кода, пять выполненных и шесть отвергнутых/неподтверждённых. D44 не найден и не создан |
| D41 | Восстановлены подробности и 13 групп кандидатов; неподтверждённые TTS/counters/moderation/commands не стали утверждёнными функциями |
| YouTube | ChatProvider сохранён; старый неопределённый integration candidate, trailer и soundtrack URL не смешаны с чатом. Монетизация требует отдельного решения |
| Не-D future | Сохранены Saved/New Auction, A8 Undo, W1 Space, service adapters/B6, девять блоков аналитики History, Public Web, Compact и GLOBAL-FOCUS |
| Условные ограничения | Локализация, официальные ссылки, API/auth feasibility, remote read-only tokens, D13→D31 и D35→D36 не потеряны |
| Закрытия | P06, FINAL GATE, Issue #3/#4/#233/#361/#366 не возвращены в активную очередь по старым шапкам |
| Старые QA-кандидаты | Наличие `NOT MERGED` в исходном checklist не отменяет последующий отдельный promotion и датированный manual PASS |
| Текущая схема | По AST и исходникам: `SCHEMA_VERSION=21`, в `_init_schema` зарегистрировано 17 именованных миграций. Это документационное исправление, не запуск миграции на пользовательской БД |
| C1 | 21/25 — последняя арифметическая отметка; перед gate пересчитать по принятым CURRENT/release, а не по номеру candidate |
| Исторические имена | August A1–A12, Product A1–A8 и Maintenance A1–A10 — разные серии; одинаковые номера не объединять |
| Реализация программы | Этот проход не открывал новых implementation scopes и не менял runtime |

Сопоставление текущих функций, исторических записей и отдельных QA-доказательств находится в существующем [техническом регистре сравнения](https://github.com/ALL-EX-E/InOneLine/blob/main/docs/UNIFIED_FUNCTIONS_DECISIONS_COMPARISON_REGISTER_2026-10-23.md). Это источник доказательств, **не вторая очередь**. Его 265 code-пунктов, 377 исторических записей и 165 эпизодов QA не складываются в количество уникальных функций. У незавершённых попунктных соответствий сохраняется честный `NEEDS REVIEW`; тематическая связь не равна доказательству полного исполнения старого контракта.

### 9.5 Что этот проход не удостоверяет

- Независимое чтение полных оригинальных экспортов всех чатов, включая отсутствующие исходники; поздний пересказ не подменяет оригинал.
- Все байты каждого установщика/вложенного ZIP, все исторические ревизии Drive/GitHub и все исходные изображения. Исторический каталог и текстовые решения не заменяют такой аудит.
- Новую ручную Windows/OBS-проверку всех функций и индивидуальную code/QA-привязку каждой из 377 исторических строк. Записи о прежней приёмке остаются датированными фактами из источников.
- Отсутствие любых возможных будущих идей за пределами проверенных материалов. Обнаруженное позднее прямое решение добавляется сюда с источником; не требуется искусственно создавать задачу после прохода без новых подтверждений.

## 10. Как вести документ дальше (обязательное правило)

Любое будущее обсуждение InOneLine начинается с этого документа. Новую идею/отложенный пункт **добавлять сюда** с ID, дословной сущностью решения, источником, статусом, зависимостями, рисками, текущим Next Gate и отметкой user approval. После реализации обновлять здесь status/QA evidence/ссылку и не удалять старое решение без причины. Другие файлы GitHub остаются историческими/техническими источниками для чтения и точной сверки кода; **не вести в них альтернативную живую очередь будущих задач**. Пользователь определяет, какая идея рассматривается следующей. Работа над реализацией всегда требует нового согласованного scope.

## Приложение А. Исходные 161 текстовых документа

Это перечень доступности полученных текстов, а не 161 новая задача и не заявление о полном чтении всех исходных чатов. Номер сохраняет связь с прежним каталогом в техническом регистре сравнения. Заголовок `CURRENT` в историческом имени не задаёт сегодняшнее состояние. При использовании источника проверять поздние решения и §0 этого документа.

| № | Раздел архива | Исходный документ | Доступность текста |
|---|---|---|---|
| 1 | Снимки_документации_GitHub | [ACTIVE_REVIEW_LEDGER](https://drive.google.com/file/d/1IfPbZVrOS7V0_kT1Ct2xCi8Y7uKrK1C1zi-hoR_ZBvE/view) | Получен |
| 2 | Снимки_документации_GitHub | [ROADMAP_RECONCILIATION_2026-10-02](https://drive.google.com/file/d/1N_d_DrigEKQ2xOM44uJJ407JX1xFJOR5DTaPISfji3M/view) | Получен |
| 3 | Снимки_документации_GitHub | [USER_IDEA_INVENTORY_2026-10-02](https://drive.google.com/file/d/1RvtF2vfvJj8B2eiqdV2_Bw9uo3NEku_227e6he86F5Q/view) | Получен |
| 4 | Снимки_документации_GitHub | [PROJECT_STATE_UPDATE_1.0.8_A9_ACCEPTED_2026-10-02](https://drive.google.com/file/d/1PRA1o5pY0dZQ6XFqF2f9oXFfnuKt_3tZorVg39sJcn8/view) | Получен |
| 5 | Снимки_документации_GitHub | [POST_D26_PATCH_BACKLOG_2026-09-30](https://drive.google.com/file/d/1s1t1MERKYGX1PJESqBMOBP39h7nugpA9YMN8824scTY/view) | Получен |
| 6 | Снимки_документации_GitHub | [PUBLICATION_REFERENCE_NAMING_RULE_2026-09-28](https://drive.google.com/file/d/10eyu6wFBRdRU1gx4xNAkmKRnL5afwGplm8_lkbYnOxI/view) | Получен |
| 7 | Архив/Сверки_2026-09-27 | [C1_POLICY_AND_1.0.2_RELEASE_2026-09-28](https://drive.google.com/file/d/1CId4Dziop2eO_2CWIKFe-uVV243TcHC5CHLgTJJbV1c/view) | Получен |
| 8 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS13_FINAL_2026-09-27.txt](https://drive.google.com/file/d/14vJ-WyZAXohgZZki8NpGetamJFrBF1Ut/view) | Получен |
| 9 | Архив/Сверки_2026-09-27 | [CHANGELOG_CURRENT_PRE_PASS13_2026-09-27.md](https://drive.google.com/file/d/1BnqChUKgXMwt2vZfFvcF19leptp1NRIK/view) | Получен |
| 10 | Архив/Сверки_2026-09-27 | [WORKFLOW_RULES_CURRENT_PRE_PASS13_2026-09-27.txt](https://drive.google.com/file/d/17VIOSN2e_O3cYkA1pUnq_rNYmqfmG3PB/view) | Получен |
| 11 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_PASS13_2026-09-27.txt](https://drive.google.com/file/d/1PdhQlDZTj9AdJ1yNrSc-asPmwcWYQRjS/view) | Получен |
| 12 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_PASS13_2026-09-27.txt](https://drive.google.com/file/d/14oF2wFCNnUPFDOjtQ-E2S5ZzDNa63Sp8/view) | Получен |
| 13 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PRE_PASS13_2026-09-27.txt](https://drive.google.com/file/d/1YbzpckV9HLKzLHsikuEZm9MCfqheCFcx/view) | Получен |
| 14 | Архив/Сверки_2026-09-27 | [CHANGELOG_CURRENT_PRE_PASS12_2026-09-27.md](https://drive.google.com/file/d/1gPkFtCjIy7YEZVvq0YLncbYqh_VWAWbL/view) | Получен |
| 15 | Архив/Сверки_2026-09-27 | [WORKFLOW_RULES_CURRENT_PRE_PASS12_2026-09-27.txt](https://drive.google.com/file/d/1vkHW87lShVXKGG8nXM3ckB7b5uaA3hQP/view) | Получен |
| 16 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_PASS12_2026-09-27.txt](https://drive.google.com/file/d/1LpC0pjVrDb4pBNWQM_zJTNSQr1wj_XMx/view) | Получен |
| 17 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_PASS12_2026-09-27.txt](https://drive.google.com/file/d/1w5GSV3PcqfOqQBJQLpPUdELDEE0HMukG/view) | Получен |
| 18 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PRE_PASS12_2026-09-27.txt](https://drive.google.com/file/d/1sEnArvlzzOF_5bH78vHbhYhIUxG5MCpx/view) | Получен |
| 19 | Архив/Сверки_2026-09-27 | [CHANGELOG_CURRENT_PRE_PASS11_2026-09-27.md](https://drive.google.com/file/d/1R86cPmlg398L-bnqH5HuONLPR4e8_fpk/view) | Получен |
| 20 | Архив/Сверки_2026-09-27 | [WORKFLOW_RULES_CURRENT_PRE_PASS11_2026-09-27.txt](https://drive.google.com/file/d/1WuZJzhV7lae9TUoKQdMgGJMiVCcguf2B/view) | Получен |
| 21 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_PASS11_2026-09-27.txt](https://drive.google.com/file/d/1MX-RUveGqCmcSDcbkxNhrxdGosutc_IG/view) | Получен |
| 22 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_PASS11_2026-09-27.txt](https://drive.google.com/file/d/1DbDWX4q3LDqFCnrDJ0iSfAQDuKA-REys/view) | Получен |
| 23 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PRE_PASS11_2026-09-27.txt](https://drive.google.com/file/d/1eg8lNYLchs_SAJdcNvv1-w48pa1AKRgQ/view) | Получен |
| 24 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_PASS10_2026-09-27.txt](https://drive.google.com/file/d/1XwQcL5M5gfydaYVI1ScWarJXzEozT_X1/view) | Получен |
| 25 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_PASS10_2026-09-27.txt](https://drive.google.com/file/d/1pN1lhJWp7XYDnvuC-qiaJF7MBWJ5cWtD/view) | Получен |
| 26 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PRE_PASS10_2026-09-27.txt](https://drive.google.com/file/d/13zbRv9meFMwBhvPPy39OvCwF8SOsc5kL/view) | Получен |
| 27 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS10_2026-09-27](https://drive.google.com/file/d/1_k-dFW6FxAfHvdnT2Emb1HdTxGDuD25DGESWu32Y9dk/view) | Получен |
| 28 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_PASS8_PASS9_2026-09-27.txt](https://drive.google.com/file/d/1ji_fxmPL_lupHriJuwy6Lf-ljJD8anEw/view) | Получен |
| 29 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_PASS8_PASS9_2026-09-27.txt](https://drive.google.com/file/d/1-7JxjWn5-WjTH1baRPN1NRGtKZ1BTHNf/view) | Получен |
| 30 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PRE_PASS8_PASS9_2026-09-27.txt](https://drive.google.com/file/d/16VOV2-z8X56Sr1e-2kLxdqKbplvy0eHg/view) | Получен |
| 31 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS9_2026-09-27](https://drive.google.com/file/d/1EdjxTTRIozsVqukyaH5mHPWLX-2w4h0W6TdUQ_f_w8o/view) | Получен |
| 32 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS8_2026-09-27](https://drive.google.com/file/d/1QL_SAEaCoHc58iX_s7nmWs4tkiRxtBYbfSpsBI17_mo/view) | Получен |
| 33 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS7_2026-09-27](https://drive.google.com/file/d/1Mt70QpYYyDOzKDk-WH_PVaIcVvLlF7iFbBErsHLQ6cc/view) | Получен |
| 34 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS5_2026-09-27.txt](https://drive.google.com/file/d/13ty6vjPYt6AkfiWKFsFIe4pD-uQHn239/view) | Получен |
| 35 | Архив/Сверки_2026-09-27 | [RECONCILIATION_PASS4](https://drive.google.com/file/d/1T-NFHDXu8jDphzz4dREoVmqa72lMFTo-xw__NZcyAME/view) | Получен |
| 36 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_PASS5_PRE_PASS6_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1-fCGaC0hPs74mbYBMGQ4aCD5UJzS4_E-/view) | Получен |
| 37 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_PASS5_PRE_PASS6_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1vfoie2aGW-vVWfxpH_2pPysdGgiC8DQc/view) | Получен |
| 38 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PASS5_PRE_PASS6_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1a-5bnbEFl20orxM0G2T_VR_fFONqNUFl/view) | Получен |
| 39 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_PRE_PASS5_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1F3e11Y4iYKaHWXHS-q-cvNr11a1aRkiv/view) | Получен |
| 40 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_PRE_PASS5_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1Gf5p0UfX4_CmFeFi8JDuLl4Jdr0L4Tlf/view) | Получен |
| 41 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_PASS3_PRE_PASS5_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1EVOs5218JE7v5QuOQsqEY_i7Bbel4sZK/view) | Получен |
| 42 | Архив/Сверки_2026-09-27 | [MASTER_CURRENT_ROADMAP_RECONCILIATION_PASS1_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1LxPWbTIWzj4_rusu0-1IqdvCBLSesyXN/view) | Получен |
| 43 | Архив/Сверки_2026-09-27 | [WORKFLOW_RULES_CURRENT_RECONCILIATION_PASS1_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1bOFu6PDW3n5NoNFUdzGSSL_tboEAtUVt/view) | Получен |
| 44 | Архив/Сверки_2026-09-27 | [CHANGELOG_CURRENT_RECONCILIATION_PASS1_ARCHIVE_2026-09-27.md](https://drive.google.com/file/d/1o1Y_JZ04rHFYFSGLge8IbvUU7pJO7y2Q/view) | Получен |
| 45 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_RECONCILIATION_PASS1_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1MQoyvJpKk-lamQgaJVaiFdvXvs875uPI/view) | Получен |
| 46 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_RECONCILIATION_PASS1_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1U2TaTzFNcsLJCRQVvysSHT5R863Rz_t4/view) | Получен |
| 47 | Архив/Сверки_2026-09-27 | [WORKFLOW_RULES_CURRENT_PRE_MASTER_RECONCILIATION_2026-09-27_ARCHIVE.txt](https://drive.google.com/file/d/17c61RsLtmiE2dpkF6o3wfE7swgJX4rDG/view) | Получен |
| 48 | Архив/Сверки_2026-09-27 | [CHANGELOG_CURRENT_PRE_MASTER_RECONCILIATION_2026-09-27_ARCHIVE.md](https://drive.google.com/file/d/1z3a21miLsZRRT9rbaUVPUsj45yDGWgM7/view) | Получен |
| 49 | Архив/Сверки_2026-09-27 | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PRE_MASTER_RECONCILIATION_2026-09-27_ARCHIVE.txt](https://drive.google.com/file/d/1hH5uVGrcC85cG_22cwYS5OT-EjWBbRGF/view) | Получен |
| 50 | Архив/Сверки_2026-09-27 | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PRE_MASTER_RECONCILIATION_2026-09-27_ARCHIVE.txt](https://drive.google.com/file/d/1FmrjHPVi_AdRmDB-MsTpLtO7q-vK32kR/view) | Получен |
| 51 | Архив/История_состояния | [PROJECT_STATE_UPDATE_1.0.7_D26_RELEASED_2026-09-30.txt](https://drive.google.com/file/d/1kiCAcPfxa2gtIeuASnTowjHupZviodbb/view) | Получен |
| 52 | Архив/История_состояния | [PROJECT_STATE_UPDATE_1.0.5_D43_RELEASED_2026-09-29](https://drive.google.com/file/d/1sdnIVs19sXetyBK8FEzMNzXUaVJZgQPYgruiNbT7bz4/view) | Получен |
| 53 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.53_2026-09-02](https://drive.google.com/file/d/1DKqxg6lTpPBogGUvo3MIeZ5yydOBABJpJWea80gA7fo/view) | Получен |
| 54 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.52_2026-09-02](https://drive.google.com/file/d/18Qsp9YvWcD8cVSvXVgxjsUO58ali449dypzcM7w92UM/view) | Получен |
| 55 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.51_2026-09-02](https://drive.google.com/file/d/13-94qzgwOth4WnehbMtLBTS3FHtvPwsssujS2JFw2gI/view) | Получен |
| 56 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.50_2026-09-02](https://drive.google.com/file/d/13OKQjvCgNn2wVVq9Q0C5-MKmQVEUh5pqKEgRWuPkUYk/view) | Получен |
| 57 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.49_2026-09-02](https://drive.google.com/file/d/1aplB7Esf-Unpsljpl3g6Dh3uiMMVBNqbZdKo9AaAucs/view) | Получен |
| 58 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.48_2026-09-02](https://drive.google.com/file/d/1QD0OKtXDkXXj-Hb5Q3sEYBjYssY_lbQ5F55w70lhv4I/view) | Получен |
| 59 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.47_2026-09-02](https://drive.google.com/file/d/1RoOyaOks0XMB7h7i6xDhXV2jjlKOwdHfALT7bbtiRf8/view) | Получен |
| 60 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.46_2026-09-02](https://drive.google.com/file/d/1ZEwj5qxnq7KExvUjjLv23N6rvkyroAEDjgn05wVKvcU/view) | Получен |
| 61 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.45_2026-09-02](https://drive.google.com/file/d/1ysCDhMWYHFEJCl7k7MCnvcxZRqMx9yPRhACZBaK0UpI/view) | Получен |
| 62 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.44_2026-09-02](https://drive.google.com/file/d/1ylImWFxjBbWzrPGoNcxvlxZCL02EaFswNe5KIcbO_Ww/view) | Получен |
| 63 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.43_2026-09-02](https://drive.google.com/file/d/1VxLc6R3eZ7hQLT_vXPkxhFA91SY-kbS_wQvzsakjgGI/view) | Получен |
| 64 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.42_2026-09-02](https://drive.google.com/file/d/1CM2xifGbdq1qqDc53X0YmpWf0tbcCg987RVjOKcrdIA/view) | Получен |
| 65 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.67_2026-09-03](https://drive.google.com/file/d/1mZj6km6Eo6Jdz3el0mlBtQjqyTzKfJTA_TdnTpzhiGI/view) | Получен |
| 66 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.68_2026-09-03](https://drive.google.com/file/d/1A4U-Rb56ofPi3VFj8qwK4MpkSecc2R6RjGQ-E2icWxE/view) | Получен |
| 67 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.66_2026-09-03](https://drive.google.com/file/d/1JVUh8CIYUJW9pruLgUQM872Led1tpwIkzWF5YpqL0kU/view) | Получен |
| 68 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.65_2026-09-03](https://drive.google.com/file/d/1d1iFycg7PJh-WxYfzrKx2Li0zX6DAuYUXtAQzRK1lgM/view) | Получен |
| 69 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.63_2026-09-03](https://drive.google.com/file/d/1B3pbjms0Ww6CknPZiwJgcmXBKPgE0DrTZ20IcNEG1R0/view) | Получен |
| 70 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.63_2026-09-03.txt](https://drive.google.com/file/d/1gNoaqT-u4BlgcgLfC_NzuBETFVEa73_I/view) | Получен |
| 71 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.62_2026-09-03](https://drive.google.com/file/d/1R67BOLUWG0R38SyQ-joVBLnqRd9eIYTaKYlrAKIUFU0/view) | Получен |
| 72 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.62_2026-09-03.txt](https://drive.google.com/file/d/1U8u8VRGPytMaapdb81pbICTj-xI4FF8S/view) | Получен |
| 73 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.61_2026-09-02.txt](https://drive.google.com/file/d/1fObrGsGT2fm0pe-giccpMeD0BEZpdXTN/view) | Получен |
| 74 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.61_2026-09-02](https://drive.google.com/file/d/1-s1UJY_qDdx3gghJJjByCCJAfS67lEGBFlpH7qcKSNA/view) | Получен |
| 75 | Архив/История_состояния | [InOneLine_PROJECT_STATE_CURRENT_0.3.60_2026-09-02](https://drive.google.com/file/d/1M1Q8Ahv6XBFAiViNWTTrnnn7VcY0XnIFnmZC0ukETpo/view) | Получен |
| 76 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.60_2026-09-02.txt](https://drive.google.com/file/d/1bfV369DlRMA_u4IqAAnmdBKMvdi118UD/view) | Получен |
| 77 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.57_2026-09-02.txt](https://drive.google.com/file/d/1prspLt1QuocazsrHCNNsQDddRRz9pkAA/view) | Получен |
| 78 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.57_2026-09-02](https://drive.google.com/file/d/1uL9Y3izWjrlRPPlF6Ll--9ppOfBttEdPB235dQLdApw/view) | Получен |
| 79 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.56_2026-09-02](https://drive.google.com/file/d/1P5k3W2_74S-RBVTBAiGmV6U1SFs-2Xo133ZalR6pNk4/view) | Получен |
| 80 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.56_2026-09-02.txt](https://drive.google.com/file/d/1oTWs07aXWuxIkz1iXAHaRVOSwlTsmYDb/view) | Получен |
| 81 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.55_2026-09-02](https://drive.google.com/file/d/10P5e1rbv_2VKHOQWsEYfQtVHOfmdW3EpqDB8cNrDIgo/view) | Получен |
| 82 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.55_2026-09-02.txt](https://drive.google.com/file/d/1qD1-OPI8h8TNfyTud-Kik1Mqi57ZDljU/view) | Получен |
| 83 | Архив/История_состояния | [StreamingManager_PROJECT_STATE_CURRENT_0.3.54_2026-09-02](https://drive.google.com/file/d/16cnx5O1VCBPFMnijwn7atpnucbHxmDBr0aimOJo238Y/view) | Получен |
| 84 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.54_2026-09-02.txt](https://drive.google.com/file/d/1jkk_CwLYaLP6qJoOkWLxG0qxVhBKP0E3/view) | Получен |
| 85 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.53_2026-09-02.txt](https://drive.google.com/file/d/1C_l67G3gYbfA1ahPRG8eIqnicqhlaodM/view) | Получен |
| 86 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.52_2026-09-02.txt](https://drive.google.com/file/d/1TL0wPAxfGd9RvnUEfRqcunkthN5Ilowu/view) | Получен |
| 87 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.51_2026-09-02.txt](https://drive.google.com/file/d/1IDstp88oq4KKc-xGtqODl56DYDK0VcUM/view) | Получен |
| 88 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.50_2026-09-02.txt](https://drive.google.com/file/d/18IvXubGwcTozj2ruy8HbwQ-LhswXLSHM/view) | Получен |
| 89 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.49_2026-09-02.txt](https://drive.google.com/file/d/1_91IEXYqaHKTDYjO1chp5EnCV3i7ECdB/view) | Получен |
| 90 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.48_2026-09-02.txt](https://drive.google.com/file/d/1GEuZkqT1G-9PZKJ3p5A480O6gghdyBvI/view) | Получен |
| 91 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.47_2026-09-02.txt](https://drive.google.com/file/d/16agr-6XDjDL85pofwFc2LKhG6iKre620/view) | Получен |
| 92 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.46_2026-09-02.txt](https://drive.google.com/file/d/1u1oDF_k-jTv-jTGpkIkeiRanijnZ-JRW/view) | Получен |
| 93 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.45_2026-09-02.txt](https://drive.google.com/file/d/1w4TwAXMecwTaQhSQtyNIBi2DOUvFIktj/view) | Получен |
| 94 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.44_2026-09-02.txt](https://drive.google.com/file/d/1b-BX6jiVO-ioISZvdOlbn_CAGpnAFg8N/view) | Получен |
| 95 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.43_2026-09-02.txt](https://drive.google.com/file/d/1Xx0AqJ62rKyJ8vusgTkGEmWs_CqS8sWj/view) | Получен |
| 96 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.42_2026-09-02.txt](https://drive.google.com/file/d/15ze9Ytd-PEvh_fZkmVLr2g8-RA8wv2ag/view) | Получен |
| 97 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.36_2026-09-01_SMOKE_TRACEBACK.txt](https://drive.google.com/file/d/1xxZj32h6OvpPXMnXDU9AP20mrB2V3Y0f/view) | Получен |
| 98 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.35_2026-09-01_FINAL_ACCEPTED.txt](https://drive.google.com/file/d/1EkNRroEjUQT7wYGGFLa2ecrziy7s_Yct/view) | Получен |
| 99 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.34_2026-08-31.txt](https://drive.google.com/file/d/17HWfdhXZQlq6zLhBZYq3LmIdyuCzZnlR/view) | Получен |
| 100 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.33_2026-08-31.txt](https://drive.google.com/file/d/1Vj-OrtSgf2GFAO2RhqLKUnxmHWBsIWCM/view) | Получен |
| 101 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.32_2026-08-31.txt](https://drive.google.com/file/d/1GxGO6H1YlDC_o3JuFtZMFyNvjDi-8qCi/view) | Получен |
| 102 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.31_2026-08-31.txt](https://drive.google.com/file/d/1oBFJdzieFY-cUlG_-0GioUbaqLVThzqq/view) | Получен |
| 103 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.30_2026-08-31.txt](https://drive.google.com/file/d/1w0l0qKOl-3obcYE3AvchmxrpsSFbB7jx/view) | Получен |
| 104 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.29_2026-08-31.txt](https://drive.google.com/file/d/1_UjBLoTRDLdhOWC27Ixw5tSoBaHhXmzc/view) | Получен |
| 105 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.28_2026-08-31.txt](https://drive.google.com/file/d/1Chjh8KQH6rLaKnCVxyQfoEeNETX0UIcR/view) | Получен |
| 106 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.27_2026-08-31.txt](https://drive.google.com/file/d/1BMtrTTsQRH_EQUvOlehzIM16zecR20mP/view) | Получен |
| 107 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.26_2026-08-31.txt](https://drive.google.com/file/d/1aRd8tNAZTk-FbCjb_i0QOdHWiomcM96I/view) | Получен |
| 108 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.25_2026-08-31.txt](https://drive.google.com/file/d/1Qv4D8UpJr59VTNKGWV_PznsSRxhH1Mqr/view) | Получен |
| 109 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.24_2026-08-31.txt](https://drive.google.com/file/d/17iLyvBtoxwiwW8_RSZnSlBUpammvvxhp/view) | Получен |
| 110 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.23_2026-08-31.txt](https://drive.google.com/file/d/1dk4BC6ljbmHOUf2XBiWJxKZmuODT6qUZ/view) | Получен |
| 111 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.22_2026-08-31.txt](https://drive.google.com/file/d/1Y94g8AgEbgzAa1fNvatKsgxPQNEEF9Fr/view) | Получен |
| 112 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.21_2026-08-31.txt](https://drive.google.com/file/d/1InFYaPgTpj1TxJmn-5XCfhJHsZ21xZV6/view) | Получен |
| 113 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.20_2026-08-31.txt](https://drive.google.com/file/d/1pGX6ajTDRHgJx8XjqxwVlVMbMU7xHwo1/view) | Получен |
| 114 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.19_2026-08-31.txt](https://drive.google.com/file/d/1olA_2-4TYdsrSQDX-lfzRdQftFm1jxk7/view) | Получен |
| 115 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.16_2026-08-22.txt](https://drive.google.com/file/d/1-oWtf3Q6n6q11A_tugr4Gdk95szAaX-4/view) | Получен |
| 116 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.15_2026-08-22.txt](https://drive.google.com/file/d/1fyVYdBHx33_4I1XeCtwluJ_0fS4oGRce/view) | Получен |
| 117 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.14_2026-08-22.txt](https://drive.google.com/file/d/16FAtM3nvqqfq9IRdCHIpifPmBA4tsgmu/view) | Получен |
| 118 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.13.txt](https://drive.google.com/file/d/1mhzfHgvcyhtIJ8JRP9RrFy8qcluYl5li/view) | Получен |
| 119 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.12.txt](https://drive.google.com/file/d/1q-wmVRdoLf7Wb3nuDMxk9E5UChF-MwEd/view) | Получен |
| 120 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.11.txt](https://drive.google.com/file/d/1UdkRVKHn5xXMVxFmrvJ86bcsAQWnGN46/view) | Получен |
| 121 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.10.txt](https://drive.google.com/file/d/1FCLsZK8byEd9FBAwdi5x_mA-5_leDPPh/view) | Получен |
| 122 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.09.txt](https://drive.google.com/file/d/15zTOVCFxtKxhbx7CKLMxbsFZT1XbW11x/view) | Получен |
| 123 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.08.txt](https://drive.google.com/file/d/19XTawIZ79gjTrriBOru8j1ezEiuQuuLg/view) | Получен |
| 124 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.07.txt](https://drive.google.com/file/d/1CaJixFCBVSFYtwcjw9vEnhIj7LWEKCoP/view) | Получен |
| 125 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.06.txt](https://drive.google.com/file/d/1Ywy9wQyacm3GJ77-Hmm_-0MTPKhofTyf/view) | Получен |
| 126 | Архив/История_состояния | [PROJECT_STATE_UPDATE_0.3.05.txt](https://drive.google.com/file/d/1mWZvPKSaHYkZj2WydkwU6GgNlP3TokSb/view) | Получен |
| 127 | Архив/История_канонической_документации | [WORKFLOW_RULES_CURRENT_PASS2_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1L_UfGMSLDOzCm7cOX7w8i6XYt8qAa_qD/view) | Получен |
| 128 | Архив/История_канонической_документации | [CHANGELOG_CURRENT_PASS2_ARCHIVE_2026-09-27.md](https://drive.google.com/file/d/17jqUJjDmJbPYcDFJSMCdhCGNG4_9hM7K/view) | Получен |
| 129 | Архив/История_канонической_документации | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_PASS2_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1URCwfJ9k1z2SdyXOrCcZzoGahE95E0VK/view) | Получен |
| 130 | Архив/История_канонической_документации | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_PASS2_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1SYTZazKb2-40su3TqLd1EEfKxWClyWy5/view) | Получен |
| 131 | Архив/История_канонической_документации | [MASTER_CURRENT_ROADMAP_PASS2_ARCHIVE_2026-09-27.txt](https://drive.google.com/file/d/1MpDQmWlo0FpYoQb4oeifTs6HUR770HMW/view) | Получен |
| 132 | Архив/История_канонической_документации | [PROJECT_HISTORY_AND_ROADMAP_PRE_D42_ARCHIVE.txt](https://drive.google.com/file/d/1lhqoeg-t1QxB5qgmeRzSVCjsjfGF4B4X/view) | Получен |
| 133 | Архив/История_канонической_документации | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_PRE_D42_ARCHIVE.txt](https://drive.google.com/file/d/14DIEOMr-icvYk99r77cVvxMAPhnrxZdP/view) | Получен |
| 134 | Архив/История_канонической_документации | [CHANGELOG_LEGACY_PRE_2026-09-02_ARCHIVE.md](https://drive.google.com/file/d/1lYS1FNSPT5PyvYwbwNhNjvLsK9csEtUr/view) | Получен |
| 135 | Архив/История_канонической_документации | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT_1.0.0_ARCHIVE.txt](https://drive.google.com/file/d/1khccb7uJu5S9QbsHyU_TT3eRwX6RRk2l/view) | Получен |
| 136 | Архив/История_канонической_документации | [PROJECT_HISTORY_AND_ROADMAP_CURRENT_1.0.0_ARCHIVE.txt](https://drive.google.com/file/d/1RJ-qwVWOm0PngsB3u9yA9U-YdCDSqLKE/view) | Получен |
| 137 | Архив/История_канонической_документации | [WORKFLOW_RULES_CURRENT_1.0.0_ARCHIVE.txt](https://drive.google.com/file/d/18avOmPSEUK7enGueDJQdXoMb5SI1ul1c/view) | Получен |
| 138 | Архив/История_канонической_документации | [CHANGELOG_CURRENT_1.0.0_ARCHIVE.md](https://drive.google.com/file/d/1HJtaR48QSIE91EtkDV7f7xnCuXs8KxzP/view) | Получен |
| 139 | Архив/История_канонической_документации | [BUILD_INFO_CURRENT_1.0.0_ARCHIVE.txt](https://drive.google.com/file/d/1-e_uZPfNSxhj-7CWNl9ysZO8zsusL0FC/view) | Получен |
| 140 | Архив/Устаревшие_TMP0377 | [__TMP0377_CHANGELOG_CURRENT.md](https://drive.google.com/file/d/1PdOssELvFlh1sATK1ke5kbJfELDyXrAx/view) | Получен |
| 141 | Архив/Устаревшие_TMP0377 | [__TMP0377_BUILD_INFO_CURRENT.txt](https://drive.google.com/file/d/1YQlqEm1FjFA7LczkN-3lyOVzb9smckKI/view) | Получен |
| 142 | Архив/Устаревшие_TMP0377 | [__TMP0377_APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT.txt](https://drive.google.com/file/d/1qVy-aiFFiLs8-MEFfNdU5eiTWE-CGtyG/view) | Получен |
| 143 | Архив/Устаревшие_TMP0377 | [__TMP0377_PROJECT_HISTORY_AND_ROADMAP_CURRENT.txt](https://drive.google.com/file/d/1X4B31oka2Jt9P20eukNMd6PTBmxo-mne/view) | Получен |
| 144 | Архив/Устаревшие_TMP0377 | [__TMP0377_WORKFLOW_RULES_CURRENT.txt](https://drive.google.com/file/d/1AC79L2uvuYAcaIptuQFyFQUSCQkvveqB/view) | Получен |
| 145 | Архив/Аудиты_и_требования | [FULL_AUDIT_CHATS_FROM_2026-08-01_AND_DRIVE_2026-08-31.txt](https://drive.google.com/file/d/1pEDrb1lxiuzXjmn-XNtL8gYQ-BGIMNOt/view) | Получен |
| 146 | Архив/Аудиты_и_требования | [FULL_PROJECT_HISTORY_DEDUP_AUDIT_2026-08-29](https://drive.google.com/file/d/1xkdEIbDHKg5sIhvIdVpif7-gVZ9YYIjKDPZ1Q_WfQMQ/view) | Получен |
| 147 | Архив/Аудиты_и_требования | [POINTAUC_WINNER_VERIFICATION_PAGE_REVIEW_2026-08-30](https://drive.google.com/file/d/11x6kSyxt26T3jLxVcVTfYV3PllUTP5R_pBqlH58yFTw/view) | Получен |
| 148 | Архив/Аудиты_и_требования | [POINTAUC_HISTORY_PAGE_REVIEW_2026-08-25](https://drive.google.com/file/d/1acCouFybLmGU87_ZmdhqHVcEWLZVPSYlCkAFDcK3L-4/view) | Получен |
| 149 | Архив/Аудиты_и_требования | [POINTAUC_WIDGETS_PAGE_REVIEW_2026-08-28](https://drive.google.com/file/d/1lykjF5ZpY5dRhQbkTSJM-nCSMUENtEgt0IdKszCcc7s/view) | Получен |
| 150 | Архив/Аудиты_и_требования | [POINTAUC_SETTINGS_PAGE_REVIEW_2026-08-26](https://drive.google.com/file/d/1Xo_5ybRmAz28P2luFX4OK5Rl4gmRhK0ZcLdNdtbPtPI/view) | Получен |
| 151 | Архив/Аудиты_и_требования | [POINTAUC_WHEEL_PAGE_REVIEW_2026-08-24.txt](https://drive.google.com/file/d/1Vj3vVySwxzd0QHg3LWur5AEbvKwnPmdZ/view) | Получен |
| 152 | Архив/Аудиты_и_требования | [AUDIT_CHATS_1-6_AND_DRIVE_2026-08-24.txt](https://drive.google.com/file/d/1RLmQbkBQiLfSp3A5oYzly73_sIkBeRUW/view) | Получен |
| 153 | Архив/Дополнения_дорожной_карты | [ROADMAP_ADDENDUM_2026-09-30_D26_RELEASED.txt](https://drive.google.com/file/d/1_DKh3wVbRIjjU3QjVT52gEzFSH4GSviS/view) | Получен |
| 154 | Архив/Дополнения_дорожной_карты | [ROADMAP_ADDENDUM_2026-09-29_D21_RELEASED_D22_NEXT.txt](https://drive.google.com/file/d/1YdyZz0fEl3dMktWKvlnW58Tc-UgI7JL6/view) | Получен |
| 155 | Архив/Дополнения_дорожной_карты | [ROADMAP_ADDENDUM_2026-09-28_D17_SKIP_D43_OBS_AUDIO](https://drive.google.com/file/d/1eDjzNbas2EvocGLmMsqflcv014IorZqc/view) | Получен |
| 156 | Архив/Исторические_текущие_сводки | [PROJECT_HISTORY_AND_ROADMAP_CURRENT.txt](https://drive.google.com/file/d/1WyJOx4u5tnEtAd00mQEgOr7onwBRErdR/view) | Получен |
| 157 | Архив/Исторические_текущие_сводки | [MASTER_CURRENT_ROADMAP.txt](https://drive.google.com/file/d/1bMqUdz8ZqW3a8EjZ6ADhPXtDj4AcayJU/view) | Получен |
| 158 | Архив/Исторические_текущие_сводки | [APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT.txt](https://drive.google.com/file/d/1g-AuJLSWz96QIHNo4KQoHWxWgTHRlbCS/view) | Получен |
| 159 | Архив/Исторические_текущие_сводки | [WORKFLOW_RULES_CURRENT.txt](https://drive.google.com/file/d/1ZV7K3ViyPY4YmUU8Fyu13YhZn4u0O69g/view) | Получен |
| 160 | Архив/Исторические_текущие_сводки | [BUILD_INFO_CURRENT.txt](https://drive.google.com/file/d/152QAXlXe1NDkjaUrPvcpzpbCJPNy2c--/view) | Получен |
| 161 | Архив/Исторические_текущие_сводки | [CHANGELOG_CURRENT.md](https://drive.google.com/file/d/1qB6_taNGG7vs1jE9ce0NRcYqlOntpMkV/view) | Получен |

