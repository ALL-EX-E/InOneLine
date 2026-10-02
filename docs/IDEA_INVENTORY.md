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

## Важное про повторно использованные A-идентификаторы

В истории проекта существуют **три разных пространства A-идентификаторов**:

1. **August Stabilization A1–A12** (включая A7.1 и A11.1) — ранний технический аудит/оптимизация 0.3.03–0.3.16, август 2026.
2. **Product A1–A8 / A6.1** — аукционные продуктовые функции 0.3.22+ / август–сентябрь 2026.
3. **Maintenance A1–A10** — findings контрольного codebase audit 2026-10-01.

Например, **August Stabilization A8 = hidden AuctionTab visual timers/refresh optimization**, **Product A8 = Undo**, а **Maintenance A8 = GitHub Actions Version Refresh**. Их нельзя смешивать.

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
- **«Очистить все игры» на вкладке «Игры»** — **IMPLEMENTED / ACCEPTED**: запрещено при открытом аукционе; требует точного destructive confirmation; перед очисткой автоматически создаётся backup; удаляются обычные/архивные/temporary game records, а завершённая история аукционов и Журнал сохраняются.

## Импорт / экспорт / синхронизация / backup

- **CSV/Excel/Google-readable import/export с безопасным обновлением существующей БД** — **IMPLEMENTED / ACCEPTED**.
- **Backup / Restore пользовательской БД и данных** — **IMPLEMENTED / ACCEPTED**.
- **Явная команда `Настройки → Восстановить из резервной копии…`** — **IMPLEMENTED / ACCEPTED**: выбранный `.db` проверяется, текущее состояние предварительно страхуется, затем выполняется безопасное восстановление.
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
- **Direct OBS title/info UX** — **IMPLEMENTED / ACCEPTED**: current-game title is centered above the game frame; the lower-right information block remains a separate block; disabling the info block frees/reuses that area for the list instead of leaving dead space.
- **Webcam/List/Info можно отключать и располагать независимо; layout переиспользует освободившееся место** — **IMPLEMENTED / ACCEPTED**.
- **Отдельные glow/frame colors для game/webcam/list/info** — **IMPLEMENTED / ACCEPTED**.
- **Прозрачны только interior cutouts game/webcam; фон, рамки, список, info/title остаются визуальными слоями** — **IMPLEMENTED / ACCEPTED**.
- **Второй режим с полностью прозрачным фоном всего Browser Source** — **EXPLICITLY REJECTED / NOT PART OF THE PRODUCT**; прозрачность ограничена внутренними вырезами game/webcam, которые следуют геометрии и исчезают вместе с отключённым блоком.
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
- **Default wheel winner/animation contract** — **IMPLEMENTED / ACCEPTED / PRESERVE**: authoritative RNG выбирает winner до визуальной анимации; winner не раскрывается зрителю до завершения spin; persisted spin/result state восстанавливается после перезапуска. D27 является отдельной будущей альтернативой, а не reinterpretation этого режима.
- **В обычном weighted wheel zero-point lot участвует с minimum effective weight, а tie-break max-amount остаётся отдельным сценарием** — **IMPLEMENTED / ACCEPTED** после Winner Verification correction.
- **Timer Start/Pause/Resume одним основным lifecycle; reset с подтверждением; ручные +/- времени; 00:00 завершает приём ставок** — **IMPLEMENTED / ACCEPTED**.
- **Temporary auction-only lot во время аукциона: название+сумма/баллы; после завершения/отмены переносится в основной список** — **IMPLEMENTED / ACCEPTED**.
- **Новый совпавший лот не создаёт дубль, а увеличивает существующий** — **IMPLEMENTED / ACCEPTED**.
- **Random.org/Random.org+ и local RNG; selector показывается только при сохранённом API key, иначе local RNG** — **IMPLEMENTED / ACCEPTED**.
- **Wheel OBS Overlay и Timer Overlay** — **IMPLEMENTED / ACCEPTED**.
- **Winner confirmation lifecycle сохраняется** — **EXISTING / PRESERVE**.
- **Cross-surface data synchronization invariant** — **IMPLEMENTED / ACCEPTED**: изменение статуса/баллов через аукцион должно без ручного F5 обновлять authoritative DB и связанные представления `Игры`, `Публичный список`, `Аукцион`, `Журнал` и применимые OBS/API surfaces; перенос temporary lots после completion/cancel следует тому же правилу.
- **Open-auction / selected-winner persistence across restart** — **IMPLEMENTED / ACCEPTED**: поддерживаемые open-session states и уже выбранный winner/frozen result должны восстанавливаться после перезапуска, а не вычисляться заново.

## Product S/A MAIN items

- **S1 — внутренние InOneLine/Streaming Manager points + миграция legacy money semantics** — **IMPLEMENTED / ACCEPTED**.
- **S1 integer conversion rule** — **IMPLEMENTED / ACCEPTED**: результат зачисления всегда целое число SM points; положительный дробный результат округляется вверх одинаково для валют и неденежных service units; reverse `SM points → money` не используется.
- **Product A1 — сохранять последнее значение общего ручного поля суммы/баллов** — **IMPLEMENTED / ACCEPTED**. Direct UX decision: numeric/manual-bid input must not expose tiny native up/down spin arrows; value entry remains explicit and wheel-safe.
- **Product A2 — постоянная inline-строка добавления нового лота в Conduct** — **IMPLEMENTED / ACCEPTED**. Название после trim/normalization не может быть пустым/whitespace-only и использует общую duplicate protection вместо создания параллельного правила. Numeric points field for adding a lot, like the shared manual-bid/points field, does not expose native up/down spin arrows.
- **Product A3 — frozen start position + live/current position** — **IMPLEMENTED / ACCEPTED**.
- **Product A4 — ручные «Добавить» / «Уменьшить» как auditable compensating operations** — **IMPLEMENTED / ACCEPTED**.
- **Product A5 — удалять только ошибочный temporary auction-only lot текущей активной сессии** — **IMPLEMENTED / ACCEPTED**.
- **Product A6 — итог `Всего: N баллов`** — **IMPLEMENTED / ACCEPTED**. Ранняя идея show/hide superseded: финально total всегда видим.
- **Product A6.1 — live `Шанс в колесе`** — **IMPLEMENTED / ACCEPTED**. Weighted-wheel-only read-only chance uses exactly the authoritative selection weights/probability math, updates live without changing business state, is hidden in ordinary max-amount context, and is distinct from W4 frozen post-result winner chance.
- **Product A7 — current-auction History + hover highlight связанного лота + compact `Ставки | История`** — **IMPLEMENTED / ACCEPTED**. Accepted detail: one mutually exclusive compact area; `Ставки` is the current-auction incoming-event feed, `История` is the current-session business-change feed distinct from global Journal/completed History; cards retain event type/time/object/details, relative time may be shown while exact timestamp remains stored, and incremental updates are preferred over heavy full rebuilds.
- **Product A8 — safe compensating Undo для обратимых действий** — **ACCEPTED / DEFERRED**. 2026-09-01 пользователь решил не включать в MAIN; нужен новый safety/design review, прежний whitelist не pre-approved.

## S2 / History / Verification

- **Поиск внутри «Журнала» по любому событию** — **IMPLEMENTED / ACCEPTED**: поиск локален для Journal, проверяет отображаемые и raw-поля события и при непустом запросе ищет по полной истории, а не только по обычному окну последних 500 записей.
- **S2 — timer auto-extension** по actual leader change / genuinely new lot / external donation, threshold, dedup, max-one-extension collision rule и 24h ceiling — **IMPLEMENTED / ACCEPTED**.
- **Внешнее денежное автопродление + optional service units** — **IMPLEMENTED / ACCEPTED** окончательно в 1.0.3.
- **Core «История аукционов»**: period filter, base summary, all closed sessions, newest-first, search/sort, pagination/lazy loading, read-only details — **IMPLEMENTED / ACCEPTED**.
- **Winner Verification snapshot** — **IMPLEMENTED / ACCEPTED**.
- **Deterministic read-only re-check из snapshot** — **IMPLEMENTED / ACCEPTED**.
- **Verification inside completed-auction details** — **IMPLEMENTED / ACCEPTED**.
- **Optional pre-spin `Данные проверки` без обязательного viewer overlay** — **IMPLEMENTED / ACCEPTED**.

---

# III. Saved/New Auction

- **«Сохранённые аукционы»** — несколько именованных reusable working auction configurations без второй Games database, с быстрым выбором/переключением и безопасными rename/delete flows — **ACCEPTED / DEFERRED TO POST-COMPLETION**. Обычный Save обновляет уже связанную saved-конфигурацию; отдельная копия создаётся только через явный Save-As-like путь.
- **Полный «Новый аукцион…»** с именем, `Начать без сохранения` / `Сохранить предыдущий и начать`, безопасной обработкой активной сессии и immutable historical name snapshot — **ACCEPTED / DEFERRED**, зависит от Saved Auctions. Создание нового working auction не очищает Games, global Journal, completed History, Saved Auctions, integration settings, Rules templates или global/widget OBS settings; сбрасывается только runtime новой рабочей сессии.
- Completed History и Saved Auctions — разные системы; переименование/удаление saved configuration не переписывает историю — **DURABLE ACCEPTED RULE**.

---

# IV. W-series / media / audio

- **W1 — Space вызывает существующий путь «Крутить»** — **ACCEPTED / DEFERRED**. Был реализован, но 2026-09-01 пользователь отменил включение в MAIN и попросил оставить улучшением готовой программы; current runtime этого shortcut не содержит.
- **W2 — единая managed-copy / external-reference media infrastructure** — **IMPLEMENTED / ACCEPTED**. Final UX distinguishes the normal contextual add/select action (for example `Добавить фон…`) from `Восстановить ссылку…`, which appears as a repair action for a missing external reference instead of looking like a second ordinary picker.
- **W2 direct UX corrections** — **IMPLEMENTED / ACCEPTED**: основное действие для фона формулируется как `Добавить фон…`; repair/restore-reference UI показывается только для реально потерянного external-файла, а не как постоянная параллельная кнопка.
- **Разные managed media folders по назначению** (backgrounds, music/soundtrack, wheel/center assets и т.п.) — **IMPLEMENTED / ACCEPTED**.
- **W3 — soundtrack колеса MP3/WAV/OGG, application-owned transport, volume/mute** — **IMPLEMENTED / ACCEPTED**.
- **W3 direct UI contract** — **IMPLEMENTED / ACCEPTED**: `Музыка колеса` и `Добавить soundtrack…` визуально разделены; крупные кнопки изменения громкости имеют полностью кликабельную площадь; Mute находится отдельной строкой; ошибки/отсутствие аудио не могут блокировать RNG/winner lifecycle.
- **Auction/Timer Music — historical pre-D26 contract + current supersession** — ранний accepted contract включал managed/local playlist, выбранный стартовый трек, Loop One/sequential library order, независимые Auction/Wheel profiles и точное сохранение Auction track+timestamp при временном Auction → Wheel → Auction context handoff. **D26 / 1.0.7 SUPERSEDED playlist semantics for current runtime**: Auction soundtrack теперь один выбранный зацикленный файл из общего `data\\soundtrack`; старый auction playlist/checkbox `Зациклить выбранный трек` больше не используется. D43 Browser Source transport/authoritative playback architecture сохраняется. Старый playlist нельзя автоматически восстанавливать как незакрытый scope; **D40** остаётся отдельной будущей идеей manual library order и требует fresh review.
- **W4 — точный frozen chance выпавшего победителя из resolved snapshot на desktop + Wheel OBS** — **IMPLEMENTED / ACCEPTED**.

---

# V. Rules / standalone widgets / stream UI

- **R1 — reusable Auction Rules package**: templates CRUD, active template, WYSIWYG editor, Undo/Redo, text-style presets, fonts/sizes/colors/highlight, bold/italic/underline, alignment, bullets/numbering, validation, unsaved-change protection and local read-only preview — **IMPLEMENTED / ACCEPTED**.
- **R1 session snapshot**: starting a local auction freezes rules template provenance/name/HTML into the auction session; historical sessions are not rewritten by later template changes — **IMPLEMENTED / ACCEPTED**.
- **R2 — standalone OBS Rules widget**: stable responsive Browser Source + read-only API, independent viewer visibility/autoscroll/background/opacity/padding and live apply — **IMPLEMENTED / ACCEPTED**.
- **R2 single-editor correction**: `Аукцион → Проведение → Правила аукциона` is the only rules editor entry and remains usable before/during/after an auction. During an unfinished session, saving/renaming the matching source template synchronizes the open session copy; after finish/cancel historical rules remain frozen — **IMPLEMENTED / ACCEPTED**.
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
- **B1 accepted Conduct/status UX details** — **IMPLEMENTED/ACCEPTED CONTRACT; ONE CURRENT UI OMISSION TRACKED AS QA-1.0.8-01**:
  - compact `Аукцион → Проведение` integration status shows only configured/used services;
  - integration errors remain visible even in compact/collapsed presentation;
  - Conduct provides navigation to `Настройки → Интеграции` instead of duplicating full provider configuration;
  - the accepted status concept includes **time of the last accepted integration event**;
  - `Отключить` and `Удалить подключение` are distinct operations; removal requires confirmation and must not delete historical `external_events`, contributions or auction history;
  - service network/auth work must not block the GUI; adapter capabilities control which provider-specific controls are applicable;
  - sufficient provider/source identifiers are preserved for future cross-service duplicate analysis, but no cross-service dedup algorithm is implicitly approved.
- **QA-1.0.8-01 — Conduct integration last-event visibility** — **ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT YET FIXED**. Current 1.0.8 still persists `integration_connections.last_event_at` and Settings shows `Последняя принятая активность`, while the current Conduct integration status/dialog does not display the accepted last-event time. No later direct user decision superseding this detail was recovered. This is a QA/reconciliation finding, not a new feature idea and not automatic authorization to change runtime.
- **B2 Twitch accepted lifecycle details** — **IMPLEMENTED / ACCEPTED**: public/native Device Code authorization without Client Secret; protected access/refresh credentials; startup/hourly validation and serialized refresh; invalid/revoked auth -> `Требует входа`, transient provider/network failures -> bounded `Ошибка`; Connect may reuse a valid preserved grant, Reconnect forces fresh authorization, Disconnect preserves local config/credential/history, Remove deletes local connection config + secret after confirmation but never historical integration/auction records.
- **Integration connection UX** — **USER-ACCEPTED / IMPLEMENTED DIRECTION**: пользователь не должен вручную управлять client secrets или собирать сложную конфигурацию; где provider позволяет, подключение идёт через штатную browser/device authorization с public client/application credentials и protected local tokens.
- **B2 Twitch first adapter** — **IMPLEMENTED / ACCEPTED**.
- **B3 — автоматическое принятие разрешённых integration events** — **IMPLEMENTED / ACCEPTED**; generic Pending queue не является MAIN.
- **B4 — Twitch Channel Points / app-managed Custom Rewards** — **FUNCTIONALLY ACCEPTED / PARTIALLY ELIGIBILITY-DEPENDENT**. Архитектура/UX приняты; user correction допускает Channel Points contribution flow и во время, и вне активного аукциона по соответствующим правилам; live redemption verification отложена до Affiliate/Partner eligibility.
- **B5 — `Ставки` feed автоматически принятых integration events** — **IMPLEMENTED / ACCEPTED**.
- **General outside-auction integration rule** — **IMPLEMENTED/ACCEPTED ARCHITECTURAL RULE**: a valid game-targeted monetary or non-monetary external event may update persistent game points even when no auction is running; it must not create/start/resume an auction or mutate auction lot/timer/wheel state, and S2 timer extension requires an eligible running auction.
- **I1 / DonationAlerts adapter** — **IMPLEMENTED / ACCEPTED**: browser authorization/status, public Client ID встроен, пользователь проходит только авторизацию. **Поздний контракт supersedes ранний auction-only toggle:** подключение/enable интеграции является permission на постоянный intake; donations маршрутизируются по source timestamp в running auction либо в persistent game list вне аукциона. Отдельного `учитывать только в аукционе` intake-переключателя больше нет.

## Принятые, но отложенные service targets

Каждый требует fresh current official API/auth/event review:

- **Kick Channel Points / Custom Rewards** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; это сохранённый provider capability scope, а не generic «любая интеграция Kick». Перед реализацией заново подтвердить официальный/надёжный API/auth/event contract.
- **VK Video Live rewards/points** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; сохранённый scope относится к viewer/channel reward/points capability и требует свежего official API/auth/event feasibility review.
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
- **D16 — local-wheel hover highlight** — **USER-APPROVED / EXPLICITLY DEFERRED**. Accepted preserved contract: local operator wheel only; use existing `game_id`; hovered logical lot keeps its color while the others may gray temporarily; leaving restores normal colors; hover is cleared/ignored during spin; no OBS hover propagation; RNG, weights and authoritative data remain unchanged.
- **D17 — random spin duration** — **USER-APPROVED / SKIPPED FOR NOW**. Fixed duration remains default; optional min/max range; actual duration is sampled once per spin and shared by local+OBS; this is animation-duration randomness only and must not affect winner RNG/Random.org; soundtrack follows the actual resolved duration.
- **D18 — wheel visual style selector** — **USER-APPROVED / SKIPPED FOR NOW**. Current wheel remains `Обычный`/default; additional original themes are presentation-only; one persisted style applies to local+OBS; weights, probability, RNG and logical geometry semantics do not change.
- **D19 — custom center image** — **IMPLEMENTED / RELEASED 1.0.4**. Поздний direct-user scope включил direct URL, Twitch, 7TV, BTTV, FFZ и quick picker. Picker intentionally has no search/source filters: one unified visual emote/image grid plus `Загрузить своё изображение`; animated emotes/local animated media animate directly in the picker so static vs animated is visible before selection.
- **D20 — visual sector split without changing logical probability** — **USER-APPROVED / DEFERRED**. One logical lot/game_id/weight may render as multiple visual fragments whose combined angular share equals the original lot share; authoritative RNG selects the logical lot first, fragment choice is only visual landing; local+OBS use one resolved layout.
- **D21 — Elimination wheel** — **IMPLEMENTED / RELEASED 1.0.6**. Released behavior supersedes early draft: каждый elimination spin использует настоящий weighted RNG текущих активных лотов; archive только после `В архив`; последний lot тоже spins.
- **D22 — Battle Royale** — **USER-APPROVED / EXPLICITLY DEFERRED**; Issue #5. Pairwise weighted duels use real RNG over temporary tournament weights; duel winner absorbs only the loser's temporary tournament weight; persistent game/auction points do not change; one selected RNG method applies consistently through the tournament; bracket/byes/extreme-weight behavior, multi-round presentation and verification storage require fresh review before implementation.
- **D23 — import custom participants** — **APPROVED POST-COMPLETION / NOT SELECTED**. Destination `В текущий аукцион` reuses existing add/increment; `Только в колесо` creates temporary wheel-only participants without normal Games/Public/status/auction-amount semantics. Preserved import design accepts `Название,вес` and `Название|вес`; omitted weight=1; empty lines ignored; invalid numeric values produce line-specific errors; duplicates within import merge by summed weight; preview+confirmation occurs before apply. Wheel-only restart lifetime remains for fresh design review; do not create a second permanent Games importer.
- **D24 — separate OBS participant list** — **APPROVED POST-COMPLETION / NOT SELECTED**. Independent Browser Source from both operator lot list and Wheel Overlay; reuse authoritative wheel state and existing standalone-list architecture; own viewer presentation settings; D20 fragments do not inflate logical participant count; operator search/filter must not filter the viewer list; future multi-round formats may show progression such as remaining N of M from authoritative run state.
- **D25 — cumulative probability of lots <= winner amount** — **APPROVED POST-COMPLETION / EXPLICITLY «НЕ НУЖНО СЕЙЧАС»**.
- **D26 — full Music Player + own OBS overlay** — **IMPLEMENTED / RELEASED 1.0.7**.
- **D27 — «Честное колесо» / final-stop physics winner** — **USER IDEA / POST-COMPLETION / NOT IMPLEMENTED**. Optional alternative only; default RNG-first wheel stays unchanged. Fresh design must separately settle randomness/initial conditions, physics/deceleration, weighted geometry/boundaries, timing independence, local+OBS synchronization, reproducibility and verification/audit model.
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
- **D40 — manual custom soundtrack/music library order** — **RETAINED POST-COMPLETION / NOT IMPLEMENTED**; D26 currently has Alphabetical/Shuffle, no manual playlist-order editor. Это отдельный future scope поверх current D26 media/audio state и **не означает восстановление superseded pre-D26 Auction playlist/Loop-One contract**.
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
- **Отдельный `Изменить текущие правила` live-only editor/workflow** — **REJECTED/SUPERSEDED**; R2 correction keeps one ordinary `Правила аукциона` editor usable at any time and synchronizes the unfinished session copy when appropriate.
- **Отдельный InOneLine write/control Integration API (`POST /api/v1/bids`/generic `PUT /lot`) вне B6 contract** — **NOT USER-APPROVED / HISTORICAL ASSISTANT PROPOSAL**. Direct user approval was for the dedicated Pointauc/B6 adapter using Pointauc's official API; do not invent a separate local write API from the old proposal.
- **Обратная конвертация internal SM points -> money как продуктовая функция** — **CANCELLED/SUPERSEDED**; S1 финально использует one-way source unit/currency -> integer SM points, positive values round upward.
- **Split installation с runtime отдельно, AppData как основной user-data root** — **REJECTED**; выбран один install root (default `C:\InOneLine`) с user-selectable destination.
- **Ранний release-only план «публичный GitHub без публикации source»** — **SUPERSEDED** поздним решением публиковать официальный SOURCE вместе с INSTALLER и использовать custom free-use/no-paid-redistribution license.

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
- **Initial GitHub release-only/no-source publication plan (2026-09-26)** — **USER-ACCEPTED THEN SUPERSEDED**. It allowed a public release repository with installer release but no published source/license; later explicit decisions replaced it with official SOURCE + INSTALLER publication and the custom no-paid-redistribution license.
- **Installer-first public deployment/update model** — **USER-ACCEPTED / IMPLEMENTED**: normal users install InOneLine through the installer, and later updates/patches are applied to the installed program while preserving mutable user data according to the accepted update/reinstall contract.
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



---

# XVII. Granular historical accepted implementation ledger — 0.2.0–0.3.02

Этот раздел восстановлен третьим reconciliation-pass 2026-10-02. Ранее эти решения были функционально учтены крупными блоками, но не были видны как отдельные исторические идеи/улучшения.

Это **закрытые/реализованные** пункты, а не future backlog. Часть возникла как пользовательские запросы, часть как предложенные в ходе аудита улучшения, после чего была отдельно проверена/принята пользователем. Там, где прямое авторство идеи пользователя не доказано, статус здесь означает **historically approved/implemented**, а не «идея точно первоначально предложена пользователем».

## 0.2.0–0.2.22 — Games/Public foundation refinements

- **0.2.0 — enlarged/cleaner UI foundation**: скрытый technical ID, status/archive counters, improved search/selection, compact review rendering, local-time updated_at, no-op save/import does not reorder/update timestamp, pre-import backup, Public search/count/local JSON, OBS/API helpers, detailed Journal changes — **IMPLEMENTED / ACCEPTED**.
- **0.2.1 — explicit save confirmation + unsaved-close warning** — **IMPLEMENTED / ACCEPTED**.
- **0.2.2 — confirmation only for real edits; reverting to original values counts as no change** — **IMPLEMENTED / ACCEPTED**.
- **0.2.3 — irreversible Delete game with warning + safety backup, distinct from Archive** — **IMPLEMENTED / ACCEPTED**.
- **0.2.4 — flexible release-date input normalized to DD.MM.YYYY** (digits, separators, Russian month text) — **IMPLEMENTED / ACCEPTED**.
- **0.2.5 — explicit invalid-date error message** — **IMPLEMENTED / ACCEPTED**.
- **0.2.6 — duplicate-title protection + navigation to existing row/archive** — **IMPLEMENTED / ACCEPTED**.
- **0.2.7 — Games filters for ИГРАЛ / НЕ ИГРАЛ / КООП / НЕ КООП** — **IMPLEMENTED / ACCEPTED**, later UI presentation superseded by statistic-card filters.
- **0.2.8 — one-click Reset filters/search/archive view** — **IMPLEMENTED / ACCEPTED**, later adapted to statistic-card UI.
- **0.2.9 — separate Played / Not played statistics** — **IMPLEMENTED / ACCEPTED**.
- **0.2.10 — status ЗАБРОШЕНО**, sorting/filter/count/Public behavior and exclusion from auction export — **IMPLEMENTED / ACCEPTED**.
- **0.2.11 — statistic ДЛЯ АУКА = ИГРАЛ + НЕ ИГРАЛ** — **IMPLEMENTED / ACCEPTED**.
- **0.2.12 — Rules of sorting dialog instead of permanent explanatory text** — **IMPLEMENTED / ACCEPTED**.
- **0.2.13 — hide technical API/status line from main UI** — **IMPLEMENTED / ACCEPTED**.
- **0.2.14 — Hide/Show Games list toggle with auto-reveal when navigation requires a row** — **IMPLEMENTED / ACCEPTED**.
- **0.2.15 — compact window behavior when list hidden + Find button/Enter search, auto-select first match, explicit no-result message** — **IMPLEMENTED / ACCEPTED**.
- **0.2.16 — adaptive compact mode that does not distort when maximized/fullscreen** — **IMPLEMENTED / ACCEPTED**.
- **0.2.17 — QSizePolicy startup correction preserving adaptive compact mode** — **IMPLEMENTED / ACCEPTED CORRECTION**.
- **0.2.18 — File-menu spacing/DPI readability correction** — **IMPLEMENTED / ACCEPTED CORRECTION**.
- **0.2.19 — Games final hardening**: Unicode case-insensitive search, DB-level duplicate guard, clear selection/actions when list hidden, active rows above archived block, strict two-phase CSV validation, microsecond backup filenames — **IMPLEMENTED / ACCEPTED**.
- **0.2.20 — persist main-window geometry/position/maximized/current tab/Games list visibility** — **IMPLEMENTED / ACCEPTED**; later storage mechanism evolved through A9 installer-user-state maintenance.
- **0.2.21 — statistic cards become clickable filters; old dropdown/archive checkbox removed** — **IMPLEMENTED / ACCEPTED**.
- **0.2.22 — Всего counts all DB games including archive; other working counters count active rows** — **IMPLEMENTED / ACCEPTED CORRECTION**.

## 0.2.23–0.2.54 — Public/OBS presentation build-out

- **0.2.23 — filter «Всего» behavior** — **IMPLEMENTED / ACCEPTED**.
- **0.2.24 — hide Public list** — **IMPLEMENTED / ACCEPTED**.
- **0.2.25 — synchronized Games/Public list visibility** — **IMPLEMENTED / ACCEPTED**.
- **0.2.27 — search in Public List** — **IMPLEMENTED / ACCEPTED**.
- **0.2.28 — synchronized search behavior between Games/Public** — **IMPLEMENTED / ACCEPTED**.
- **0.2.29 — lower-right OBS information block** — **IMPLEMENTED / ACCEPTED**.
- **0.2.30 — readable OBS JSON** — **IMPLEMENTED / ACCEPTED**.
- **0.2.31 — built-in OBS overlay** — **IMPLEMENTED / ACCEPTED**.
- **0.2.32–0.2.33 — current-game title + lower-right information block refinements** — **IMPLEMENTED / ACCEPTED**.
- **0.2.35 — Top-3 + list scroll direction** — **IMPLEMENTED / ACCEPTED**.
- **0.2.36 — corrected Top-3 composition** — **IMPLEMENTED / ACCEPTED CORRECTION**.
- **0.2.37 — configurable overlay placement** — **IMPLEMENTED / ACCEPTED**.
- **0.2.38 — hide zero sums from scrolling viewer list where applicable** — **IMPLEMENTED / ACCEPTED**.
- **0.2.39–0.2.40 — per-block/adaptive overlay typography and Top-3 typography** — **IMPLEMENTED / ACCEPTED**.
- **0.2.41 — large current-game title typography** — **IMPLEMENTED / ACCEPTED**.
- **0.2.42–0.2.43 — adaptive Stream/OBS tab, size controls and scroll restoration** — **IMPLEMENTED / ACCEPTED**.
- **0.2.44–0.2.46 — glow/frame colors, list/info glow and independent frame colors** — **IMPLEMENTED / ACCEPTED**.
- **0.2.47–0.2.48 — transparent game/webcam cutouts inside otherwise opaque visual overlay** — **IMPLEMENTED / ACCEPTED**.
- **0.2.49 — separate OBS URL for list** — **IMPLEMENTED / ACCEPTED**.
- **0.2.50 — overlay background-image library** — **IMPLEMENTED / ACCEPTED**.
- **0.2.51 — GIF/video backgrounds** — **IMPLEMENTED / ACCEPTED**.
- **0.2.52 — scrollable settings + compact presentation controls** — **IMPLEMENTED / ACCEPTED**.
- **0.2.53 — synchronize frames and transparent cutouts** — **IMPLEMENTED / ACCEPTED**.
- **0.2.54 — final verification of first three tabs** — **CLOSED / ACCEPTED**.

## 0.2.55–0.2.72 — Auction/wheel operator UX

- **0.2.55 — clearer Preview button names** — **IMPLEMENTED / ACCEPTED**.
- **0.2.56 — unified Auction search** — **IMPLEMENTED / ACCEPTED**.
- **0.2.57 — Auction table** — **IMPLEMENTED / ACCEPTED**.
- **0.2.58 — local Auction mode foundation** — **IMPLEMENTED / ACCEPTED**.
- **0.2.59 — nested Auction tabs** — **IMPLEMENTED / ACCEPTED**.
- **0.2.60 — per-subtab `Правила вкладки / Скрыть правила` on Auction → Lots / Conducting / Pointauc**; help text hidden by default and toggled locally — **IMPLEMENTED / ACCEPTED**.
- **0.2.61 — conduct auction from one operator surface**: manual bid moved from Lots to Conducting; Conducting contains its own current-session lot list/search/manual amount controls; smooth ping-pong autoscroll pauses for real user interaction; manual amount field drops the old ₽ suffix — **IMPLEMENTED / ACCEPTED**.
- **0.2.62 — Conducting interaction/synchronization corrections**: timer refresh no longer steals input focus; autoscroll pauses while interacting; manual amount/status changes propagate immediately across Games/Public/both Auction lists/Journal and OBS/API through the common DB path; Conduct search/selection synchronizes correctly — **IMPLEMENTED / ACCEPTED CORRECTIONS**.
- **0.2.63 — direct search/focus/info/tie UX decisions** — **IMPLEMENTED / ACCEPTED**: Auction search field is simply `Поиск`; switching Auction tabs does not automatically transfer focus into search; OBS `Текст информационного блока` has no preset dropdowns; tie state is named `Несколько победителей` and offers `Дополнительное время` or wheel; tie-wheel leaders use equal chances, including all-zero tie fallback.
- **0.2.64 — tie/search focus refinement**: empty focused search does not stop autoscroll, entered text does; click on empty Conducting area clears focus; `Несколько победителей → Использовать колесо` reliably exposes `Запустить колесо` and identifies `Максимальная сумма → Колесо (тай-брейк)` — **IMPLEMENTED / ACCEPTED**.
- **0.2.65 — restore active auction state after restart** — **IMPLEMENTED / ACCEPTED**.
- **0.2.66 — random-number generator choices** — **IMPLEMENTED / ACCEPTED**.
- **0.2.67 — visual wheel** — **IMPLEMENTED / ACCEPTED**.
- **0.2.68 — wheel preview, smoothness and adding new lots during auction** — **IMPLEMENTED / ACCEPTED**.
- **0.2.69 — protection against clicks leaking through other windows/dialogs** — **IMPLEMENTED / ACCEPTED**.
- **0.2.70 — local wheel smoothness rework** — **IMPLEMENTED / ACCEPTED**.
- **0.2.71 — readable local-wheel labels** — **IMPLEMENTED / ACCEPTED**.
- **0.2.72 — tie-wheel timing and larger time arrows/controls** — **IMPLEMENTED / ACCEPTED**.

## 0.2.73–0.2.93 — performance/safety/detail hardening

- **0.2.73 — technical optimization/decomposition**: UI/DB facades split into subject modules, batched settings transaction, fewer API DB connections, WAL configured once, named migrations, remote RNG off GUI thread, dirty/lazy heavy tabs, cached OBS HTML, temp-DB smoke, cleaner docs/release archive — **IMPLEMENTED / ACCEPTED**.
- **0.2.75 — relative-import correction after decomposition + static import check** — **IMPLEMENTED / ACCEPTED**.
- **0.2.77 — Windows smoke + immediate release of SQLite backup handles** — **IMPLEMENTED / ACCEPTED**.
- **0.2.78 — cancel promotes temporary lots with saved points + readable adaptive local-wheel labels** — **IMPLEMENTED / ACCEPTED**.
- **0.2.79 — cancel refreshes Games/Public/Auction/Journal immediately + full OBS wheel labels** — **IMPLEMENTED / ACCEPTED**.
- **0.2.80 — responsive destructive delete + minimal audit tombstone** — **IMPLEMENTED / ACCEPTED**.
- **0.2.81 — isolated-process backup + aggregate Games counters + performance diagnostics** — **IMPLEMENTED / ACCEPTED**.
- **0.2.82 — responsive Journal via model/view + background loading** — **IMPLEMENTED / ACCEPTED**.
- **0.2.83 — targeted SQLite performance indexes** — **IMPLEMENTED / ACCEPTED**.
- **0.2.84 — RNG selector shown only when RANDOM.ORG API key is configured** — **IMPLEMENTED / ACCEPTED**.
- **0.2.85 — Wheel OBS URL/preview controls shown only when wheel is relevant** — **IMPLEMENTED / ACCEPTED**.
- **0.2.86 — correct word-boundary wrapping in standalone list overlay** — **IMPLEMENTED / ACCEPTED**.
- **0.2.87 — preserve list-overlay scroll position across live resort/re-render** — **IMPLEMENTED / ACCEPTED**.
- **0.2.88 — bounded/rotating technical logs; performance trace opt-in** — **IMPLEMENTED / ACCEPTED**.
- **0.2.89 — asynchronous full-history Journal search with debounce/stale-result protection** — **IMPLEMENTED / ACCEPTED**.
- **0.2.90 — safe background CSV import with isolated backup/prune gate** — **IMPLEMENTED / ACCEPTED**.
- **0.2.91 — flexible CSV import/compatibility refinements** — **IMPLEMENTED / ACCEPTED**.
- **0.2.92 — safe backup restore** — **IMPLEMENTED / ACCEPTED**.
- **0.2.93 — destructive «Очистить все игры…» with typed confirmation, mandatory backup, open-auction guard and historical auction-entry snapshots** — **IMPLEMENTED / ACCEPTED**.

## 0.2.94–0.3.02 — Auction timer point 9

- **0.2.94 — compact timer controls**: one Start/Pause/Resume button, quick +/- time, Reset with confirmation, persistence through deadline state — **IMPLEMENTED / ACCEPTED**.
- **0.2.95 — millisecond timer + editable HH:MM:SS.mmm, -10/-1/+1/+10 min, Finish intake and Stop auction actions** — **IMPLEMENTED / ACCEPTED**.
- **0.2.96 — contextual timer**: max-amount countdown vs direct weighted-wheel spin duration in the same large timer; tie overtime/wheel reuses same UI — **IMPLEMENTED / ACCEPTED**.
- **0.2.97 — startup compatibility re-export correction after timer refactor** — **IMPLEMENTED / ACCEPTED CORRECTION**.
- **0.2.98 — wheel duration up to 24h, timer remains visible after result, winner_selected can still be cancelled with audit preservation, long-spin visual scaling** — **IMPLEMENTED / ACCEPTED**.
- **0.2.99 — persist edited wheel duration before tie-break refresh can overwrite it** — **IMPLEMENTED / ACCEPTED CORRECTION**.
- **0.3.00 — Settings → General/Auction split + persisted default wheel-spin duration** — **IMPLEMENTED / ACCEPTED**.
- **0.3.01 — six-digit HHMMSS shorthand normalized to HH:MM:SS.000** — **IMPLEMENTED / ACCEPTED**.
- **0.3.02 — persisted default max-amount duration, independent from current live session** — **IMPLEMENTED / ACCEPTED**.
- Historical proposal for a separate tie-overtime default existed at this stage; later E3 decision **SUPERSEDED** it by reusing the existing duration model instead of creating another independent setting.

---

# XVIII. August Stabilization A1–A12 — separate historical namespace

These identifiers are **not** Product A1–A8 and **not** Maintenance A1–A10 from October.

- **August Stabilization A1 / 0.3.03 — safe update/release archive**: user DB/WAL/SHM/backups/media/logs/temp excluded; single fail-closed release builder; atomic final ZIP replacement; clean-install/update simulations — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A2 / 0.3.04 — secret settings redaction in Journal**: RANDOM.ORG API key stored normally for RNG but audit before/after contains only `[СКРЫТО]` — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A3/A4 / 0.3.05 — protect games participating in unfinished auction from archive/delete; unrelated games remain editable; winner forced visible/not archived** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A5 / 0.3.06 — eliminate wheel-payload N+1 DB access via shared connection-aware payload path** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A6 / 0.3.07 — atomic CSV import transaction; no partial commits after later-row failure** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A7 / 0.3.08 — large MP4/WEBM background copy off GUI thread via existing worker pool** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A7.1 / 0.3.09 — selecting an external video whose filename already exists reuses existing library item instead of creating `(2)` duplicate** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A8 / 0.3.10 — hidden AuctionTab stops unnecessary high-frequency visual timers/refresh while functional deadline watchdog remains active** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A9 / 0.3.11 — synchronized search updates visible table immediately while hidden tables become dirty and catch up lazily** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A10 / 0.3.12 — local wheel frame timer stops in idle/static state** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A11 / 0.3.13 — OBS wheel does not keep permanent requestAnimationFrame in idle; later spins can restart animation without page reload** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A11.1 / 0.3.14 — corrected wheel motion profile with acceleration, cruise and deceleration while preserving RNG/result** — **CLOSED / MANUALLY ACCEPTED**.
- **August Stabilization A12 / 0.3.15→0.3.16 — GUI smoke direct weighted-wheel path must use the real operator `start_auction()` flow; corrected hidden-tab initialization before asserting local animation** — **CLOSED / MANUALLY ACCEPTED**.
- The stale OBS Browser Source self-reload/version-handshake proposal was explicitly deferred at this stage and later became **IMPLEMENTED** through the accepted overlay version/cache-busting mechanism; it is not an open item.


# XIX. User-approved pre-1.0 stabilization / release-stage ledger

Эти пункты не являются current feature backlog. Они отдельно восстановлены третьим reconciliation-pass как пользовательски одобренные/принятые engineering, deployment и UI scopes перед публичным 1.0.0.

## Post-MAIN engineering audits

- **FINAL MAIN STABILIZATION / 0.3.83** — полный regression/documentation/manual closure уже реализованного MAIN без изменения product bytes — **CLOSED / MANUALLY ACCEPTED**.
- **Optimization & Deep Audit / 0.3.84** — меньше SQLite connections/narrow projections на hot read paths, bounded Rules sanitizer cache, batched integration-status reads, demand-driven UI timers, sleeping static Browser Source RAF loops, compact JSON with optional pretty mode, denser release compression/docs — **IMPLEMENTED / ACCEPTED CURRENT** before 0.3.85. Product behavior/schema intentionally unchanged.
- **Optimization & Reliability Audit II / 0.3.89** — one-snapshot Games/Public refresh composition, safe QTableWidgetItem reuse with complete state rewrite, Main/List serialization cleanup, shared Qt thread-pool cap/idle expiry and explicit release-clean separation of end-user source from QA/dev material — **CLOSED / MANUALLY ACCEPTED**.
- **Release-clean QA separation** — clean end-user package excludes tests/tools/dev harness/caches/runtime-user data; separate QA package may contain verification tooling but must never be promoted as CURRENT — **IMPLEMENTED / ACCEPTED**.

## E1 focused UI follow-up

- **0.3.91 — remove native up/down arrows from Games `Баллы` numeric field** while preserving numeric entry/range/step and mouse-wheel protection — **USER REQUEST / IMPLEMENTED / MANUALLY ACCEPTED**.

## R1.0.x public-1.0 release-stage decisions

- **R1.0.1 — one selected installation root**: default `C:\InOneLine`, user may choose another drive/folder; app-owned `data/backups/logs` stay under that root; no AppData split — **USER-ACCEPTED / IMPLEMENTED**.
- **R1.0.2 — external full `.iolbackup` create/validate/restore/rollback** — **IMPLEMENTED / INCLUDED IN ACCEPTED 1.0.0**. It remains distinct from ordinary internal SQLite-only safety backups.
- **R1.0.3 — production Windows installer + approved application/shortcut icon behavior** — installer/GUI/icon gate **USER ACCEPTED / CLOSED**. Approved icon preserves the green rounded-square/black branching-arrow identity without a white square/background.
- **R1.0.4 — final uninstall policy**: explicit destructive warning, safe Cancel/No path, confirmed removal of program + app-owned data/backups/logs/private settings/shortcuts/registration while external `.iolbackup` and merely referenced external files survive — **USER ACCEPTED / CLOSED**.
- **R1.0.5 — update/reinstall contract**: stable AppId/previous chosen custom root is reused; immutable runtime refreshed while mutable `data/backups/logs` survives — **QA-ONLY GATE / USER ACCEPTED / CLOSED**.
- **R1.0.6 — real-host no-development-stack proof**: installed InOneLine must run without Visual Studio/Python/Inno/build environment and must not install unrelated development components — **USER-DEFINED GATE / MANUAL PASS / CLOSED**.
- **R1.0.7 scope — global MainWindow geometry stability**: tab/subtab/dynamic-control changes must not resize the user-chosen top-level window; Games/Public hide/show and duplicate navigation cannot force hard-coded geometry; dense Auction content must reflow/scroll internally — **USER EXPLICITLY PULLED FORWARD BEFORE 1.0.0**. The R1.0.7 candidate itself failed minimum-window QA, but the geometry contract survived into final 1.0.10.
- **R1.0.8 retained fix — minimum-window vertical readability**: Settings pages and Auction/Conduct use vertical scroll/minimum-layout constraints instead of collapsing/overlapping dense controls — **IMPLEMENTED IN FINAL 1.0.10** after the R1.0.8 candidate exposed a residual time-field defect.
- **R1.0.9 retained UI organization** — **USER APPROVED / IMPLEMENTED IN FINAL 1.0.10**:
  - Auction top-level subtabs reduced to Lots / Conducting; visible Auction Export removed;
  - new Settings → Export centralizes CSV/JSON/Excel + Pointauc CSV/Copy list;
  - Public List keeps search/Public XLSX but loses duplicate CSV/JSON/Excel buttons;
  - shared main-list XLSX controls move to Games;
  - auction time editors receive explicit readable width floors.
- **R1.0.10 — cold-start auction-duration field height floor**: minimum 34 px avoids first-layout vertical clipping at saved 1100×700 without reintroducing automatic window resizing — **MANUALLY ACCEPTED / RELEASED as 1.0.0**.
- R1.0.7, R1.0.8 and R1.0.9 candidate statuses themselves remain **SUPERSEDED / NOT ACCEPTED**; only their retained corrected behavior is part of final accepted 1.0.0.

# XX. Reconciliation conclusion 2026-10-02

После третьего глубокого cross-source pass и финального zero-delta поиска по прошлым чатам:

- **D44 не найден**.
- Восстановлены granular 0.2.x implementation ledger, отдельный August Stabilization A1–A12/A7.1/A11.1 namespace и pre-1.0 stabilization/release-stage ledger.
- Исправлено сопоставление Rules: **R1 = editor/templates/session snapshot**, **R2 = standalone OBS Rules viewer**.
- Восстановлены direct UX details Auction/Conducting, Saved/New Auction, A6.1, B1/B2, D19 picker, W2 repair flow и provider-neutral outside-auction contribution rule.
- Старый отдельный local write API `POST /api/v1/bids`/generic `PUT /lot` подтверждён как assistant-only proposal, а не user-approved backlog; пользователь утвердил Pointauc/B6 adapter.
- Зафиксирован superseded initial GitHub release-only/no-source plan и более поздняя official SOURCE+INSTALLER/license model.
- Advanced History analytics остаётся **USER-ACCEPTED post-completion/post-integration**, D9–D12 сохраняют direct-user provenance/conditionality.
- Все новые находки этого прохода — реализованные/закрытые/исторические решения или уточнения provenance; **нового future implementation candidate не найдено**.
- Финальный conversation orphan search после внесения этих исправлений не вернул дополнительной direct user-proposed функции: только уже записанные решения и operational/assistant-only false positives.
- GitHub Issues не являются полным backlog.
- Любой будущий найденный старый пункт сначала проверяется против более позднего direct-user decision и current/released behavior, и только затем может менять `ROADMAP.md`.

Canonical current selection: `PROJECT_STATE.md` + `ROADMAP.md`.
Полная история идей: этот файл.
