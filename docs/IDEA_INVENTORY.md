# InOneLine — Полный реестр пользовательских идей

Обновлено: **2026-10-02**

Этот файл — долговременный инвентарь продуктовых идей и решений пользователя по InOneLine / Streaming Manager. Он не заменяет `PROJECT_STATE.md` и `ROADMAP.md`: здесь сохраняется **полная история идей**, включая уже выполненные, отложенные, отклонённые и superseded.

Проверены:
- доступная история рабочих чатов «Программа для стрима» 1–31;
- прямые пользовательские решения августа–октября 2026;
- старые cumulative Drive history/order/audit records и dedicated review documents;
- GitHub current source, Issues, release notes 1.0.0–1.0.8 и maintenance QA.

## Как читать статусы

- **IMPLEMENTED / ACCEPTED** — реализовано и прошло пользовательскую приёмку.
- **ACCEPTED / DEFERRED** — идея пользователем принята, но реализация отложена.
- **ACCEPTED AS POSSIBLE** — пользователь согласился сохранить идею как возможное улучшение; это не pre-authorization на код.
- **CONDITIONAL** — идея принята только при появлении prerequisite/resource/API.
- **REJECTED** — пользователь отказался от функции.
- **SUPERSEDED** — ранняя формулировка заменена более поздним решением.
- **EXISTING / PRESERVE** — это уже существующее поведение, которое требуется сохранять, а не новая задача.
- **NOT USER-APPROVED / HISTORICAL** — попало в старые assistant-authored планы, но прямого пользовательского утверждения нет.

Любой незакрытый пункт перед реализацией всё равно проходит fresh exact-CURRENT review и отдельное явное approval.

## Важное про идентификаторы A1–A10

В проекте существуют **два разных пространства A-идентификаторов**:

1. **Product A1–A8 / A6.1** — аукционные функции 2026-08/09.
2. **Maintenance A1–A10** — findings контрольного codebase audit 2026-10-01.

Например, **Product A8 = Undo**, а **Maintenance A8 = GitHub Actions Version Refresh**. Их нельзя смешивать.

---

# I. Ранние базовые идеи проекта — реализованы

Эти решения появились до окончательной буквенно-цифровой нумерации и позже стали основой MAIN.

## Игры / публичный список

- **Локальная SQLite БД как source of truth, stable IDs, архив вместо обычного destructive delete, audit/history и backups** — **IMPLEMENTED / ACCEPTED**.
- **Статусы игр и каноническая сортировка** — **IMPLEMENTED / ACCEPTED**. Финальная логика учитывает статус, сумму/баллы и дату; `ПРОХОДИТСЯ` сохраняет особый приоритет, `ПРОЙДЕНО` уходит вниз.
- **Архивирование и восстановление игр с подтверждением** — **IMPLEMENTED / ACCEPTED**.
- **Поиск на «Игры» и «Публичный список» с одинаковой логикой и Enter** — **IMPLEMENTED / ACCEPTED**.
- **Синхронное скрытие/показ списка на Games/Public** — **IMPLEMENTED / ACCEPTED**; позже стало частью persisted UI state.
- **Статистические карточки вместо старого dropdown-фильтра** — **IMPLEMENTED / ACCEPTED**.
- **Общий список + отдельный нижний блок архива в total-view** — **IMPLEMENTED / ACCEPTED**.
- **Public List не показывает архив** — **IMPLEMENTED / ACCEPTED**.
- **Защита от дубликатов при добавлении/импорте** — **IMPLEMENTED / ACCEPTED**.

## Импорт / экспорт / синхронизация / backup

- **CSV/Excel/Google-readable import/export с безопасным обновлением существующей БД** — **IMPLEMENTED / ACCEPTED**.
- **Backup / Restore пользовательской БД и данных** — **IMPLEMENTED / ACCEPTED**.
- **Full external `.iolbackup` для восстановления после полного удаления программы** — **IMPLEMENTED / ACCEPTED**: authoritative DB, protected credentials и managed media; backup хранится вне install root и переживает uninstall; logs/temp/runtime/external referenced files не встраиваются.
- **P1 — одностороннее публичное XLSX-зеркало для Google Drive/Sheets** — **IMPLEMENTED / ACCEPTED**. Финальный публичный файл содержит только `НАЗВАНИЕ ИГРЫ / БАЛЛЫ / ОТЗЫВ / СТАТУС`.
- **C2 — обычный .xlsx общего основного списка с двусторонней синхронизацией между экземплярами, last-change-wins** — **IMPLEMENTED / ACCEPTED**.
- **Не создавать собственный закрытый формат для C2; файл должен читаться Google Sheets** — **IMPLEMENTED / ACCEPTED**.

## OBS main/list presentation

- **Отдельный URL OBS для списка игр** — **IMPLEMENTED / ACCEPTED**.
- **Top-3 фиксирован сверху, затем separator + прокрутка списка с #4** — **IMPLEMENTED / ACCEPTED**.
- **Бесшовная автопрокрутка списка сверху вниз** — **IMPLEMENTED / ACCEPTED**.
- **Длинные названия переносятся по словам; сумма выравнивается по последней строке названия** — **IMPLEMENTED / ACCEPTED**.
- **Основной OBS layout: игровая область 16:9, webcam, list, info/title blocks** — **IMPLEMENTED / ACCEPTED**.
- **Webcam/List/Info можно отключать и располагать независимо; layout переиспользует освободившееся место** — **IMPLEMENTED / ACCEPTED**.
- **Отдельные glow/frame colors для game/webcam/list/info** — **IMPLEMENTED / ACCEPTED**.
- **Прозрачны только interior cutouts game/webcam; фон, рамки, список, info/title остаются визуальными слоями** — **IMPLEMENTED / ACCEPTED**.
- **Фон сцены из файла + Stretch/Fit/Fill/Center** — **IMPLEMENTED / ACCEPTED**.
- **Фоны PNG/JPG/JPEG/WebP/GIF/MP4/WebM** — **IMPLEMENTED / ACCEPTED**.
- **Изменения сохранённых presentation settings применяются к открытым Browser Sources без смены URL** — **IMPLEMENTED / ACCEPTED**.
- **OBS композиция/позиционирование остаётся задачей OBS, а InOneLine даёт standalone responsive widgets** — **IMPLEMENTED / ACCEPTED**.

---

# II. Основной аукцион / колесо — ранние идеи и MAIN

## Базовый аукцион

- **Два основных режима: «Максимальная сумма» и weighted wheel** — **IMPLEMENTED / ACCEPTED**.
- **Метод выбирается до старта и не меняется молча в ходе сессии** — **IMPLEMENTED / ACCEPTED**.
- **При ничьей в max-amount используется отдельный tie-break wheel только среди лидеров** — **IMPLEMENTED / ACCEPTED**.
- **Weighted wheel использует суммы/баллы как веса, local + OBS синхронизированы** — **IMPLEMENTED / ACCEPTED**.
- **В обычном weighted wheel zero-point lot участвует с minimum effective weight, а tie-break max-amount остаётся отдельным сценарием** — **IMPLEMENTED / ACCEPTED** после Winner Verification correction.
- **Timer Start/Pause/Resume одним основным lifecycle; reset с подтверждением; ручные +/- времени; 00:00 завершает приём ставок** — **IMPLEMENTED / ACCEPTED**.
- **Temporary auction-only lot во время аукциона: название+сумма/баллы; после завершения/отмены переносится в основной список** — **IMPLEMENTED / ACCEPTED**.
- **Новый совпавший лот не создаёт дубль, а увеличивает существующий** — **IMPLEMENTED / ACCEPTED**.
- **Random.org/Random.org+ и local RNG; selector показывается только при сохранённом API key, иначе local RNG** — **IMPLEMENTED / ACCEPTED**.
- **Wheel OBS Overlay и Timer Overlay** — **IMPLEMENTED / ACCEPTED**.
- **Winner confirmation lifecycle сохраняется** — **EXISTING / PRESERVE**.

## Product S/A MAIN items

- **S1 — внутренние InOneLine/Streaming Manager points + миграция legacy money semantics** — **IMPLEMENTED / ACCEPTED**.
- **Product A1 — сохранять последнее значение общего ручного поля суммы/баллов** — **IMPLEMENTED / ACCEPTED**.
- **Product A2 — постоянная inline-строка добавления нового лота в Conduct** — **IMPLEMENTED / ACCEPTED**.
- **Product A3 — frozen start position + live/current position** — **IMPLEMENTED / ACCEPTED**.
- **Product A4 — ручные «Добавить» / «Уменьшить» как auditable compensating operations** — **IMPLEMENTED / ACCEPTED**.
- **Product A5 — удалять только ошибочный temporary auction-only lot текущей активной сессии** — **IMPLEMENTED / ACCEPTED**.
- **Product A6 — итог `Всего: N баллов`** — **IMPLEMENTED / ACCEPTED**. Ранняя идея show/hide superseded: финально total всегда видим.
- **Product A6.1 — live `Шанс в колесе`** — **IMPLEMENTED / ACCEPTED**.
- **Product A7 — current-auction History + hover highlight связанного лота + compact `Ставки | История`** — **IMPLEMENTED / ACCEPTED**.
- **Product A8 — safe compensating Undo для обратимых действий** — **ACCEPTED / DEFERRED**. 2026-09-01 пользователь решил не включать в MAIN; нужен новый safety/design review, прежний whitelist не pre-approved.

## S2 / History / Verification

- **S2 — timer auto-extension** по actual leader change / genuinely new lot / external donation, threshold, dedup, max-one-extension collision rule и 24h ceiling — **IMPLEMENTED / ACCEPTED**.
- **Внешнее денежное автопродление + optional service units** — **IMPLEMENTED / ACCEPTED** окончательно в 1.0.3.
- **Core «История аукционов»**: period filter, base summary, all closed sessions, newest-first, search/sort, pagination/lazy loading, read-only details — **IMPLEMENTED / ACCEPTED**.
- **Winner Verification snapshot** — **IMPLEMENTED / ACCEPTED**.
- **Deterministic read-only re-check из snapshot** — **IMPLEMENTED / ACCEPTED**.
- **Verification inside completed-auction details** — **IMPLEMENTED / ACCEPTED**.
- **Optional pre-spin `Данные проверки` без обязательного viewer overlay** — **IMPLEMENTED / ACCEPTED**.

---

# III. Saved/New Auction

- **«Сохранённые аукционы»** — несколько именованных reusable working auction configurations без второй Games database, с быстрым выбором/переключением и безопасными rename/delete flows — **ACCEPTED / DEFERRED TO POST-COMPLETION**.
- **Полный «Новый аукцион…»** с именем, `Начать без сохранения` / `Сохранить предыдущий и начать`, безопасной обработкой активной сессии и immutable historical name snapshot — **ACCEPTED / DEFERRED**, зависит от Saved Auctions.
- Completed History и Saved Auctions — разные системы; переименование/удаление saved configuration не переписывает историю — **DURABLE ACCEPTED RULE**.

---

# IV. W-series / media / audio

- **W1 — Space вызывает существующий путь «Крутить»** — **ACCEPTED / DEFERRED**. Был реализован, но 2026-09-01 пользователь отменил включение в MAIN и попросил оставить улучшением готовой программы; current runtime этого shortcut не содержит.
- **W2 — единая managed-copy / external-reference media infrastructure** — **IMPLEMENTED / ACCEPTED**.
- **Разные managed media folders по назначению** (backgrounds, music/soundtrack, wheel/center assets и т.п.) — **IMPLEMENTED / ACCEPTED**.
- **W3 — soundtrack колеса MP3/WAV/OGG, application-owned transport, volume/mute** — **IMPLEMENTED / ACCEPTED**.
- **Auction/Timer Music** с Pause/Resume на точной позиции, loop/profile и отдельным Auction/Wheel state — **IMPLEMENTED / ACCEPTED**; позднее transport расширен D43.
- **W4 — точный frozen chance выпавшего победителя из resolved snapshot на desktop + Wheel OBS** — **IMPLEMENTED / ACCEPTED**.

---

# V. Rules / standalone widgets / stream UI

- **R2 / WYSIWYG Rules package**: editor + templates CRUD, active template, validation, Undo/Redo, fonts/sizes/colors/highlight, bold/italic/underline, alignment, bullets/numbering, scrolling, unsaved-change protection — **IMPLEMENTED / ACCEPTED**.
- **Rules snapshot на сессию аукциона** — **IMPLEMENTED / ACCEPTED**.
- **Standalone OBS Rules widget** — **IMPLEMENTED / ACCEPTED**.
- **Rules OBS autoscroll** — **IMPLEMENTED / ACCEPTED**: overflow-only, pause top -> smooth down -> pause bottom -> reset, без сложных speed sliders в первой версии.
- **S3 — общий screen color eyedropper** — **IMPLEMENTED / ACCEPTED**.
- **Standalone widget foundation в «Стрим / OBS» со stable URLs и responsive Browser Sources** — **IMPLEMENTED / ACCEPTED**.
- **Standalone Timer viewer только с authoritative timer value, без второго timer engine** — **IMPLEMENTED / ACCEPTED**; пропущенный MAIN пункт был восстановлен и окончательно принят в 0.3.88.
- **Общие presentation controls standalone widgets** — **IMPLEMENTED / ACCEPTED** там, где применимо.
- **Built-in «Как добавить в OBS»** — **IMPLEMENTED / ACCEPTED**.
- **Одна общая инструкция OBS вместо одинаковой кнопки в каждом виджете** — **IMPLEMENTED / ACCEPTED in 1.0.2**.
- OBS flags `Shutdown source when not visible` / `Refresh browser when scene becomes active` — **ACCEPTED AS OPTIONAL GUIDANCE**, не обязательны для работы.

---

# VI. Интеграции

## Реализованная архитектура

- **B1 — единый `Настройки → Интеграции` center, adapter/status/security contract, DPAPI credential storage** — **IMPLEMENTED / ACCEPTED**.
- **B2 Twitch first adapter** — **IMPLEMENTED / ACCEPTED**.
- **B3 — автоматическое принятие разрешённых integration events** — **IMPLEMENTED / ACCEPTED**; generic Pending queue не является MAIN.
- **B4 — Twitch Channel Points / app-managed Custom Rewards** — **FUNCTIONALLY ACCEPTED / PARTIALLY ELIGIBILITY-DEPENDENT**. Архитектура/UX приняты; live redemption verification отложена до Affiliate/Partner eligibility.
- **B5 — `Ставки` feed автоматически принятых integration events** — **IMPLEMENTED / ACCEPTED**.
- **I1 / DonationAlerts adapter** с browser auth/status и отдельным auction enable; public Client ID встроен, user вводит только authorization — **IMPLEMENTED / ACCEPTED**.

## Принятые, но отложенные service targets

Каждый требует fresh current official API/auth/event review:

- **Kick** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**.
- **VK Video Live** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**.
- **iHAQ Donate v2.0** — **ACCEPTED / DEFERRED**.
- **Donate Helper** — **ACCEPTED / DEFERRED**.
- **DonatePay** — **ACCEPTED / DEFERRED**.
- **DonateX** — **ACCEPTED / DEFERRED**.
- **ODA/OpenDonationAssistant** — **DEFERRED / CONTRACT-BLOCKED** до безопасного official auth/event/history contract.
- **B6 Pointauc API adapter** — **ACCEPTED / DEFERRED**. Поздняя refinement: normal direction — InOneLine source of truth -> external mirror; emergency recovery только явно подтверждённым оператором. Перед кодом заново определить conflicts, IDs, dedup, writes/recovery.
- **Older YouTube platform/integration candidate** — **RETAINED / SCOPE UNDEFINED**. Не путать с D41 chat provider и не путать с historical soundtrack-source wording.

---

# VII. История — принятая post-completion аналитика

Текущий core History уже реализован. Следующие блоки были **прямо приняты пользователем** как будущая аналитика, а не просто assistant suggestions:

- **Activity calendar / heatmap аукционов** — **ACCEPTED / POST-COMPLETION**.
- **Распределение по дням недели** — **ACCEPTED / POST-COMPLETION**.
- **Лучшие участники / rankings** — **ACCEPTED / POST-INTEGRATION + POST-COMPLETION**, требует stable participant identity.
- **Отдельная статистика Points и Donations** — **ACCEPTED / POST-INTEGRATION + POST-COMPLETION**; raw units/currencies не смешиваются без определённой базы.
- **Record card «Самый большой аукцион»** — **ACCEPTED / POST-COMPLETION**.
- **Record card «Самый популярный»** — **ACCEPTED / POST-INTEGRATION**.
- **Record card «Больше всего баллов»** — **ACCEPTED / POST-INTEGRATION**.
- **Record card «Больше всего донатов»** — **ACCEPTED / POST-INTEGRATION**.
- **«Самый дорогой победивший лот»** — **ACCEPTED / POST-COMPLETION**; считать по historical snapshot, не по текущей mutable сумме игры.

Ранний D5 umbrella поэтому **PARTIALLY SUPERSEDED**: core History реализован, а перечисленная advanced analytics остаётся принятой future work.

---

# VIII. D1–D43 — полный статус

- **D1 — double timer / elapsed count-up** — **ACCEPTED AS POSSIBLE / DEFERRED**; текущий single timer сохраняется.
- **D2 — закрепить/открепить лот** — **ACCEPTED AS POSSIBLE / DEFERRED**.
- **D3 — universal inline editing во всех таблицах** — **POSSIBLE POST-COMPLETION**; основной edit остаётся через Games.
- **D4 — отдельная top-level страница Wheel** — **REJECTED / SUPERSEDED**; wheel остаётся внутри Auction.
- **D5 — History umbrella** — **PARTIALLY SUPERSEDED**: core реализован; advanced analytics из раздела VII **USER-ACCEPTED / DEFERRED**.
- **D6 — generic Widgets umbrella / named instances / composite builder** — **SUPERSEDED / REJECTED**; вместо него standalone function widgets.
- **D7 — Winner Verification umbrella** — MAIN verification **IMPLEMENTED**; whole-snapshot cryptographic tamper-resistance **ACCEPTED AS POST-COMPLETION HARDENING**.
- **D8 — Video Requests** — **REJECTED / NOT NEEDED**.
- **D9 — Localization/languages** — **ACCEPTED / DEFERRED POST-COMPLETION**; русский остаётся primary, будущие языки не зафиксированы.
- **D10 — GitHub link** — **CONDITIONAL FUTURE ITEM**; public repo prerequisite теперь существует, но нужен fresh review.
- **D11 — Telegram link** — **CONDITIONAL FUTURE ITEM** только после появления официального проекта/канала.
- **D12 — Support/Boosty link** — **CONDITIONAL FUTURE ITEM** только после появления официального support resource.
- **D13 — Pending/manual-processing queue** — **ACCEPTED AS POSSIBLE POST-COMPLETION**, не MAIN.
- **D14 — historical operator/wheel umbrella** — **SUPERSEDED** concrete W/D items.
- **D15 — Twitch AI-bot/neural network** — **NOT A CONFIRMED InOneLine USER IDEA / HISTORICAL ONLY**.
- **D16 — local-wheel hover highlight** — **USER-APPROVED / EXPLICITLY DEFERRED**.
- **D17 — random spin duration** — **USER-APPROVED / SKIPPED FOR NOW**.
- **D18 — wheel visual style selector** — **USER-APPROVED / SKIPPED FOR NOW**.
- **D19 — custom center image** — **IMPLEMENTED / RELEASED 1.0.4**. Поздний user scope включил direct URL, Twitch, 7TV, BTTV, FFZ и quick picker.
- **D20 — visual sector split without changing logical probability** — **USER-APPROVED / DEFERRED**.
- **D21 — Elimination wheel** — **IMPLEMENTED / RELEASED 1.0.6**. Released behavior supersedes early draft: каждый elimination spin использует настоящий weighted RNG текущих активных лотов; archive только после `В архив`; последний lot тоже spins.
- **D22 — Battle Royale** — **USER-APPROVED / EXPLICITLY DEFERRED**; Issue #5.
- **D23 — import custom participants** — **APPROVED POST-COMPLETION / NOT SELECTED**. Current-auction destination переиспользует add/increment; wheel-only creates temporary participants; preview/duplicate merge preserved.
- **D24 — separate OBS participant list** — **APPROVED POST-COMPLETION / NOT SELECTED**.
- **D25 — cumulative probability of lots <= winner amount** — **APPROVED POST-COMPLETION / EXPLICITLY «НЕ НУЖНО СЕЙЧАС»**.
- **D26 — full Music Player + own OBS overlay** — **IMPLEMENTED / RELEASED 1.0.7**.
- **D27 — «Честное колесо» / final-stop physics winner** — **USER IDEA / POST-COMPLETION / NOT IMPLEMENTED**.
- **D28 — artificial/fixed probability mode** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; только отдельный explicit artificial-chance mode.
- **D29 — viewer names in viewer-facing table** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION / INTEGRATION-DEPENDENT**.
- **D30 — blind/hidden amounts for viewers** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; operator/authoritative amounts and RNG stay real.
- **D31 — `Никогда / При совпадении / Всегда` auto-processing selector** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**, только extension будущего D13.
- **D32 — viewer name as order text** — **USER-ACCEPTED, LATER NARROWED** to a separate future participant/viewer-based mode; ordinary game auction uses message/order text and stores sender identity separately.
- **D33 — alternative display sorts old/new/cheap/expensive** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; default remains expensive/amount-desc.
- **D34 — Tourniquet donation adapter** — **USER-RETAINED / DEFERRED POST-COMPLETION**; API/security/event delivery must be freshly rechecked.
- **D35 — per-bet Fortune Wheel multiplier** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**; works on normalized points before final credit, separate from winner wheel.
- **D36 — Viewer chooses lot** — **USER-ACCEPTED AS POSSIBLE POST-COMPLETION**, dependent on D35; exact interaction to re-investigate.
- **D37 — presets export/import** — **USER-ACCEPTED / DEFERRED POST-COMPLETION**; secrets never silently included.
- **D38 — optional LAN access for standalone OBS widgets from second PC** — **USER-ACCEPTED / EXPLICITLY DEFERRED POST-COMPLETION**; MAIN default localhost, no Internet exposure.
- **D39 — per-scene widget style profiles** — **NOT DIRECTLY USER-APPROVED / HISTORICAL ASSISTANT POSSIBILITY / NOT ACTIONABLE**.
- **D40 — manual custom soundtrack/music library order** — **RETAINED POST-COMPLETION / NOT IMPLEMENTED**; D26 currently has Alphabetical/Shuffle, no manual playlist-order editor.
- **D41 — cross-platform chat aggregation + separate OBS chat overlay** — **USER IDEA / POST-COMPLETION**. Twitch/YouTube/VK/other supported chat providers; ordinary chat does not mutate auction/points/timer/wheel; reuse B1/B2 auth/adapter infrastructure.
- **D42 — current lot/sector under pointer during spin** — **USER-APPROVED POST-COMPLETION / NOT SELECTED**; local+OBS, toggleable, no RNG changes.
- **D43 — audio/music transport through OBS Browser Source so OBS controls loudness** — **IMPLEMENTED / RELEASED 1.0.5**. Auction/Wheel soundtrack uses Timer Browser Source; later D26 Music Player has own Browser Source and shared AudioCoordinator ownership.

**D44 не найден.**

---

# IX. Post-1.0 идеи и патчи

- **1.0.1 Auction Lots OBS Browser Source** — **IMPLEMENTED / ACCEPTED**: authoritative lot order/positions/points/chance, shared autoscroll, fixed header, presentation settings, quick URLs/previews, timer-overlay wheel/tie synchronization.
- **1.0.2 одна общая кнопка OBS help для всех widgets** — **IMPLEMENTED / ACCEPTED**.
- **1.0.3 External donation/service-unit timer extension completion** — **IMPLEMENTED / ACCEPTED**.
- **1.0.4 D19 center image + remote sources** — **IMPLEMENTED / ACCEPTED**.
- **1.0.5 D43 OBS audio transport** — **IMPLEMENTED / ACCEPTED**.
- **1.0.6 D21 Elimination** — **IMPLEMENTED / ACCEPTED**.
- **1.0.7 D26 Music Player** — **IMPLEMENTED / ACCEPTED**.
- **1.0.8 Global Conditional UI Visibility** — **IMPLEMENTED / ACCEPTED**: logically inapplicable controls hidden; temporarily unavailable but applicable controls remain visible+disabled.
- **Global Multi-File Import / Issue #4** — **ACCEPTED/RECORDED POST-D26 BACKLOG / ELIGIBLE FOR FRESH REVIEW / NOT SELECTED**. Reuse D26 Ctrl/Shift multi-select pattern in applicable `Добавить файл…` flows.

---

# X. Public Web / list presentation residuals

- **Ordinary Public Web/site representation of the public game list** — **RETAINED FUTURE DIRECTION / SCOPE UNDEFINED / NOT AUTO-AUTHORIZED**. Distinct from local JSON API, OBS list overlay and XLSX mirrors.
- **Games/List `Обычный / Компактный` presentation** — earlier accepted, later **EXPLICITLY POSTPONED** until a real need appears.
- **Дополнительный общий persisted Games/List Autoscroll control** — **NO LONGER A LIVE TASK**. Более позднее решение пользователя: не добавлять отдельную новую функцию, потому что нужная автопрокрутка уже есть.
- **Auction Lots Normal/Compact** — **SPECIFICATION-RECONCILIATION ONLY**, не подтверждённый defect.

---

# XI. Отклонённые / superseded идеи

## F-series

- **F1 — direct inline amount editing in row/cell** — **SUPERSEDED** общим manual Add/Decrease workflow.
- **F2 — отдельная quick `+` в каждой строке** — **REJECTED / SUPERSEDED** одним shared amount field.
- **F3 — Pending + manual Accept/Reject как MAIN integration flow** — **SUPERSEDED** B3 automatic acceptance; Pending только possible D13.
- **F4 — temporary lot переносится только после winner confirmation** — **SUPERSEDED**: cancel тоже promotes.
- **F5 — connection-status architecture якобы впервые появилась в позднем reference review** — **SUPERSEDED HISTORICAL CLAIM**.
- **F6 — reroll того же unresolved participant set** — **REJECTED / NOT NEEDED**.
- **F7 — generic Delete Lot из winner result panel** — **REJECTED**; безопасный delete только Product A5 для temporary lot.
- **F8 — заменять ссылки в названии лота на текст** — **REJECTED / NOT NEEDED**.
- **F9 — «Шаровой аукцион»** — **REJECTED / EXCLUDED**.

## Другие rejected/superseded

- **Composite drag/drop widget canvas / generic named widget-instance manager** — **REJECTED / SUPERSEDED** standalone widgets.
- **Отдельная top-level Wheel page** — **REJECTED**.
- **Video Requests** — **REJECTED**.
- **Historical `Трейлер (YouTube)`** — **RESOLVED/CLOSED**, не roadmap.
- **Historical YouTube URL/video-ID soundtrack source** — **REFERENCE-ONLY**, не direct user-approved scope.
- **Отдельный сложный advanced autoscroll control с independent speed/pause sliders** — **REJECTED/SUPERSEDED** простым/существующим scrolling behavior.
- **Отдельный второй Rules backend/text store** — **REJECTED BY ARCHITECTURE**; viewer uses authoritative Rules state.

---

# XII. H-series — существующее поведение, не future features

- **H1** — RNG selector / Random.org/Random.org+ workflow — **EXISTING / PRESERVE**.
- **H2** — winner confirmation lifecycle — **EXISTING / PRESERVE**.
- **H3** — operator lot list remains internal; viewer list is separate D24 — **EXISTING / PRESERVE**.
- **H4** — ordinary weighted wheel/current visual baseline remains default; future formats/themes cannot silently replace it — **EXISTING / PRESERVE**.

---

# XIII. E-series / installer / deployment — выполнено

- **E1 — production EXE/PyInstaller readiness** — **IMPLEMENTED / ACCEPTED**.
- **E2 — stale OBS Browser Source version-handshake/cache-busting reload** — **IMPLEMENTED / ACCEPTED**.
- **E3 — tie extra-time default using existing duration model** — **IMPLEMENTED / ACCEPTED**; отдельная лишняя настройка не создаётся.
- **E4 — Windows Long Path/deep path deployment contract** — **IMPLEMENTED / ACCEPTED** в поддерживаемом <260 path contract. Arbitrary >=260 direct portable launch — out of scope/new separate scope, не unfinished E4.
- **Default install root `C:\InOneLine` + user-selectable destination/drive** — **IMPLEMENTED / ACCEPTED**.
- **No portable-user migration** — **USER DECISION / PRESERVE**.
- **Official artifacts after 1.0: SOURCE + INSTALLER; portable not CURRENT** — **USER DECISION / PRESERVE**.
- **Uninstall warning + confirmation; удалить app-owned DB/data/QSettings after confirmation; external .iolbackup/external referenced files preserve** — **IMPLEMENTED / ACCEPTED**.
- **Canonical icon: улучшить существующий дизайн (толще/центрированнее/резче) и переиспользовать** — **IMPLEMENTED / ACCEPTED**.

---

# XIV. Distribution / public project decisions

Это не feature backlog, но прямые пользовательские проектные решения:

- **Публичный GitHub repository + GitHub Releases** — **IMPLEMENTED / ACCEPTED**.
- **GitHub становится source of truth; Drive остаётся history/backup** — **IMPLEMENTED / ACCEPTED**.
- **Публично указать, что InOneLine создан автором с помощью ChatGPT от OpenAI; другие нейросети не использовались** — **IMPLEMENTED / ACCEPTED**.
- **Программа и source можно бесплатно использовать, изменять и бесплатно распространять; платное распространение запрещено** — **IMPLEMENTED / ACCEPTED** custom license policy.
- **Не покупать платный Authenticode; документировать SmartScreen/Unknown Publisher UX** — **USER DECISION / IMPLEMENTED IN DOCS**.
- **В публичных материалах называть функции по назначению, а не именем стороннего reference product; сторонние названия только для реальных integrations/APIs/dependencies** — **USER DECISION / PRESERVE**.
- **Release exact accepted bytes without rebuild after manual acceptance** — **DURABLE PROCESS RULE**.
- **Candidate/FIX не считаются в release cadence; только принятые CURRENT/released** — **DURABLE PROCESS RULE**.
- **C1 audit каждые 25 принятых releases/versions; перед фактическим gate счётчик сверяется по release history** — **DURABLE PROCESS RULE**.

---

# XV. Maintenance A1–A10 — отдельное пространство имён, все закрыто

Это **не пользовательские продуктовые feature ideas**, а findings контрольного codebase audit 2026-10-01. Они перечислены здесь только для предотвращения путаницы с Product A1–A8.

- **Maintenance A1 — source ZIP pollution / source snapshot hygiene** — **CLOSED**.
- **Maintenance A2 — permanent regression foundation missing** — **CLOSED**.
- **Maintenance A3 — exact build dependency lock** — **CLOSED**.
- **Maintenance A4 — Managed Media Sync transaction optimization** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A5 — verified unused imports** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A6 — dead private helpers** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A7 — publication CI consolidation** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A8 — GitHub Actions major refresh** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A9 — installer user-state/HKCU ownership** — **CLOSED / ACCEPTED / MERGED**.
- **Maintenance A10 — documentation drift/synchronization** — **CLOSED**.

---

# XVI. Текущий незакрытый survivable inventory

Не означает выбранную implementation queue.

## Eligible for fresh review
- Global Multi-File Import / #4.
- D40 manual library order.
- D34 Tourniquet adapter.
- D41 multi-chat + OBS chat.
- older YouTube integration candidate.
- D38 LAN widgets.
- Public Web.
- D27 fair/physics wheel.
- D7 cryptographic hardening.

## Accepted/deferred or parked
- Product A8 Undo.
- Saved Auctions + New Auction.
- W1 Space shortcut.
- D1, D2, D9–D13, D16–D18, D20, D22–D25, D28–D38, D40–D42 according to their exact statuses above.
- Advanced History analytics in section VII.
- B6 and deferred provider adapters.
- Games/List Compact presentation.

## Explicitly not live
- extra Games/List Autoscroll task.
- D15 AI bot.
- D39 per-scene profiles unless user explicitly reopens.
- rejected/superseded F/D umbrella items.

---

# XVII. Reconciliation conclusion 2026-10-02

После второго полного cross-source pass:

- **D44 не найден**.
- Отдельного durable user-proposed feature, отсутствующего из этого inventory, не найдено.
- Обнаружена и исправлена важная provenance/status ошибка: advanced History analytics были user-accepted post-completion ideas, а не просто assistant-proposed possibilities.
- D9–D12 также сохранены с direct-user provenance/conditionality.
- GitHub Issues не являются полным backlog.
- Любой будущий найденный старый пункт сначала проверяется против более позднего direct-user decision и current/released behavior, и только затем может менять `ROADMAP.md`.

Canonical current selection: `PROJECT_STATE.md` + `ROADMAP.md`.
Полная история идей: этот файл.
