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
- **Full external `.iolbackup` для восстановления после полного удаления программы** — **IMPLEMENTED / ACCEPTED**: authoritative DB, protected credentials и managed media; backup хранится вне install root и переживает uninstall; logs/temp/runtime/external referenced files не встраиваются. Accepted UI wording is exactly `Создать полную резервную копию в случае полного удаления программы`; separate full restore remains available.
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
- **Изменения сохранённых presentation settings применяются к открытым Browser Sources без смены URL** — **IMPLEMENTED / ACCEPTED**. Accepted 5.9 detail: only explicit Save/Apply changes authoritative viewer configuration; unsaved intermediate edits are not pushed. Ordinary settings updates require no manual OBS refresh and should preserve unrelated runtime visual/business state where practical; this is separate from E2 app-version stale-page reload.
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
- **Product A2 — постоянная inline-строка добавления нового лота в Conduct** — **IMPLEMENTED / ACCEPTED**. Название после trim/normalization не может быть пустым/whitespace-only и использует общую duplicate protection вместо создания параллельного правила. Numeric points field for adding a lot, like the shared manual-bid/points field, does not expose native up/down spin arrows. Accepted explanatory rule remains visible beside this flow; its early `после подтверждения победителя` wording was later superseded by accepted runtime semantics: temporary lot stays current-auction-only while the auction is open, is promoted to the main Games list after **completion or cancellation**, confirmed winner becomes `ПРОХОДИТСЯ`, otherwise it remains `НЕ ИГРАЛ`, after which it is editable in Games.
- **Product A3 — frozen start position + live/current position** — **IMPLEMENTED / ACCEPTED**.
- **Product A4 — ручные «Добавить» / «Уменьшить» как auditable compensating operations** — **IMPLEMENTED / ACCEPTED**.
- **Product A5 — удалять только ошибочный temporary auction-only lot текущей активной сессии** — **IMPLEMENTED / ACCEPTED**.
- **Product A6 — итог `Всего: N баллов`** — **IMPLEMENTED / ACCEPTED**. Ранняя идея show/hide superseded: финально total всегда видим.
- **Product A6.1 — live `Шанс в колесе`** — **IMPLEMENTED / ACCEPTED**. Weighted-wheel-only read-only chance uses exactly the authoritative selection weights/probability math, updates live without changing business state, is hidden in ordinary max-amount context, and is distinct from W4 frozen post-result winner chance.
- **Product A7 — current-auction History + hover highlight связанного лота + compact `Ставки | История`** — **IMPLEMENTED / ACCEPTED**. Accepted detail: one mutually exclusive compact area; `Ставки` is the current-auction incoming-event feed, `История` is the current-session business-change feed distinct from global Journal/completed History; cards retain event type/time/object/details, relative time may be shown while exact timestamp remains stored, and incremental updates are preferred over heavy full rebuilds. History cards must identify the affected lot/object and relevant values/details clearly; standard event types use understandable icons, with color only as a secondary cue rather than the sole distinction. Hover linkage is operator UI only and does not create viewer-side control state.
- **Product A8 — safe compensating Undo для обратимых действий** — **ACCEPTED / DEFERRED**. 2026-09-01 пользователь решил не включать в MAIN; нужен новый safety/design review, прежний whitelist не pre-approved. Durable safety invariants from the original acceptance still survive: Undo must create a new auditable compensating event rather than delete/rewrite the original history record; it must be unavailable once later dependent changes make reversal unsafe; and Undo is operator-only inside InOneLine, never exposed to viewer OBS outputs. Exact reversible-action whitelist remains intentionally unapproved until fresh review.

## S2 / History / Verification

- **Поиск внутри «Журнала» по любому событию** — **IMPLEMENTED / ACCEPTED**: поиск локален для Journal, проверяет отображаемые и raw-поля события и при непустом запросе ищет по полной истории, а не только по обычному окну последних 500 записей.
- **S2 — timer auto-extension** по actual leader change / genuinely new lot / external donation, threshold, dedup, max-one-extension collision rule и 24h ceiling — **IMPLEMENTED / ACCEPTED**. Exact accepted semantics: new-lot reason fires only on actual creation of a new lot, not on increment of an existing match or manual correction; external-event reason fires only after successful common-pipeline acceptance/dedup and never twice for the same source+external_event_id; one originating action/event may yield only one extension, using the largest configured duration among simultaneously matched enabled reasons rather than summing them; threshold is persisted/configurable, equality at the threshold is eligible, disabling threshold allows enabled reasons throughout a running auction, paused/non-running sessions do not auto-extend, and an already expired timer is never resurrected.
- **Внешнее денежное автопродление + optional service units** — **IMPLEMENTED / ACCEPTED** окончательно в 1.0.3.
- **Core «История аукционов»**: period filter, base summary, all closed sessions, newest-first, search/sort, pagination/lazy loading, read-only details — **IMPLEMENTED / ACCEPTED**.
- **Winner Verification immutable per-run snapshot** — **IMPLEMENTED / ACCEPTED**: preserve the exact ordered participants and effective weights/chances, effective draw range/equal-weight fallback as applicable, selected RNG method, generated random value, resolved winner, timestamp and algorithm/mapping version; Random.org+ reuses the existing signed ticket/signature evidence where present. Later game/app edits must not rewrite this historical snapshot.
- **Deterministic read-only re-check из snapshot** — **IMPLEMENTED / ACCEPTED**: mathematical replay/check only; it never redraws RNG, changes winner, mutates auction state or rewrites history.
- **Verification inside completed-auction details** — **IMPLEMENTED / ACCEPTED**; no duplicate top-level verification page.
- **Optional pre-spin `Данные проверки`** — **IMPLEMENTED / ACCEPTED**: read-only frozen participant/weight/chance/range/RNG data and Random.org+ Ticket ID where present; opening it is never required before spin and never mutates RNG/ticket/winner state; no mandatory viewer OBS overlay is created.
- **D7 whole-snapshot cryptographic hardening boundary** — **USER-ACCEPTED / POST-COMPLETION ONLY**: MAIN relies on immutable app snapshot + existing Random.org+ signed authenticity where applicable + deterministic replay/read-only History. A same-database SHA-256 alone is explicitly **not** considered meaningful protection against intentional tampering. Whole-snapshot signing, protected key management, external hash publication/notarization or independent off-app verification require a separate future security design. A separate public Internet-hosted verification page is likewise **not implied by MAIN**; localhost remains the default serving boundary, while LAN/public sharing requires its own separately approved D38/Public-Web/security design.

---

# III. Saved/New Auction

- **«Сохранённые аукционы»** — несколько именованных reusable working auction configurations без второй Games database, с быстрым выбором/переключением и безопасными rename/delete flows — **ACCEPTED / DEFERRED TO POST-COMPLETION**. Обычный Save обновляет уже связанную saved-конфигурацию; отдельная копия создаётся только через явный Save-As-like путь.
- **Полный «Новый аукцион…»** с именем, `Начать без сохранения` / `Сохранить предыдущий и начать`, безопасной обработкой активной сессии и immutable historical name snapshot — **ACCEPTED / DEFERRED**, зависит от Saved Auctions. Создание нового working auction не очищает Games, global Journal, completed History, Saved Auctions, integration settings, Rules templates или global/widget OBS settings; сбрасывается только runtime новой рабочей сессии.
- Completed History и Saved Auctions — разные системы; переименование/удаление saved configuration не переписывает историю — **DURABLE ACCEPTED RULE**.

---

# IV. W-series / media / audio

- **W1 — Space вызывает существующий путь «Крутить»** — **ACCEPTED / DEFERRED**. Был реализован, но 2026-09-01 пользователь отменил включение в MAIN и попросил оставить улучшением готовой программы; current runtime этого shortcut не содержит. Accepted guard contract for any future reintroduction: Space must call the existing Spin action rather than a second start/RNG path; it must be ignored while focus is in text/numeric/other controls where Space has normal meaning, and it must not cause duplicate/re-entrant spin while spinning or when Spin is otherwise unavailable.
- **W2 — единая managed-copy / external-reference media infrastructure** — **IMPLEMENTED / ACCEPTED**. Final UX distinguishes the normal contextual add/select action (for example `Добавить фон…`) from `Восстановить ссылку…`, which appears as a repair action for a missing external reference instead of looking like a second ordinary picker. External-reference contract: InOneLine never modifies/deletes the referenced original file; moved/renamed/deleted/disconnected/unavailable media degrades safely instead of crashing; the user can repair/reselect the reference; Browser Sources never receive arbitrary filesystem access or raw absolute-path exposure, and existing traversal/range-serving protections remain authoritative for referenced video/media.
- **W2 direct UX corrections** — **IMPLEMENTED / ACCEPTED**: основное действие для фона формулируется как `Добавить фон…`; repair/restore-reference UI показывается только для реально потерянного external-файла, а не как постоянная параллельная кнопка.
- **Разные managed media folders по назначению** (backgrounds, music/soundtrack, wheel/center assets и т.п.) — **IMPLEMENTED / ACCEPTED**.
- **W3 — soundtrack колеса MP3/WAV/OGG, application-owned transport, volume/mute** — **IMPLEMENTED / ACCEPTED**.
- **W3 direct UI contract** — **IMPLEMENTED / ACCEPTED**: `Музыка колеса` и `Добавить soundtrack…` визуально разделены; крупные кнопки изменения громкости имеют полностью кликабельную площадь; Mute находится отдельной строкой; ошибки/отсутствие аудио не могут блокировать RNG/winner lifecycle.
- **Auction/Timer Music — historical pre-D26 contract + current supersession** — ранний accepted contract включал managed/local playlist, выбранный стартовый трек, Loop One/sequential library order, независимые Auction/Wheel profiles и точное сохранение Auction track+timestamp при временном Auction → Wheel → Auction context handoff. **D26 / 1.0.7 SUPERSEDED playlist semantics for current runtime**: Auction soundtrack теперь один выбранный зацикленный файл из общего `data\\soundtrack`; старый auction playlist/checkbox `Зациклить выбранный трек` больше не используется. D43 Browser Source transport/authoritative playback architecture сохраняется. Старый playlist нельзя автоматически восстанавливать как незакрытый scope; **D40** остаётся отдельной будущей идеей manual library order и требует fresh review.
- **W4 — точный frozen chance выпавшего победителя из resolved snapshot на desktop + Wheel OBS** — **IMPLEMENTED / ACCEPTED**.

---

# V. Rules / standalone widgets / stream UI

- **R1 — reusable Auction Rules package**: templates CRUD, active template, WYSIWYG editor, Undo/Redo, text-style presets, fonts/sizes/colors/highlight, bold/italic/underline, alignment, bullets/numbering, validation, unsaved-change protection and local read-only preview — **IMPLEMENTED / ACCEPTED**. Accepted editor-detail contract: presets are simple `Обычный текст / Заголовок / Подзаголовок` rather than H1–H6; formatting applies to selected fragments where appropriate; quick colors + arbitrary color picker; create-template confirmation/cancel; template name non-empty/normalized duplicate protection/reasonable length; active template visibly marked; editor opens directly in edit mode; Save persists and closes; unsaved-change protection covers template switch/editor close/current-template delete; rules content/style remains separate from viewer geometry/background/layout.
- **R1 session snapshot**: starting a local auction freezes rules template provenance/name/HTML into the auction session; historical sessions are not rewritten by later template changes — **IMPLEMENTED / ACCEPTED**.
- **R2 — standalone OBS Rules widget**: stable responsive Browser Source + read-only API, independent viewer visibility/autoscroll/background/opacity/padding and live apply — **IMPLEMENTED / ACCEPTED**. Direct control UX: Rules background `Непрозрачность` and `Внутренний отступ` use wide external ▲/▼ controls with manual numeric entry and hold/repeat; mouse-wheel scrolling must not silently change these values.
- **R2 single-editor correction**: `Аукцион → Проведение → Правила аукциона` is the only rules editor entry and remains usable before/during/after an auction. During an unfinished session, saving/renaming the matching source template synchronizes the open session copy; after finish/cancel historical rules remain frozen — **IMPLEMENTED / ACCEPTED**.
- **Rules OBS autoscroll** — **IMPLEMENTED / ACCEPTED**: overflow-only, pause top -> smooth down -> pause bottom -> reset, без сложных speed sliders в первой версии.
- **S3 — общий screen color eyedropper** — **IMPLEMENTED / ACCEPTED**: reusable across applicable color controls; temporary screen-pick mode works across visible monitors and mixed DPI/scaling, shows a magnified pixel grid/reticle, captures the exact center pixel on confirm, Escape/cancel leaves the prior color unchanged, and only updates the selected setting without a second color-storage backend.
- **Standalone widget foundation в «Стрим / OBS» со stable URLs и responsive Browser Sources** — **IMPLEMENTED / ACCEPTED**. Durable architecture: keep `Стрим / OBS` as the single top-level viewer-output center; do not create a duplicate top-level Widgets tab or generic named-instance/composite canvas. OBS owns composition/positioning, Browser Source Width/Height defines the viewport, URLs stay stable, and each standalone viewer function adapts responsively. Only information useful to viewers gets an OBS output by default; operator-only controls/status do not receive widgets merely for parity with another product. Any in-app preview-size control is preview-only, not a runtime canvas contract.
- **Standalone Timer viewer только с authoritative timer value, без второго timer engine** — **IMPLEMENTED / ACCEPTED**; пропущенный MAIN пункт был восстановлен и окончательно принят в 0.3.88. Exact viewer contract: Timer Browser Source shows only the timer value—no labels/start/pause/resume/adjustment/operator controls. When no auction is active it shows the configured initial/default duration for the next auction (respecting the current pre-start max-amount/wheel mode); during an auction it mirrors authoritative current timer state. Current 1.0.8 `current_timer_payload()` implements this idle/default-duration behavior.
- **Общие presentation controls standalone widgets** — **IMPLEMENTED / ACCEPTED** там, где применимо.
- **Built-in «Как добавить в OBS»** — **IMPLEMENTED / ACCEPTED**.
- **Одна общая инструкция OBS вместо одинаковой кнопки в каждом виджете** — **IMPLEMENTED / ACCEPTED in 1.0.2**.
- OBS flags `Shutdown source when not visible` / `Refresh browser when scene becomes active` — **ACCEPTED AS OPTIONAL GUIDANCE**, не обязательны для работы.

---

# VI. Интеграции

## Реализованная архитектура

- **B1 — единый `Настройки → Интеграции` center, adapter/status/security contract, DPAPI credential storage** — **IMPLEMENTED / ACCEPTED**. Accepted secret-hygiene boundary: plaintext tokens/passwords/API secrets must not be stored in main SQLite, ordinary settings/provider config, logs/diagnostics, exports or backup manifests/content; protected credential files may be included in full backup only as protected DPAPI ciphertext. Secret-bearing error/diagnostic text must be masked/sanitized. Accepted Integration Center structure: catalog grouped by purpose; each service is its own adapter/card with specialized settings rather than one giant generic form; moderate branding only; show operational capabilities/events/limits/status, not promotional fee/payment-logo clutter; multiple integrations may be active simultaneously; each adapter exposes capabilities so unsupported controls can be hidden; each integration has a manual connection/auth test outside the GUI thread plus adapter-appropriate automatic status tracking rather than a meaningless universal rapid poll.
- **B1 accepted Conduct/status UX details** — **IMPLEMENTED/ACCEPTED CONTRACT; ONE CURRENT UI OMISSION TRACKED AS QA-1.0.8-01**:
  - compact `Аукцион → Проведение` integration status shows only configured/used services;
  - integration errors remain visible even in compact/collapsed presentation;
  - Conduct provides navigation to `Настройки → Интеграции` instead of duplicating full provider configuration;
  - the accepted status concept includes **time of the last accepted integration event**;
  - `Отключить` and `Удалить подключение` are distinct operations; removal requires confirmation and must not delete historical `external_events`, contributions or auction history;
  - service network/auth work must not block the GUI; adapter capabilities control which provider-specific controls are applicable;
  - sufficient provider/source identifiers are preserved for future cross-service duplicate analysis, but no cross-service dedup algorithm is implicitly approved.
- **QA-1.0.8-01 — Conduct integration last-event visibility** — **ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT YET FIXED**. Current 1.0.8 still persists `integration_connections.last_event_at` and Settings shows `Последняя принятая активность`, while the current Conduct integration status/dialog does not display the accepted last-event time. No later direct user decision superseding this detail was recovered. This is a QA/reconciliation finding, not a new feature idea and not automatic authorization to change runtime.
- **B2 Twitch accepted lifecycle details** — **IMPLEMENTED / ACCEPTED**: public/native Device Code authorization without Client Secret; protected access/refresh credentials; startup/hourly validation and serialized refresh; invalid/revoked auth -> `Требует входа`, transient provider/network failures -> bounded `Ошибка`; Connect may reuse a valid preserved grant, Reconnect forces fresh authorization, Disconnect preserves local config/credential/history, Remove deletes local connection config + secret after confirmation but never historical integration/auction records. When disconnected/usage-disabled, the persisted account/config/credential metadata remains and restart stays disabled **without background provider validation** until use is re-enabled; accepted visible state is `Статус: Подключено · использование отключено` when a preserved connected grant is disabled. Remove returns the integration to `Не настроено` while retaining historical business records.
- **Integration connection UX** — **USER-ACCEPTED / IMPLEMENTED DIRECTION**: пользователь не должен вручную управлять client secrets или собирать сложную конфигурацию; где provider позволяет, подключение идёт через штатную browser/device authorization с public client/application credentials и protected local tokens.
- **B2 Twitch first adapter** — **IMPLEMENTED / ACCEPTED**.
- **B3 — автоматическое принятие разрешённых integration events** — **IMPLEMENTED / ACCEPTED**; generic Pending queue не является MAIN.
- **B4 — Twitch Channel Points / app-managed Custom Rewards** — **FUNCTIONALLY ACCEPTED / PARTIALLY ELIGIBILITY-DEPENDENT**. Архитектура/UX приняты; user correction допускает Channel Points contribution flow и во время, и вне активного аукциона по соответствующим правилам; live redemption verification отложена до Affiliate/Partner eligibility. Accepted management contract: InOneLine manages only rewards it created/registered for auction use; stores Twitch reward IDs; configurable common title plus per-reward cost/color; viewer text input carries game/lot message; redemptions flow through common B2/B3/S1 conversion. Reward availability may follow bid-intake state (start/resume enable, pause/completion disable). Unlinking Twitch is distinct from deleting rewards; destructive reward deletion requires explicit confirmation. Gracefully handle channels where Custom Rewards are unavailable.
- **B5 — `Ставки` feed автоматически принятых integration events** — **IMPLEMENTED / ACCEPTED**.
- **General outside-auction integration rule** — **IMPLEMENTED/ACCEPTED ARCHITECTURAL RULE**: a valid monetary or non-monetary external event may update persistent Games even when no auction is running. If the adapter supplies a usable title that does not yet exist, the accepted rule is to create a **normal persistent game** and credit it in the same transaction; do not create/start/resume an auction, `auction_only` row, auction entry, timer state or wheel state. Unknown conversion rate remains Pending and does not pre-create the game before credit can actually be applied. S2 timer extension requires an eligible running auction.
- **B3 matching-state detail** — **USER-ACCEPTED / PARTLY IMPLEMENTED**: during a running auction an unknown usable title becomes the ordinary temporary `auction_only` lot through the common auction path; outside auction it becomes a persistent game as above. A missing/unusable title must **not** auto-create or auto-credit; accepted behavior is a separate **`Требует привязки`** state awaiting manual binding to a game/lot, distinct from `pending_conversions` (unknown rate/unit). Current 1.0.8 instead marks `missing_target` as `inapplicable` and exposes no manual bind path. Track as **QA-1.0.8-03 / ACCEPTED B3 WORKFLOW OMISSION / NOT FIXED / NOT AUTO-AUTHORIZED**.
- **General B2 test/sandbox/demo event safety rule** — **USER-ACCEPTED / DURABLE SAFETY CONTRACT**: when a provider explicitly marks an event as test/sandbox/demo (e.g. a provider test flag), it must never mutate real business state: no SM-points credit, no create/increment lot/game, no leader change, no S2/3.3–3.5 timer extension, no wheel/winner effect. It may be retained only as technical integration diagnostics/history marked as test. **Current 1.0.8 generic normalized-event core has no explicit test-event field/gate**, so this accepted invariant is not represented generically yet; future adapters exposing an equivalent flag must enforce it through the common B2/B3 path. Track as **QA-1.0.8-02 / ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / NOT AUTO-AUTHORIZED**; no current supported-provider reproduction was established in this audit.
- **I1 / DonationAlerts adapter** — **IMPLEMENTED / ACCEPTED**: browser authorization/status, accepted built-in public OAuth Client ID is **20915**, поэтому пользователь проходит только авторизацию и не создаёт собственное приложение/не вводит Client Secret. **Поздний контракт supersedes ранний auction-only toggle:** подключение/enable интеграции является permission на постоянный intake; donations маршрутизируются по source timestamp в running auction либо в persistent game list вне аукциона. Отдельного `учитывать только в аукционе` intake-переключателя больше нет.

## Принятые, но отложенные service targets

Каждый требует fresh current official API/auth/event review:

- **Kick Channel Points / Custom Rewards** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; это сохранённый provider capability scope, а не generic «любая интеграция Kick». Перед реализацией заново подтвердить официальный/надёжный API/auth/event contract.
- **VK Video Live rewards/points** — **ACCEPTED / DEFERRED / FEASIBILITY-CONDITIONAL**; сохранённый scope относится к viewer/channel reward/points capability и требует свежего official API/auth/event feasibility review.
- **Common deferred donation-adapter contract** — **USER-ACCEPTED / PRESERVE**: reuse one B2/B3 ingestion path; deduplicate by source + external event ID; convert source currency/unit through common S1/POINT 5.4 rules; donation message/order text is the ordinary game/lot text while sender identity remains separate metadata; preserve original amount/unit/message/sender/event ID/time, applied conversion rate and resulting SM points in immutable history so later rate changes do not rewrite old donations; reuse common timer rules rather than provider-specific auction logic; use official/confirmed reliable programmatic APIs only, never page scraping/OBS-widget parsing/browser automation.
- **iHAQ Donate v2.0** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Preserve source/user/amount/currency/message/event identifiers; special interactive/super-donation mechanics are not automatically auction bets without a later explicit rule.
- **Donate Helper** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Official API/reliable transport/payload must be freshly verified; if no reliable programmatic interface exists, defer. Common history/conversion/matching rules remain authoritative.
- **DonatePay** — **ACCEPTED / DEFERRED / FEASIBILITY-GATED**. Realtime API/Centrifugo-style path was considered technically plausible, but exact current endpoint/auth/channel/payload/currency/event-ID contract must be reverified; REST recovery/reconciliation only where current API supports it.
- **DonateX** — **ACCEPTED / DEFERRED / OFFICIAL-API PATH PREVIOUSLY CONFIRMED, DELIVERY CONTRACT TO REVERIFY**. Preserve its provider test flag when present and apply the general B2 test-event safety rule; exact current live-delivery/auth/cursor/payload/identifier contract must be rechecked before implementation.
- **ODA/OpenDonationAssistant** — **DEFERRED / CONTRACT-BLOCKED** до безопасного official auth/event/history contract.
- **B6 Pointauc API adapter** — **ACCEPTED / DEFERRED**. Поздняя refinement: normal direction — InOneLine source of truth -> external mirror; emergency recovery только явно подтверждённым оператором. Перед кодом заново определить conflicts, IDs, dedup, writes/recovery. The provider token is a secret and must reuse B1 protected credential storage rather than plaintext main-SQLite storage. The adapter must wrap the common integration/auction business paths rather than become a second auction backend; source-of-truth direction, conflict handling, lot-ID mapping, bid deduplication, temporary-lot behavior and allowed provider write operations all require fresh explicit design before coding.
- **Older YouTube platform/integration candidate** — **RETAINED / SCOPE UNDEFINED**. Не путать с D41 chat provider и не путать с historical soundtrack-source wording.

---

# VII. История — принятая post-completion аналитика

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
- **D9 — Localization/languages** — **ACCEPTED / DEFERRED POST-COMPLETION**; русский остаётся primary. Accepted boundary: локализация должна быть централизованной на уровне UI/программных строк; пользовательские данные, названия игр и исторические записи не переводятся автоматически. Конкретный набор будущих языков не зафиксирован.
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
- **D25 — cumulative probability of lots <= winner amount** — **APPROVED POST-COMPLETION / EXPLICITLY «НЕ НУЖНО СЕЙЧАС»**. If revisited, compute only from the immutable snapshot of a completed **ordinary weighted-wheel** run; do not recalculate from later mutable game state and do not automatically inject the metric into the core post-result/viewer UI without a separate display decision.
- **D26 — full Music Player + own OBS overlay** — **IMPLEMENTED / RELEASED 1.0.7**.
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
- **D39 — per-scene widget style profiles** — **NOT DIRECTLY USER-APPROVED / HISTORICAL ASSISTANT POSSIBILITY / NOT ACTIONABLE**.
- **D40 — manual custom soundtrack/music library order** — **RETAINED POST-COMPLETION / NOT IMPLEMENTED**; D26 currently has Alphabetical/Shuffle, no manual playlist-order editor. Это отдельный future scope поверх current D26 media/audio state и **не означает восстановление superseded pre-D26 Auction playlist/Loop-One contract**.
- **D41 — cross-platform chat aggregation + separate OBS chat overlay** — **USER IDEA / POST-COMPLETION**. Twitch/YouTube/VK/other supported chat providers; ordinary chat does not mutate auction/points/lots/leader/timer/wheel/winner and is distinct from D15 AI-bot. Reuse B1/B2 auth/service adapters rather than a second connection manager; verify each platform's chat capability/API immediately before implementation. Exact cross-chat ordering, author fields, badges/emotes, moderation/filtering, history/persistence, styling and OBS presentation contract are **NOT YET APPROVED** and must be designed only when D41 is explicitly reopened.
- **D42 — current lot/sector under pointer during spin** — **USER-APPROVED POST-COMPLETION / NOT SELECTED**. During every visual spin frame show the logical lot currently under the pointer/arrow, based on actual rendered rotation (including lead-in/deceleration/final target), not the already-known future winner. Same behavior local+OBS; user-toggleable, preferably one shared persisted setting; reuse existing sectors/game_id/weight/rotation geometry; no second RNG/store or changes to winner/probability/verification/DB. Post-spin label persistence vs hide remains for fresh implementation review.
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
- **Отдельный InOneLine write/control Integration API (`POST /api/v1/bids`/generic `PUT /lot`) вне B6 contract** — **NOT USER-APPROVED / HISTORICAL ASSISTANT PROPOSAL**. Direct user approval was for the dedicated B6 provider adapter using that provider's official API; do not invent a separate local write API from the old proposal.
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

- **E1 — production EXE/PyInstaller readiness** — **IMPLEMENTED / ACCEPTED**. Historical native-EXE acceptance gate required the exact `build_exe.bat` run to visibly reach `[9/9] BUILD EXE: OK`; an auto-closing console was not accepted, so the run was repeated from CMD/PowerShell with the console left open (`pause` / `Press any key to continue...`) and full output visible. Build success itself still did not equal release acceptance: exact binary/manual EXE verification + explicit user approval remained mandatory.
- **E2 — stale OBS Browser Source version-handshake/cache-busting reload** — **IMPLEMENTED / ACCEPTED**.
- **E3 — tie extra-time default using existing duration model** — **IMPLEMENTED / ACCEPTED**; отдельная лишняя настройка не создаётся.
- **E4 — Windows Long Path/deep path deployment contract** — **IMPLEMENTED / ACCEPTED** в поддерживаемом <260 path contract. Arbitrary >=260 direct portable launch — out of scope/new separate scope, не unfinished E4.
- **Default install root `C:\InOneLine` + user-selectable destination/drive** — **IMPLEMENTED / ACCEPTED**.
- **No portable-user migration** — **USER DECISION / PRESERVE**.
- **Official artifacts after 1.0: SOURCE + INSTALLER; portable not CURRENT** — **USER DECISION / PRESERVE**.
- **Uninstall warning + confirmation; удалить app-owned DB/data/QSettings after confirmation; external .iolbackup/external referenced files preserve** — **IMPLEMENTED / ACCEPTED**.
- **Canonical icon: approved green InOneLine icon; improve the existing design (thicker/centered/sharper) and reuse one canonical asset for app/Setup/shortcuts** — **IMPLEMENTED / ACCEPTED**.

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
- **Release/QA defect numbering** — **DURABLE PROCESS RULE**: release/reconciliation findings use `QA-<version>-NN`; permanent D/A/W/B/E/R identifiers are not recycled for temporary defects/omissions.

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
- **0.2.60 — per-subtab `Правила вкладки / Скрыть правила` on Auction → Lots / Conducting / legacy third subtab**; help text hidden by default and toggled locally — **IMPLEMENTED / ACCEPTED**.
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
  - new Settings → Export centralizes CSV/JSON/Excel + legacy auction-pipe CSV/Copy list;
  - Public List keeps search/Public XLSX but loses duplicate CSV/JSON/Excel buttons;
  - shared main-list XLSX controls move to Games;
  - auction time editors receive explicit readable width floors.
- **R1.0.10 — cold-start auction-duration field height floor**: minimum 34 px avoids first-layout vertical clipping at saved 1100×700 without reintroducing automatic window resizing — **MANUALLY ACCEPTED / RELEASED as 1.0.0**.
- R1.0.7, R1.0.8 and R1.0.9 candidate statuses themselves remain **SUPERSEDED / NOT ACCEPTED**; only their retained corrected behavior is part of final accepted 1.0.0.

# XX. Reconciliation conclusion 2026-10-02

The original early-pass conclusion was superseded by the user's repeated full rechecks on the same date. The authoritative final reconciliation state is:

- **D1–D43 are accounted for; there is no actual D44 item.**
- Three historical A namespaces remain separate: **August Stabilization A1–A12 (including A7.1/A11.1)**, **Product A1–A8/A6.1**, and **Maintenance A1–A10**.
- Rules aliases remain corrected: **R1 = editor/templates/session snapshot**, **R2 = standalone OBS Rules viewer**.
- Current accepted-scope QA findings are explicitly tracked: **QA-1.0.8-01**, **QA-1.0.8-02**, **QA-1.0.8-03**. They are findings, not automatic authorization to change runtime.
- The repeated seventh–tenth sequence recovered the B2 test-event safety rule, B3 `Требует привязки`, outside-auction persistent-game behavior, provider contracts, E1 exact build gate, publication/reference-wording rules, detailed Rules/B1/Winner/D28–D42 boundaries and then reached a clean post-correction control.
- The repeated **eleventh–fourteenth** sequence then recovered further durable detail:
  - the missing 2026-08-21 original reference-image archive gap and the `QA-<version>-NN` defect-numbering convention;
  - advanced History identity/comparability rules, W1 input/re-entrancy guards and W2 external-reference safety;
  - exact standalone Timer idle/default-duration behavior and deferred A8 compensating-Undo invariants;
  - exact S2 collision/threshold semantics, standalone-widget architecture, B6 protected-secret/common-backend rules, Winner Verification public-hosting boundary and A7 history-card/hover semantics;
  - the full B1 plaintext-secret exclusion plus disabled-integration/no-background-validation lifecycle;
  - one production-unreachable DonationAlerts manual-Client-ID fallback branch, classified as **source-hygiene/compatibility residue**, not a runtime QA defect and not auto-authorized for cleanup.
- **Fifteenth post-correction orphan-only control: CLEAN.** After all of those corrections were written, no additional durable direct-user product requirement, future idea, rejection, UX rule, provider contract, deployment rule, release/QA rule or documentation/process rule remained orphaned.
- Therefore the repeated audit itself was **not zero-delta**, but the **final post-correction control had zero additional delta**.
- GitHub Issues remain tracking aids only, not the complete backlog. Open tracking remains #4 Global Multi-File Import and #5 D22 Battle Royale; stale PR #9 remains repository hygiene, not product scope.
- No implementation scope was automatically selected by this reconciliation.
- Current runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**.

Canonical current selection: `PROJECT_STATE.md` + `ROADMAP.md`.
Full exhaustive idea/history ledger: this file.
Detailed reconciliation trail: `docs/history/ROADMAP_RECONCILIATION_2026-10-02.md`.
