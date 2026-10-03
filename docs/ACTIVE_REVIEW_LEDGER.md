# Active Review Ledger

**ПЕРВОЕ И ОБЯЗАТЕЛЬНОЕ ПРАВИЛО:** перед каждым ответом по текущей работе над InOneLine сначала сверяться с этим документом. Этот файл является рабочим журналом текущего этапа: поиск багов, доработка интерфейса и улучшение уже существующих функций. Он не разрешает автоматически менять программу.

## 1. Текущий режим работы

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

## 2. Постоянное инженерное правило этого этапа

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

## 3. Правила накопления задач

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

## 4. Очередь замечаний по скриншотам

Пока пусто. Новые пункты добавляются сюда по мере разбора присылаемых пользователем скриншотов.

### 4.1 Просмотренные экраны / visual baseline

- **SCREEN-001 — вкладка `Игры` — 2026-10-03 — BASELINE CAPTURED.**
  - Скриншот получен до формулировки замечаний пользователя.
  - Код/runtime не изменялись.
  - Экран используется как исходная визуальная точка для последующих замечаний по вкладке `Игры`.

Для каждого пункта фиксировать:

- ID;
- экран/вкладку;
- существующую функцию;
- что видно сейчас;
- что именно пользователь хочет изменить;
- предполагаемое переиспользуемое основание;
- риск затронуть другие функции;
- статус;
- после начала реализации — способ ручной проверки и результат пользователя.

## 5. Известные ранее найденные проблемы, которые нельзя потерять

Эти пункты уже документированы в проекте. Они не считаются новой функциональностью и не начинают исправляться автоматически:

- **QA-1.0.8-01** — в compact Auction -> Conduct integration status отсутствует показ времени последнего принятого integration event при уже существующем `integration_connections.last_event_at`.
- **QA-1.0.8-02** — общий normalized-event core не имеет явного общего safety gate для provider events, помеченных test/sandbox/demo; такие события по принятому contract не должны влиять на реальные баллы/лоты/лидера/таймер/колесо/победителя.
- **QA-1.0.8-03** — отсутствует принятый B3 workflow `Требует привязки` для integration event без пригодного game/lot title; это отдельный сценарий от pending conversion.

До отдельного выбора пользователем все три остаются только зафиксированными findings.

## 6. Реестр уже существующих функций — baseline для сохранения

Этот раздел нужен как рабочий checklist. Он не заменяет `IDEA_INVENTORY.md`, `ROADMAP.md`, `DECISIONS.md` и код. При разборе каждого скриншота сначала проверяется, какие пункты из этого реестра затрагиваются.

### 6.1 Игры

- локальная SQLite БД как source of truth;
- поиск по названию/отзыву, кнопка `Найти` и `Сбросить фильтры`;
- `Добавить игру`, `Изменить`, `Удалить`;
- `Импорт CSV` и встроенная справка `?`;
- `Очистить все игры` с open-auction guard, подтверждением и backup;
- statistic cards/filters: `Всего`, `Проходится`, `ДЛЯ АУКА`, `Играл`, `Не играл`, `Пройдено`, `Заброшено`, `Архив`, `Кооп`, `Не кооп`;
- `Правила сортировки`;
- статусы игр и единая каноническая сортировка Games/Public;
- защита от дубликатов;
- архивирование и восстановление;
- отдельное необратимое удаление с защитой/backup;
- поиск и навигация к найденной игре;
- общий активный список и отдельный архивный блок;
- `Скрыть список` / показ списка с сохранением UI state;
- `Копировать URL списка`;
- `Открыть предпросмотр списка`;
- основная таблица со столбцами `СТАРТ`, `ТЕКУЩАЯ`, `НАЗВАНИЕ ИГРЫ`, `ДАТА ВЫХОДА`, `БАЛЛЫ`, `КООП/НЕ КООП`, `СТАТУС`, `ОТЗЫВ`;
- синхронизация Games и Public List;
- гибкий ввод/проверка даты;
- числовое поле `Баллы` без native spin arrows.

### 6.2 Публичный список / импорт / синхронизация

- блок `Совместная таблица` на вкладке `Игры`;
- `Создать таблицу`;
- `Подключить таблицу`;
- отображение состояния подключения и времени последнего изменения;
- Public List без архивных игр;
- поиск Public List;
- синхронная видимость Games/Public;
- CSV/Excel/Google-readable import/export;
- строгая валидация импорта и duplicate protection;
- P1 публичное XLSX-зеркало;
- C2 обычный XLSX с двусторонней синхронизацией/last-change-wins.

### 6.3 Backup / Restore / пользовательское состояние

- внутренние safety backups;
- восстановление из резервной DB с предварительной страховочной копией и restart;
- запрет использовать рабочий `data\streaming.db` как собственный restore source;
- внешний полный `.iolbackup`;
- восстановление full backup/rollback;
- managed media входят в full backup, внешние referenced files — нет;
- сохранение geometry/position/maximized/current tab и применимого UI state;
- единый installation root и app-owned data/backups/logs внутри него.

### 6.4 OBS / Browser Source / представление

- основной OBS layout;
- отдельный URL списка игр;
- Top-3 + прокручиваемая часть списка;
- перенос длинных названий;
- current-game title;
- lower-right information block;
- независимые Webcam/List/Info blocks;
- переиспользование освободившегося места при отключении блока;
- отдельные frame/glow colors;
- прозрачные interior cutouts game/webcam;
- background media library и Stretch/Fit/Fill/Center;
- PNG/JPG/JPEG/WebP/GIF/MP4/WebM;
- live apply сохранённых presentation settings без смены URL;
- standalone responsive widgets;
- Wheel OBS Overlay;
- Timer Overlay;
- Auction Lots OBS overlay;
- version/cache-busting stale-page update mechanism.

### 6.5 Аукцион

- режим `Максимальная сумма`;
- weighted wheel;
- tie-break wheel при ничьей;
- authoritative RNG/result до визуальной анимации;
- Local RNG и RANDOM.ORG при настроенном ключе;
- timer Start/Pause/Resume/Reset и ручные -10/-1/+1/+10 минут;
- contextual max-amount/wheel timer;
- длительность wheel до 24 часов;
- temporary auction-only lots и их promotion после completion/cancel;
- увеличение существующего совпавшего лота вместо дубля;
- inline добавление лота в Conduct;
- ручные `Добавить` / `Уменьшить` как auditable operations;
- удаление ошибочного temporary lot текущей сессии;
- frozen start position + live position;
- `Всего: N баллов`;
- live `Шанс в колесе`;
- current-auction `Ставки | История`;
- History hover -> reveal/highlight lot без изменения operator selection;
- Auction Lots/Conduct/OBS shared session-only autoscroll;
- восстановление open auction/selected winner после restart;
- winner confirmation lifecycle;
- cross-surface synchronization Games/Public/Auction/Journal/OBS;
- elimination format и принятые between-round switching semantics.

### 6.6 История / Журнал / Verification

- глобальный Journal;
- поиск Journal по полной истории;
- background/debounced history search;
- Auction History с period filter, summary, search/sort, pagination/lazy loading и read-only details;
- immutable Winner Verification snapshots;
- сохранение per-run/per-spin verification data;
- audit records для бизнес-изменений и compensating operations.

### 6.7 Points / conversion / integrations

- внутренние целочисленные points;
- conversion rates для currency/service units;
- unknown-rate pending state;
- отдельное ручное `Применить` после настройки rate;
- service-specific conversion rows показываются только при доступной integration capability;
- timer auto-extension S2 с threshold/dedup/max-one-extension/24h ceiling;
- optional service units для внешнего автопродления;
- Integration Center / B1 connection state;
- protected credentials;
- RANDOM.ORG key в `Настройки -> Интеграции`;
- сохранение `last_event_at`;
- accepted integration event dedup/conversion/history foundations.

### 6.8 Rules / настройки интерфейса

- Rules editor/templates/session snapshot;
- отдельный OBS Rules viewer;
- создание/переименование шаблонов правил;
- scroll-safe numeric controls там, где это уже принято;
- S3 eyedropper с accept/cancel и освобождением temporary grabs;
- conditional UI visibility;
- minimum-window/scroll behavior для плотных Settings/Auction pages;
- persisted defaults Auction/wheel duration и другие принятые settings.

### 6.9 Музыка / soundtrack

- Music Player;
- shared managed media model;
- managed/external music entries;
- импорт с filename dedup;
- external -> managed promotion без потери media ID/queue position;
- shared soundtrack library;
- context-local external Auction/Wheel soundtrack selection;
- безопасное очищение пропавшего external soundtrack source;
- filesystem synchronization managed `data\music` / `data\soundtrack`;
- связанный audio lifecycle между Music Player и Auction soundtrack;
- OBS/browser-source audio path, где он уже реализован.

### 6.10 Системная стабильность и QA

- whole-program Windows accidental click-through input guard;
- bounded/rotating technical logs;
- performance trace opt-in;
- background heavy operations для применимых import/media paths;
- targeted SQLite indexes;
- WAL/named migrations;
- demand-driven UI timers и sleeping idle Browser Source animation loops;
- permanent regression foundation;
- Windows candidate/manual QA;
- immutable accepted release/publication workflow;
- candidate/FIX не считаются released CURRENT.

## 7. Как обновлять этот реестр

- Если на скриншоте обнаружена уже существующая функция, которой нет в разделе 6, сначала добавить её сюда как **EXISTING / PRESERVE**, а не создавать новую feature-задачу.
- Если выясняется, что функция из реестра больше не существует или была superseded, не удалять её молча: сначала сверить `IDEA_INVENTORY.md`/историю/код и записать причину изменения.
- Каждый принятый фикс после ручной проверки должен обновлять соответствующую запись задачи, а при изменении durable behavior — канонические project docs.
- Перед ответом пользователю в рамках этого этапа сначала читать этот ledger, затем при необходимости `PROJECT_STATE.md`, `ROADMAP.md`, `DECISIONS.md`, `IDEA_INVENTORY.md` и текущий код.
