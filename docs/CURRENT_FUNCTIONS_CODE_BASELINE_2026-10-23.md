# InOneLine Реестр доступных функций

Контрольный срез для дальнейшего сравнения

Этот документ фиксирует доступные по коду возможности InOneLine на 23 октября 2026 года. Он служит исходной точкой для сравнения с будущими изменениями: у каждой записи есть постоянный ID, описание поведения, вход в интерфейсе, условия и ссылка на реализацию.

Проверен текущий срез ветки main указанного ниже коммита. В реестре 265 записей по 18 разделам. Запись описывает пользовательскую возможность, существенный режим или технический интерфейс; это не подсчёт независимых экранов или Python-методов.

Метод проверки — чтение исходного кода и прослеживание связей от основного окна, виджетов и HTTP-обработчиков к вызываемым реализациям. Windows-сборка, OBS и внешние сервисы в ходе этой инвентаризации не запускались. Наличие реализации не является новой ручной приёмкой или гарантией доступности внешнего сервиса.

Названия существующих полей и статусов приведены по текущему интерфейсу, включая ПРОХОДИТСЯ, КООП и другие предметные обозначения. Реестр описывает зафиксированный коммит; установленная сборка с тем же номером версии может содержать другой набор изменений.

## Основание и версия

| Поле | Значение |
|---|---|
| Репозиторий | ALL-EX-E/InOneLine |
| Ветка | main |
| Коммит исходного кода | 5101439b2e0177a7e7b248955e7438084352d95b |
| Дата исходного коммита | 23 октября 2026 года 00:40:45 UTC+7 |
| Версия приложения | 1.0.8 |
| Версия схемы SQLite | 21 |
| Область инвентаризации | app.py и streaming_manager — 72 Python-файла и 9 HTML JS SVG; дополнительно проверены установщик и структура поставки |

[Зафиксированный исходный коммит](https://github.com/ALL-EX-E/InOneLine/commit/5101439b2e0177a7e7b248955e7438084352d95b)

Обозначения: **Доступно по коду** — достижимая реализация в текущем приложении. **При условиях** — реализация зависит от состояния сессии, подключения, настройки или доступности файла. Точные ограничения перечислены в самой записи. Оба обозначения относятся к статической проверке.

## Содержание

| Раздел | Записей | Диапазон ID |
|---|---:|---|
| Общее управление и сохранение состояния | 9 | CORE-001 … CORE-009 |
| Основной список и совместная таблица | 25 | LIST-001 … LIST-025 |
| Публичный список и экспорт | 10 | PUB-001 … PUB-010 |
| Музыкальный плеер | 14 | MUS-001 … MUS-014 |
| Проведение аукциона и управление лотами | 38 | AUC-001 … AUC-038 |
| Колесо и источники случайных чисел | 22 | WHL-001 … WHL-022 |
| Музыка аукциона и колеса | 9 | AUD-001 … AUD-009 |
| Правила аукциона и редактор шаблонов | 18 | RUL-001 … RUL-018 |
| История аукционов и проверка результата | 12 | HIST-001 … HIST-012 |
| Журнал изменений и событий | 6 | JRN-001 … JRN-006 |
| Виджеты OBS и их оформление | 34 | OBS-001 … OBS-034 |
| Изображение центра колеса | 6 | CENTER-001 … CENTER-006 |
| Резервное копирование и восстановление | 10 | BACKUP-001 … BACKUP-010 |
| Общее управление подключениями | 9 | INT-001 … INT-009 |
| Twitch и награды канала | 13 | INT-010 … INT-022 |
| DonationAlerts и пожертвования | 6 | INT-023 … INT-028 |
| Конвертация и ожидающие поступления | 15 | CONV-001 … CONV-015 |
| Локальный HTTP API и медиа | 9 | API-001 … API-009 |

## Порядок дальнейшего сравнения

- Сохранять ID существующей записи при изменении поведения. Новую возможность добавлять с новым ID, удалённую сохранять в сравнении с явной отметкой.

- Сравнивать не только наличие кнопки, но и её доступность по состояниям, сохранение параметров, форматы, пределы значений и влияние на историю.

- Для каждого сравнения фиксировать новый коммит и результат: без изменений, изменено, добавлено, удалено либо требует проверки. Подтверждение по коду и ручной PASS указывать отдельно.

- Использовать этот реестр как снимок реализованного поведения. Будущие идеи и решения по очередности ведутся в UNIFIED_FUTURE_WORK_AND_RULES.md; наличие идеи там не означает её реализацию здесь.

## Общее управление и сохранение состояния

### CORE-001 Восемь рабочих вкладок

**Состояние:** Доступно по коду.

Основное окно открывает Список, Публичный список, Музыку, Аукцион, Историю аукционов, Журнал, Стрим / OBS и Настройки в этом порядке.

**Доступ:** Основное окно

**Условия и границы:** Настройки содержат страницы Общие, Аукцион, Интеграции и Конвертация.

**Код:** [streaming_manager/views/main_window.py строки 261–285 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L261-L285); [streaming_manager/views/settings.py строки 294–733 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L294-L733).

### CORE-002 Компактное окно и прокрутка содержимого

**Состояние:** Доступно по коду.

Окно можно уменьшить до 520 × 360. При недостатке ширины подписи вкладок сокращаются, строки управления перестраиваются, содержимое страниц прокручивается; размер внешнего окна задаёт пользователь.

**Доступ:** Изменение размера основного окна

**Условия и границы:** Описаны правила компоновки в коде; удобство на конкретном экране требует визуальной проверки.

**Код:** [streaming_manager/views/main_window.py строки 125–134 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L125-L134); [streaming_manager/views/main_window.py строки 501–596 — MainWindow._update_responsive_layout](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L501-L596).

### CORE-003 Принудительное обновление по F5

**Состояние:** Доступно по коду.

F5 обновляет Список, Публичный список, Стрим / OBS, Музыку, Историю и Журнал, затем принудительно обновляет Аукцион. Подсказка расположена в верхней части окна.

**Доступ:** Клавиша F5

**Условия и границы:** Отдельные меню Файл и Вид не создаются; поля Настроек не перезаписываются этим обработчиком.

**Код:** [streaming_manager/views/main_window.py строки 812–821 — MainWindow._make_menu](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L812-L821); [streaming_manager/views/main_window.py строки 926–939 — MainWindow.refresh_all](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L926-L939).

### CORE-004 Сохранение окна и выбранной вкладки

**Состояние:** Доступно по коду.

При закрытии сохраняются геометрия окна, максимизация и ключ активной вкладки. При следующем запуске они восстанавливаются из data/ui_state.ini; старые индексы вкладок переводятся в ключи.

**Доступ:** Автоматически при запуске и закрытии

**Условия и границы:** При подготовке полной резервной копии состояние окна также сохраняется.

**Код:** [streaming_manager/views/main_window.py строки 651–699 — MainWindow._restore_ui_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L651-L699); [streaming_manager/views/main_window.py строки 701–712 — MainWindow._save_ui_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L701-L712).

### CORE-005 Перенос прежних настроек интерфейса

**Состояние:** При условиях.

Установленная Windows-сборка однократно переносит прежние QSettings в собственный INI, сохраняет legacy_ui_state_backup.ini и очищает старые значения после успешной записи.

**Доступ:** Автоматически при первом запуске подходящей Windows-сборки

**Условия и границы:** Исходный режим и другие платформы по умолчанию такой перенос не выполняют.

**Код:** [streaming_manager/ui_settings.py строки 130–180 — open_ui_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/ui_settings.py#L130-L180).

### CORE-006 Защита от второго экземпляра

**Состояние:** Доступно по коду.

Вторая копия программы с тем же каталогом данных сообщает, что In one line уже запущена, и завершает запуск.

**Доступ:** Запуск программы

**Условия и границы:** Блокировка относится к конкретной папке данных.

**Код:** [app.py строки 115–134 — main](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py#L115-L134); [streaming_manager/single_instance.py строки 10–19 — acquire_instance_lock](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/single_instance.py#L10-L19).

### CORE-007 Защита от случайного ввода сквозь другое окно

**Состояние:** При условиях.

На Windows фильтр блокирует мышь, колесо, контекстное меню и перетаскивание, если ввод принадлежит окну другого процесса.

**Доступ:** Автоматически при работе окна

**Условия и границы:** При недоступности Windows API дополнительная защита отключается, приложение продолжает запуск.

**Код:** [app.py строки 135–140 — main](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py#L135-L140); [streaming_manager/input_guard.py строки 119–137 — WindowsInputGuard.eventFilter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/input_guard.py#L119-L137).

### CORE-008 Локальное хранение и совместимость данных

**Состояние:** Доступно по коду.

Списки, настройки и история хранятся в SQLite data/streaming.db. При запуске применяются именованные миграции до версии схемы 21; управляемые файлы находятся в подпапках data, резервные копии и логи — рядом.

**Доступ:** Автоматически при работе программы

**Условия и границы:** Версия приложения в коде 1.0.8. Номер приложения и номер схемы — разные величины.

**Код:** [streaming_manager/app_paths.py строки 9–71 — AppPaths](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/app_paths.py#L9-L71); [streaming_manager/db/schema.py строки 300–338 — SchemaMixin._init_schema](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/schema.py#L300-L338); [streaming_manager/constants.py строки 3–7 — module](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L3-L7).

### CORE-009 Сообщение об ошибке запуска

**Состояние:** При условиях.

Необработанная ошибка запуска записывается в logs/startup_error.log; при доступном Qt отображается окно с ошибкой и путём журнала. Размер лога ограничен с ротацией.

**Доступ:** Автоматически при ошибке запуска

**Условия и границы:** Диагностический лог ограничен 1 МиБ и одной предыдущей копией; известные шаблоны секретов маскируются.

**Код:** [app.py строки 27–42 — write_startup_error](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py#L27-L42); [app.py строки 143–164 — main](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py#L143-L164); [streaming_manager/diagnostic_logs.py строки 36–82 — append_capped_log](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/diagnostic_logs.py#L36-L82).

## Основной список и совместная таблица

### LIST-001 Просмотр основного списка

**Состояние:** Доступно по коду.

Таблица показывает позицию, название, дату выхода, баллы, КООП/НЕ КООП, статус и отзыв. Внутренний ID скрыт. Список включает обычные записи; временные auction_only-лоты до завершения сессии сюда не входят. Редактирование выполняется отдельной формой, выбор — по одной строке.

**Доступ:** Главная вкладка «Список».

**Код:** [streaming_manager/views/main_window.py строки 167–168 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L167-L168); [streaming_manager/views/main_window.py строки 261–267 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L261-L267); [streaming_manager/views/games.py строки 610–627 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L610-L627); [streaming_manager/db/games.py строки 517–543 — GamesMixin._list_games_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L517-L543).

### LIST-002 Автоматическая сортировка и объяснение правил

**Состояние:** Доступно по коду.

Сначала неархивные записи, затем архив; внутри — ПРОХОДИТСЯ, объединённая группа ИГРАЛ/НЕ ИГРАЛ, ПРОЙДЕНО, ЗАБРОШЕНО. Для ПРОХОДИТСЯ дата новее → баллы больше; для остальных групп баллы больше → дата новее. Пустые даты идут после известных, затем последнее изменение новее и ID по возрастанию. Кнопка показывает эти правила; сортировка заголовками таблицы отключена.

**Доступ:** «Список» → «Правила сортировки»; порядок применяется автоматически.

**Код:** [streaming_manager/views/games.py строки 563–570 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L563-L570); [streaming_manager/views/games.py строки 968–995 — GamesTab.show_sorting_rules](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L968-L995); [streaming_manager/db/games.py строки 17–34 — GamesMixin.GAME_ORDER_SQL](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L17-L34).

### LIST-003 Показ актуальной аукционной позиции

**Состояние:** При условиях.

Колонка ПОЗИЦИЯ выводит текущую позицию из общей карты аукциона. Без открытой сессии ранжируются неархивные обычные игры ИГРАЛ/НЕ ИГРАЛ: баллы, дата, изменение, ID. С открытой сессией используются активные entries и их текущая сумма; строки без карты позиции показывают пустую ячейку.

**Доступ:** «Список» → колонка «ПОЗИЦИЯ».

**Условия и границы:** Позиция доступна только для записей, присутствующих в карте позиций; это не сквозной номер всех строк списка.

**Код:** [streaming_manager/views/games.py строки 1095–1107 — GamesTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1095-L1107); [streaming_manager/db/auction_session.py строки 1143–1202 — AuctionSessionMixin._auction_position_map_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1143-L1202).

### LIST-004 Поиск по названию и отзыву

**Состояние:** Доступно по коду.

Ввод фильтрует название или отзыв по подстроке с Unicode NFKC, свёрткой регистра и нормализацией пробелов. Пока запрос непустой, поиск охватывает все обычные записи, включая архив, независимо от выбранного статистического фильтра.

**Доступ:** «Список» → поле поиска; Ctrl+F переводит фокус в него.

**Код:** [streaming_manager/views/games.py строки 438–442 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L438-L442); [streaming_manager/views/games.py строки 1058–1073 — GamesTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1058-L1073); [streaming_manager/db/games.py строки 556–565 — GamesMixin._list_games_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L556-L565); [streaming_manager/db/common.py строки 80–90 — normalize_text_key / normalize_title_key](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L80-L90).

### LIST-005 Выбор первого результата и синхронизация поиска

**Состояние:** Доступно по коду.

Enter выделяет первую строку результата и прокручивает к ней; при непустом запросе без результатов выводится сообщение. Текст поиска и выбранный по Enter результат синхронизируются между «Списком» и «Публичным списком», а до запуска сессии — также с аукционом. Архивная игра в публичном списке не выбирается; при открытой сессии аукционный поиск остаётся отдельным.

**Доступ:** Поле поиска → Enter; синхронизация текста действует при вводе.

**Код:** [streaming_manager/views/games.py строки 885–891 — GamesTab._search_text_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L885-L891); [streaming_manager/views/games.py строки 938–966 — GamesTab.activate_search](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L938-L966); [streaming_manager/views/main_window.py строки 317–344 — MainWindow.sync_search_text](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L317-L344); [streaming_manager/views/main_window.py строки 356–383 — MainWindow.sync_search_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L356-L383).

### LIST-006 Статистика, сумма баллов и быстрые фильтры

**Состояние:** Доступно по коду.

Доступны 10 кликабельных показателей: Всего, Проходится, ДЛЯ АУКА (ИГРАЛ+НЕ ИГРАЛ), Играл, Не играл, Пройдено, Заброшено, Архив, Кооп, Не кооп. Всего и общая сумма баллов включают архив обычных записей; статусные и кооперативные счётчики относятся к неархивным. Временные auction_only-лоты в статистику не входят. Нажатие показателя выбирает соответствующий фильтр; активный поиск имеет приоритет над ним.

**Доступ:** «Список» → показатели над таблицей.

**Код:** [streaming_manager/views/games.py строки 498–557 — GamesTab.__init__.make_stat_button](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L498-L557); [streaming_manager/views/games.py строки 1038–1056 — GamesTab._update_stats](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1038-L1056); [streaming_manager/views/games.py строки 1200–1210 — GamesTab.apply_stat_filter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1200-L1210); [streaming_manager/db/games.py строки 486–510 — GamesMixin._game_stats_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L486-L510).

### LIST-007 Добавление записи

**Состояние:** Доступно по коду.

Форма создаёт обычную неархивную запись с обязательным названием, необязательной датой, целыми баллами 0–999999999, признаком КООП/НЕ КООП, одним из пяти статусов и необязательным многострочным отзывом. Новая форма по порядку combo начинает со статуса ПРОХОДИТСЯ, 0 баллов и НЕ КООП. При сохранении название и отзыв обрезаются по краям.

**Доступ:** «Список» → «Добавить» или Ctrl+N.

**Условия и границы:** Кнопка блокируется, пока выполняется CSV-импорт, одиночное удаление или очистка списка.

**Код:** [streaming_manager/views/games.py строки 87–135 — GameDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L87-L135); [streaming_manager/views/games.py строки 342–350 — GameDialog.payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L342-L350); [streaming_manager/views/games.py строки 1000–1012 — GamesTab._apply_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1000-L1012); [streaming_manager/views/games.py строки 1179–1198 — GamesTab.add_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1179-L1198).

### LIST-008 Редактирование записи

**Состояние:** Доступно по коду.

Открывает ту же форму с текущими названием, датой, баллами, кооперативом, статусом и отзывом; дополнительно показываются ID и время последнего изменения. Фактическое изменение обновляет запись и журнал; сохранение без изменений не сдвигает updated_at и порядок сортировки.

**Доступ:** «Список» → выбрать строку → «Изменить», двойной щелчок или Ctrl+E.

**Условия и границы:** Нужна выбранная запись; операция недоступна при массовом/удаляющем worker.

**Код:** [streaming_manager/views/games.py строки 138–159 — GameDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L138-L159); [streaming_manager/views/games.py строки 649–664 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L649-L664); [streaming_manager/views/games.py строки 1231–1260 — GamesTab.edit_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1231-L1260); [streaming_manager/db/games.py строки 163–190 — GamesMixin._update_game_conn / update_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L163-L190).

### LIST-009 Гибкий ввод и нормализация даты

**Состояние:** Доступно по коду.

Можно оставить дату пустой либо ввести ДД.ММ.ГГГГ, восемь цифр ДДММГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ, ДД ММ ГГГГ, ГГГГ-ММ-ДД, ГГГГ/ММ/ДД или русское название/сокращение месяца. При цифровом вводе автоматически ставятся точки, распознанная дата приводится к ДД.ММ.ГГГГ; несуществующая дата блокирует сохранение. В базе дата хранится ISO.

**Доступ:** Форма «Добавить»/«Изменить» → «Дата».

**Код:** [streaming_manager/views/games.py строки 167–225 — GameDialog._format_date_while_typing / _normalize_date_field](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L167-L225); [streaming_manager/views/games.py строки 251–267 — GameDialog._validate_and_accept](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L251-L267); [streaming_manager/db/common.py строки 102–177 — normalize_date_text / parse_date](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L102-L177).

### LIST-010 Защита от дубликатов и переход к существующей записи

**Состояние:** Доступно по коду.

Добавление и переименование сравнивают названия с Unicode NFKC, без учёта регистра и лишних пробелов, включая архив. При дубликате новой записи форма закрывается и выделяется существующая игра, при необходимости переключается фильтр архива и очищается поиск. При конфликтующем переименовании форма остаётся открытой для исправления.

**Доступ:** Автоматически при сохранении карточки.

**Код:** [streaming_manager/views/games.py строки 269–296 — GameDialog._validate_and_accept](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L269-L296); [streaming_manager/views/games.py строки 1179–1198 — GamesTab.add_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1179-L1198); [streaming_manager/views/games.py строки 1212–1229 — GamesTab.focus_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1212-L1229); [streaming_manager/db/games.py строки 68–86 — GamesMixin._find_game_by_title_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L68-L86); [streaming_manager/db/common.py строки 80–90 — normalize_title_key](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L80-L90).

### LIST-011 Подтверждение сохранения и защита несохранённой формы

**Состояние:** Доступно по коду.

Новая запись и фактические изменения требуют подтверждения сохранения. Неизменённая существующая форма закрывается без лишнего вопроса. Отмена или закрытие изменённой формы спрашивает, закрывать ли без сохранения; снимок учитывает видимые значения, включая ещё некорректную дату.

**Доступ:** Диалог «Добавить»/«Изменить» → «Сохранить», «Отмена», закрытие окна.

**Код:** [streaming_manager/views/games.py строки 227–249 — GameDialog._form_state / _ask_yes_no](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L227-L249); [streaming_manager/views/games.py строки 298–340 — GameDialog._validate_and_accept / reject / closeEvent](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L298-L340).

### LIST-012 Перемещение записи в архив

**Состояние:** При условиях.

После подтверждения меняет флаг архива без удаления данных. Архивная запись перестаёт входить в публичный список и обычную аукционную выборку. Архивирование блокируется, если игра участвует в незавершённом аукционе; интерфейс предлагает сначала завершить или отменить его.

**Доступ:** «Список» → выбрать неархивную запись → «В архив».

**Условия и границы:** Действие видно для выбранной неархивной игры; недоступно для участника открытой сессии и во время операции worker.

**Код:** [streaming_manager/views/games.py строки 1021–1028 — GamesTab._apply_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1021-L1028); [streaming_manager/views/games.py строки 1262–1291 — GamesTab.archive_selected](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1262-L1291); [streaming_manager/db/games.py строки 36–51 — GamesMixin._assert_game_not_in_open_auction_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L36-L51); [streaming_manager/db/games.py строки 581–587 — GamesMixin._public_games_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L581-L587).

### LIST-013 Восстановление из архива

**Состояние:** При условиях.

Возвращает выбранную архивную запись в обычный список, снимая флаг архива и обновляя связанные представления. Для восстановления отдельного подтверждения в обработчике нет.

**Доступ:** «Список» → фильтр «Архив» или «Всего» → архивная строка → «Восстановить из архива».

**Условия и границы:** Кнопка появляется для выбранной архивной записи; недоступна при worker.

**Код:** [streaming_manager/views/games.py строки 1021–1028 — GamesTab._apply_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1021-L1028); [streaming_manager/views/games.py строки 1262–1291 — GamesTab.archive_selected](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1262-L1291); [streaming_manager/db/games.py строки 192–193 — GamesMixin.archive_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L192-L193).

### LIST-014 Безвозвратное удаление одной записи с резервной копией

**Состояние:** При условиях.

После предупреждения создаёт резервную копию базы, оставляет до 30 копий и удаляет игру, contributions и связанные auction_entries. Предыдущий подробный game-журнал этой игры очищается, остаётся факт удаления с названием; ссылка на текущую игру OBS очищается. Сообщение об успехе показывает путь к копии. Это отличается от массовой очистки, сохраняющей entries истории.

**Доступ:** «Список» → выбрать запись → «Удалить».

**Условия и границы:** Нельзя удалить участника незавершённого аукциона; нужна успешная резервная копия и отсутствие другого import/delete/clear worker.

**Код:** [streaming_manager/views/games.py строки 1373–1448 — GamesTab.delete_selected](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1373-L1448); [streaming_manager/views/games.py строки 1470–1478 — GamesTab._delete_completed / _delete_failed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1470-L1478); [streaming_manager/db/games.py строки 195–246 — GamesMixin.delete_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L195-L246).

### LIST-015 Массовая очистка списка с сохранением закрытой истории

**Состояние:** При условиях.

Удаляет все обычные, архивные и временные игры и живые contributions, очищает текущую игру OBS; закрытые auction_entries сохраняются за счёт снимков и отвязки game_id, общий change_log сохраняется. Требует точно ввести «УДАЛИТЬ ЗАПИСИ». Перед удалением обязательна резервная копия, хранение до 30 копий; ошибки копии/очистки старых копий останавливают удаление. Итог показывает число удалённых игр, сохранённых entries и путь копии.

**Доступ:** «Список» → «Очистить список».

**Условия и границы:** Список должен быть непустым; открытая локальная сессия аукциона и другой worker блокируют действие.

**Код:** [streaming_manager/views/games.py строки 352–404 — DeleteAllGamesDialog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L352-L404); [streaming_manager/views/games.py строки 1293–1366 — GamesTab.clear_all_games / _clear_all_completed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1293-L1366); [streaming_manager/db/services.py строки 2588–2623 — ServicesMixin.clear_all_games_with_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2588-L2623); [streaming_manager/db/games.py строки 367–471 — GamesMixin.clear_all_games](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L367-L471).

### LIST-016 Импорт CSV с заголовками

**Состояние:** Доступно по коду.

Принимает UTF-8/UTF-8-BOM CSV с определением разделителя ; , или табуляции (fallback ;). Обязателен НАЗВАНИЕ или НАЗВАНИЕ ИГРЫ. Необязательны ДАТА/ДАТА ВЫХОДА, БАЛЛЫ/БАЛЛЫ SM/СУММА, КООП/НЕ КООП, СТАТУС, ОТЗЫВ; порядок свободный, неизвестные столбцы игнорируются. Пустые названия строк пропускаются. Правила и примеры доступны кнопкой «?».

**Доступ:** «Список» → «Импорт CSV»; «?» → «Правила импорта CSV».

**Условия и границы:** Диалог предлагает *.csv и все файлы; это CSV-парсер, а не универсальный импорт Excel/JSON.

**Код:** [streaming_manager/views/games.py строки 1485–1527 — GamesTab.show_import_csv_help](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1485-L1527); [streaming_manager/views/games.py строки 1529–1552 — GamesTab.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1529-L1552); [streaming_manager/db/services.py строки 2764–2782 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2764-L2782); [streaming_manager/db/services.py строки 2829–2879 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2829-L2879).

### LIST-017 Слияние CSV с существующими записями

**Состояние:** Доступно по коду.

UI всегда вызывает merge=True: совпавшие по нормализованному названию игры обновляются только переданными непустыми значениями, поэтому пустая ячейка не стирает сохранённое поле. Новые получают: дата пустая, 0 баллов, НЕ КООП, НЕ ИГРАЛ, отзыв пустой, архив выключен. Совпадение ищется и среди архивных/других game-строк базы; отдельного режима замены списка или merge=False в UI нет.

**Доступ:** Автоматически при «Импорт CSV».

**Код:** [streaming_manager/views/games.py строки 1543–1553 — GamesTab.import_csv.perform_import](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1543-L1553); [streaming_manager/db/services.py строки 2703–2762 — ServicesMixin.import_csv.parse_optional_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2703-L2762); [streaming_manager/db/services.py строки 2881–2917 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2881-L2917); [streaming_manager/db/games.py строки 68–86 — GamesMixin._find_game_by_title_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L68-L86).

### LIST-018 Импорт старого формата Название|Баллы

**Состояние:** Доступно по коду.

Поддерживает файл без заголовков, по одной записи Название|Баллы в строке; разбиение идёт по последнему символу |. Баллы обязательны, для отсутствующих нужно 0. Пустые строки и пустое название пропускаются; отсутствие | или баллов выдаёт ошибку с номером строки. Для выбора legacy-ветки проверяется первый непустой текст с | без «НАЗВАНИЕ ИГРЫ».

**Доступ:** «Список» → «Импорт CSV» → файл старого формата.

**Код:** [streaming_manager/views/games.py строки 1514–1524 — GamesTab.show_import_csv_help](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1514-L1524); [streaming_manager/db/services.py строки 2784–2828 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2784-L2828).

### LIST-019 Проверка CSV, резервная копия и отчёт об импорте

**Состояние:** Доступно по коду.

До записи валидируется весь файл: дубликаты нормализованных названий, статус, кооператив, дата и число баллов дают сообщения с контекстом строки/игры. Записи и журнал применяются одной транзакцией. До импорта обязательна резервная копия и обрезка хранения до 30 копий; при ошибке копии, обрезки или импорта показывается ошибка и путь доступной копии. Итог: добавлено, изменено, без изменений/пропущено. Числовой парсер фактически принимает неотрицательные дроби и округляет вверх, несмотря на текст справки «целое число».

**Доступ:** Автоматически при «Импорт CSV».

**Условия и границы:** Статусы и кооператив распознаются также по совместимым алиасам из constants.py; отрицательные и некорректные числа не принимаются.

**Код:** [streaming_manager/db/services.py строки 2625–2670 — ServicesMixin.import_csv_with_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2625-L2670); [streaming_manager/db/services.py строки 2691–2762 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2691-L2762); [streaming_manager/db/services.py строки 2881–2917 — ServicesMixin.import_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2881-L2917); [streaming_manager/views/games.py строки 1580–1590 — GamesTab._import_completed / _import_failed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1580-L1590); [streaming_manager/conversion.py строки 155–172 — convert_source_to_sm_points / parse_sm_points](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/conversion.py#L155-L172); [streaming_manager/constants.py строки 239–267 — STATUS_FROM_LABEL / COOP_FROM_LABEL](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L239-L267).

### LIST-020 Клавиатурные команды списка и обновление данных

**Состояние:** Доступно по коду.

Ctrl+N открывает добавление, Ctrl+E — изменение выбранной записи, Ctrl+F — поиск, F5 — обновление. Главное окно также предоставляет глобальное «Обновить»/F5 с обновлением Списка, Публичного списка, Музыки, OBS, Истории, Журнала и аукциона.

**Доступ:** «Список» → клавиатура; F5 также доступна как глобальная команда основного окна.

**Код:** [streaming_manager/views/games.py строки 655–664 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L655-L664); [streaming_manager/views/main_window.py строки 813–818 — MainWindow._make_menu](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L813-L818); [streaming_manager/views/main_window.py строки 926–939 — MainWindow.refresh_all](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L926-L939).

### LIST-021 Создание совместной таблицы основного списка

**Состояние:** При условиях.

Создаёт обычный XLSX из полного постоянного списка, включая архив, и подключает его к синхронизации. Лист spisok: ПОЗИЦИЯ, НАЗВАНИЕ ИГРЫ, ДАТА ВЫХОДА, БАЛЛЫ, КООП/НЕ КООП, СТАТУС, ОТЗЫВ, АРХИВ. Есть фильтр, закреплённая первая строка и списки допустимых кооператива, статуса и архива. Перед заменой существующего файла задаётся вопрос.

**Доступ:** «Список» → «Совместная таблица» → «Создать таблицу».

**Условия и границы:** Нужен доступный для записи локальный путь *.xlsx; временные auction_only-лоты не выгружаются.

**Код:** [streaming_manager/views/main_window.py строки 224–228 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L224-L228); [streaming_manager/views/games.py строки 783–833 — GamesTab.attach_shared_xlsx_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L783-L833); [streaming_manager/views/auction.py строки 1263–1288 — AuctionTab._shared_xlsx_create](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1263-L1288); [streaming_manager/shared_xlsx.py строки 20–31 — SHARED_XLSX_HEADERS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L20-L31); [streaming_manager/shared_xlsx.py строки 102–121 — main_games_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L102-L121); [streaming_manager/shared_xlsx.py строки 203–264 — write_shared_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L203-L264).

### LIST-022 Подключение и проверка существующего совместного XLSX

**Состояние:** При условиях.

Выбранная таблица сразу читается как источник. Предпочтителен лист spisok, иначе активный; строка заголовков ищется в первых 20 строках по НАЗВАНИЕ ИГРЫ. Обязательны все 7 предметных столбцов, ПОЗИЦИЯ необязательна; дубликаты, строки с данными без названия и некорректные значения отклоняются до изменения базы. Полностью пустые предметные строки пропускаются. Путь/включение сохраняются и восстанавливаются при запуске.

**Доступ:** «Список» → «Совместная таблица» → «Подключить таблицу».

**Условия и границы:** Нужен читаемый XLSX установленной схемы; поддерживаются даты Excel date/datetime и текстовые даты; формулы не вычисляются этим reader.

**Код:** [streaming_manager/views/auction.py строки 1204–1233 — AuctionTab._init_shared_xlsx_sync](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1204-L1233); [streaming_manager/views/auction.py строки 1290–1337 — AuctionTab._shared_xlsx_connect / _shared_xlsx_activate](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1290-L1337); [streaming_manager/shared_xlsx.py строки 46–99 — _parse_archive / _parse_coop / _parse_status / _parse_release_date](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L46-L99); [streaming_manager/shared_xlsx.py строки 297–410 — read_shared_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L297-L410).

### LIST-023 Двусторонняя синхронизация полного состояния основного списка

**Состояние:** При условиях.

Локальные изменения планируют полную выгрузку через 350 мс. Внешний файл опрашивается раз в 1000 мс, перед чтением его mtime/размер должны стабилизироваться; последняя полученная валидная версия применяется целиком с backup. Совпадение — по нормализованному названию: новые добавляются, существующие обновляются, отсутствующие постоянные строки удаляются атомарно. Временные auction_only-лоты исключены. ПОЗИЦИЯ вычисляется программой, не импортируется и при несовпадении переписывается. Перестановка физических строк не меняет logical state. Архивирование/удаление участников открытой сессии блокирует весь apply.

**Доступ:** После создания/подключения «Совместной таблицы» — автоматически в обе стороны.

**Условия и границы:** Это обмен локальным XLSX; для нескольких компьютеров требуется внешняя доставка файла, например Google Drive Desktop. Переименование строки меняет ключ сопоставления и может привести к удалению/добавлению записи.

**Код:** [streaming_manager/views/games.py строки 802–807 — GamesTab.attach_shared_xlsx_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L802-L807); [streaming_manager/views/auction.py строки 1357–1376 — AuctionTab.shared_xlsx_local_data_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1357-L1376); [streaming_manager/views/auction.py строки 1470–1544 — AuctionTab._shared_xlsx_poll / _shared_xlsx_start_import](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1470-L1544); [streaming_manager/shared_xlsx.py строки 124–200 — state_hash / presentation_hash / position_projection_matches](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L124-L200); [streaming_manager/db/games.py строки 248–360 — GamesMixin.sync_main_games_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L248-L360); [streaming_manager/constants.py строки 13–16 — SHARED_XLSX_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L13-L16).

### LIST-024 Состояние и отключение совместной синхронизации

**Состояние:** При условиях.

Показываются путь, состояние и последнее изменение. Отсутствующий файл ожидается; временная недоступность/неготовый XLSX повторно проверяются, ошибка валидации показывается и та же ошибочная сигнатура не читается повторно до изменения файла. Ошибка записи повторяется с задержкой 1500 мс. «Отключить» останавливает таймеры и очищает сохранённое подключение, сохраняя текущую базу и файл.

**Доступ:** «Список» → «Совместная таблица» → индикаторы и «Отключить».

**Условия и границы:** Отключение доступно при активном подключении и отсутствии worker.

**Код:** [streaming_manager/views/games.py строки 819–825 — GamesTab.attach_shared_xlsx_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L819-L825); [streaming_manager/views/auction.py строки 1236–1261 — AuctionTab._shared_xlsx_signature / _shared_xlsx_update_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1236-L1261); [streaming_manager/views/auction.py строки 1339–1355 — AuctionTab._shared_xlsx_disconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1339-L1355); [streaming_manager/views/auction.py строки 1470–1492 — AuctionTab._shared_xlsx_poll](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1470-L1492); [streaming_manager/views/auction.py строки 1576–1593 — AuctionTab._shared_xlsx_worker_failed / _shared_xlsx_worker_finished](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1576-L1593).

### LIST-025 Быстрый доступ к OBS-списку

**Состояние:** Доступно по коду.

«Копировать URL списка» кладёт в буфер адрес /list-overlay; «Открыть предпросмотр списка» открывает /list-overlay?preview=1 через системный браузер. Это те же действия Stream/OBS, подключённые в главном окне.

**Доступ:** «Список» → «Копировать URL списка» / «Открыть предпросмотр списка».

**Код:** [streaming_manager/views/games.py строки 572–585 — GamesTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L572-L585); [streaming_manager/views/main_window.py строки 210–217 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L210-L217); [streaming_manager/views/stream.py строки 1560–1564 — StreamTab.copy_list_overlay_url / open_list_overlay_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1560-L1564).

## Публичный список и экспорт

### PUB-001 Публичное представление основной базы

**Состояние:** Доступно по коду.

Таблица только для чтения: ПОЗИЦИЯ, НАЗВАНИЕ, БАЛЛЫ, ОТЗЫВ, СТАТУС; показывает число строк. Формируется напрямую из основной базы без отдельной редактируемой копии, исключает архив и auction_only-лоты, использует общий порядок сортировки и карту позиций.

**Доступ:** Главная вкладка «Публичный список».

**Код:** [streaming_manager/views/main_window.py строки 261–266 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L261-L266); [streaming_manager/views/public.py строки 54–58 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L54-L58); [streaming_manager/views/public.py строки 152–168 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L152-L168); [streaming_manager/views/public.py строки 471–511 — PublicTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L471-L511); [streaming_manager/db/games.py строки 581–607 — GamesMixin._public_games_conn / public_games](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L581-L607).

### PUB-002 Поиск и выбор публичных записей

**Состояние:** Доступно по коду.

Поиск по подстроке названия/отзыва использует ту же Unicode-нормализацию, регистр и пробелы, что основной список; Enter выбирает первый результат или сообщает об отсутствии. Текст и выбранный результат передаются Списку и аукциону до открытой сессии; архив в эту выборку не попадает.

**Доступ:** «Публичный список» → поле поиска → Enter.

**Код:** [streaming_manager/views/public.py строки 64–69 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L64-L69); [streaming_manager/views/public.py строки 405–411 — PublicTab._search_text_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L405-L411); [streaming_manager/views/public.py строки 445–485 — PublicTab.activate_search / refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L445-L485); [streaming_manager/views/main_window.py строки 317–344 — MainWindow.sync_search_text](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L317-L344); [streaming_manager/views/main_window.py строки 356–383 — MainWindow.sync_search_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L356-L383).

### PUB-003 Разовый экспорт публичного CSV

**Состояние:** Доступно по коду.

Сохраняет полный текущий публичный список в .csv, UTF-8 с BOM, разделитель ;, заголовки НАЗВАНИЕ ИГРЫ;БАЛЛЫ;ОТЗЫВ;СТАТУС. Поисковый фильтр вкладки не передаётся экспортёру. Позиции в этом формате нет, автоматического обновления файла нет; расширение добавляется/заменяется автоматически, результат или ошибка показываются сообщением.

**Доступ:** «Публичный список» → «Экспорт списка» → «Экспорт CSV».

**Код:** [streaming_manager/views/public.py строки 87–105 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L87-L105); [streaming_manager/views/public.py строки 554–570 — PublicTab._save / export_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L554-L570); [streaming_manager/exporters.py строки 13–23 — PUBLIC_HEADERS / export_public_csv](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py#L13-L23).

### PUB-004 Разовый экспорт публичного JSON

**Состояние:** Доступно по коду.

Сохраняет UTF-8 .json с version:1, columns из четырёх публичных заголовков и games из полной db.public_games(): id, title, sm_points, совместимое поле sum, review, русский status. Позиция не включается; текущий поиск не ограничивает файл, он сам не обновляется.

**Доступ:** «Публичный список» → «Экспорт JSON».

**Код:** [streaming_manager/views/public.py строки 554–573 — PublicTab._save / export_json](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L554-L573); [streaming_manager/exporters.py строки 26–34 — export_public_json](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py#L26-L34); [streaming_manager/db/games.py строки 590–607 — GamesMixin._public_games_conn / public_games](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L590-L607).

### PUB-005 Разовый экспорт публичного Excel

**Состояние:** Доступно по коду.

Создаёт .xlsx, лист spisok с четырьмя колонками НАЗВАНИЕ ИГРЫ, БАЛЛЫ, ОТЗЫВ, СТАТУС; баллы числовые, заголовки выделены, текст переносится. Позиции нет; экспортируется полный публичный список независимо от поиска, файл остаётся снимком без автообновления.

**Доступ:** «Публичный список» → «Экспорт Excel».

**Код:** [streaming_manager/views/public.py строки 554–576 — PublicTab._save / export_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L554-L576); [streaming_manager/exporters.py строки 37–57 — export_public_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py#L37-L57).

### PUB-006 Создание односторонней публичной таблицы XLSX

**Состояние:** При условиях.

Создаёт и подключает отдельное зеркало .xlsx (по умолчанию «Публичный список.xlsx»). Лист spisok содержит ПОЗИЦИЯ, НАЗВАНИЕ ИГРЫ, БАЛЛЫ, ОТЗЫВ, СТАТУС; первая строка закреплена, есть автофильтр. Перед заменой существующего файла запрашивается подтверждение; запись идёт атомарной заменой.

**Доступ:** «Публичный список» → «Публичная таблица» → «Создать таблицу».

**Условия и границы:** Нужен путь с правами записи.

**Код:** [streaming_manager/views/public.py строки 114–137 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L114-L137); [streaming_manager/views/public.py строки 238–262 — PublicTab._public_xlsx_create](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L238-L262); [streaming_manager/public_xlsx.py строки 15–22 — PUBLIC_XLSX_HEADERS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L15-L22); [streaming_manager/public_xlsx.py строки 78–146 — write_public_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L78-L146).

### PUB-007 Подключение XLSX как получателя публичного зеркала

**Состояние:** При условиях.

Выбранный существующий .xlsx становится назначением: его содержимое намеренно игнорируется и заменяется текущим публичным списком. In one line остаётся источником, внешние правки и Google Таблицы обратно не импортируются. Путь/включение сохраняются; при следующем запуске сохранённое подключение активируется с принудительной записью.

**Доступ:** «Публичный список» → «Публичная таблица» → «Подключить таблицу».

**Условия и границы:** Выбирается XLSX-получатель; это не импорт и не совместная двусторонняя таблица.

**Код:** [streaming_manager/views/public.py строки 118–122 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L118-L122); [streaming_manager/views/public.py строки 186–211 — PublicTab._init_public_xlsx_mirror](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L186-L211); [streaming_manager/views/public.py строки 264–294 — PublicTab._public_xlsx_connect / _public_xlsx_activate](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L264-L294).

### PUB-008 Автообновление публичного зеркала

**Состояние:** При условиях.

После изменения данных главного окна планирует выгрузку через 350 мс, используя полный публичный список и актуальные позиции. Хеш включает порядок и публичные поля; если они не изменились и файл существует, повторная запись пропускается. Фоновая работа не читает внешнее содержимое XLSX.

**Доступ:** Автоматически после подключения «Публичной таблицы».

**Условия и границы:** Подключение активно; обработчик изменения данных вызывается путями MainWindow.refresh_game_data_views / notify_game_data_changed.

**Код:** [streaming_manager/views/main_window.py строки 901–923 — MainWindow.refresh_game_data_views / notify_game_data_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L901-L923); [streaming_manager/views/public.py строки 311–317 — PublicTab.public_xlsx_local_data_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L311-L317); [streaming_manager/views/public.py строки 348–378 — PublicTab._public_xlsx_start_write](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L348-L378); [streaming_manager/public_xlsx.py строки 33–75 — public_mirror_rows / public_state_hash](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L33-L75); [streaming_manager/constants.py строки 18–21 — PUBLIC_XLSX_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L18-L21).

### PUB-009 Состояние, восстановление отсутствующего файла и повтор записи

**Состояние:** При условиях.

Показывает путь, состояние и время последнего обновления. Раз в 1000 мс проверяет только существование целевого файла; удалённый файл пересоздаётся. Временные ошибки доступа/занятость показываются в состоянии и запись повторяется через 1500 мс; прочие ошибки отображаются как ошибка синхронизации.

**Доступ:** «Публичный список» → «Публичная таблица» → индикаторы.

**Условия и границы:** Нужно активное подключение. Внешние правки существующего файла таймер не импортирует и не отслеживает как содержимое.

**Код:** [streaming_manager/views/public.py строки 140–150 — PublicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L140-L150); [streaming_manager/views/public.py строки 199–203 — PublicTab._init_public_xlsx_mirror](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L199-L203); [streaming_manager/views/public.py строки 319–332 — PublicTab._public_xlsx_check_target_exists](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L319-L332); [streaming_manager/views/public.py строки 380–398 — PublicTab._public_xlsx_write_succeeded / _public_xlsx_worker_failed / _public_xlsx_worker_finished](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L380-L398); [streaming_manager/public_xlsx.py строки 142–160 — write_public_xlsx](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L142-L160).

### PUB-010 Отключение публичного зеркала

**Состояние:** При условиях.

Останавливает таймеры записи и проверки отсутствия, очищает путь/включение в настройках, сбрасывает индикаторы. Основная база и уже созданный XLSX при отключении не удаляются.

**Доступ:** «Публичный список» → «Публичная таблица» → «Отключить».

**Условия и границы:** Кнопка видна при подключённой таблице, недоступна во время worker.

**Код:** [streaming_manager/views/public.py строки 220–231 — PublicTab._public_xlsx_update_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L220-L231); [streaming_manager/views/public.py строки 296–309 — PublicTab._public_xlsx_disconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L296-L309).

## Музыкальный плеер

### MUS-001 Пакетное добавление аудиофайлов

**Состояние:** Доступно по коду.

За один выбор добавляет один или несколько файлов MP3, WAV или OGG. Проверяет наличие и расширение, продолжает обработку пригодных файлов и выводит сводку пропущенных и ошибочных.

**Доступ:** Музыка → Добавить музыку

**Условия и границы:** Сетевые потоки и URL в этом диалоге не поддерживаются; фактическое декодирование зависит от мультимедийной системы.

**Код:** [streaming_manager/views/music.py строки 425–593 — MusicTab._import_music](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L425-L593).

### MUS-002 Копия музыки или ссылка на оригинал

**Состояние:** Доступно по коду.

При добавлении предлагает скопировать музыку в data/music либо сохранить путь к исходному файлу. Внешний оригинал не копируется и остаётся нужен для воспроизведения.

**Доступ:** Диалог добавления музыки

**Условия и границы:** Режим выбирается на всю выбранную группу.

**Код:** [streaming_manager/views/music.py строки 368–397 — MusicTab._choose_storage_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L368-L397); [streaming_manager/views/music.py строки 425–593 — MusicTab._import_music](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L425-L593).

### MUS-003 Обработка одинаковых имён музыки

**Состояние:** Доступно по коду.

Для существующей внутренней копии предлагает использовать её, заменить, сохранить отдельную копию с номером или отменить. Повторное добавление внешней ссылки по совпадающему имени выбирает имеющуюся запись; внешнюю запись можно перевести во внутреннюю копию.

**Доступ:** При добавлении совпадающего файла

**Условия и границы:** Сопоставление здесь по имени файла, а не по аудиосодержимому.

**Код:** [streaming_manager/views/music.py строки 399–423 — MusicTab._duplicate_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L399-L423); [streaming_manager/views/music.py строки 425–593 — MusicTab._import_music](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L425-L593); [streaming_manager/db/media.py строки 79–142 — MediaMixin.promote_external_media_asset_to_managed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/media.py#L79-L142).

### MUS-004 Библиотека и поиск по отображаемому названию

**Состояние:** Доступно по коду.

Показывает текущую очередь, выделяет текущий трек жирным и фильтрует строки по подстроке без учёта регистра. Очистка поиска возвращает строки; двойной щелчок запускает выбранный трек с начала.

**Доступ:** Музыка → Библиотека / Очередность

**Условия и границы:** Поиск скрывает строки только в представлении и не меняет очередь воспроизведения.

**Код:** [streaming_manager/views/music.py строки 209–227 — MusicTab.refresh_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L209-L227); [streaming_manager/views/music.py строки 306–310 — MusicTab._apply_filter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L306-L310); [streaming_manager/views/music.py строки 312–315 — MusicTab._activate_item](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L312-L315).

### MUS-005 Воспроизведение пауза и остановка

**Состояние:** Доступно по коду.

Play запускает выбранный трек, Пауза удерживает позицию, Стоп останавливает и выгружает источник. Следующий Play после Стоп начинает трек сначала.

**Доступ:** Музыка → кнопки транспорта

**Условия и границы:** Если текущий трек ещё не выбран, Play использует первый в очереди.

**Код:** [streaming_manager/music_player.py строки 398–429 — MusicPlayerController.play_pause](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L398-L429); [streaming_manager/music_player.py строки 431–443 — MusicPlayerController.stop](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L431-L443).

### MUS-006 Переход между треками

**Состояние:** Доступно по коду.

Предыдущий и Следующий переходят по кругу и сохраняют состояние Play, Пауза или Стоп. После конца трека автоматически выбирается следующий; при новом круге перемешанной очереди избегается немедленный повтор последнего трека, если есть альтернатива.

**Доступ:** Музыка → Предыдущий / Следующий и конец трека

**Условия и границы:** Кнопка Предыдущий выбирает предыдущую запись, а не специальное действие возврата к началу текущей.

**Код:** [streaming_manager/music_player.py строки 462–477 — MusicPlayerController.next_track](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L462-L477); [streaming_manager/music_player.py строки 479–485 — MusicPlayerController.previous_track](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L479-L485); [streaming_manager/music_player.py строки 487–513 — MusicPlayerController._change_track_preserving_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L487-L513); [streaming_manager/music_player.py строки 717–738 — MusicPlayerController._on_media_status](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L717-L738).

### MUS-007 Перемотка и время трека

**Состояние:** Доступно по коду.

Отображает прошедшее и полное время; ползунок меняет позицию в пределах длительности. Обновления текущего времени не мешают перетаскиванию ползунка.

**Доступ:** Музыка → ползунок позиции

**Условия и границы:** Длительность и точность перемотки зависят от загруженного аудио.

**Код:** [streaming_manager/views/music.py строки 255–263 — MusicTab._position_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L255-L263); [streaming_manager/views/music.py строки 268–270 — MusicTab._seek_released](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L268-L270); [streaming_manager/music_player.py строки 445–454 — MusicPlayerController.seek](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L445-L454).

### MUS-008 Алфавитный или перемешанный порядок

**Состояние:** Доступно по коду.

Предлагает два режима: По алфавиту и Перемешать. Алфавит использует имя файла из библиотеки; перемешанный порядок сохраняется, новые файлы добавляются в оставшуюся очередь.

**Доступ:** Музыка → Режим

**Условия и границы:** Ручное перетаскивание и произвольный порядок в интерфейсе не предусмотрены.

**Код:** [streaming_manager/music_player.py строки 223–266 — MusicPlayerController.refresh_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L223-L266); [streaming_manager/music_player.py строки 515–540 — MusicPlayerController.set_order_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L515-L540); [streaming_manager/views/music.py строки 87–99 — MusicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L87-L99).

### MUS-009 Повтор текущего трека

**Состояние:** Доступно по коду.

Флаг Повторять текущий трек запускает тот же файл с нуля при его завершении вместо перехода дальше.

**Доступ:** Музыка → Повторять текущий трек

**Условия и границы:** Не создаёт отдельный пользовательский плейлист.

**Код:** [streaming_manager/music_player.py строки 542–546 — MusicPlayerController.set_repeat_current](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L542-L546); [streaming_manager/music_player.py строки 717–738 — MusicPlayerController._on_media_status](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L717-L738).

### MUS-010 Громкость и отключение звука

**Состояние:** Доступно по коду.

Громкость регулируется от 0 до 100 процентов; Без звука сохраняет отдельный признак отключения. Значения сохраняются и передаются в состояние браузерного виджета.

**Доступ:** Музыка → Громкость / Без звука

**Условия и границы:** При внешнем владении звуком аукционом локальный вывод плеера также подавляется.

**Код:** [streaming_manager/music_player.py строки 558–564 — MusicPlayerController.set_volume_percent](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L558-L564); [streaming_manager/music_player.py строки 566–572 — MusicPlayerController.set_muted](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L566-L572); [streaming_manager/music_player.py строки 574–581 — MusicPlayerController._apply_local_audio_route](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L574-L581).

### MUS-011 Вывод музыки через приложение или OBS

**Состояние:** При условиях.

В режиме В приложении играет локальный аудиовыход; в режиме Через OBS Browser Source локальный выход заглушён, а аудио получает виджет музыкального плеера. Кнопки копируют его URL и открывают предпросмотр.

**Доступ:** Музыка → Вывод звука / Копировать URL плеера / Открыть предпросмотр

**Условия и границы:** Для режима OBS нужен добавленный браузерный источник. Справка поясняет Windows-микшер, Управление аудио через OBS и мониторинг.

**Код:** [streaming_manager/views/music.py строки 102–145 — MusicTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L102-L145); [streaming_manager/views/music.py строки 286–304 — MusicTab._show_obs_audio_help](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L286-L304); [streaming_manager/music_player.py строки 548–556 — MusicPlayerController.set_output_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L548-L556); [streaming_manager/music_player.py строки 787–834 — MusicPlayerController._refresh_browser_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L787-L834).

### MUS-012 Название исполнителя и встроенная обложка

**Состояние:** Доступно по коду.

Читает теги title и artist и встроенную обложку. Когда заполнены оба тега, отображает Исполнитель - Название; иначе использует имя файла. Виджет получает обложку или стандартную заглушку.

**Доступ:** Автоматически для библиотеки и виджета плеера

**Условия и границы:** Редактора тегов и загрузки обложек из сети в этом плеере нет.

**Код:** [streaming_manager/music_player.py строки 620–661 — MusicPlayerController.metadata_for_asset](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L620-L661); [streaming_manager/music_player.py строки 663–706 — MusicPlayerController._extract_cover](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L663-L706); [streaming_manager/music_player.py строки 787–834 — MusicPlayerController._refresh_browser_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L787-L834).

### MUS-013 Восстановление трека и позиции без автозапуска

**Состояние:** Доступно по коду.

Сохраняет текущий трек, позицию, очередь, порядок, повтор, маршрут, громкость и mute. При следующем запуске подготавливает сохранённый доступный трек и позицию на паузе.

**Доступ:** Автоматически при работе и закрытии

**Условия и границы:** Позиция периодически сохраняется примерно раз в 1,5 секунды; после запуска музыка сама не включается.

**Код:** [streaming_manager/music_player.py строки 118–139 — MusicPlayerController.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L118-L139); [streaming_manager/music_player.py строки 279–308 — MusicPlayerController._restore_saved_current](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L279-L308); [streaming_manager/music_player.py строки 764–785 — MusicPlayerController._persist_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L764-L785); [streaming_manager/music_player.py строки 840–850 — MusicPlayerController.shutdown](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L840-L850).

### MUS-014 Обновление библиотеки по файлам на диске

**Состояние:** Доступно по коду.

Поддерживаемые файлы, вручную помещённые в data/music, появляются после обновления. Пропавшие внутренние записи удаляются из каталога; недоступные оригиналы исключаются из очереди. При исчезновении текущего трека выбирается первый оставшийся на паузе.

**Доступ:** Музыка → обновление библиотеки или F5

**Условия и границы:** Кнопки удаления музыки и исправления пути внешнего файла на этой вкладке не создаются.

**Код:** [streaming_manager/db/media.py строки 519–605 — MediaMixin.sync_managed_media_category](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/media.py#L519-L605); [streaming_manager/music_player.py строки 216–221 — MusicPlayerController._available_assets](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L216-L221); [streaming_manager/music_player.py строки 223–266 — MusicPlayerController.refresh_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L223-L266).

## Проведение аукциона и управление лотами

### AUC-001 Выбор режима на вкладке «Аукцион»

**Состояние:** Доступно по коду.

Одна основная вкладка объединяет проведение, общий таймер, таблицу лотов, локальное колесо и контекстные действия. Перед новой сессией можно выбрать «Максимальная сумма» или «Взвешенное колесо»; после создания сессии выбор режима и генератора отключается.

**Доступ:** Главное окно → Аукцион → «Способ определения победителя».

**Условия и границы:** Режим редактируется только без открытой сессии и без фоновой подготовки RANDOM.ORG.

**Код:** [streaming_manager/views/main_window.py строки 184–200 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L184-L200); [streaming_manager/views/main_window.py строки 269–277 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L269-L277); [streaming_manager/views/auction.py строки 386–403 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L386-L403); [streaming_manager/views/auction_parts/state.py строки 229–255 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L229-L255).

### AUC-002 Предстартовый состав лотов

**Состояние:** Доступно по коду.

В таблицу до запуска попадают обычные неархивные игры со статусами ИГРАЛ и НЕ ИГРАЛ. ПРОХОДИТСЯ, ПРОЙДЕНО, ЗАБРОШЕНО и временные auction_only-записи не входят в начальный состав. Начальный порядок соответствует общему списку: баллы по убыванию, затем дата выпуска, время обновления и ID.

**Доступ:** Аукцион → Список лотов до старта.

**Условия и границы:** Применяется к начальному составу; явное добавление по названию в работающий аукцион имеет отдельный путь переиспользования существующей игры.

**Код:** [streaming_manager/views/auction.py строки 2215–2237 — AuctionTab._entries_for_table](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2215-L2237); [streaming_manager/db/games.py строки 17–34 — GamesMixin.GAME_ORDER_SQL](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L17-L34); [streaming_manager/db/games.py строки 517–554 — GamesMixin._list_games_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L517-L554); [streaming_manager/db/games.py строки 634–637 — GamesMixin.auction_eligible_games](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L634-L637).

### AUC-003 Одна открытая сессия и стартовый снимок состава

**Состояние:** При условиях.

Создание сессии закрепляет участвующие ID, исходные баллы, названия и другие поля игр, а также стартовые позиции. Вторую локальную сессию создать нельзя, пока первая имеет статус running, paused, awaiting_wheel, winner_selected или tie_break_required.

**Доступ:** Аукцион → Старт / Крутить → подтверждение запуска.

**Условия и границы:** Состав создаётся из текущих допустимых игр. Обычный аукцион и обычное колесо требуют минимум два лота; выбывание допускает один.

**Код:** [streaming_manager/db/auction_session.py строки 43–47 — AuctionSessionMixin.AUCTION_OPEN_STATUSES](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L43-L47); [streaming_manager/db/auction_session.py строки 301–322 — AuctionSessionMixin.create_auction_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L301-L322); [streaming_manager/db/auction_session.py строки 343–435 — AuctionSessionMixin.create_auction_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L343-L435).

### AUC-004 Предварительное подтверждение запуска

**Состояние:** При условиях.

Перед созданием сессии показывается диалог с числом лотов, режимом, генератором и длительностью; для колеса также указан формат, для Random.org+ — билет. Ответ по умолчанию «Нет». После подтверждения прямого взвешенного режима запускается первое вращение без второго диалога.

**Доступ:** Аукцион → Старт или Крутить.

**Условия и границы:** Для удалённого RNG предварительная проверка API и создание первого подписанного билета происходят до этого диалога.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 31–97 — AuctionActionMixin.start_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L31-L97); [streaming_manager/views/auction_parts/actions.py строки 106–180 — AuctionActionMixin._confirm_and_create_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L106-L180).

### AUC-005 Ввод времени с точностью до миллисекунд

**Состояние:** Доступно по коду.

Общий таймер принимает ровно шесть цифр ЧЧММСС либо время с двоеточиями и дробной частью 1–3 цифры; дробь дополняется справа до миллисекунд. Пустой ввод, неверная длина сокращения, минуты/секунды больше 59 отклоняются. Для приёма ставок, допвремени и колеса рабочий диапазон 00:00:01.000–24:00:00.000.

**Доступ:** Аукцион → большое поле таймера; также Настройки → Аукцион.

**Условия и границы:** Редактирование доступно до запуска, при настройке допвремени и до вращения awaiting_wheel. Во время приёма ставок, паузы и вращения поле служит индикатором.

**Код:** [streaming_manager/time_input.py строки 4–62 — parse_duration_input](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/time_input.py#L4-L62); [streaming_manager/views/auction.py строки 2239–2297 — AuctionTab._format_milliseconds / _prestart_timer_ms / _wheel_timer_ms](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2239-L2297); [streaming_manager/views/auction_parts/state.py строки 274–284 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L274-L284).

### AUC-006 Сохраняемые длительности по умолчанию

**Состояние:** Доступно по коду.

В настройках независимо сохраняются длительность «Максимальной суммы» и длительность колеса. Начальные значения — 10 минут и 8 секунд; недопустимое сохранённое значение заменяется соответствующим начальным значением. Смена предстартового режима сохраняет введённое время отдельно для каждого контекста. Сохранение новых defaults не переписывает длительность уже открытой сессии.

**Доступ:** Настройки → Аукцион → два поля длительности → «Сохранить настройки аукциона».

**Условия и границы:** Оба значения должны укладываться в 1 секунду–24 часа. После закрытия максимального аукциона следующий его таймер восстанавливается из сохранённой настройки.

**Код:** [streaming_manager/views/settings.py строки 313–361 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L313-L361); [streaming_manager/views/settings.py строки 895–991 — SettingsTab.save_auction_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L895-L991); [streaming_manager/views/auction.py строки 1177–1202 — AuctionTab._saved_max_amount_default_duration_ms / _saved_wheel_default_duration_ms](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1177-L1202); [streaming_manager/views/auction.py строки 1868–1898 — AuctionTab.refresh_auction_settings / _prepare_next_max_amount_timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1868-L1898); [streaming_manager/views/auction.py строки 2051–2077 — AuctionTab._handle_prestart_mode_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2051-L2077).

### AUC-007 Короткая подготовка перед отсчётом

**Состояние:** При условиях.

Обычный старт и старт допвремени записывают начало фазы на 1200 мс позже текущего момента. До этой границы отображается полная заданная длительность, затем она отсчитывается до сохранённого deadline. Отдельной кнопки «Подготовить» для создания сессии нет.

**Доступ:** Аукцион → Старт; при ничьей → Дополнительное время → Старт.

**Условия и границы:** Эта задержка относится к таймеру, а не к отдельному бизнес-статусу: статус уже running. В обработчиках ручных ставок и нового лота нет дополнительного запрета по времени подготовительной фазы.

**Код:** [streaming_manager/constants.py строки 11–11 — AUCTION_PREPARATION_LEAD_IN_MS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L11-L11); [streaming_manager/db/auction_session.py строки 324–341 — AuctionSessionMixin.create_auction_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L324-L341); [streaming_manager/db/auction_session.py строки 1216–1246 — AuctionSessionMixin._remaining_ms_from_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1216-L1246); [streaming_manager/db/auction_session.py строки 3355–3364 — AuctionSessionMixin.start_auction_tie_overtime](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3355-L3364).

### AUC-008 Пауза и продолжение приёма ставок

**Состояние:** При условиях.

Одна кнопка меняется с «Пауза» на «Продолжить». Пауза сохраняет текущий остаток миллисекунд и убирает deadline; продолжение создаёт новый deadline из остатка. На паузе ручные ставки, уменьшение и строка нового лота скрываются. Если пауза произошла до начала подготовительной фазы, продолжение назначает новую задержку 1200 мс.

**Доступ:** Аукцион → кнопка общего таймера.

**Условия и границы:** Пауза доступна при running, продолжение — при paused. У колеса нет команды паузы; оно имеет отдельную остановку с повтором сохранённого результата.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 14–29 — AuctionActionMixin.handle_timer_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L14-L29); [streaming_manager/views/auction_parts/actions.py строки 182–193 — AuctionActionMixin.toggle_pause](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L182-L193); [streaming_manager/views/auction_parts/state.py строки 326–333 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L326-L333); [streaming_manager/db/auction_session.py строки 2926–3022 — AuctionSessionMixin.pause_auction / resume_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2926-L3022).

### AUC-009 Быстрая корректировка остатка времени

**Состояние:** При условиях.

Кнопки −10 мин, −1 мин, +1 мин, +10 мин изменяют предстартовое время, время настройки допвремени или остаток running/paused-сессии. До запуска диапазон ограничивается 1 секундой–24 часами; действующий остаток — 0–24 часа. Уменьшение действующего остатка до нуля вызывает завершение приёма ставок. У колеса эти кнопки скрыты.

**Доступ:** Аукцион → Таймер → четыре кнопки минут.

**Условия и границы:** Кнопки недоступны при подготовке RNG. Истёкший running-deadline этим действием не возобновляется.

**Код:** [streaming_manager/views/auction.py строки 542–569 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L542-L569); [streaming_manager/views/auction_parts/actions.py строки 195–243 — AuctionActionMixin.adjust_timer_minutes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L195-L243); [streaming_manager/views/auction_parts/state.py строки 335–358 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L335-L358); [streaming_manager/db/auction_session.py строки 3024–3083 — AuctionSessionMixin.adjust_auction_time_ms](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3024-L3083).

### AUC-010 Контекстный сброс таймера

**Состояние:** При условиях.

До старта «Сбросить» берёт сохранённый default выбранного режима; в подготовке допвремени — default максимальной суммы; в awaiting_wheel — default колеса. Для running/paused после подтверждения возвращает исходную длительность текущей фазы, сохраняя лоты и ставки. При настройке допвремени его длительность становится исходной для этой фазы.

**Доступ:** Аукцион → Таймер → Сбросить.

**Условия и границы:** В состоянии выбранного результата и во время вращения кнопка скрыта. Сброс действующей фазы имеет диалог Yes/No с ответом «Нет» по умолчанию.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 245–300 — AuctionActionMixin.reset_auction_timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L245-L300); [streaming_manager/views/auction_parts/state.py строки 360–376 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L360-L376); [streaming_manager/db/auction_session.py строки 3093–3145 — AuctionSessionMixin.reset_auction_timer_ms](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3093-L3145); [streaming_manager/db/auction_session.py строки 3373–3397 — AuctionSessionMixin.start_auction_tie_overtime](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3373-L3397).

### AUC-011 Автоматическое завершение по deadline и продолжение после возврата

**Состояние:** При условиях.

После исчерпания остатка приложение вызывает тот же переход завершения, что и ручная кнопка, без дополнительного подтверждения. Функциональный таймер продолжает проверять открытый аукцион при скрытой вкладке. При перечитывании running-сессии с истёкшим deadline приём ставок завершается; открытая сессия подхватывается из БД при следующем открытии приложения.

**Доступ:** Автоматически во время открытой сессии; состояние видно на Аукцион → Таймер.

**Условия и границы:** Это описание переходов по коду; точность исполнения в реальном времени не измерялась. Большой индикатор показывает ЧЧ:ММ:СС.мс; для OBS есть кнопки URL и предпросмотра таймера.

**Код:** [streaming_manager/views/auction_parts/state.py строки 39–46 — AuctionStateMixin._sync_auction_timer_activity](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L39-L46); [streaming_manager/views/auction_parts/state.py строки 74–97 — AuctionStateMixin._refresh_visible_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L74-L97); [streaming_manager/views/auction_parts/state.py строки 856–922 — AuctionStateMixin._tick_timer_display / _tick_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L856-L922); [streaming_manager/views/auction.py строки 2205–2213 — AuctionTab._current_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2205-L2213); [streaming_manager/views/auction.py строки 590–615 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L590-L615).

### AUC-012 Досрочное завершение приёма ставок

**Состояние:** При условиях.

«Завершить приём ставок» останавливает отсчёт и переводит сессию к кандидату, ничьей либо отсутствию победителя. Кнопка показывается как при running, так и на паузе. Ручное действие требует подтверждения с ответом «Нет» по умолчанию; завершение не откатывает баллы.

**Доступ:** Аукцион → Таймер → Завершить приём ставок.

**Условия и границы:** В прямом взвешенном режиме периода приёма ставок нет, поэтому этой кнопки нет. Наличие ожидающих конвертаций не мешает самому завершению отсчёта.

**Код:** [streaming_manager/views/auction.py строки 656–661 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L656-L661); [streaming_manager/views/auction_parts/actions.py строки 302–359 — AuctionActionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L302-L359); [streaming_manager/views/auction_parts/state.py строки 378–379 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L378-L379); [streaming_manager/db/auction_session.py строки 3178–3275 — AuctionSessionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3178-L3275).

### AUC-013 Предварительный победитель по максимальной сумме

**Состояние:** При условиях.

После приёма ставок сравниваются стартовые баллы плюс начисленные в этой сессии. Единственный максимальный лот становится winner_selected, несколько равных максимальных лотов — tie_break_required, отсутствие активных лотов — finished_no_winner. Нулевой максимум не исключён: равные нулевые суммы также дают ничью.

**Доступ:** Аукцион → режим «Максимальная сумма» → окончание таймера или досрочное завершение.

**Условия и границы:** Это предварительный результат до отдельного подтверждения. В таблице поздней корректировки остаются доступными сохранившиеся нелидеры; их можно изменить и пересчитать результат.

**Код:** [streaming_manager/db/auction_session.py строки 3151–3176 — AuctionSessionMixin._max_leaders_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3151-L3176); [streaming_manager/db/auction_session.py строки 3196–3226 — AuctionSessionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3196-L3226); [streaming_manager/db/auction_session.py строки 561–577 — AuctionSessionMixin.list_provisional_max_amount_entries](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L561-L577); [streaming_manager/views/auction_parts/actions.py строки 334–342 — AuctionActionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L334-L342).

### AUC-014 Подтверждение победителя и перенос временных игр

**Состояние:** При условиях.

Отдельное подтверждение выбранного победителя переводит игру в ПРОХОДИТСЯ и снимает её архивный признак. Все сохранившиеся временные игры этой сессии становятся обычными играми списка; остальные временные лоты сохраняют НЕ ИГРАЛ. Сессия получает confirmed, после чего можно создать следующую.

**Доступ:** Аукцион → Подтвердить победителя → диалог Yes/No.

**Условия и границы:** Нужен winner_selected, существующая игра и отсутствие необработанных поступлений текущей сессии. После колеса UI показывает действие только по окончании анимации. В формате выбывания вместо этого действует «В архив».

**Код:** [streaming_manager/views/auction_parts/rng.py строки 419–463 — AuctionRngMixin.confirm_winner](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L419-L463); [streaming_manager/views/auction_parts/state.py строки 395–409 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L395-L409); [streaming_manager/db/auction_session.py строки 3494–3572 — AuctionSessionMixin.confirm_auction_winner](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3494-L3572).

### AUC-015 Выбор действия при ничьей

**Состояние:** При условиях.

При одинаковом максимуме появляется диалог «Несколько победителей» с вариантами «Дополнительное время», «Использовать колесо» и «Позже». После «Позже» те же действия остаются на вкладке; проигравшие промежуточного сравнения сохраняются в истории как неактивные.

**Доступ:** Аукцион → окончание максимальной суммы → диалог ничьей; затем контекстные кнопки.

**Условия и границы:** Только tie_break_required. Переход к колесу блокируется необработанными поступлениями; настройка допвремени этим UI-gate не отключается.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 344–348 — AuctionActionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L344-L348); [streaming_manager/views/auction_parts/actions.py строки 361–390 — AuctionActionMixin._show_tie_break_dialog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L361-L390); [streaming_manager/views/auction_parts/state.py строки 411–433 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L411-L433); [streaming_manager/db/auction_session.py строки 3247–3266 — AuctionSessionMixin.finish_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3247-L3266).

### AUC-016 Дополнительное время после ничьей

**Состояние:** При условиях.

Нажатие «Дополнительное время» только подготавливает общий таймер со значением default максимальной суммы. Можно изменить длительность, применить минутные кнопки или сброс. Отсчёт начинается отдельным «Старт»; исходными активными участниками остаются лидеры ничьей. Во время подготовки всё ещё можно выбрать колесо.

**Доступ:** Аукцион → Дополнительное время → задать время → Старт.

**Условия и границы:** Допвремя: 1 секунда–24 часа, статус до старта tie_break_required. После старта действует общий running-интерфейс, включая добавление нового лота; отдельного UI-запрета новых лотов в overtime нет.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 392–439 — AuctionActionMixin.start_tie_overtime / _start_pending_tie_overtime](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L392-L439); [streaming_manager/views/auction_parts/state.py строки 423–428 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L423-L428); [streaming_manager/db/auction_session.py строки 3331–3409 — AuctionSessionMixin.start_auction_tie_overtime](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3331-L3409); [streaming_manager/views/auction_parts/state.py строки 476–488 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L476-L488).

### AUC-017 Колесо как тай-брейк максимальной суммы

**Состояние:** При условиях.

«Использовать колесо» переводит ничью в awaiting_wheel и подставляет default длительности колеса. Это подготовка; вращение запускается отдельным «Крутить». Активными остаются равные лидеры, поэтому их шансы равны; при нулевых баллах используется равный вес 1. Формат выбывания для максимальной суммы не предлагается.

**Доступ:** Аукцион → при ничьей → Использовать колесо → Крутить.

**Условия и границы:** Нужна разрешённая очередь конвертаций данной сессии. После перехода awaiting_wheel ручная корректировка максимальной суммы уже недоступна.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 441–468 — AuctionActionMixin.use_wheel_for_tie](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L441-L468); [streaming_manager/db/auction_session.py строки 3411–3466 — AuctionSessionMixin.start_auction_tie_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3411-L3466); [streaming_manager/db/wheel.py строки 29–46 — WheelMixin._wheel_algorithm_for_mode / _effective_wheel_weight](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L29-L46); [streaming_manager/views/auction_parts/rng.py строки 93–99 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L93-L99).

### AUC-018 Остановка всей сессии без отката баллов

**Состояние:** При условиях.

«Остановить аукцион» отменяет любую открытую сессию, в том числе уже выбранный результат и вращающееся колесо. Добавленные баллы остаются у игр, временные лоты переходят в основной список, история определения результата сохраняется. В выбывании уже архивированные лоты остаются в архиве, текущий выбранный лот без «В архив» не архивируется.

**Доступ:** Аукцион → Таймер → Остановить аукцион → предупреждение Yes/No.

**Условия и границы:** Действие доступно во всех AUCTION_OPEN_STATUSES. При ожидающих поступлениях диалог отдельно предупреждает, что остановка их не применяет и не отклоняет.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 507–602 — AuctionActionMixin.cancel_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L507-L602); [streaming_manager/views/auction_parts/state.py строки 381–393 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L381-L393); [streaming_manager/db/auction_session.py строки 3574–3642 — AuctionSessionMixin.cancel_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3574-L3642).

### AUC-019 Сохраняемое поле ручных баллов

**Состояние:** При условиях.

Для выбранного лота используется одно целочисленное поле 1–10 000 000 баллов, шаг клавиатуры/колеса spinbox — 10. Начальное значение 10; последнее выбранное значение сохраняется при окончании ввода и при успешной попытке добавить/уменьшить баллы и восстанавливается после открытия.

**Доступ:** Аукцион → «Баллы к выбранному лоту».

**Условия и границы:** Поле видно при running и при предварительном результате максимальной суммы до перехода к колесу. Изменение самого значения поля не меняет баллы лота.

**Код:** [streaming_manager/views/auction.py строки 729–750 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L729-L750); [streaming_manager/views/auction.py строки 1146–1155 — AuctionTab._persist_manual_bid_points](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1146-L1155); [streaming_manager/constants.py строки 98–101 — AUCTION_MANUAL_BID_POINTS_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L98-L101); [streaming_manager/views/auction_parts/actions.py строки 703–710 — AuctionActionMixin.add_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L703-L710).

### AUC-020 Добавление ручной ставки во время приёма

**Состояние:** При условиях.

Оператор выбирает активный лот и нажимает «Добавить». Баллы прибавляются и к его сумме в текущем аукционе, и к постоянным баллам игры; создаются contribution и отдельное событие аудита. После обновления выбранная строка сохраняется, связанные списки получают уведомление об изменении.

**Доступ:** Аукцион → выбрать строку → Баллы → Добавить.

**Условия и границы:** Только running, выбранный активный лот и положительная сумма. На paused ручной приём недоступен; поздний max_amount имеет отдельный путь корректировки.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 671–726 — AuctionActionMixin.add_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L671-L726); [streaming_manager/db/auction_session.py строки 2027–2150 — AuctionSessionMixin.add_auction_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2027-L2150).

### AUC-021 Уменьшение добавленных баллов во время приёма

**Состояние:** При условиях.

«Уменьшить» вычитает баллы текущей сессии и постоянные баллы игры, сохраняя стартовую сумму как нижнюю границу. Нельзя вычесть больше текущего bid_sm_points. Отрицательный contribution не создаётся: уменьшение записывается отдельным событием change_log.

**Доступ:** Аукцион → выбрать строку → Баллы → Уменьшить.

**Условия и границы:** Только running и активный лот; сумма больше нуля. У совершенно нового временного лота, созданного во время приёма с начальными баллами, эти баллы записаны как starting_sm_points и данным действием не уменьшаются.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 728–778 — AuctionActionMixin.decrease_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L728-L778); [streaming_manager/db/auction_session.py строки 2340–2437 — AuctionSessionMixin.decrease_auction_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2340-L2437); [streaming_manager/db/auction_session.py строки 1843–1849 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1843-L1849).

### AUC-022 Новый временный лот, объединение по названию и переиспользование игры

**Состояние:** При условиях.

Встроенная строка принимает непустое название и 0–10 000 000 баллов. Название сопоставляется по Unicode-нормализации, регистру и пробелам: активный лот с тем же названием получает баллы вместо дубликата; существующая игра базы может подключиться к сессии; неизвестное название создаёт временную НЕ ИГРАЛ с auction_only=1, невидимую в общих списках до окончания или отмены.

**Доступ:** Аукцион → Название нового лота / Баллы → Добавить лот.

**Условия и границы:** Во время приёма — running, не paused. Поля очищаются только после успешной записи; при объединении показывается сообщение. Первичный статусный фильтр не повторяется при явном поиске существующей игры по названию в этом пути.

**Код:** [streaming_manager/views/auction.py строки 793–836 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L793-L836); [streaming_manager/views/auction_parts/actions.py строки 604–669 — AuctionActionMixin.add_new_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L604-L669); [streaming_manager/db/auction_session.py строки 1660–1797 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1660-L1797); [streaming_manager/db/auction_session.py строки 1799–1889 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1799-L1889); [streaming_manager/db/common.py строки 80–90 — normalize_text_key / normalize_title_key](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L80-L90).

### AUC-023 Удаление ошибочного временного лота во время приёма

**Состояние:** При условиях.

Для выбранного временного лота появляется «Удалить лот». После подтверждения физически удаляется временная игра и связанные contributions; строка аукциона сохраняется как removed с сохранённым названием. Этот лот не переносится в основной список при закрытии сессии.

**Доступ:** Аукцион → выбрать временный лот → Удалить лот → предупреждение.

**Условия и границы:** Во время running удалять этим действием можно только auction_only=1; постоянная игра не удаляется. Позднее удаление после 00:00 имеет дополнительные ограничения.

**Код:** [streaming_manager/views/auction.py строки 760–765 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L760-L765); [streaming_manager/views/auction.py строки 2680–2713 — AuctionTab._update_delete_lot_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2680-L2713); [streaming_manager/views/auction_parts/actions.py строки 881–963 — AuctionActionMixin.delete_temporary_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L881-L963); [streaming_manager/db/auction_session.py строки 2710–2792 — AuctionSessionMixin.delete_temporary_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2710-L2792); [streaming_manager/db/auction_session.py строки 2828–2861 — AuctionSessionMixin.delete_temporary_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2828-L2861).

### AUC-024 Поздняя ручная прибавка с пересчётом результата

**Состояние:** При условиях.

После 00:00 «Добавить» работает для сохранившегося участника максимальной суммы, включая неактивного нелидера ничьей. Прибавка меняет сессию и игру, затем атомарно пересчитывает предварительного победителя или ничью без перезапуска таймера и автопродления.

**Доступ:** Аукцион → после 00:00 выбрать лот → Добавить.

**Условия и границы:** mode=max_amount, status=winner_selected или tie_break_required, wheel_spin_id отсутствует. Нельзя изменить removed, архивный или чужой сессии лот. Ожидающие конвертации сами по себе не отключают эту ручную прибавку.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 671–711 — AuctionActionMixin.add_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L671-L711); [streaming_manager/views/auction.py строки 2227–2237 — AuctionTab._entries_for_table](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2227-L2237); [streaming_manager/db/auction_session.py строки 2152–2248 — AuctionSessionMixin.add_post_expiry_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2152-L2248); [streaming_manager/db/services.py строки 1377–1458 — ServicesMixin._apply_post_expiry_source_entry_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1377-L1458).

### AUC-025 Позднее уменьшение с сохранением стартовой суммы

**Состояние:** При условиях.

После 00:00 можно уменьшить баллы сохранившегося лота максимальной суммы, включая нелидера, только в пределах bid_sm_points и при неотрицательном результате постоянных баллов игры. Предварительный победитель/ничья пересчитываются без запуска таймера; contribution не откатывается, записывается отдельная корректировка.

**Доступ:** Аукцион → после 00:00 выбрать лот → Уменьшить.

**Условия и границы:** Та же предварительная max_amount-фаза без wheel_spin_id. Сумма должна быть положительной и не больше добавленных в этой сессии баллов. Наличие pending-конвертаций не является отдельным gate этого метода.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 728–767 — AuctionActionMixin.decrease_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L728-L767); [streaming_manager/db/auction_session.py строки 2250–2338 — AuctionSessionMixin.decrease_post_expiry_manual_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2250-L2338); [streaming_manager/db/services.py строки 1416–1458 — ServicesMixin._apply_post_expiry_source_entry_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1416-L1458).

### AUC-026 Позднее добавление или объединение лота

**Состояние:** При условиях.

После 00:00 строка нового лота остаётся доступной. Совпадение с сохранившимся участником добавляет ему баллы; неизвестное название создаёт временную игру; обычная существующая неархивная игра может подключиться по названию. Новый поздний лот получает следующую стартовую позицию и участвует в пересчёте предварительного результата, таймер остаётся завершённым.

**Доступ:** Аукцион → после 00:00 → Название нового лота / Баллы → Добавить лот.

**Условия и границы:** max_amount, winner_selected/tie_break_required, без wheel_spin_id; 0–10 000 000 баллов в UI. Removed/архивный лот нельзя добавить повторно; при нескольких совпадениях предложено выбрать строку и изменить её баллы. Ожидающие конвертации не являются отдельным запретом этой операции.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 604–651 — AuctionActionMixin.add_new_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L604-L651); [streaming_manager/db/auction_session.py строки 1516–1642 — AuctionSessionMixin.add_post_expiry_manual_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1516-L1642); [streaming_manager/db/services.py строки 1305–1375 — ServicesMixin._post_expiry_title_lot_allowed_conn / _create_post_expiry_title_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1305-L1375).

### AUC-027 Позднее удаление временного лота

**Состояние:** При условиях.

После 00:00 временный лот можно удалить с пересчётом кандидата/ничьей, сохранив removed-снимок истории и не запуская таймер. Физически удаляются временная игра и её contributions. Удаление последнего сохранившегося лота запрещено.

**Доступ:** Аукцион → после 00:00 выбрать временный лот → Удалить лот.

**Условия и границы:** Предварительная max_amount-фаза без перехода к колесу. Не должно быть pending-конвертаций этой сессии. Запрещено при внешних начислениях у временной игры и при её использовании другой сессией.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 881–963 — AuctionActionMixin.delete_temporary_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L881-L963); [streaming_manager/db/auction_session.py строки 2733–2826 — AuctionSessionMixin.delete_temporary_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2733-L2826); [streaming_manager/db/auction_session.py строки 2859–2924 — AuctionSessionMixin.delete_temporary_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2859-L2924).

### AUC-028 Позднее исключение постоянного лота без удаления игры

**Состояние:** При условиях.

После 00:00 для постоянного лота кнопка меняется на «Исключить лот». Операция исключает только запись этой сессии, сохраняет игру, её накопленные баллы и contributions, пересчитывает предварительный результат без перезапуска таймера. Вернуть удалённый участник под тем же названием через позднее добавление нельзя.

**Доступ:** Аукцион → после 00:00 выбрать постоянный лот → Исключить лот.

**Условия и границы:** Предварительная max_amount-фаза, без wheel_spin_id, pending-конвертаций и архива у игры. Нельзя исключить последнего сохранившегося лота. Во время работающего приёма постоянный лот этой кнопкой не исключается.

**Код:** [streaming_manager/views/auction.py строки 2696–2713 — AuctionTab._update_delete_lot_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2696-L2713); [streaming_manager/views/auction_parts/actions.py строки 930–960 — AuctionActionMixin.delete_temporary_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L930-L960); [streaming_manager/db/auction_session.py строки 2439–2584 — AuctionSessionMixin.exclude_post_expiry_permanent_auction_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2439-L2584); [streaming_manager/db/auction_session.py строки 1560–1587 — AuctionSessionMixin.add_post_expiry_manual_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1560-L1587).

### AUC-029 Позднее переименование изолированного временного лота

**Состояние:** При условиях.

После 00:00 для выбранного временного лота доступен модальный ввод нового названия и отдельное подтверждение «Было/Станет» с «Нет» по умолчанию. Меняются название игры и snapshot_title, баллы сохраняются. Это переименование, а не объединение с существующей игрой.

**Доступ:** Аукцион → после 00:00 выбрать временный лот → Переименовать.

**Условия и границы:** Только предварительный max_amount без wheel_spin_id, pending-конвертаций, архива и removed. Игра не должна использоваться другой сессией или иметь внешние contributions. Запрещены пустое/совпадающее название, дубликат любой игры и название другого исторического лота этой сессии, включая удалённый.

**Код:** [streaming_manager/views/auction.py строки 2714–2721 — AuctionTab._update_delete_lot_action_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2714-L2721); [streaming_manager/views/auction_parts/actions.py строки 780–879 — AuctionActionMixin.rename_temporary_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L780-L879); [streaming_manager/db/auction_session.py строки 2586–2708 — AuctionSessionMixin.rename_post_expiry_temporary_lot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2586-L2708).

### AUC-030 Текущие и стартовые позиции, фиксированный порядок таблицы

**Состояние:** Доступно по коду.

Лоты сессии показываются по убыванию starting_sm_points+bid_sm_points, затем по стартовой позиции, названию без ASCII-регистра, ID игры и записи. Максимальная сумма показывает колонки СТАРТ/ТЕКУЩАЯ сразу; взвешенное колесо — после появления выбранного/архивированного результата выбывания. До этого используется ПОЗИЦИЯ. Комментарий игры доступен подсказкой названия.

**Доступ:** Аукцион → Список лотов.

**Условия и границы:** Таблица только для чтения, выбор одной строки; пользовательской сортировки по нажатию заголовка в этом UI не включено. Для нового лота во время приёма стартовая позиция фиксируется в позиции его появления; для позднего нового лота дописывается следующая позиция.

**Код:** [streaming_manager/db/auction_session.py строки 509–555 — AuctionSessionMixin._list_auction_entries_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L509-L555); [streaming_manager/db/auction_session.py строки 1912–1957 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1912-L1957); [streaming_manager/position_policy.py строки 15–49 — position_columns_for_surface](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/position_policy.py#L15-L49); [streaming_manager/views/auction.py строки 887–917 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L887-L917); [streaming_manager/views/auction.py строки 2327–2451 — AuctionTab._populate_lot_table](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2327-L2451).

### AUC-031 Поиск по лотам и синхронизация до старта

**Состояние:** Доступно по коду.

Видимая строка фильтрует названия лотов по Unicode-нормализации без учёта регистра и с нормализованными пробелами. Enter выбирает первую найденную строку, прокручивает к ней и при пустом результате выводит сообщение. До старта текст и выбранный результат синхронизируются со «Списком» и «Публичным списком»; во время открытой сессии запрос ограничен её лотами.

**Доступ:** Аукцион → Поиск по лотам… → Enter при необходимости.

**Условия и границы:** Счётчик «Лотов» показывает число строк после фильтра. Поиск аукциона фильтрует именно title; отдельный поиск комментариев в этой таблице не реализован.

**Код:** [streaming_manager/views/auction.py строки 707–726 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L707-L726); [streaming_manager/views/auction_parts/search.py строки 9–20 — AuctionSearchMixin._search_text_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/search.py#L9-L20); [streaming_manager/views/auction_parts/search.py строки 65–88 — AuctionSearchMixin.activate_conduct_search](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/search.py#L65-L88); [streaming_manager/views/auction_parts/state.py строки 100–113 — AuctionStateMixin._refresh_visible_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L100-L113); [streaming_manager/views/main_window.py строки 317–383 — MainWindow.sync_search_text / sync_search_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L317-L383).

### AUC-032 Общая сумма аукциона и отдельная сумма оверлея

**Состояние:** Доступно по коду.

Плашка «Всего: … баллов» постоянно показывает всю сумму текущего аукциона, независимо от поискового фильтра. Она включает сохранившихся неактивных нелидеров ничьей и исключает все записи result=removed. До старта сумма берётся по допустимому составу. Галочка «Показать сумму в оверлее» отдельно сохраняет видимость нижней суммы OBS; начальное состояние выключено.

**Доступ:** Аукцион → строка «Список лотов» → Всего / Показать сумму в оверлее.

**Условия и границы:** Позднее исключение постоянного лота убирает его сумму из итога сессии, хотя постоянные баллы игры сохраняются.

**Код:** [streaming_manager/views/auction.py строки 861–882 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L861-L882); [streaming_manager/views/auction.py строки 2117–2121 — AuctionTab._set_auction_overlay_total_visible](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2117-L2121); [streaming_manager/views/auction_parts/state.py строки 605–615 — AuctionStateMixin._update_auction_total_display](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L605-L615); [streaming_manager/db/auction_session.py строки 484–507 — AuctionSessionMixin.auction_total_sm_points](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L484-L507); [streaming_manager/constants.py строки 68–69 — AUCTION_LOTS_SHOW_TOTAL_FOOTER_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L68-L69).

### AUC-033 Предупреждение об ожидающих поступлениях и блокировка финализации

**Состояние:** При условиях.

В открытой сессии показываются число её необработанных поступлений и кнопка перехода в Настройки → Конвертация. Пока есть awaiting_rate/awaiting_manual_apply, отключены подтверждение результата, переход ничьей к колесу и новый розыгрыш. Проверки дублируются на границе операций БД; остановка сессии остаётся возможной после предупреждения.

**Доступ:** Аукцион → предупреждение «Есть необработанные поступления…» → Перейти к конвертации.

**Условия и границы:** Счётчик ограничен auction_id текущей исходной сессии. Повтор уже замороженного остановленного вращения освобождён от запрета нового розыгрыша. Поздние удалить/исключить/переименовать также требуют разрешить очередь; поздние +/−/новый лот — нет.

**Код:** [streaming_manager/views/auction.py строки 341–373 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L341-L373); [streaming_manager/views/auction_parts/state.py строки 194–214 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L194-L214); [streaming_manager/views/auction_parts/state.py строки 297–323 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L297-L323); [streaming_manager/db/auction_session.py строки 3468–3492 — AuctionSessionMixin._unresolved_auction_conversion_count_conn / _require_auction_conversions_resolved_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3468-L3492); [streaming_manager/views/auction_parts/rng.py строки 52–76 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L52-L76).

### AUC-034 Настройка причин и порога автопродления

**Состояние:** Доступно по коду.

В Настройки → Аукцион независимо включаются смена лидера, новый временный лот и внешнее поступление; у внешнего есть дополнительная галочка неденежных единиц. Продление и порог вводятся в миллисекундах, 00:00:00.001–24:00:00.000. Причины по умолчанию выключены; их значения 30 с / 60 с / 60 с; общий порог включён и равен 2 минутам.

**Доступ:** Настройки → Аукцион → Автопродление таймера → Сохранить настройки аукциона.

**Условия и границы:** Поля длительности причины видны при включённой причине; поле порога — при включённом пороге. Сохранение проверяет также значения скрытых полей.

**Код:** [streaming_manager/views/settings.py строки 433–561 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L433-L561); [streaming_manager/views/settings.py строки 812–871 — SettingsTab._update_auto_extend_conditional_visibility / _make_auto_extend_duration_editor](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L812-L871); [streaming_manager/views/settings.py строки 895–991 — SettingsTab.save_auction_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L895-L991); [streaming_manager/constants.py строки 204–222 — AUCTION_AUTO_EXTEND_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L204-L222).

### AUC-035 Автопродление при изменении множества лидеров

**Состояние:** При условиях.

При положительной ручной ставке либо положительном добавлении/увеличении лота до и после операции сравнивается множество максимальных лидеров. Если оно изменилось, формируется причина leader_change; это включает появление или разрешение равенства на первом месте. Уменьшение баллов отдельного вызова этого автопродления не содержит.

**Доступ:** Настройки → Аукцион → Автопродление → Смена лидера; затем обычная ставка/добавление.

**Условия и границы:** Причина включена, сессия running, остаток положителен, общий порог соблюдён. После 00:00 корректировки не продлевают отсчёт.

**Код:** [streaming_manager/db/auction_session.py строки 1680–1684 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1680-L1684); [streaming_manager/db/auction_session.py строки 1762–1788 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1762-L1788); [streaming_manager/db/auction_session.py строки 2003–2018 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2003-L2018); [streaming_manager/db/auction_session.py строки 2137–2150 — AuctionSessionMixin.add_auction_bid](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L2137-L2150).

### AUC-036 Автопродление при создании нового временного лота

**Состояние:** При условиях.

Причина new_lot формируется, когда реально создана новая временная игра. Она возможна и при нулевых начальных баллах. Совпадение с активным лотом и подключение уже существующей игры не считаются этой причиной.

**Доступ:** Настройки → Аукцион → Автопродление → Новый временный лот; затем Добавить лот.

**Условия и границы:** Причина включена и выполнены общий порог, running и положительный остаток. Позднее создание после 00:00 не вызывает автопродление.

**Код:** [streaming_manager/db/auction_session.py строки 1828–1851 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1828-L1851); [streaming_manager/db/auction_session.py строки 1993–2018 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1993-L2018); [streaming_manager/views/settings.py строки 477–492 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L477-L492).

### AUC-037 Автопродление при внешнем зачислении

**Состояние:** При условиях.

Успешное положительное внешнее зачисление во время running может дать причину external_donation для денежных единиц. Для unit_kind=service нужна одновременно основная галочка внешних поступлений и дополнительная галочка неденежных единиц; длительность берётся одна и та же. Применение ожидающего события в ещё running-источник использует тот же путь.

**Доступ:** Настройки → Аукцион → Автопродление → Внешнее поступление / Также учитывать неденежные единицы интеграций.

**Условия и границы:** Нужны реально применённые положительные баллы; очередь без зачисления не равна внешнему автопродлению. Также соблюдаются общий порог и предел остатка.

**Код:** [streaming_manager/db/services.py строки 73–80 — _external_auto_extend_reasons](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L73-L80); [streaming_manager/db/services.py строки 995–1023 — ServicesMixin.record_external_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L995-L1023); [streaming_manager/db/services.py строки 1693–1712 — ServicesMixin.apply_pending_conversion](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1693-L1712); [streaming_manager/db/auction_session.py строки 1325–1352 — AuctionSessionMixin._auto_extend_settings_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1325-L1352); [streaming_manager/views/settings.py строки 495–524 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L495-L524).

### AUC-038 Общие ограничения автопродления

**Состояние:** При условиях.

Для одной исходной операции выбирается максимум включённых подходящих продлений, а не их сумма. При включённом пороге продление происходит только если остаток не больше порога. Итоговый остаток ограничен 24 часами; пауза, нулевой/истёкший deadline и остальные статусы не получают отложенного продления. В журнал записываются причины, запрошенная и фактическая прибавки.

**Доступ:** Настройки → Аукцион → Автопродление → общий порог; применяется автоматически.

**Условия и границы:** Нужны running, остаток &gt; 0 и хотя бы одна включённая причина. Изменения настроек читаются при очередном подходящем действии; копия этих настроек в сессии не создаётся.

**Код:** [streaming_manager/db/auction_session.py строки 1363–1477 — AuctionSessionMixin._maybe_auto_extend_auction_timer_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1363-L1477); [streaming_manager/views/settings.py строки 526–556 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L526-L556).

## Колесо и источники случайных чисел

### WHL-001 Прямой запуск взвешенного колеса без приёма ставок

**Состояние:** При условиях.

Режим «Взвешенное колесо» создаёт сессию сразу awaiting_wheel: отдельного аукционного deadline и периода ставок нет. Первое нажатие «Крутить» подтверждает состав и запускает фактический розыгрыш. Обычному формату нужны минимум два допустимых лота; «Выбыванию» достаточно одного.

**Доступ:** Аукцион → Способ определения победителя → Взвешенное колесо → Крутить.

**Условия и границы:** Нет другой открытой сессии. Состав берётся из обычных допустимых игр; поздние ручные max_amount-корректировки к этому режиму не применяются.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 35–58 — AuctionActionMixin.start_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L35-L58); [streaming_manager/views/auction_parts/actions.py строки 151–180 — AuctionActionMixin._confirm_and_create_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L151-L180); [streaming_manager/db/auction_session.py строки 278–322 — AuctionSessionMixin.create_auction_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L278-L322).

### WHL-002 Обычный формат, выбывание и переключение на границе вращений

**Состояние:** При условиях.

Селектор «Формат колеса» предлагает «Обычное» и «Выбывание», сохраняет выбор для новых сессий. В открытом взвешенном режиме формат можно изменить при awaiting_wheel без wheel_spin_id и без выполняющегося запроса RNG. Это также фактически допускает изменение после остановки анимации, когда результат уже сохранён.

**Доступ:** Аукцион → Взвешенное колесо → Формат колеса.

**Условия и границы:** Во время вращения и при раскрытом выбранном результате селектор отключён. У max_amount формат принудительно standard и селектор скрыт. Проверка чистой границы не запрещает наличие сохранённых rng_value/winner_game_id.

**Код:** [streaming_manager/views/auction.py строки 415–443 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L415-L443); [streaming_manager/views/auction.py строки 2079–2115 — AuctionTab._handle_wheel_format_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2079-L2115); [streaming_manager/views/auction_parts/state.py строки 244–271 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L244-L271); [streaming_manager/db/auction_session.py строки 438–482 — AuctionSessionMixin.set_auction_wheel_format](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L438-L482).

### WHL-003 Взвешенные шансы с минимальным весом единица

**Состояние:** При условиях.

В прямом weighted_wheel эффективный вес каждого участника равен max(1, стартовые баллы + баллы сессии). Поэтому нулевой лот участвует с весом 1 даже рядом с положительными лотами. Диапазон выбора — сумма эффективных весов; участники расположены по ID игры, а попадание в полуоткрытый интервал [начало, конец) определяет результат.

**Доступ:** Аукцион → Взвешенное колесо → Крутить; математика видна через Данные проверки.

**Условия и границы:** У max_amount-тай-брейка применяется алгоритм v1 с равными текущими лидерами, а при общей нулевой сумме — весом 1 каждому. Размер видимых секторов соответствует тем же эффективным весам.

**Код:** [streaming_manager/db/wheel.py строки 25–116 — WheelMixin._effective_wheel_weight / _wheel_draw_info_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L25-L116); [streaming_manager/db/wheel.py строки 130–155 — WheelMixin._verification_participants](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L130-L155); [streaming_manager/db/wheel.py строки 272–295 — WheelMixin.run_weighted_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L272-L295); [streaming_manager/db/wheel.py строки 1142–1191 — WheelMixin._wheel_payload_from_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1142-L1191).

### WHL-004 Настройка длительности вращения

**Состояние:** При условиях.

Для колеса общий таймер задаёт 1 секунду–24 часа, default 8 секунд. До фактического вращения длительность можно редактировать и сохранять при окончании ввода, а «Сбросить» возвращает сохранённый default колеса. Быстрые минутные кнопки скрыты. После остановки только анимации повтору можно назначить другую длительность без нового результата.

**Доступ:** Аукцион → Взвешенное колесо или тай-брейк → общий таймер перед Крутить.

**Условия и границы:** Редактирование в активной сессии требует awaiting_wheel и отсутствие wheel_spin_id/фонового запроса RNG. После запуска вращения длительность заблокирована до его остановки или завершения.

**Код:** [streaming_manager/views/auction.py строки 2274–2325 — AuctionTab._wheel_timer_ms / _save_wheel_duration_from_editor](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2274-L2325); [streaming_manager/views/auction_parts/actions.py строки 266–276 — AuctionActionMixin.reset_auction_timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L266-L276); [streaming_manager/db/auction_session.py строки 3277–3329 — AuctionSessionMixin.set_auction_wheel_duration_ms](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3277-L3329); [streaming_manager/views/auction_parts/state.py строки 274–376 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L274-L376).

### WHL-005 Локальное колесо до запуска и URL того же колеса для OBS

**Состояние:** При условиях.

При выбранном взвешенном режиме до сессии показывается неподвижное колесо текущего допустимого состава. В активном взвешенном режиме и max_amount-тай-брейке показывается колесо сессии. «Копировать URL колеса» и «Открыть предпросмотр колеса» используют /wheel-overlay и /wheel-overlay?preview=1; в «Стрим / OBS» кнопки вызывают те же действия.

**Доступ:** Аукцион → выбрать Взвешенное колесо; блок OBS колесо. Дублирующие ссылки: Стрим / OBS.

**Условия и границы:** В обычном max_amount до перехода к колесу панель и блок ссылок скрыты. Предстартовый секторный порядок по ID совпадает с порядком после создания сессии.

**Код:** [streaming_manager/views/auction.py строки 457–475 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L457-L475); [streaming_manager/views/auction.py строки 2735–2742 — AuctionTab.copy_wheel_overlay_url / open_wheel_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2735-L2742); [streaming_manager/views/main_window.py строки 213–218 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L213-L218); [streaming_manager/views/auction_parts/state.py строки 695–718 — AuctionStateMixin._wheel_context_relevant / _update_wheel_panel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L695-L718); [streaming_manager/obs_visibility.py строки 98–108 — wheel_context_relevant](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L98-L108); [streaming_manager/db/wheel.py строки 1263–1357 — WheelMixin._preview_wheel_payload_from_conn / current_wheel_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1263-L1357).

### WHL-006 Локальный генератор без внешнего сервиса

**Состояние:** Доступно по коду.

«Стандартный (локальный)» использует Python secrets.randbelow по математическому диапазону текущего состава. Сервисный API key и сеть для этого выбора не нужны; внешней подписанной квитанции у него нет. Кнопка «О методах» до запуска объясняет локальный, обычный RANDOM.ORG и подписанный RANDOM.ORG+.

**Доступ:** Аукцион → Генератор → Стандартный (локальный); «О методах». Без ключа локальный вариант выбирается автоматически.

**Условия и границы:** Метод фиксируется при создании сессии. Исторический математический снимок формируется и для локального результата.

**Код:** [streaming_manager/views/auction.py строки 396–406 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L396-L406); [streaming_manager/views/auction_parts/rng.py строки 157–164 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L157-L164); [streaming_manager/views/auction_parts/rng.py строки 344–386 — AuctionRngMixin.show_rng_methods](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L344-L386); [streaming_manager/db/wheel.py строки 272–280 — WheelMixin.run_weighted_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L272-L280).

### WHL-007 Условная видимость удалённых генераторов и предварительная проверка

**Состояние:** При условиях.

Список генераторов с RANDOM.ORG/Random.org+ показывается только при непустом сохранённом ключе; без него выбор возвращается к local и поле генератора скрывается. Для выбранного удалённого метода перед созданием сессии выполняется getUsage; для Plus также создаётся первый билет. При ошибке запуск не продолжается, показывается сообщение.

**Доступ:** Настройки → Интеграции → RANDOM.ORG → Сохранить ключ; затем Аукцион → Генератор.

**Условия и границы:** Выбор только до сессии, без фоновой подготовки. Непустой сохранённый ключ разрешает показать варианты, но сам по себе не доказывает доступность API.

**Код:** [streaming_manager/views/auction.py строки 2031–2049 — AuctionTab.refresh_rng_availability](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2031-L2049); [streaming_manager/views/auction_parts/actions.py строки 61–104 — AuctionActionMixin.start_auction / _auction_rng_failed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L61-L104); [streaming_manager/views/auction_parts/state.py строки 229–242 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L229-L242).

### WHL-008 Сохранение и проверка ключа RANDOM.ORG

**Состояние:** Доступно по коду.

В настройках ключ вводится в скрытом поле. «Сохранить ключ» явно сохраняет или очищает его; простой ввод ничего не сохраняет. «Проверить API» выполняет getUsage для введённого значения и показывает остаток запросов/битов, различая проверенный и сохранённый ключ, в том числе если поле изменено во время запроса.

**Доступ:** Настройки → Интеграции → RANDOM.ORG → API key / Сохранить ключ / Проверить API.

**Условия и границы:** Для проверки требуется непустой ввод, одновременно выполняется не более одной проверки. Ошибка проверки не меняет сохранённые настройки. Способ хранения указан в INT-007.

**Код:** [streaming_manager/views/settings.py строки 592–619 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L592-L619); [streaming_manager/views/settings.py строки 2423–2489 — SettingsTab.save_random_org_key / check_random_org_api / _random_org_usage_ready](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2423-L2489).

### WHL-009 Обычный RANDOM.ORG Integer API

**Состояние:** При условиях.

Обычный удалённый метод запрашивает одно целое generateIntegers из диапазона 0…draw_upper−1. Он не создаёт подписанное доказательство; сервисные ограничения и ошибки показываются оператору. Максимальный поддерживаемый draw_upper — 1 000 000 001 значение, так как max не может превышать 1 000 000 000.

**Доступ:** Аукцион → Генератор → Random.org → запуск сессии и Крутить.

**Условия и границы:** Нужны сохранённый API key и доступность удалённого сервиса. Внешний клиент имеет timeout по умолчанию 12 секунд. При слишком большом весе локальный выбор автоматически не подставляется.

**Код:** [streaming_manager/random_sources.py строки 11–12 — RANDOM_ORG_API_URL / RANDOM_ORG_MAX_INTEGER](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L11-L12); [streaming_manager/random_sources.py строки 73–79 — RandomOrgClient.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L73-L79); [streaming_manager/random_sources.py строки 201–220 — RandomOrgClient.draw_below](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L201-L220); [streaming_manager/random_sources.py строки 240–264 — RandomOrgClient.draw_below](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L240-L264); [streaming_manager/views/auction_parts/rng.py строки 166–211 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L166-L211).

### WHL-010 RANDOM.ORG+ с билетом, подписью и восстановлением использованного результата

**Состояние:** При условиях.

Plus заранее создаёт билет showResult=true, использует generateSignedIntegers и требует успешной verifySignature. Каждый фактический новый раунд выбывания получает свой билет, сохранённый до потребления. Перед запросом клиент проверяет билет: если у него есть usedTime и result, восстанавливает тот же подписанный ответ и проверяет подпись вместо новой генерации.

**Доступ:** Аукцион → Генератор → Random.org+ → Крутить; при ошибке можно повторить действие.

**Условия и границы:** Нужны ключ, сеть и билет; неверная подпись не принимается. В userData нового запроса передаются auction ID, spinIndex, формат, drawUpper, число лотов и SHA-256 строки ID:вес. Восстановление не является бесшумным переходом на другой RNG.

**Код:** [streaming_manager/random_sources.py строки 130–159 — RandomOrgClient.create_ticket / verify_signed_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L130-L159); [streaming_manager/random_sources.py строки 221–264 — RandomOrgClient.draw_below](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L221-L264); [streaming_manager/views/auction_parts/rng.py строки 28–42 — AuctionRngMixin._rng_user_data](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L28-L42); [streaming_manager/views/auction_parts/rng.py строки 174–202 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L174-L202); [streaming_manager/db/wheel.py строки 397–422 — WheelMixin.set_auction_rng_ticket_id](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L397-L422).

### WHL-011 Ошибка удалённого RNG не заменяет метод и не оживляет отменённую сессию

**Состояние:** При условиях.

При ошибке внешнего запроса показывается ошибка, рабочая кнопка после завершения фоновой задачи снова обновляется. Автоматического переключения на secrets или другой сервис нет. Поздний ответ или ошибка проверяются против исходного auction_id и awaiting_wheel; отменённая или уже сменившая состояние сессия такой callback игнорирует.

**Доступ:** Аукцион → удалённый RNG → Крутить; доступна общая Остановить аукцион.

**Условия и границы:** Одновременно действует не больше одного _wheel_rng_worker. «Восстановить результат по билету» в Plus выполняется при следующем запросе через тот же билет; автоматический немедленный повтор в обработчике ошибки отсутствует.

**Код:** [streaming_manager/views/auction_parts/rng.py строки 44–50 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L44-L50); [streaming_manager/views/auction_parts/rng.py строки 213–267 — AuctionRngMixin._apply_wheel_draw / _wheel_rng_failed / _wheel_rng_finished](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L213-L267); [streaming_manager/random_sources.py строки 81–125 — RandomOrgClient._rpc](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L81-L125).

### WHL-012 Предварительные данные проверки без жеребьёвки

**Состояние:** При условиях.

«Данные проверки» открывает текстовый read-only состав, исходные и эффективные веса, диапазоны будущего выбора, метод и формат. До сессии это предварительные данные текущего допустимого состава; перед новым вращением активного взвешенного режима — данные этой сессии и следующего spinIndex. Действие не создаёт snapshot и не запрашивает RNG.

**Доступ:** Аукцион → Взвешенное колесо → Данные проверки до старта либо в awaiting_wheel.

**Условия и границы:** До сессии должен быть хотя бы один допустимый лот; само обычное вращение всё ещё требует два для создания сессии. В max_amount-тай-брейке метод поддержан обработчиком, но кнопка скрыта вместе с setup_widget: эту ветку не считать доступной UI-возможностью.

**Код:** [streaming_manager/views/auction.py строки 408–413 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L408-L413); [streaming_manager/views/auction_parts/rng.py строки 306–342 — AuctionRngMixin.show_pre_spin_verification](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L306-L342); [streaming_manager/db/wheel.py строки 807–892 — WheelMixin.preview_wheel_verification_data](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L807-L892); [streaming_manager/views/auction_parts/state.py строки 246–253 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L246-L253).

### WHL-013 Отдельный исторический снимок каждого фактического розыгрыша

**Состояние:** При условиях.

Выбор сохраняет результат, rng_value и исторический снимок одной транзакцией. Снимок содержит run_id, номер раунда, вид результата, версию алгоритма, исходные/эффективные веса, упорядоченные ID и названия участников, границы диапазонов, метод и доказательство Plus при наличии. Последующие раунды добавляют новые снимки; повтор остановленной анимации нового снимка не создаёт.

**Доступ:** Создаётся при Крутить; чтение и детерминированная проверка сохранённых снимков доступны в Истории аукционов, которую описывает отдельный раздел аудита.

**Условия и границы:** Новый розыгрыш требует разрешить все pending-конвертации своей сессии до freeze весов. Детерминированный проверяющий поддерживает v1/v2, проверяет непрерывность интервалов, веса и совпадение результата без сети/RNG. Историческая неизменность описывает штатные пути приложения, а не защиту от ручной правки SQLite.

**Код:** [streaming_manager/db/wheel.py строки 157–247 — WheelMixin._insert_wheel_verification_snapshot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L157-L247); [streaming_manager/db/wheel.py строки 249–395 — WheelMixin.run_weighted_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L249-L395); [streaming_manager/db/wheel.py строки 697–805 — WheelMixin.verify_wheel_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L697-L805); [streaming_manager/views/auction_parts/rng.py строки 141–152 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L141-L152).

### WHL-014 Копирование билета и внешняя проверка подписи Plus

**Состояние:** При условиях.

У текущей сессии билет Random.org+ можно скопировать отдельной кнопкой. Когда сохранены random JSON и signature, появляется «Проверить Random.org+», открывающая официальную форму signatures/form с закодированным random-объектом и подписью.

**Доступ:** Аукцион → контекстные кнопки «Копировать билет Random.org+» / «Проверить Random.org+».

**Условия и границы:** Копирование требует ticket_id; открытие формы — одновременно random JSON и signature. Код видимости этих кнопок не требует окончания анимации: при уже сохранённом доказательстве они могут быть доступны до визуального раскрытия результата.

**Код:** [streaming_manager/views/auction.py строки 689–702 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L689-L702); [streaming_manager/views/auction_parts/state.py строки 435–450 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L435-L450); [streaming_manager/views/auction_parts/rng.py строки 269–304 — AuctionRngMixin.copy_rng_ticket / open_rng_verification](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L269-L304); [streaming_manager/random_sources.py строки 53–69 — RandomDraw.verification_url](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L53-L69).

### WHL-015 Общая временная шкала и раскрытие результата после анимации

**Состояние:** При условиях.

Результат вычисляется до начала анимации, затем сохраняются spin ID, время старта и целевой угол. Локальный виджет и OBS получают одно состояние; стандартный lead-in 1200 мс даёт общий будущий старт. До окончания штатная плашка победителя и кнопка подтверждения скрывают результат, после него раскрывают победителя или выбывающий лот.

**Доступ:** Аукцион → Крутить; локальное колесо и /wheel-overlay.

**Условия и границы:** Визуальный стоп соответствует центру целочисленного интервала (pick+0.5)/draw_upper. Открытие подписанного внешнего доказательства имеет самостоятельный gate и может быть доступно раньше. Синхронность описывает общий saved payload; фактическая плавность и сетевые задержки не измерялись.

**Код:** [streaming_manager/db/wheel.py строки 978–1090 — WheelMixin.prepare_wheel_animation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L978-L1090); [streaming_manager/db/wheel.py строки 1193–1247 — WheelMixin._wheel_payload_from_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1193-L1247); [streaming_manager/views/wheel.py строки 213–244 — AuctionWheelWidget.set_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L213-L244); [streaming_manager/views/auction_parts/state.py строки 536–557 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L536-L557); [streaming_manager/views/auction_parts/state.py строки 924–944 — AuctionStateMixin._handle_local_wheel_spin_finished](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L924-L944).

### WHL-016 Остановка только анимации и повтор того же результата

**Состояние:** При условиях.

«Остановить колесо» во время вращения отменяет анимацию и возвращает awaiting_wheel с полной заданной длительностью, сохраняя участников, winner_game_id, rng_value и доказательство. Следующее «Крутить» создаёт новую анимацию того же результата; новой жеребьёвки и нового verification snapshot нет. Для отмены результата используется отдельная остановка всего аукциона.

**Доступ:** Аукцион → во время вращения → Остановить колесо → предупреждение; затем Крутить.

**Условия и границы:** Требуются winner_selected, wheel_spin_id и незавершённая анимация. Повтор сохранённого результата разрешён даже при позднее появившихся pending-конвертациях. После полной остановки штатным временем кнопка «Остановить колесо» исчезает.

**Код:** [streaming_manager/views/auction_parts/actions.py строки 470–505 — AuctionActionMixin.stop_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L470-L505); [streaming_manager/db/wheel.py строки 935–976 — WheelMixin.stop_wheel_animation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L935-L976); [streaming_manager/views/auction_parts/rng.py строки 52–59 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L52-L59); [streaming_manager/views/auction_parts/rng.py строки 118–152 — AuctionRngMixin.run_wheel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L118-L152); [streaming_manager/db/wheel.py строки 1040–1067 — WheelMixin.prepare_wheel_animation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1040-L1067).

### WHL-017 Обычный результат колеса требует подтверждения победителя

**Состояние:** При условиях.

В обычном формате выбранный сектор после окончания анимации остаётся предварительным результатом. «Подтвердить победителя» после Yes/No переводит игру в ПРОХОДИТСЯ и закрывает сессию. Простого появления сектора недостаточно для изменения статуса игры; до подтверждения всю сессию можно остановить.

**Доступ:** Аукцион → обычное колесо → дождаться остановки → Подтвердить победителя.

**Условия и границы:** Нужны winner_selected и разрешённые pending-конвертации. В тай-брейке максимальной суммы используется то же подтверждение; в выбывании оно заменено архивированием.

**Код:** [streaming_manager/views/auction_parts/rng.py строки 388–399 — AuctionRngMixin.handle_wheel_result_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L388-L399); [streaming_manager/views/auction_parts/rng.py строки 419–463 — AuctionRngMixin.confirm_winner](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L419-L463); [streaming_manager/views/auction_parts/state.py строки 395–409 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L395-L409); [streaming_manager/db/auction_session.py строки 3494–3572 — AuctionSessionMixin.confirm_auction_winner](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3494-L3572).

### WHL-018 Выбывание с явным архивированием и следующими раундами

**Состояние:** При условиях.

В формате выбывания сектор означает кандидата на выбывание. После полной остановки «В архив» архивирует выбранную игру, делает её обычной auction_only=0, помечает участника eliminated и исключает из следующих вращений. При оставшихся лотах сессия возвращается awaiting_wheel с очищенным RNG/animation-состоянием; каждый следующий новый розыгрыш получает свой snapshot. Если участников не осталось, сессия завершается без победителя.

**Доступ:** Аукцион → Взвешенное колесо → Выбывание → Крутить → В архив; затем следующий раунд.

**Условия и границы:** Минимум один начальный лот; последний единственный участник также разыгрывается и может быть отправлен в архив, автоматического «победителя-выжившего» нет. Кнопка UI отключена при pending-конвертациях; archive_elimination_result сам эту конкретную очередь не проверяет, но проверяет завершение анимации. Дополнительного Yes/No в обработчике «В архив» нет.

**Код:** [streaming_manager/views/auction_parts/rng.py строки 388–417 — AuctionRngMixin.handle_wheel_result_action / archive_elimination_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L388-L417); [streaming_manager/views/auction_parts/state.py строки 395–400 — AuctionStateMixin._update_session_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L395-L400); [streaming_manager/db/wheel.py строки 424–555 — WheelMixin.archive_elimination_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L424-L555).

### WHL-019 Переключаемый столбец вероятностей

**Состояние:** При условиях.

Галочка «Показывать шанс в колесе» показывает/скрывает столбец вероятностей в операторской таблице; настройка сохраняется, default включён. Доли берутся из реального weighted payload, показываются в процентах с двумя десятичными знаками и десятичной запятой. Переключение меняет представление, а не веса или RNG.

**Доступ:** Аукцион → Взвешенное колесо → Список лотов → Показывать шанс в колесе.

**Условия и границы:** Галочка и столбец применимы только к настоящему weighted_wheel, включая предстарт. В max_amount, включая равное колесо ничьей, галочка скрыта.

**Код:** [streaming_manager/views/auction.py строки 847–852 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L847-L852); [streaming_manager/views/auction.py строки 1157–1175 — AuctionTab._set_wheel_chance_visible / _format_wheel_probability](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1157-L1175); [streaming_manager/views/auction_parts/state.py строки 633–693 — AuctionStateMixin._weighted_wheel_chance_context / _sync_wheel_chance_visibility / _wheel_probability_map](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L633-L693); [streaming_manager/constants.py строки 102–103 — AUCTION_WHEEL_CHANCE_VISIBLE_*](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L102-L103).

### WHL-020 Шанс выбранного результата из исторического снимка

**Состояние:** При условиях.

После остановки прямого взвешенного вращения отдельно показывается шанс выбранного победителя или лота на выбывание именно в этом раунде. Он читается из effective_weight/draw_upper verification snapshot, а не пересчитывается по текущим баллам игры. Если подходящих данных нет, UI пишет «недоступен».

**Доступ:** Аукцион → завершённое вращение weighted_wheel → плашка шанса.

**Условия и границы:** Только weighted_wheel + winner_selected и законченная анимация. Для max_amount-тай-брейка такая плашка не показывается.

**Код:** [streaming_manager/views/auction_parts/state.py строки 559–603 — AuctionStateMixin._update_winner_chance_display](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L559-L603); [streaming_manager/db/wheel.py строки 636–695 — WheelMixin._resolved_winner_chance_from_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L636-L695); [streaming_manager/db/wheel.py строки 1207–1227 — WheelMixin._wheel_payload_from_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1207-L1227).

### WHL-021 Читаемое локальное колесо и подпись сектора

**Состояние:** При условиях.

Локальные секторы имеют устойчивый цвет по ID игры, площадь пропорциональна весу; текст с переносом и адаптацией шрифта рисуется при угле сектора не менее 4°. Неподвижный указатель показывает текущий сектор; при включённой в оформлении pointer_label подпись во время вращения использует его название, иначе «Колесо вращается…». По завершении подпись меняется на «Победитель» или «Выбывает».

**Доступ:** Аукцион → видимая панель колеса; внешний вид pointer_label и свечение настраиваются через Стрим / OBS, см. OBS-027.

**Условия и границы:** Это описание ветвей отрисовки, не результат визуального запуска. Малые сектора остаются участниками даже если подпись не нарисована.

**Код:** [streaming_manager/views/wheel.py строки 33–56 — AuctionWheelWidget.PALETTE / sector_color](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L33-L56); [streaming_manager/views/wheel.py строки 332–350 — AuctionWheelWidget.sector_under_pointer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L332-L350); [streaming_manager/views/wheel.py строки 437–505 — AuctionWheelWidget._build_wheel_cache](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L437-L505); [streaming_manager/views/wheel.py строки 626–673 — AuctionWheelWidget.paintEvent](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L626-L673).

### WHL-022 Разгон, равномерное вращение и торможение

**Состояние:** При условиях.

Визуальная кривая имеет разгон, равномерную фазу и торможение. Разгон занимает min(22% длительности, 2 с), торможение — min(30%, 3 с); длинные вращения проводят основное время с постоянной скоростью. Число оборотов масштабируется относительно 8 секунд; 6–9 базовых полных оборотов влияют на анимацию, а не на сохранённый случайный результат.

**Доступ:** Автоматически после Крутить в локальном колесе и общем состоянии вращения.

**Условия и границы:** Целевой угол вычислен из уже выбранного результата. Локальная шкала привязывает saved UTC start к monotonic clock один раз на spin_id; повторное чтение payload не начинает анимацию заново.

**Код:** [streaming_manager/wheel_motion.py строки 6–59 — wheel_motion_progress](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/wheel_motion.py#L6-L59); [streaming_manager/views/wheel.py строки 213–239 — AuctionWheelWidget.set_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L213-L239); [streaming_manager/views/wheel.py строки 305–330 — AuctionWheelWidget._animation_progress / _rotation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py#L305-L330); [streaming_manager/db/wheel.py строки 1010–1038 — WheelMixin.prepare_wheel_animation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L1010-L1038).

## Музыка аукциона и колеса

### AUD-001 Общий каталог саундтреков с раздельным выбором

**Состояние:** Доступно по коду.

Музыка аукциона и музыка колеса используют общий каталог внутренних MP3, WAV и OGG в data/soundtrack, но сохраняют независимые выбранные файлы, громкость и mute. Можно выбрать вариант без soundtrack.

**Доступ:** Аукцион → Проведение → блок таймера

**Условия и границы:** Основной музыкальный плеер использует отдельный каталог data/music.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 54–107 — AuctionAudioMixin._init_wheel_audio](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L54-L107); [streaming_manager/views/auction_parts/audio.py строки 366–376 — AuctionAudioMixin._refresh_shared_soundtrack_catalogs](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L366-L376); [streaming_manager/views/auction_parts/audio.py строки 295–364 — AuctionAudioMixin._build_wheel_soundtrack_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L295-L364); [streaming_manager/views/auction_parts/audio.py строки 881–943 — AuctionAudioMixin._build_auction_soundtrack_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L881-L943).

### AUD-002 Пакетное добавление саундтреков

**Состояние:** Доступно по коду.

Выбор одного или нескольких файлов выполняет проверку форматов и единый выбор Копировать в программу или Использовать исходный файл; файлы обрабатываются последовательно, ошибки собираются, последняя успешная запись выбирается после группы.

**Доступ:** Аукцион → Добавить soundtrack

**Условия и границы:** Импорт разрешён и во время активного воспроизведения; успешный выбор применяется после завершения группы.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 634–669 — AuctionAudioMixin._start_soundtrack_import_batch](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L634-L669); [streaming_manager/views/auction_parts/audio.py строки 671–704 — AuctionAudioMixin._continue_soundtrack_import_batch](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L671-L704); [streaming_manager/views/auction_parts/audio.py строки 815–829 — AuctionAudioMixin._import_wheel_soundtrack](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L815-L829); [streaming_manager/views/auction_parts/audio.py строки 1179–1193 — AuctionAudioMixin._import_auction_soundtrack](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1179-L1193).

### AUD-003 Повторные и внешние саундтреки

**Состояние:** Доступно по коду.

При совпадении имени внутреннего файла доступны Использовать существующий, Заменить, Сохранить отдельную копию и Отмена. Внешний оригинал доступен в селекторе только пока выбран в данном контексте.

**Доступ:** Добавление soundtrack и его список выбора

**Условия и границы:** Прежние внешние пути не образуют общую повторно выбираемую библиотеку; для их возврата используется добавление файла.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 731–763 — AuctionAudioMixin._resolve_soundtrack_copy_target](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L731-L763); [streaming_manager/views/auction_parts/audio.py строки 463–486 — AuctionAudioMixin._soundtrack_assets_for_setting](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L463-L486).

### AUD-004 Зацикленная музыка таймера аукциона

**Состояние:** При условиях.

В режиме Максимальная сумма один выбранный саундтрек повторяется, запускается на общей границе старта таймера, ставится на паузу вместе с ним и возобновляется. При подготовке дополнительного времени сохраняет позицию; завершение фазы возвращает управление музыкой плееру.

**Доступ:** Автоматически при таймере аукциона

**Условия и границы:** Хотя внутренний движок умеет playlist, текущий обработчик передаёт ровно один выбранный файл с loop_one=True.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 1242–1250 — AuctionAudioMixin._resolved_auction_soundtrack_playlist](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1242-L1250); [streaming_manager/views/auction_parts/audio.py строки 1272–1323 — AuctionAudioMixin._start_auction_soundtrack_for_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1272-L1323); [streaming_manager/views/auction_parts/audio.py строки 1339–1350 — AuctionAudioMixin._finish_auction_soundtrack_phase](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1339-L1350).

### AUD-005 Музыка вращения колеса

**Состояние:** При условиях.

Выбранный саундтрек колеса повторяется в течение окна вращения, привязан к сохранённому времени начала и длительности анимации и останавливается с её завершением.

**Доступ:** Автоматически при вращении колеса

**Условия и границы:** Музыка не выбирает победителя и не определяет длительность вращения.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 1416–1455 — AuctionAudioMixin._schedule_wheel_soundtrack](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1416-L1455); [streaming_manager/audio.py строки 186–235 — ApplicationAudioEngine.schedule_loop](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/audio.py#L186-L235).

### AUD-006 Живое переключение и регулировка саундтрека

**Состояние:** Доступно по коду.

Во время аукциона или вращения можно изменить выбранный soundtrack, громкость 0–100 процентов и Без звука. Смена активного файла перезапускает соответствующее воспроизведение; выбор без файла его останавливает.

**Доступ:** Блок музыки текущего таймера

**Условия и границы:** На время фонового копирования кнопка добавления блокируется; сами настройки двух контекстов независимы.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 571–593 — AuctionAudioMixin._wheel_soundtrack_selection_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L571-L593); [streaming_manager/views/auction_parts/audio.py строки 1049–1078 — AuctionAudioMixin._auction_soundtrack_selection_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1049-L1078); [streaming_manager/views/auction_parts/audio.py строки 1474–1480 — AuctionAudioMixin._set_wheel_soundtrack_edit_enabled](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1474-L1480); [streaming_manager/views/auction_parts/audio.py строки 1376–1383 — AuctionAudioMixin._set_auction_soundtrack_edit_enabled](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1376-L1383).

### AUD-007 Вывод саундтреков через приложение или виджет таймера

**Состояние:** При условиях.

Общий маршрут для аукциона и колеса переключает локальное воспроизведение либо передачу звука через OBS-виджет таймера. В режиме OBS локальные Qt-выходы приглушены, но продолжают вести позицию.

**Доступ:** Аукцион → Проведение → Вывод звука

**Условия и границы:** Для обоих саундтреков используется именно виджет таймера, а не виджет колеса и не музыкального плеера.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 124–137 — AuctionAudioMixin._audio_output_mode_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L124-L137); [streaming_manager/views/auction_parts/audio.py строки 139–145 — AuctionAudioMixin._apply_audio_output_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L139-L145); [streaming_manager/views/auction_parts/audio.py строки 221–288 — AuctionAudioMixin._refresh_browser_audio_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L221-L288); [streaming_manager/views/auction.py строки 606–641 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L606-L641).

### AUD-008 Приоритет музыки аукциона перед плеером

**Состояние:** Доступно по коду.

При доступном выбранном soundtrack без mute аукцион или колесо временно ставит независимый плеер на паузу. После возврата владения плеер продолжает согласно последнему пользовательскому состоянию; подготовка старта и отсутствие саундтрека не должны забирать звук.

**Доступ:** Автоматически при воспроизведении саундтреков

**Условия и границы:** Настройка mute проверяется отдельно от значения громкости; даже нулевая громкость без mute может удерживать владение звуком.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 170–219 — AuctionAudioMixin._sync_audio_owner_with_session](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L170-L219); [streaming_manager/audio.py строки 49–62 — AudioCoordinator.acquire_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/audio.py#L49-L62); [streaming_manager/audio.py строки 64–78 — AudioCoordinator.release_auction](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/audio.py#L64-L78); [streaming_manager/music_player.py строки 600–618 — MusicPlayerController.restore_from_external](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py#L600-L618).

### AUD-009 Продолжение аукциона при проблеме со звуком

**Состояние:** При условиях.

Ошибка декодирования саундтрека показывается в его состоянии и освобождает плеер; аукцион и колесо продолжают работу. После обновления недоступный выбранный файл сбрасывается, соответствующий звук останавливается.

**Доступ:** Автоматически при ошибке или пропавшем файле

**Условия и границы:** Это обработка ошибок в коде, а не подтверждение работы каждого аудиоформата на Windows.

**Код:** [streaming_manager/views/auction_parts/audio.py строки 1368–1374 — AuctionAudioMixin._auction_audio_error](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1368-L1374); [streaming_manager/views/auction_parts/audio.py строки 1468–1472 — AuctionAudioMixin._wheel_audio_error](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1468-L1472); [streaming_manager/views/auction_parts/audio.py строки 502–535 — AuctionAudioMixin._refresh_wheel_soundtrack_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L502-L535); [streaming_manager/views/auction_parts/audio.py строки 984–1011 — AuctionAudioMixin._refresh_auction_soundtrack_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L984-L1011).

## Правила аукциона и редактор шаблонов

### RUL-001 Единый редактор правил

**Состояние:** Доступно по коду.

Модальное окно доступно до, во время и после аукциона. При открытом аукционе изначально выбирается его исходный шаблон; иначе активный. Текст и оформление доступны рядом в изменяемом разделителе.

**Доступ:** Аукцион → Правила аукциона

**Код:** [streaming_manager/views/auction.py строки 296–301 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L296-L301); [streaming_manager/views/auction.py строки 2183–2197 — AuctionTab.open_auction_rules_editor](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2183-L2197); [streaming_manager/views/rules_editor.py строки 150–176 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L150-L176).

### RUL-002 Выбор шаблона и маркировка активного

**Состояние:** Доступно по коду.

Список показывает сохранённые шаблоны; активный выделен зелёным. Выбранный шаблон может отличаться от активного. Для активного скрыта кнопка активации, для единственного — удаления; отдельное уведомление объясняет, использует ли выбранный шаблон текущий аукцион.

**Доступ:** Редактор правил → Шаблон

**Код:** [streaming_manager/views/rules_editor.py строки 515–543 — AuctionRulesEditorDialog._reload_templates](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L515-L543); [streaming_manager/views/rules_editor.py строки 771–795 — AuctionRulesEditorDialog._update_rules_session_notice](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L771-L795); [streaming_manager/views/rules_editor.py строки 1072–1092 — AuctionRulesEditorDialog._update_status](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1072-L1092).

### RUL-003 Создание и переименование шаблонов

**Состояние:** Доступно по коду.

Создание добавляет пустой неактивный шаблон. Название нормализуется по пробелам, не может быть пустым или длиннее 80 символов; повторные нормализованные имена запрещены. Переименование исходного шаблона синхронизируется с открытой локальной сессией.

**Доступ:** Редактор правил → Создать / Переименовать

**Код:** [streaming_manager/views/rules_editor.py строки 1206–1239 — AuctionRulesEditorDialog._create_template / _rename_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1206-L1239); [streaming_manager/db/rules.py строки 36–52 — RULE_TEMPLATE_NAME_MAX / _validate_rule_template_name](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L36-L52); [streaming_manager/db/rules.py строки 127–174 — RulesMixin._assert_rule_template_name_unique_conn / create_rule_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L127-L174); [streaming_manager/db/rules.py строки 381–405 — RulesMixin.rename_rule_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L381-L405).

### RUL-004 Замена шаблона и сохранение копии

**Состояние:** Доступно по коду.

Сохранение изменённого существующего шаблона предлагает заменить текущий, сохранить как новый или отменить. Новая копия получает своё название и остаётся неактивной; исходный шаблон не меняется. Сохранение оставляет редактор открытым.

**Доступ:** Редактор правил → Сохранить

**Код:** [streaming_manager/views/rules_editor.py строки 440–443 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L440-L443); [streaming_manager/views/rules_editor.py строки 1106–1186 — AuctionRulesEditorDialog._save_current / _save_with_choice](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1106-L1186).

### RUL-005 Активация и переключение правил в эфире

**Состояние:** Доступно по коду.

«Сделать активным» переключает общий активный шаблон и снимок правил открытого локального аукциона вместе с оформлением. Для грязного шаблона требуется явное «Сохранить и активировать».

**Доступ:** Редактор правил → Сделать активным

**Код:** [streaming_manager/views/rules_editor.py строки 1268–1295 — AuctionRulesEditorDialog._make_active](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1268-L1295); [streaming_manager/db/rules.py строки 428–481 — RulesMixin.set_active_rule_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L428-L481).

### RUL-006 Удаление шаблонов с сохранением истории

**Состояние:** Доступно по коду.

Удаление требует подтверждения, последний шаблон удалить нельзя. При удалении активного выбирается оставшийся шаблон; уже существующие снимки аукционов сохраняются.

**Доступ:** Редактор правил → Удалить

**Код:** [streaming_manager/views/rules_editor.py строки 1241–1266 — AuctionRulesEditorDialog._delete_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1241-L1266); [streaming_manager/db/rules.py строки 483–524 — RulesMixin.delete_rule_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L483-L524).

### RUL-007 Защита несохранённых изменений

**Состояние:** Доступно по коду.

Показывается статус «Есть несохранённые изменения» или «Сохранено». При смене шаблона, создании, переименовании, удалении и закрытии можно сохранить, не сохранять или отменить действие; обычное подтверждение сохранения заменяет текущий шаблон.

**Доступ:** Редактор правил → смена шаблона / действия / Закрыть

**Код:** [streaming_manager/views/rules_editor.py строки 729–741 — AuctionRulesEditorDialog._template_index_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L729-L741); [streaming_manager/views/rules_editor.py строки 1101–1104 — AuctionRulesEditorDialog._update_status](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1101-L1104); [streaming_manager/views/rules_editor.py строки 1188–1204 — AuctionRulesEditorDialog._confirm_discard_or_save](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1188-L1204); [streaming_manager/views/rules_editor.py строки 1410–1417 — AuctionRulesEditorDialog.closeEvent](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1410-L1417).

### RUL-008 Форматирование текста без HTML-кода

**Состояние:** Доступно по коду.

Редактор принимает форматированный текст, позволяет выбирать семейство и размер 6–96 pt, полужирный, курсив, подчёркивание, цвет палитрой или пипеткой. Есть стили «Обычный текст», «Заголовок» (24 pt жирный) и «Подзаголовок» (18 pt жирный).

**Доступ:** Редактор правил → панель форматирования текста

**Код:** [streaming_manager/views/rules_editor.py строки 321–378 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L321-L378); [streaming_manager/views/rules_editor.py строки 402–404 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L402-L404); [streaming_manager/views/rules_editor.py строки 1365–1379 — AuctionRulesEditorDialog._apply_paragraph_style](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1365-L1379).

### RUL-009 Выравнивание и списки правил

**Состояние:** Доступно по коду.

Доступно выравнивание слева, по центру, справа и по ширине, а также маркированный и нумерованный список. Формат применяется к текущему выделению или месту ввода.

**Доступ:** Редактор правил → Слева / Центр / Справа / По ширине / • Список / 1. Список

**Код:** [streaming_manager/views/rules_editor.py строки 381–398 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L381-L398); [streaming_manager/views/rules_editor.py строки 1327–1335 — AuctionRulesEditorDialog._merge_char_format](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1327-L1335); [streaming_manager/views/rules_editor.py строки 1381–1388 — AuctionRulesEditorDialog._make_list](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1381-L1388).

### RUL-010 Редактирование на оформленном фоне

**Состояние:** Доступно по коду.

Та же редактируемая область сразу отражает выбранный цвет, непрозрачность, светящийся контур, изображение, GIF или беззвучное циклическое видео. Фон лежит под текстом и не заменяет документ картинкой.

**Доступ:** Редактор правил → текстовая область и Оформление OBS

**Код:** [streaming_manager/views/rules_editor.py строки 808–859 — AuctionRulesEditorDialog._refresh_local_rules_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L808-L859); [streaming_manager/views/rules_editor.py строки 914–950 — AuctionRulesEditorDialog._load_rules_media_source](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L914-L950); [streaming_manager/views/rules_editor.py строки 952–1014 — AuctionRulesEditorDialog._update_rules_media_layer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L952-L1014).

### RUL-011 Фон, непрозрачность и контур правил

**Состояние:** Доступно по коду.

Оформление принадлежит выбранному шаблону: прозрачный, цветной или собственный фон; цвет с пипеткой; непрозрачность цветного фона 0–100%; включаемый светящийся контур со своим цветом. Радиус и параметры размытия фиксированы, отдельной настройки толщины нет.

**Доступ:** Редактор правил → Оформление OBS

**Код:** [streaming_manager/views/rules_editor.py строки 219–316 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L219-L316); [streaming_manager/views/rules_editor.py строки 636–645 — AuctionRulesEditorDialog._obs_background_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L636-L645); [streaming_manager/web/rules_overlay.html строки 25–41 — root / glow CSS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L25-L41).

### RUL-012 Медиафоны правил из общей библиотеки

**Состояние:** Доступно по коду.

Можно выбирать доступные PNG/JPG/JPEG/WEBP/GIF/MP4/WEBM общей библиотеки, включая анимацию и беззвучное видео. Кнопка «Добавить фон…» вызывает общий импортёр, но именно из редактора правил он фактически разрешает только PNG/JPG/JPEG/WEBP; GIF и видео надо предварительно добавить через другой блок OBS.

**Доступ:** Редактор правил → Свой → Из библиотеки / Добавить фон…

**Условия и границы:** Прямой импорт из правил ограничен статическими изображениями, несмотря на более широкую подсказку кнопки.

**Код:** [streaming_manager/views/rules_editor.py строки 648–692 — AuctionRulesEditorDialog._refresh_rules_media_library / _import_rules_media_file](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L648-L692); [streaming_manager/views/stream.py строки 1878–1907 — StreamTab.import_rules_background_media / _import_background_media_for](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1878-L1907); [streaming_manager/views/stream.py строки 2020–2022 — StreamTab._apply_background_import](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2020-L2022).

### RUL-013 Автопрокрутка правил в OBS

**Состояние:** Доступно по коду.

При включённой автопрокрутке длинный текст идёт вниз со скоростью 22 px/с, делает паузы сверху и снизу и плавно возвращается к началу. Для короткого текста прокрутка не запускается.

**Доступ:** Редактор правил → Автопрокрутка

**Код:** [streaming_manager/views/rules_editor.py строки 219–221 — AuctionRulesEditorDialog.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L219-L221); [streaming_manager/web/rules_overlay.html строки 108–112 — scroll constants](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L108-L112); [streaming_manager/web/rules_overlay.html строки 239–249 — syncAnimationLoop](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L239-L249); [streaming_manager/web/rules_overlay.html строки 294–318 — animate](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L294-L318).

### RUL-014 Браузерный предпросмотр выбранного шаблона и черновика

**Состояние:** Доступно по коду.

Кнопка открывает ссылку с отдельным токеном редактора, которая следует выбранному шаблону и обновляет несохранённый текст и оформление через память процесса. Рабочий OBS-источник продолжает читать сохранённые правила. После закрытия редактора ссылка истекает; API возвращает preview_expired вместо подмены рабочими правилами.

**Доступ:** Редактор правил → Проверить в браузере

**Условия и границы:** Черновик ограничен 1 000 000 символов HTML; видимая подсказка про «только сохранённый вариант» отстаёт от реализованного поведения.

**Код:** [streaming_manager/views/rules_editor.py строки 486–513 — AuctionRulesEditorDialog._open_selected_template_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L486-L513); [streaming_manager/views/rules_editor.py строки 1040–1070 — AuctionRulesEditorDialog._publish_unsaved_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1040-L1070); [streaming_manager/views/rules_editor.py строки 1410–1415 — AuctionRulesEditorDialog.closeEvent](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1410-L1415); [streaming_manager/api_server.py строки 660–690 — Handler.do_GET rules preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L660-L690).

### RUL-015 Синхронизация правил открытого аукциона и исторические снимки

**Состояние:** Доступно по коду.

Сессия начинается с копии активного шаблона. Сохранение и переименование её исходного шаблона обновляют текст в открытых локальных сессиях; сохранение его оформления обновляет оформление. Завершённая история хранит последнюю синхронизированную копию. Сохранение другого неактивированного шаблона текущий аукцион не меняет.

**Доступ:** Редактор правил → Сохранить / Переименовать; работа с текущим аукционом

**Код:** [streaming_manager/db/rules.py строки 27–34 — RulesMixin](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L27-L34); [streaming_manager/db/rules.py строки 267–314 — RulesMixin.save_rule_template_presentation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L267-L314); [streaming_manager/db/rules.py строки 329–379 — RulesMixin._sync_open_sessions_from_rule_template_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L329-L379); [streaming_manager/views/rules_editor.py строки 784–794 — AuctionRulesEditorDialog._update_rules_session_notice](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L784-L794).

### RUL-016 Разделение глобального показа и оформления шаблона

**Состояние:** Доступно по коду.

Режим показа правил общий для источника и сохраняется в Стрим / OBS. Текст, автопрокрутка, фон, прозрачность и контур сохраняются в шаблоне и переходят в снимок сессии. Старые шаблоны без явного оформления получают совместимые значения прежних общих настроек.

**Доступ:** Стрим / OBS → Виджет правил; Редактор правил → Оформление OBS

**Код:** [streaming_manager/views/stream.py строки 1531–1540 — StreamTab._save_rules_overlay_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1531-L1540); [streaming_manager/views/rules_editor.py строки 743–758 — AuctionRulesEditorDialog._load_template](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L743-L758); [streaming_manager/db/rules.py строки 718–772 — RulesMixin.current_rules_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L718-L772).

### RUL-017 Автоматические отступы и перенос текста

**Состояние:** Доступно по коду.

Редактор и OBS выбирают внутренний отступ автоматически по размеру области в диапазоне 8–24 px; длинные слова и абзацы переносятся по ширине источника. Старое поле padding сохраняется для совместимости, но пользовательского регулятора и влияния на геометрию больше нет.

**Доступ:** Редактор правил / виджет /rules-overlay

**Код:** [streaming_manager/views/rules_editor.py строки 608–612 — AuctionRulesEditorDialog._obs_presentation_values](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L608-L612); [streaming_manager/views/rules_editor.py строки 1016–1027 — AuctionRulesEditorDialog._responsive_rules_padding](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1016-L1027); [streaming_manager/web/rules_overlay.html строки 52–70 — viewport / content CSS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L52-L70).

### RUL-018 Ограниченный форматированный HTML правил

**Состояние:** Доступно по коду.

В OBS передаётся безопасное подмножество текста и типографики: абзацы, div/span, переносы, жирный/курсив/подчёркивание, заголовки h1–h4, списки и цитаты. Скрипты, iframe, SVG, встроенные объекты, изображения, внешние ресурсы и обработчики событий не являются поддерживаемым содержимым правил.

**Доступ:** Вставка или редактирование форматированного текста → сохранение → виджет правил

**Код:** [streaming_manager/rules_html.py строки 9–25 — _ALLOWED_TAGS / _safe_style](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/rules_html.py#L9-L25); [streaming_manager/rules_html.py строки 35–83 — _RulesHtmlSanitizer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/rules_html.py#L35-L83); [streaming_manager/db/rules.py строки 750–756 — RulesMixin.current_rules_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L750-L756).

## История аукционов и проверка результата

### HIST-001 Архив закрытых аукционов только для чтения

**Состояние:** Доступно по коду.

Отдельная вкладка перечисляет закрытые сессии со статусами confirmed (ЗАВЕРШЁН), cancelled (ОТМЕНЁН), finished_no_winner (БЕЗ ПОБЕДИТЕЛЯ), legacy finished. Таблица: дата, аукцион, фактический путь режима, статус, победитель и число лотов. Победитель показывается только для confirmed, removed-лоты не входят в счётчик/детали.

**Доступ:** Главная вкладка «История аукционов».

**Код:** [streaming_manager/views/main_window.py строки 228–229 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L228-L229); [streaming_manager/views/main_window.py строки 261–267 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L261-L267); [streaming_manager/views/completed_auction_history.py строки 20–25 — STATUS_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L20-L25); [streaming_manager/views/completed_auction_history.py строки 50–113 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L50-L113); [streaming_manager/db/auction_session.py строки 938–970 — AuctionSessionMixin.COMPLETED_AUCTION_STATUSES / _completed_auction_filters](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L938-L970); [streaming_manager/db/auction_session.py строки 1043–1062 — AuctionSessionMixin.list_completed_auction_sessions](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1043-L1062).

### HIST-002 Поиск закрытых аукционов по имени, ID и лотам

**Состояние:** Доступно по коду.

Ищет по имени сессии, текстовому ID и snapshot_title любого не-removed лота, в том числе победившего. Запрос применяется вместе с датами; ввод задержан на 250 мс. Фактический поиск — SQLite LIKE/COLLATE NOCASE, поэтому он не имеет такой же Unicode NFKC/casefold-нормализации, как Список/Публичный список.

**Доступ:** «История аукционов» → поле «Поиск по аукциону, ID, победителю или лоту…».

**Код:** [streaming_manager/views/completed_auction_history.py строки 54–58 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L54-L58); [streaming_manager/views/completed_auction_history.py строки 220–224 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L220-L224); [streaming_manager/views/completed_auction_history.py строки 269–275 — CompletedAuctionHistoryTab._query_args](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L269-L275); [streaming_manager/db/auction_session.py строки 943–970 — AuctionSessionMixin._completed_auction_filters](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L943-L970).

### HIST-003 Фильтр по периоду

**Состояние:** Доступно по коду.

Доступны Всё время, Сегодня, Последние 7 дней, Последние 30 дней, Этот месяц и Произвольный период с календарями ДД.ММ.ГГГГ. Границы строятся по локальным дням и переводятся в UTC; конечная дата включается целиком. 7/30 дней включают сегодня; если конец произвольного периода раньше начала, берётся один день начала. Фильтр использует finished_at, иначе started_at, иначе created_at.

**Доступ:** «История аукционов» → период и, для произвольного, даты начала/конца.

**Код:** [streaming_manager/views/completed_auction_history.py строки 60–77 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L60-L77); [streaming_manager/views/completed_auction_history.py строки 233–267 — CompletedAuctionHistoryTab._period_changed / _date_bounds](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L233-L267); [streaming_manager/db/auction_session.py строки 949–956 — AuctionSessionMixin._completed_auction_filters](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L949-L956).

### HIST-004 Сортировка и порционная загрузка истории

**Состояние:** Доступно по коду.

Можно переключить Новые → старые / Старые → новые. Сортировка — по finished_at, иначе started_at, иначе created_at, с ID как дополнительным критерием в том же направлении. История подгружается по 50 строк кнопкой «Загрузить ещё»; кнопка скрывается, когда продолжения нет. Изменение поиска/периода/сортировки начинает загрузку заново.

**Доступ:** «История аукционов» → порядок и «Загрузить ещё».

**Код:** [streaming_manager/views/completed_auction_history.py строки 36–37 — CompletedAuctionHistoryTab.PAGE_SIZE](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L36-L37); [streaming_manager/views/completed_auction_history.py строки 79–84 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L79-L84); [streaming_manager/views/completed_auction_history.py строки 277–321 — CompletedAuctionHistoryTab.refresh / load_more](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L277-L321); [streaming_manager/db/auction_session.py строки 1037–1061 — AuctionSessionMixin.list_completed_auction_sessions](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1037-L1061).

### HIST-005 Сводные счётчики закрытых аукционов

**Состояние:** Доступно по коду.

По текущему поиску и периоду показывает: Закрыто аукционов, С победителем, Отменено, Без победителя. Счётчики охватывают всю подходящую выборку, а не только подгруженные 50 строк. Legacy finished входит в общее число, но не добавляется автоматически ни к confirmed, ни к cancelled/no_winner.

**Доступ:** «История аукционов» → показатели над таблицей.

**Код:** [streaming_manager/views/completed_auction_history.py строки 87–96 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L87-L96); [streaming_manager/views/completed_auction_history.py строки 284–289 — CompletedAuctionHistoryTab._refresh_summary](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L284-L289); [streaming_manager/db/auction_session.py строки 1071–1099 — AuctionSessionMixin.completed_auction_summary](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1071-L1099).

### HIST-006 Общие сведения и фактически пройденный режим

**Состояние:** Доступно по коду.

Выбор аукциона открывает «Общие»: ID, имя, режим, статус, локальные время начала/завершения и подтверждённого победителя. Режим выводится из реально записанных wheel-событий и immutable snapshots: максимальная сумма, колесо при ничьей, обычное колесо, выбывание либо цепочка сменявшихся форматов. При отсутствии фактических spins используется сохранённый выбранный формат/режим.

**Доступ:** «История аукционов» → выбрать строку → «Общие».

**Код:** [streaming_manager/views/completed_auction_history.py строки 119–135 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L119-L135); [streaming_manager/views/completed_auction_history.py строки 544–559 — CompletedAuctionHistoryTab._load_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L544-L559); [streaming_manager/views/auction_history.py строки 14–105 — format_completed_auction_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_history.py#L14-L105); [streaming_manager/db/auction_session.py строки 973–1022 — AuctionSessionMixin._completed_auction_mode_evidence_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L973-L1022).

### HIST-007 Исторический состав и итог каждого лота

**Состояние:** Доступно по коду.

Вкладка «Лоты» показывает стартовую позицию, snapshot-название, баллы на старте, добавленные баллы, итог и результат. Результаты: Победитель, Не победил, Ничья, Выбран на выбывание, Выбыл → архив, пусто. Данные берутся из сохранённых auction_entries, не из текущей карточки; removed-лоты исключаются, порядок — стартовая позиция и ID. Массовая очистка игр сохраняет этот архив, одиночное удаление игры может удалить связанные entries.

**Доступ:** «История аукционов» → выбрать аукцион → «Лоты».

**Код:** [streaming_manager/views/completed_auction_history.py строки 26–33 — RESULT_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L26-L33); [streaming_manager/views/completed_auction_history.py строки 137–148 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L137-L148); [streaming_manager/views/completed_auction_history.py строки 561–577 — CompletedAuctionHistoryTab._load_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L561-L577); [streaming_manager/db/auction_session.py строки 1111–1124 — AuctionSessionMixin.completed_auction_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1111-L1124); [streaming_manager/db/games.py строки 230–235 — GamesMixin.delete_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L230-L235); [streaming_manager/db/games.py строки 404–452 — GamesMixin.clear_all_games](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L404-L452).

### HIST-008 Лента событий выбранного аукциона

**Состояние:** Доступно по коду.

«События» показывает хронологическую ленту из общего change_log: ставки, уменьшения, новые/удалённые/исключённые/переименованные лоты, таймер, автопродление, ничья, выбор и смена формата колеса, раунды, остановка/повтор, коррекции после 00:00, подтверждение, отмена. Короткое локальное время включено в строку, точное время и change_log ID доступны в подсказке. Действия из ленты не выполняются.

**Доступ:** «История аукционов» → выбрать аукцион → «События».

**Код:** [streaming_manager/views/completed_auction_history.py строки 150–152 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L150-L152); [streaming_manager/views/completed_auction_history.py строки 579–585 — CompletedAuctionHistoryTab._load_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L579-L585); [streaming_manager/db/auction_session.py строки 579–724 — AuctionSessionMixin.list_auction_history_events](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L579-L724); [streaming_manager/views/auction_history.py строки 136–441 — format_auction_history_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_history.py#L136-L441).

### HIST-009 Проверочные снимки реальных вращений и выбор раунда

**Состояние:** При условиях.

«Проверка результата» появляется только при наличии сохранённого spin-snapshot или wheel-события, а не просто выбранного режима/запущенной анимации. У каждого реального вращения свой snapshot. Можно выбрать раунд; по умолчанию показывается последний. Отображаются Run ID, алгоритм, RNG, время, случайное значение, число участников, сохранённый победитель/выбывший и результат пересчёта. Если есть wheel-факт, но snapshot отсутствует, показано «Невозможно проверить», прошлые входные данные не восстанавливаются.

**Доступ:** «История аукционов» → аукцион с фактическим вращением → «Проверка результата» → «Раунд».

**Условия и границы:** Для точной проверки необходим snapshot выбранного вращения; старые аукционы могут его не иметь.

**Код:** [streaming_manager/views/completed_auction_history.py строки 154–216 — CompletedAuctionHistoryTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L154-L216); [streaming_manager/views/completed_auction_history.py строки 362–448 — CompletedAuctionHistoryTab._load_verification_details / _verification_spin_changed / _render_verification_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L362-L448); [streaming_manager/views/completed_auction_history.py строки 587–600 — CompletedAuctionHistoryTab._load_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L587-L600); [streaming_manager/db/wheel.py строки 557–582 — WheelMixin.list_wheel_verification_snapshots](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L557-L582).

### HIST-010 Детерминированная проверка сохранённого результата

**Состояние:** При условиях.

«Проверить результат» пересчитывает выбранный snapshot без нового RNG, сети и записей в базу. Проверяет поддерживаемую версию алгоритма, последовательность участников, неотрицательные веса, сумму, equal-fallback, эффективные веса, непрерывные интервалы, диапазон RNG и попадание значения в интервал; затем сравнивает ID и snapshot-название результата. Выводит «Совпадает», «НЕ СОВПАДАЕТ» с ожидаемым результатом либо «Невозможно проверить» с причиной отсутствующих/повреждённых данных или неподдерживаемого алгоритма.

**Доступ:** «История аукционов» → «Проверка результата» → «Проверить результат».

**Условия и границы:** Кнопка видна, когда загружен snapshot; локальный пересчёт не является повторной сетевой проверкой подписи RANDOM.ORG.

**Код:** [streaming_manager/views/completed_auction_history.py строки 443–448 — CompletedAuctionHistoryTab._render_verification_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L443-L448); [streaming_manager/views/completed_auction_history.py строки 472–501 — CompletedAuctionHistoryTab._verify_selected_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L472-L501); [streaming_manager/db/wheel.py строки 697–805 — WheelMixin.verify_wheel_result](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L697-L805).

### HIST-011 Подробные проверочные данные всех раундов

**Состояние:** При условиях.

Открывает текстовое окно только для чтения со всеми сохранёнными snapshots аукциона. Для каждого: раунд, Run ID, алгоритм, режим/RNG, локальное и точное время, значение и диапазон RNG, сумма исходных весов, equal-fallback, результат, математический порядок участников, исходный/эффективный вес, шанс с двумя десятичными знаками и полуоткрытый интервал каждого участника. Для RANDOM.ORG+ также ticket, serial, сохранённый статус подписи, signature и random JSON.

**Доступ:** «История аукционов» → «Проверка результата» → «Подробные данные».

**Условия и границы:** Нужен хотя бы один сохранённый snapshot; окно не содержит отдельной кнопки экспорта/публикации.

**Код:** [streaming_manager/views/completed_auction_history.py строки 503–513 — CompletedAuctionHistoryTab._show_verification_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L503-L513); [streaming_manager/views/winner_verification.py строки 21–71 — _percent / format_verification_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/winner_verification.py#L21-L71); [streaming_manager/views/winner_verification.py строки 108–120 — show_readonly_text_dialog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/winner_verification.py#L108-L120).

### HIST-012 Переход к официальной проверке RANDOM.ORG+

**Состояние:** При условиях.

Для сохранённого random_org_plus-snapshot показывает Ticket ID и известный статус подписи (подтверждена/не подтверждена/неизвестен). Если сохранены random JSON и signature, появляется «Открыть проверку RANDOM.ORG»: собирает ссылку из доказательства и открывает её в системном браузере; отсутствие/невалидность доказательства выдаёт ошибку.

**Доступ:** «История аукционов» → «Проверка результата» → «Открыть проверку RANDOM.ORG».

**Условия и границы:** Только RNG random_org_plus с сохранёнными rng_random_json и rng_signature; открытие внешней страницы требует соответствующей доступности браузера/сервиса.

**Код:** [streaming_manager/views/completed_auction_history.py строки 450–470 — CompletedAuctionHistoryTab._render_verification_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L450-L470); [streaming_manager/views/completed_auction_history.py строки 515–542 — CompletedAuctionHistoryTab._open_verification_random_org](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L515-L542).

## Журнал изменений и событий

### JRN-001 Просмотр общего журнала изменений и событий

**Состояние:** Доступно по коду.

Только для чтения показывает ВРЕМЯ, ОБЪЕКТ, ID, ДЕЙСТВИЕ, ПОДРОБНОСТИ. Без поиска загружает последние 500 change_log-записей в порядке новых ID сверху; время представлено в локальном часовом поясе, полные подробности доступны в подсказке. Включает игры, список, аукционы, ставки, настройки, интеграции, конвертацию и совместный Excel.

**Доступ:** Главная вкладка «Журнал».

**Код:** [streaming_manager/views/main_window.py строки 228–229 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L228-L229); [streaming_manager/views/main_window.py строки 265–266 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L265-L266); [streaming_manager/views/log.py строки 22–49 — LogTableModel](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L22-L49); [streaming_manager/views/log.py строки 84–104 — LogTab.ENTITY_LABELS / ACTION_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L84-L104); [streaming_manager/views/log.py строки 127–169 — LogTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L127-L169); [streaming_manager/db/services.py строки 114–138 — ServicesMixin.list_log](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L114-L138); [streaming_manager/db/common.py строки 189–199 — display_datetime_local](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L189-L199).

### JRN-002 Читаемая история создания, удаления и изменения полей игры

**Состояние:** Доступно по коду.

Для создания/удаления показывает название и смысл операции. При обновлении перечисляет изменившиеся поля «старое → новое»: название, дата, баллы, кооператив, статус, отзыв, архив; значения дат, статусов, кооператива и архива форматируются для пользователя. Одиночное удаление предварительно очищает подробные старые game-записи и оставляет только факт удаления.

**Доступ:** «Журнал» → строки объекта «Игра».

**Код:** [streaming_manager/views/log.py строки 73–82 — LogTab.FIELD_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L73-L82); [streaming_manager/views/log.py строки 172–183 — LogTab._format_value](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L172-L183); [streaming_manager/views/log.py строки 362–377 — LogTab._details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L362-L377); [streaming_manager/db/games.py строки 224–246 — GamesMixin.delete_game](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L224-L246).

### JRN-003 Русское представление событий аукциона

**Состояние:** Доступно по коду.

Строки аукциона, лотов и ставок используют общий formatter истории: запуск/пауза/продолжение, правки и автопродление таймера, ставки и уменьшения, создание/удаление лотов, приём ставок завершён, ничья/тай-брейк, колесо и раунды выбывания, остановка/повтор анимации, коррекции после 00:00, подтверждение и отмена. Для неизвестных кодов сохранён технический fallback; это просмотр факта, а не действие из журнала.

**Доступ:** «Журнал» → строки «Аукцион», «Лот аукциона», «Ставка».

**Код:** [streaming_manager/views/log.py строки 379–412 — LogTab._auction_presentation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L379-L412); [streaming_manager/views/log.py строки 424–439 — LogTab._load_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L424-L439); [streaming_manager/views/auction_history.py строки 136–441 — format_auction_history_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_history.py#L136-L441).

### JRN-004 История поступлений подключённых интеграций

**Состояние:** При условиях.

По записи integration_event показывает источник Twitch/DonationAlerts, отправителя или «Аноним», исходную сумму и единицу, целевой/сгенерированный лот, идентификатор внешнего события. Различает начислено (в аукцион или основной список), ожидание курса/применения, отклонено оператором и неприменимо с причиной; для принятого события показывает начисленные баллы. Представление использует нормализованные поля, а не произвольный сырой provider payload.

**Доступ:** «Журнал» → объект «Интеграция».

**Условия и границы:** Строки появляются при наличии соответствующих сохранённых событий интеграций.

**Код:** [streaming_manager/views/log.py строки 105–112 — LogTab.INTEGRATION_ACTION_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L105-L112); [streaming_manager/views/log.py строки 185–297 — LogTab._integration_event_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L185-L297); [streaming_manager/db/services.py строки 121–130 — ServicesMixin.list_log](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L121-L130).

### JRN-005 Просмотр изменений настроек и конвертации

**Состояние:** Доступно по коду.

У настроек отображает ключ и старое/новое значение; секретные ключи скрывает как [СКРЫТО], включая legacy-записи. Для external_conversion выводит известные поля: источник, сумма, единица, ID игры, аукцион, статус. Прочие объекты, например общий Excel, имеют общий вывод сохранённых сведений; полного перевода всех технических полей нет.

**Доступ:** «Журнал» → объекты «Настройка», «Конвертация», «Общий Excel».

**Код:** [streaming_manager/views/log.py строки 314–360 — LogTab._details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L314-L360); [streaming_manager/db/services.py строки 83–96 — _setting_key_is_secret / _setting_audit_value](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L83-L96).

### JRN-006 Поиск по всему журналу

**Состояние:** Доступно по коду.

Непустой запрос снимает обычное ограничение 500 строк и ищет во всей change_log-истории: по показанным времени/объекту/ID/действию/подробностям и оригинальным entity/action/JSON/timestamp. Сопоставление — casefold-подстрока; ввод задерживается на 250 мс, устаревший результат фоновой загрузки не подменяет новый. Очистка запроса возвращает последние 500 строк.

**Доступ:** «Журнал» → «Поиск в журнале…».

**Код:** [streaming_manager/views/log.py строки 133–145 — LogTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L133-L145); [streaming_manager/views/log.py строки 414–467 — LogTab._load_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L414-L467); [streaming_manager/views/log.py строки 469–497 — LogTab._search_text_changed / refresh / _apply_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L469-L497); [streaming_manager/db/services.py строки 114–138 — ServicesMixin.list_log](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L114-L138).

## Виджеты OBS и их оформление

### OBS-001 Семь отдельных источников OBS

**Состояние:** Доступно по коду.

Главный оверлей, список игр, таймер, музыкальный плеер, колесо, список лотов и правила имеют собственные URL, кнопки копирования и браузерного предпросмотра.

**Доступ:** Стрим / OBS → соответствующий блок

**Условия и границы:** Локальный HTTP-сервер приложения должен работать.

**Код:** [streaming_manager/views/stream.py строки 202–226 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L202-L226); [streaming_manager/views/stream.py строки 546–559 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L546-L559); [streaming_manager/views/stream.py строки 583–596 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L583-L596); [streaming_manager/views/stream.py строки 706–719 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L706-L719); [streaming_manager/views/stream.py строки 892–909 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L892-L909); [streaming_manager/views/stream.py строки 951–964 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L951-L964); [streaming_manager/views/stream.py строки 1131–1171 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1131-L1171).

### OBS-002 Справка по добавлению виджета в OBS

**Состояние:** Доступно по коду.

Встроенная инструкция проводит через создание источника «Браузер», вставку URL, выбор размеров и расположение на сцене. Объясняет обновление после сохранения и работу звука через соответствующий Browser Source.

**Доступ:** Стрим / OBS → Как добавить виджет в OBS

**Код:** [streaming_manager/views/stream.py строки 1392–1410 — StreamTab._show_obs_widget_help](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1392-L1410).

### OBS-003 Предпросмотр скрытых виджетов

**Состояние:** Доступно по коду.

Параметр preview=1 показывает самостоятельный виджет даже при сохранённом режиме «Не показывать» или отсутствии контекста колеса. До первого ответа API обычный источник скрыт, чтобы не мигало ранее сохранённое содержимое.

**Доступ:** Кнопки предпросмотра; URL виджета с ?preview=1

**Условия и границы:** Это переопределение общей политики источника; отключённые внутренние блоки главного оверлея сохраняют своё состояние.

**Код:** [streaming_manager/web/obs_visibility.js строки 4–29 — ObsVisibility](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/obs_visibility.js#L4-L29); [streaming_manager/views/stream.py строки 1560–1574 — StreamTab.open_list_overlay_preview](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1560-L1574).

### OBS-004 Режимы показа и их область действия

**Состояние:** Доступно по коду.

Для списка, таймера, лотов и правил доступны «Не показывать» и «Показывать постоянно». Один режим списка управляет и самостоятельным списком, и его блоком внутри главного оверлея. Скрытие меняет прозрачность и события указателя, а опрос данных и звук продолжают жить по логике виджета.

**Доступ:** Стрим / OBS → Показ виджета → Сохранить

**Код:** [streaming_manager/obs_visibility.py строки 38–71 — WIDGETS / show_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L38-L71); [streaming_manager/web/obs_visibility.js строки 1–23 — ObsVisibility](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/obs_visibility.js#L1-L23); [streaming_manager/views/stream.py строки 410–415 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L410-L415); [streaming_manager/db/services.py строки 2486–2491 — ServicesMixin.current_stream_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2486-L2491).

### OBS-005 Выбор текущей игры

**Состояние:** Доступно по коду.

Можно явно выбрать игру либо использовать автоматический выбор первой игры со статусом «ПРОХОДИТСЯ». Название выводится над игровой рамкой; если подходящей игры нет, виден текст «Нет текущей игры».

**Доступ:** Стрим / OBS → Главный оверлей → Текущая игра → Сохранить

**Код:** [streaming_manager/views/stream.py строки 2447–2455 — StreamTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2447-L2455); [streaming_manager/db/services.py строки 2380–2386 — ServicesMixin.current_stream_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2380-L2386); [streaming_manager/web/overlay.html строки 1008–1017 — renderGame](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L1008-L1017).

### OBS-006 Игровая рамка и прозрачные области

**Состояние:** Доступно по коду.

Выбор формата 16:9 или 4:3 меняет размер игровой рамки с учётом занятых боковых колонок и высоты заголовка. Полотно масштабируется пропорционально окну Browser Source; игровые и камерные вырезы открывают расположенные под оверлеем источники OBS.

**Доступ:** Стрим / OBS → Игровое окно → Формат

**Код:** [streaming_manager/constants.py строки 269–269 — STREAM_FORMATS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py#L269-L269); [streaming_manager/web/overlay.html строки 292–318 — overlay backdrop mask](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L292-L318); [streaming_manager/web/overlay.html строки 415–418 — scaleOverlay](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L415-L418); [streaming_manager/web/overlay.html строки 692–740 — applyGameFrame](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L692-L740); [streaming_manager/views/stream.py строки 504–510 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L504-L510).

### OBS-007 Информационный блок

**Состояние:** Доступно по коду.

Вводится отдельный текст, включается или полностью убирается информационная панель. Скрытый текст сохраняется; другие блоки занимают освободившееся место. Положение, шрифт и контур настраиваются отдельно.

**Доступ:** Стрим / OBS → Информационный блок

**Код:** [streaming_manager/views/stream.py строки 264–276 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L264-L276); [streaming_manager/views/stream.py строки 2353–2361 — StreamTab._update_info_enabled_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2353-L2361); [streaming_manager/views/stream.py строки 2773–2777 — StreamTab.save](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2773-L2777); [streaming_manager/web/overlay.html строки 754–773 — applyOverlayLayout](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L754-L773).

### OBS-008 Камерная рамка

**Состояние:** Доступно по коду.

Камерный вырез можно включить или выключить и разместить в любом из четырёх углов. При выключении настройки положения и контура камеры скрываются. Это рамка для отдельного источника OBS, а не захват камеры приложением.

**Доступ:** Стрим / OBS → Веб-камера

**Код:** [streaming_manager/views/stream.py строки 420–432 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L420-L432); [streaming_manager/views/stream.py строки 2370–2375 — StreamTab._update_main_overlay_conditional_visibility](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2370-L2375); [streaming_manager/web/overlay.html строки 339–342 — webcam-frame](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L339-L342); [streaming_manager/web/overlay.html строки 765–777 — applyOverlayLayout](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L765-L777).

### OBS-009 Автоматическое и ручное размещение боковых блоков

**Состояние:** Доступно по коду.

Список размещается слева, справа или автоматически за камерой. Информационный блок поддерживает четыре угла и автоматическое размещение. Автоматический список следует стороне камеры; информационный блок при нижней камере ставится над ней.

**Доступ:** Стрим / OBS → Список → Положение списка; Информационный блок → Положение

**Код:** [streaming_manager/views/stream.py строки 434–452 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L434-L452); [streaming_manager/web/overlay.html строки 742–812 — applyOverlayLayout](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L742-L812).

### OBS-010 Цвета светящихся рамок

**Состояние:** Доступно по коду.

Игровая рамка, камера, список и информационный блок имеют независимые цвета контура. Цвет выбирается в диалоге или экранной пипеткой; для отключённых блоков их цветовые настройки скрываются.

**Доступ:** Стрим / OBS → соответствующий блок → Рамка

**Код:** [streaming_manager/views/stream.py строки 454–502 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L454-L502); [streaming_manager/views/stream.py строки 2387–2400 — StreamTab._update_main_overlay_conditional_visibility](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2387-L2400); [streaming_manager/web/overlay.html строки 613–624 — applyFrameColors](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L613-L624).

### OBS-011 Раздельная типографика главного оверлея и списка

**Состояние:** Доступно по коду.

Для заголовка текущей игры, Top-1, Top-2, Top-3, прокручиваемой части списка и информационного текста отдельно выбираются семейство, размер 8–96 px и цвет с палитрой или пипеткой.

**Доступ:** Стрим / OBS → текущая игра / Список / Информационный блок

**Код:** [streaming_manager/views/stream.py строки 289–292 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L289-L292); [streaming_manager/views/stream.py строки 528–539 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L528-L539); [streaming_manager/views/stream.py строки 574–578 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L574-L578); [streaming_manager/views/stream.py строки 2117–2124 — StreamTab._add_typography_row](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2117-L2124); [streaming_manager/views/stream.py строки 2190–2204 — StreamTab._add_typography_row](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2190-L2204).

### OBS-012 Top-3 и бесконечный список игр

**Состояние:** Доступно по коду.

Список показывает названия и баллы игр, допущенных к аукциону из общего списка: три первых места закреплены сверху, начиная с четвёртого работает автоматическая циклическая прокрутка. Источник берёт актуальные данные из /api/data.

**Доступ:** Список внутри главного оверлея и отдельный /list-overlay

**Код:** [streaming_manager/db/services.py строки 2433–2436 — ServicesMixin.current_stream_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2433-L2436); [streaming_manager/web/overlay.html строки 900–947 — renderList](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L900-L947); [streaming_manager/web/overlay.html строки 984–1005 — rebuildInfiniteScroll](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L984-L1005); [streaming_manager/web/overlay.html строки 1030–1036 — update](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L1030-L1036).

### OBS-013 Самостоятельный оверлей списка

**Состояние:** Доступно по коду.

Отдельный Browser Source содержит только Top-3 и прокручиваемый список на полупрозрачной панели. Наследует шрифты, цвет контура и режим показа списка; при изменении данных сохраняет относительную позицию прокрутки. URL и предпросмотр доступны также из списка игр.

**Доступ:** Стрим / OBS → Список; Список игр → кнопки URL и предпросмотра

**Код:** [streaming_manager/web/list_overlay.html строки 16–41 — list panel CSS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/list_overlay.html#L16-L41); [streaming_manager/web/list_overlay.html строки 233–268 — renderRows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/list_overlay.html#L233-L268); [streaming_manager/web/list_overlay.html строки 300–324 — rebuildInfiniteScroll / update](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/list_overlay.html#L300-L324); [streaming_manager/views/main_window.py строки 210–217 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L210-L217).

### OBS-014 Добавление файлов фона

**Состояние:** Доступно по коду.

Фоны добавляются в общую библиотеку через выбор одного или нескольких файлов. Главный оверлей, таймер и лоты принимают PNG, JPG, JPEG, WEBP, GIF, MP4, WEBM. Выбранный фон применяется сохранением соответствующего виджета.

**Доступ:** Стрим / OBS → Фон оверлея / таймер / лоты → Добавить фон…

**Код:** [streaming_manager/media.py строки 26–29 — MEDIA_CATEGORY_EXTENSIONS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/media.py#L26-L29); [streaming_manager/views/stream.py строки 1889–1942 — StreamTab._import_background_media_for](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1889-L1942); [streaming_manager/views/stream.py строки 1944–1970 — StreamTab._import_background_media_for](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1944-L1970).

### OBS-015 Копия фона или ссылка на исходный файл

**Состояние:** Доступно по коду.

При добавлении выбирается управляемая копия в data/overlay_backgrounds либо зарегистрированная ссылка на оригинал. Оригинал не изменяется; OBS получает локальный URL по идентификатору, а не абсолютный путь.

**Доступ:** Добавить фон… → Копировать в программу / Использовать исходный файл

**Код:** [streaming_manager/views/stream.py строки 1833–1867 — StreamTab._choose_background_storage_mode](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1833-L1867); [streaming_manager/views/stream.py строки 2042–2061 — StreamTab._apply_background_import](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2042-L2061); [streaming_manager/db/services.py строки 2492–2508 — ServicesMixin.current_stream_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2492-L2508).

### OBS-016 Пакетное добавление и повторные имена фонов

**Состояние:** Доступно по коду.

Пакет использует общий выбор способа хранения, добавляет допустимые файлы, сообщает о пропусках и выбирает последний успешно добавленный фон. Совпадающее имя повторно использует существующую запись; недоступную внешнюю ссылку можно восстановить повторным добавлением файла с тем же именем.

**Доступ:** Добавить фон… → выбрать несколько файлов

**Код:** [streaming_manager/views/stream.py строки 1972–2006 — StreamTab._continue_background_import_batch](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1972-L2006); [streaming_manager/views/stream.py строки 2026–2069 — StreamTab._apply_background_import](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2026-L2069); [streaming_manager/views/stream.py строки 1671–1683 — StreamTab._select_imported_background](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1671-L1683).

### OBS-017 Проверка доступности фонов

**Состояние:** Доступно по коду.

Селекторы общей библиотеки показывают доступные файлы; главный блок отдельно показывает источник и состояние. Отсутствующий выбранный фон главного оверлея сбрасывается при обновлении вкладки. Без доступного медиа браузер использует штатную подложку или прозрачный фон соответствующего виджета.

**Доступ:** Стрим / OBS → Фон оверлея → Источник / Состояние / Фон

**Код:** [streaming_manager/views/stream.py строки 352–361 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L352-L361); [streaming_manager/views/stream.py строки 1580–1593 — StreamTab._background_assets](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1580-L1593); [streaming_manager/views/stream.py строки 2489–2494 — StreamTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2489-L2494); [streaming_manager/web/overlay.html строки 535–560 — applyBackgroundMedia](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L535-L560); [streaming_manager/web/timer_overlay.html строки 239–257 — applyPresentation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html#L239-L257).

### OBS-018 Режимы отображения фона главного оверлея

**Состояние:** Доступно по коду.

Фон можно растянуть, вписать, заполнить или оставить по центру. GIF показывается как анимация, видео воспроизводится циклически без звука; маска сохраняет прозрачные вырезы игры и камеры.

**Доступ:** Стрим / OBS → Фон оверлея → Режим отображения

**Код:** [streaming_manager/views/stream.py строки 363–379 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L363-L379); [streaming_manager/web/overlay.html строки 292–318 — background media mask](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L292-L318); [streaming_manager/web/overlay.html строки 535–568 — applyBackgroundMedia](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L535-L568).

### OBS-019 Сохранение настроек по блокам

**Состояние:** Доступно по коду.

Кнопки «Сохранить» в разделах главного оверлея вызывают один общий обработчик и сохраняют все текущие поля главного оверлея. У таймера, плеера, колеса, лотов и правил собственные сохранения; правила здесь сохраняют только глобальный режим показа.

**Доступ:** Стрим / OBS → Сохранить соответствующего блока

**Код:** [streaming_manager/views/stream.py строки 235–245 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L235-L245); [streaming_manager/views/stream.py строки 2760–2802 — StreamTab.save](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2760-L2802); [streaming_manager/views/stream.py строки 1531–1557 — StreamTab._save_rules_overlay_settings / _save_wheel_overlay_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1531-L1557).

### OBS-020 Отдельный точный таймер аукциона и колеса

**Состояние:** Доступно по коду.

Виджет показывает часы, минуты, секунды и миллисекунды, отражает запуск, паузу, возобновление и подготовительную фазу действующего таймера. До старта показывает сохранённую длительность выбранного режима; для вращения отображает таймер колеса. Размер текста автоматически уменьшается, если источник слишком мал.

**Доступ:** /timer-overlay; настройки в Стрим / OBS → Виджет таймера

**Код:** [streaming_manager/db/services.py строки 1941–1995 — ServicesMixin.current_timer_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1941-L1995); [streaming_manager/web/timer_overlay.html строки 169–190 — formatMilliseconds / currentRemaining](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html#L169-L190); [streaming_manager/web/timer_overlay.html строки 208–220 — fitTimer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html#L208-L220).

### OBS-021 Шрифт и фон таймера

**Состояние:** Доступно по коду.

Для таймера задаются шрифт, размер 8–300 px, цвет текста, прозрачный/цветной/собственный медиафон. Цвета доступны через палитру и пипетку; фоновое видео беззвучно и зациклено.

**Доступ:** Стрим / OBS → Виджет таймера

**Код:** [streaming_manager/views/stream.py строки 598–671 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L598-L671); [streaming_manager/web/timer_overlay.html строки 104–106 — timer background elements](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html#L104-L106); [streaming_manager/views/stream.py строки 1249–1273 — StreamTab._save_timer_overlay_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1249-L1273).

### OBS-022 Список лотов с актуальными позициями

**Состояние:** Доступно по коду.

Отдельный виджет показывает текущие лоты, названия и баллы. До старта берёт допущенные игры; в сессии берёт её записи. Для Max Amount после начала показываются «СТАРТ» и «ТЕКУЩАЯ», для прямого колеса — одна позиция до прогресса исключения, затем две.

**Доступ:** /auction-lots-overlay; Стрим / OBS → Виджет списка лотов

**Код:** [streaming_manager/db/services.py строки 2133–2183 — ServicesMixin.current_auction_lots_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2133-L2183); [streaming_manager/position_policy.py строки 15–50 — position_columns_for_surface](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/position_policy.py#L15-L50); [streaming_manager/web/auction_lots_overlay.html строки 359–408 — renderRows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L359-L408).

### OBS-023 Шансы и общая сумма в оверлее лотов

**Состояние:** Доступно по коду.

В режиме колеса можно показывать дополнительную колонку вероятности. По отдельному флагу внизу виджета выводится «Всего баллов в аукционе» из общего итога сессии, включая неактивную историю и исключая удалённые записи; итог не пересчитывается по видимой части таблицы.

**Доступ:** Аукцион → Показывать шанс в колесе / Показать сумму в оверлее

**Условия и границы:** Колонка шанса доступна только для weighted_wheel.

**Код:** [streaming_manager/views/auction.py строки 831–836 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L831-L836); [streaming_manager/views/auction.py строки 868–875 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L868-L875); [streaming_manager/views/auction.py строки 2117–2121 — AuctionTab._set_auction_overlay_total_visible](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L2117-L2121); [streaming_manager/db/services.py строки 2185–2225 — ServicesMixin.current_auction_lots_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2185-L2225); [streaming_manager/web/auction_lots_overlay.html строки 530–540 — renderFooter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L530-L540).

### OBS-024 Управляемая автопрокрутка лотов

**Состояние:** Доступно по коду.

Включается отдельной кнопкой аукциона, сохраняется между перезапусками и относится только к OBS-списку. Переполненный список движется вниз и вверх со скоростью 25 px/с; локальная таблица остаётся с ручной прокруткой.

**Доступ:** Аукцион → Автопрокрутка оверлея: ВКЛ/ВЫКЛ

**Код:** [streaming_manager/views/auction.py строки 838–845 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L838-L845); [streaming_manager/views/auction_parts/search.py строки 101–112 — AuctionSearchMixin._set_lot_overlay_auto_scroll](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/search.py#L101-L112); [streaming_manager/web/auction_lots_overlay.html строки 215–217 — overlay constants](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L215-L217); [streaming_manager/web/auction_lots_overlay.html строки 543–564 — scrollFrame](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L543-L564).

### OBS-025 Оформление списка лотов

**Состояние:** Доступно по коду.

Настраиваются основной шрифт 8–160 px и цвет, прозрачный/цветной/свой медиафон, цвет и непрозрачность 0–100% контейнера, строк и заголовков, цвета контуров, отдельный шрифт заголовков 8–160 px и его цвет. Поля цветов поддерживают пипетку.

**Доступ:** Стрим / OBS → Виджет списка лотов

**Код:** [streaming_manager/views/stream.py строки 966–1039 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L966-L1039); [streaming_manager/views/stream.py строки 1043–1109 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1043-L1109); [streaming_manager/web/auction_lots_overlay.html строки 421–494 — applyPresentation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L421-L494).

### OBS-026 OBS-зеркало колеса и результата

**Состояние:** Доступно по коду.

Виджет рисует сектора с весами, вращение и стрелку по состоянию приложения. После завершения показывает «Победитель» или «Выбывает» и доступную вероятность результата. Центр поддерживает тот же выбранный локальный медиаактив; при отсутствии пользовательского изображения служит встроенная иконка.

**Доступ:** /wheel-overlay; Стрим / OBS → Виджет колеса; Аукцион → кнопки колеса

**Условия и границы:** Состояние результата выбирается в приложении; браузерный рендер не определяет победителя.

**Код:** [streaming_manager/web/wheel_overlay.html строки 222–247 — syncCenterImage](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html#L222-L247); [streaming_manager/web/wheel_overlay.html строки 265–342 — draw](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html#L265-L342); [streaming_manager/views/main_window.py строки 198–203 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L198-L203).

### OBS-027 Контекст и оформление виджета колеса

**Состояние:** Доступно по коду.

Доступны скрытие, постоянный показ и «Когда колесо используется». Контекст активен для выбранного прямого колеса либо сессии колеса, ожидания колеса или существующего вращения. Включаются цветной светящийся контур и название текущего лота под стрелкой во время вращения, одинаково для программы и OBS.

**Доступ:** Стрим / OBS → Виджет колеса → Показ / Контур / Текущий лот под стрелкой

**Код:** [streaming_manager/obs_visibility.py строки 48–50 — WIDGETS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L48-L50); [streaming_manager/obs_visibility.py строки 98–108 — wheel_context_relevant](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L98-L108); [streaming_manager/views/stream.py строки 906–945 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L906-L945); [streaming_manager/web/wheel_overlay.html строки 313–332 — draw](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html#L313-L332).

### OBS-028 Карточка музыкального плеера

**Состояние:** Доступно по коду.

Виджет показывает обложку, название исполнителя/трека либо имя файла и частотный спектр. При отсутствии обложки используется встроенная заглушка; длинный заголовок прокручивается. В предпросмотре без воспроизведения показывается пример заголовка.

**Доступ:** /music-player-overlay; Стрим / OBS → Виджет музыкального плеера; Музыка → предпросмотр

**Код:** [streaming_manager/web/music_player_overlay.html строки 437–495 — updateCover / updateTitle](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L437-L495); [streaming_manager/web/music_player_overlay.html строки 654–661 — poll](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L654-L661); [streaming_manager/views/main_window.py строки 192–197 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L192-L197).

### OBS-029 Цвета и типографика музыкального виджета

**Состояние:** Доступно по коду.

Выбираются шрифт 8–200 px, цвет названия, прозрачный или цветной фон, цвета рамки и визуализатора. Автоподбор по обложке заменяет цвета фона и рамки, оставляя текст и спектр пользовательскими; без пригодной обложки возвращаются ручные цвета.

**Доступ:** Стрим / OBS → Виджет музыкального плеера

**Код:** [streaming_manager/views/stream.py строки 721–842 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L721-L842); [streaming_manager/views/stream.py строки 1299–1315 — StreamTab._update_music_player_overlay_enabled_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1299-L1315); [streaming_manager/web/music_player_overlay.html строки 347–435 — applyAppearance / applyAutoColorsIfPossible](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L347-L435).

### OBS-030 Показ музыкального виджета при смене трека

**Состояние:** Доступно по коду.

Доступны «Не показывать», «При смене трека» и «Показывать постоянно». Для смены трека задаётся длительность 1–120 с; браузер использует время события, поэтому перезагрузка не запускает старое появление заново. В обычном источнике карточка скрывается при остановке или подавлении плеера.

**Доступ:** Стрим / OBS → Виджет музыкального плеера → Показ / Время показа

**Код:** [streaming_manager/obs_visibility.py строки 42–45 — WIDGETS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L42-L45); [streaming_manager/views/stream.py строки 848–856 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L848-L856); [streaming_manager/web/music_player_overlay.html строки 574–601 — evaluateVisibility](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L574-L601); [streaming_manager/views/stream.py строки 1317–1321 — StreamTab._update_music_player_overlay_enabled_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1317-L1321).

### OBS-031 Анимация музыкального виджета

**Состояние:** Доступно по коду.

Для появления доступны проявление и выезд. У выезда выбирается направление слева, справа, сверху или снизу; при скрытом виджете анимационные настройки прячутся, направление видно только для выезда.

**Доступ:** Стрим / OBS → Виджет музыкального плеера → Анимация / Направление

**Код:** [streaming_manager/views/stream.py строки 858–871 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L858-L871); [streaming_manager/views/stream.py строки 1317–1330 — StreamTab._update_music_player_overlay_enabled_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1317-L1330); [streaming_manager/web/music_player_overlay.html строки 512–557 — applyAppearanceStateTransition](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L512-L557).

### OBS-032 Частотный спектр и беззвучный предпросмотр плеера

**Состояние:** При условиях.

Визуализатор получает реальные частотные данные проигрываемого трека через WebAudio, а при отсутствии сигнала рисует ровные низкие столбики. Если браузер блокирует анализ до действия пользователя, виджет предлагает включить музыку и нажать на предпросмотр. Сам предпросмотр остаётся беззвучным.

**Доступ:** Музыка / Стрим / OBS → предпросмотр музыкального плеера

**Условия и границы:** Для движущегося спектра нужен проигрываемый трек и разрешённый браузером WebAudio.

**Код:** [streaming_manager/web/music_player_overlay.html строки 188–196 — setSpectrumUnlockRequired](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L188-L196); [streaming_manager/web/music_player_overlay.html строки 251–260 — setAudioGain](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L251-L260); [streaming_manager/web/music_player_overlay.html строки 609–639 — drawSpectrum](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L609-L639); [streaming_manager/web/music_player_overlay.html строки 686–693 — spectrum unlock handlers](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L686-L693).

### OBS-033 Рабочий виджет правил

**Состояние:** Доступно по коду.

Рабочий URL показывает правила и оформление снимка открытого аукциона; без открытой сессии — активного шаблона. Пустой сохранённый текст скрывает содержимое рабочего источника; предпросмотр использует демонстрационный текст. Глобальный показ сохраняется в OBS, текст и оформление — в редакторе правил.

**Доступ:** Стрим / OBS → Виджет правил; Аукцион → Правила аукциона

**Код:** [streaming_manager/views/stream.py строки 1131–1171 — StreamTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L1131-L1171); [streaming_manager/db/rules.py строки 675–689 — RulesMixin.current_rules_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L675-L689); [streaming_manager/web/rules_overlay.html строки 153–165 — applyPayload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L153-L165).

### OBS-034 Автоматическое обновление открытых Browser Source

**Состояние:** Доступно по коду.

Все виджеты опрашивают локальные данные и применяют сохранённые изменения без ручного обновления источника: главный/список раз в секунду, колесо/лоты — 200 мс, правила — 500 мс, таймер/плеер — 100 мс. После смены версии приложения встроенная проверка выполняет один сброс кэша и перезагрузку страницы.

**Доступ:** Открытые Browser Source

**Код:** [streaming_manager/web/overlay.html строки 1129–1129 — update timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html#L1129-L1129); [streaming_manager/web/list_overlay.html строки 398–398 — update timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/list_overlay.html#L398-L398); [streaming_manager/web/wheel_overlay.html строки 376–376 — poll timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html#L376-L376); [streaming_manager/web/auction_lots_overlay.html строки 215–217 — POLL_MS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html#L215-L217); [streaming_manager/web/rules_overlay.html строки 108–108 — POLL_MS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L108-L108); [streaming_manager/web/timer_overlay.html строки 114–115 — POLL_MS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html#L114-L115); [streaming_manager/web/music_player_overlay.html строки 697–697 — poll timer](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L697-L697); [streaming_manager/api_server.py строки 29–72 — _inject_overlay_version_handshake](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L29-L72).

## Изображение центра колеса

### CENTER-001 Постоянный выбор изображения или логотипа

**Состояние:** Доступно по коду.

В Настройках выбирается изображение центра из собственной библиотеки либо встроенный логотип InOneLine. Выбор сразу сохраняется и применяется к локальному колесу и OBS.

**Доступ:** Настройки → Аукцион → Изображение центра колеса

**Условия и границы:** Недоступный файл нельзя заново выбрать; для него предлагается добавить изображение повторно.

**Код:** [streaming_manager/views/settings.py строки 1010–1031 — SettingsTab._refresh_wheel_center_image_library](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1010-L1031); [streaming_manager/views/settings.py строки 1033–1050 — SettingsTab._save_wheel_center_selection_immediately](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1033-L1050); [streaming_manager/views/main_window.py строки 241–256 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L241-L256).

### CENTER-002 Пакетный импорт изображений центра

**Состояние:** Доступно по коду.

Выбирает несколько PNG, JPG, JPEG, WEBP или GIF, последовательно проверяет и сохраняет собственные подготовленные копии. Повторное одинаковое подготовленное содержимое использует имя на основе хеша; после группы выбирается последнее успешное изображение.

**Доступ:** Настройки → Аукцион → Добавить файл или загрузка через центр колеса

**Условия и границы:** Максимум 10 МиБ на исходник; размер до 8192 по каждой стороне и до 40 млн пикселей. Исходники сохраняются без изменений.

**Код:** [streaming_manager/views/settings.py строки 1105–1121 — SettingsTab._import_wheel_center_image_file](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1105-L1121); [streaming_manager/views/settings.py строки 1123–1143 — SettingsTab._continue_wheel_center_file_batch](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1123-L1143); [streaming_manager/wheel_center_media.py строки 42–71 — store_prepared_center_image](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/wheel_center_media.py#L42-L71); [streaming_manager/remote_image.py строки 345–355 — load_local_image](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py#L345-L355); [streaming_manager/remote_image.py строки 269–320 — prepare_image_bytes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py#L269-L320).

### CENTER-003 Загрузка изображения по внешнему адресу

**Состояние:** При условиях.

Принимает публичный прямой HTTP(S) URL, ссылки или сокращённые записи 7tv:ID, bttv:ID, ffz:ID, а также twitch:login или страницу Twitch для аватара. Полученное изображение сохраняется локально.

**Доступ:** Настройки → Аукцион → поле источника → Загрузить

**Условия и границы:** Twitch-профиль требует подключённый Twitch. Локальные и служебные адреса отклоняются; сетевой ответ и декодируемое изображение проходят проверку.

**Код:** [streaming_manager/views/settings.py строки 1088–1092 — SettingsTab._prepare_wheel_center_remote](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1088-L1092); [streaming_manager/views/settings.py строки 1145–1152 — SettingsTab._import_wheel_center_image_url](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1145-L1152); [streaming_manager/remote_image.py строки 166–249 — resolve_external_image_source](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py#L166-L249); [streaming_manager/remote_image.py строки 363–389 — download_external_image](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py#L363-L389).

### CENTER-004 Быстрый выбор через центр колеса

**Состояние:** Доступно по коду.

Нажатие на центр локального колеса открывает сетку собственных изображений и кнопку Загрузить своё изображение. Выбор сохраняет тот же параметр, что и Настройки.

**Доступ:** Аукцион → нажатие на центр локального колеса

**Условия и границы:** Показывает только доступные собственные файлы; отдельного второго параметра центра нет.

**Код:** [streaming_manager/views/auction.py строки 1036–1043 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1036-L1043); [streaming_manager/views/auction.py строки 1624–1656 — AuctionTab._open_wheel_center_picker](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1624-L1656); [streaming_manager/views/auction.py строки 1730–1751 — AuctionTab._apply_wheel_center_asset](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1730-L1751); [streaming_manager/views/wheel_center_picker.py строки 101–250 — WheelCenterPickerDialog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel_center_picker.py#L101-L250).

### CENTER-005 Каталог смайликов подключённого канала

**Состояние:** При условиях.

Быстрый выбор может загрузить Twitch-смайлики и смайлики канала из 7TV, BetterTTV и FrankerFaceZ. Превью выбирается в сетке, выбранное изображение загружается в локальную библиотеку.

**Доступ:** Аукцион → центр колеса при подключённом Twitch

**Условия и границы:** Требуются включённое подключение Twitch и сеть. Каталог кэшируется в текущем окне программы; ошибка каталога не препятствует выбору локальных изображений.

**Код:** [streaming_manager/views/auction.py строки 1668–1708 — AuctionTab._load_wheel_center_catalog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1668-L1708); [streaming_manager/views/auction.py строки 1798–1815 — AuctionTab._wheel_center_picker_remote_selected](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1798-L1815); [streaming_manager/emote_catalog.py строки 188–261 — fetch_third_party_channel_emotes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/emote_catalog.py#L188-L261).

### CENTER-006 Сохранение поддерживаемой анимации

**Состояние:** При условиях.

При подготовке анимированные GIF/WEBP сохраняются в исходном анимированном формате, если текущий Qt умеет его воспроизводить. Остальные декодированные изображения нормализуются в PNG; сетка выбора поддерживает анимированное превью.

**Доступ:** Автоматически при импорте центра и его выборе

**Условия и границы:** Поддержка конкретной анимации зависит от Qt; это не поддержка видеофайлов в центре колеса.

**Код:** [streaming_manager/remote_image.py строки 269–320 — prepare_image_bytes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py#L269-L320); [streaming_manager/views/wheel_center_picker.py строки 55–64 — _PickerImageButton.set_movie_file](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel_center_picker.py#L55-L64); [streaming_manager/views/wheel_center_picker.py строки 66–87 — _PickerImageButton.set_movie_bytes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel_center_picker.py#L66-L87).

## Резервное копирование и восстановление

### BACKUP-001 Резервная копия базы по кнопке

**Состояние:** Доступно по коду.

Создаёт согласованную копию SQLite в папке backups через фоновую задачу, сообщает путь к созданному файлу. Сохраняются 30 последних обычных копий.

**Доступ:** Настройки → Общие → Создать резервную копию

**Условия и границы:** Это копия базы; файлы медиа, защищённые подключения и INI состояния окна добавляются только в полную копию.

**Код:** [streaming_manager/views/settings.py строки 2512–2536 — SettingsTab.backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2512-L2536); [streaming_manager/backup_restore.py строки 792–810 — create_sqlite_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L792-L810); [streaming_manager/backup_restore.py строки 813–820 — prune_backup_files](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L813-L820).

### BACKUP-002 Автоматическая копия при запуске

**Состояние:** Доступно по коду.

После запуска ставит в фон создание резервной копии базы и очистку старых обычных копий сверх 30.

**Доступ:** Автоматически при запуске

**Условия и границы:** Отдельный пользовательский планировщик или интервальное расписание резервирования в интерфейсе не предусмотрены.

**Код:** [streaming_manager/views/main_window.py строки 296–305 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L296-L305); [streaming_manager/views/main_window.py строки 868–880 — MainWindow._startup_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L868-L880).

### BACKUP-003 Открытие каталогов данных и копий

**Состояние:** Доступно по коду.

Показывает путь рабочей базы; отдельными кнопками открывает папку данных и папку резервных копий в файловом менеджере.

**Доступ:** Настройки → Общие

**Условия и границы:** При необходимости каталог создаётся.

**Код:** [streaming_manager/views/settings.py строки 219–242 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L219-L242); [streaming_manager/views/settings.py строки 2491–2493 — SettingsTab._open_folder](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2491-L2493).

### BACKUP-004 Восстановление из файла базы

**Состояние:** Доступно по коду.

После подтверждения проверяет выбранную .db, готовит восстановление, сохраняет страховочную копию текущей базы и запускает отдельный помощник для замены с перезапуском приложения.

**Доступ:** Настройки → Общие → Восстановить из резервной копии

**Условия и границы:** Текущий рабочий файл нельзя выбрать как резервный. Операция блокирует окно на время подготовки.

**Код:** [streaming_manager/views/settings.py строки 2538–2587 — SettingsTab.restore_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2538-L2587); [streaming_manager/backup_restore.py строки 854–924 — apply_staged_restore](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L854-L924).

### BACKUP-005 Проверка совместимости и целостности базы

**Состояние:** Доступно по коду.

Перед восстановлением выполняет SQLite quick_check, integrity_check, foreign_key_check и проверяет обязательные таблицы и поля. Распознаваемые старые базы допускаются к последующей миграции.

**Доступ:** При восстановлении базы и полной копии

**Условия и границы:** База с версией схемы выше 21 отклоняется. Ошибка проверки не должна заменять рабочие данные.

**Код:** [streaming_manager/backup_restore.py строки 687–789 — validate_streaming_manager_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L687-L789).

### BACKUP-006 Полная резервная копия пользовательского состояния

**Состояние:** Доступно по коду.

Создаёт файл .iolbackup с базой, credentials, управляемыми фонами, музыкой, soundtrack, изображениями центра колеса и ui_state.ini. Записывает состав, размеры и SHA-256 файлов.

**Доступ:** Настройки → Общие → Создать полную резервную копию

**Условия и границы:** В копию не входят исполняемая программа, журналы, вложенные резервные копии и внешние оригиналы, сохранённые как ссылки.

**Код:** [streaming_manager/views/settings.py строки 2589–2657 — SettingsTab.create_full_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2589-L2657); [streaming_manager/backup_restore.py строки 349–443 — create_full_backup_archive](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L349-L443).

### BACKUP-007 Выбор безопасного места полной копии

**Состояние:** Доступно по коду.

Диалог предлагает сохранить .iolbackup вне каталога установки; попытка выбрать папку внутри InOneLine отклоняется.

**Доступ:** При создании полной копии

**Условия и границы:** Защита нужна, поскольку полное удаление программы удаляет её собственные данные и локальные копии.

**Код:** [streaming_manager/views/settings.py строки 2589–2657 — SettingsTab.create_full_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2589-L2657); [streaming_manager/backup_restore.py строки 195–208 — validate_full_backup_destination](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L195-L208).

### BACKUP-008 Полное восстановление и откат при сбое

**Состояние:** Доступно по коду.

Проверяет контейнер, состав и контрольные суммы, создаёт страховочную полную копию, заменяет базу, управляемые файлы и состояние интерфейса. При ошибке предусмотрен откат; затем программа запускается заново и показывает результат.

**Доступ:** Настройки → Общие → Восстановить из полной резервной копии

**Условия и границы:** Защищённые данные подключений ориентированы на того же пользователя Windows. На другом ПК или в другой учётной записи может потребоваться повторное подключение сервисов; внешние оригиналы не заменяются.

**Код:** [streaming_manager/views/settings.py строки 2692–2733 — SettingsTab.restore_full_backup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2692-L2733); [streaming_manager/backup_restore.py строки 311–346 — validate_full_backup_archive](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L311-L346); [streaming_manager/backup_restore.py строки 530–671 — apply_staged_full_restore](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L530-L671).

### BACKUP-009 Совместимость прежних полных архивов

**Состояние:** При условиях.

Полное восстановление принимает прежний состав каталогов с wheel_jingles, а запуск базы переводит старые саундтреки в общий каталог soundtrack. Для старого архива без INI предусмотрено сохранение текущего состояния окна.

**Доступ:** Восстановление подходящего прежнего .iolbackup

**Условия и границы:** Это совместимость пользовательских данных, а не установка старого исполняемого файла.

**Код:** [streaming_manager/backup_restore.py строки 216–308 — _full_backup_manifest_and_infos](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L216-L308); [streaming_manager/backup_restore.py строки 530–671 — apply_staged_full_restore](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py#L530-L671); [streaming_manager/db/media.py строки 272–517 — MediaMixin.migrate_legacy_wheel_jingles](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/media.py#L272-L517).

### BACKUP-010 Установка и удаление Windows-сборки

**Состояние:** При условиях.

Установщик рассчитан на Windows 10 и новее x64, позволяет выбрать локальную папку и необязательный ярлык. Переустановка заменяет исполняемые файлы, сохраняя данные. Удаление требует отдельного подтверждения полного удаления собственных данных.

**Доступ:** Установщик InOneLine

**Условия и границы:** Сетевые и UNC-пути не разрешены; полный путь к InOneLine.exe должен быть короче 260 символов. Внешние файлы за пределами установки не удаляются.

**Код:** [installer/InOneLine.iss строки 10–92 — Setup](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/installer/InOneLine.iss#L10-L92); [installer/InOneLine.iss строки 94–148 — InitializeUninstall](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/installer/InOneLine.iss#L94-L148).

## Общее управление подключениями

### INT-001 Центр подключений Twitch и DonationAlerts

**Состояние:** Доступно по коду.

В текущем основном окне зарегистрированы два настоящих адаптера — Twitch и DonationAlerts. Карточки показывают состояние «Не настроено», «Требует входа», «Подключено» или «Ошибка», признак отключённого использования, сведения об аккаунте, возможности, ошибку, последнее время проверки и последнюю принятую активность. Время отображается в локальной зоне.

**Доступ:** Настройки → Интеграции; карточки создаются из зарегистрированных адаптеров.

**Код:** [streaming_manager/views/main_window.py строки 95–114 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L95-L114); [streaming_manager/views/settings.py строки 567–630 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L567-L630); [streaming_manager/views/settings.py строки 1485–1552 — SettingsTab._refresh_integrations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1485-L1552); [streaming_manager/integrations.py строки 19–31 — STATUS_LABELS](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L19-L31).

### INT-002 Действия подключения зависят от состояния

**Состояние:** Доступно по коду.

Для ненастроенного сервиса доступно «Подключить»; для отключённого сохранённого — «Включить», удаление и при ошибке/необходимости входа переподключение; для включённого — проверка, переподключение, отключение и удаление. Сетевые операции выполняются в фоновом worker, кнопки на время операции блокируются.

**Доступ:** Кнопки карточки сервиса в Настройки → Интеграции.

**Условия и границы:** Для обращения к провайдеру нужны сеть и доступность соответствующего сервиса.

**Код:** [streaming_manager/views/settings.py строки 1456–1476 — SettingsTab._integration_action_specs](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1456-L1476); [streaming_manager/views/settings.py строки 1554–1573 — SettingsTab._refresh_integrations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1554-L1573); [streaming_manager/views/settings.py строки 2276–2354 — SettingsTab._run_integration_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2276-L2354).

### INT-003 Проверка соединения и периодическая проверка сессии

**Состояние:** При условиях.

«Проверить соединение» обращается к реальному адаптеру и сохраняет результат и время проверки; сама диагностика сохраняет включённое/отключённое состояние. Временные ошибки повторяются до трёх попыток с задержками 0,5 и 1,5 секунды; ошибки входа становятся «Требует входа». При запуске и затем раз в час проверяются только включённые подключения со статусом «Подключено». Это диагностика авторизации/профиля, а не генерация пробного пожертвования.

**Доступ:** Кнопка «Проверить соединение» активной карточки; автоматическая проверка при работе основного окна.

**Условия и границы:** Автоматическая проверка пропускает отключённые, ненастроенные и уже ошибочные подключения.

**Код:** [streaming_manager/integrations.py строки 170–181 — IntegrationManager.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L170-L181); [streaming_manager/integrations.py строки 252–297 — IntegrationManager._run_adapter_operation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L252-L297); [streaming_manager/views/main_window.py строки 299–305 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L299-L305); [streaming_manager/views/main_window.py строки 755–787 — MainWindow._validate_active_integrations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L755-L787).

### INT-004 Отключить и включить сохранённое подключение

**Состояние:** При условиях.

«Отключить» прекращает локальное использование, сохраняя credential и конфигурацию. Перед отключением Twitch программа пытается выключить зарегистрированные удалённые награды; DonationAlerts сбрасывает курсор, чтобы последующее включение начиналось с нового текущего уровня истории. «Включить» проверяет сохранённую авторизацию и активирует источник только при успешной проверке; отдельный вход выполняется через переподключение.

**Доступ:** Карточка сервиса → «Отключить» или «Включить».

**Условия и границы:** Twitch перед отключением может потребовать доступный API и право управления наградами. Отключение не является отзывом выданного провайдером OAuth-разрешения.

**Код:** [streaming_manager/integrations.py строки 308–353 — IntegrationManager.enable / _disconnect_locked](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L308-L353); [streaming_manager/views/settings.py строки 2302–2317 — SettingsTab._run_integration_action.perform_operation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2302-L2317); [streaming_manager/twitch_b4.py строки 241–244 — TwitchChannelPointsService.prepare_disconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L241-L244); [streaming_manager/donationalerts_runtime.py строки 122–131 — DonationAlertsDonationService.on_connection_removed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L122-L131).

### INT-005 Удаление локального подключения отдельно от истории и наград

**Состояние:** При условиях.

После подтверждения удаляются запись подключения и её credential из защищённого хранилища. История внешних событий, взносов и аукционов сохраняется. У Twitch выключаются учётные флаги наград; удаление самих удалённых Custom Rewards выполняется отдельной кнопкой, а не удалением подключения.

**Доступ:** Карточка сервиса → «Удалить подключение» → подтверждение.

**Условия и границы:** Применяется предварительное отключение удалённых наград Twitch; ошибка этого шага может остановить действие.

**Код:** [streaming_manager/views/settings.py строки 2408–2421 — SettingsTab._confirm_remove_integration](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2408-L2421); [streaming_manager/views/settings.py строки 2302–2319 — SettingsTab._run_integration_action.perform_operation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2302-L2319); [streaming_manager/integrations.py строки 355–363 — IntegrationManager.remove_connection](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L355-L363); [streaming_manager/twitch_b4.py строки 246–254 — TwitchChannelPointsService.on_connection_removed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L246-L254).

### INT-006 Оперативный индикатор интеграций в аукционе

**Состояние:** Доступно по коду.

Кнопка состояния объединяет сохранённое состояние подключений и ошибки работающих EventSub/Centrifugo. Диалог показывает включённые настроенные сервисы, их подключение и состояние событий в реальном времени, включая отсутствие наград Twitch. Из диалога можно перейти к настройкам интеграций.

**Доступ:** Аукцион → область проведения → кнопка «Интеграции: …» → «Настройки интеграций».

**Код:** [streaming_manager/views/auction.py строки 335–344 — AuctionTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L335-L344); [streaming_manager/views/auction.py строки 1900–1906 — AuctionTab._active_integration_views](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1900-L1906); [streaming_manager/views/auction.py строки 1915–2029 — AuctionTab.refresh_integration_status / _show_integration_status_dialog](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L1915-L2029); [streaming_manager/views/main_window.py строки 714–753 — MainWindow._integration_runtime_health_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L714-L753); [streaming_manager/views/main_window.py строки 792–799 — MainWindow.open_integrations_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L792-L799).

### INT-007 Защищённое хранение авторизации и API-ключа

**Состояние:** Доступно по коду.

OAuth-данные и RANDOM.ORG API key сохраняются отдельно от SQLite; в базе остаются непрозрачные ссылки cred_…. Windows использует файлы, зашифрованные DPAPI текущего пользователя, с атомарной заменой; вне Windows реализовано только хранилище в памяти процесса. Конфигурация провайдера рекурсивно отклоняет поля с именами token/secret/password/api_key и подобными; внешние метаданные с такими ключами маскируются перед записью.

**Доступ:** Автоматически при авторизации и явном сохранении ключа RANDOM.ORG.

**Условия и границы:** Постоянное защищённое хранение реализовано для Windows. Вне Windows credentials не переживают завершение процесса.

**Код:** [streaming_manager/credentials.py строки 42–73 — MemoryCredentialStore](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/credentials.py#L42-L73); [streaming_manager/credentials.py строки 91–107 — WindowsDpapiCredentialStore](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/credentials.py#L91-L107); [streaming_manager/credentials.py строки 188–221 — WindowsDpapiCredentialStore.put / create_credential_store](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/credentials.py#L188-L221); [streaming_manager/db/integrations.py строки 24–36 — _assert_non_secret_provider_config](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/integrations.py#L24-L36); [streaming_manager/db/services.py строки 529–543 — ServicesMixin._sanitize_external_event_metadata](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L529-L543).

### INT-008 Допуск внешних событий и атомарное начисление

**Состояние:** При условиях.

Приём допускает только зарегистрированный адаптер, разрешённый им тип события и включённое подключение со статусом «Подключено». Проверка повторяется внутри транзакции SQLite. Событие, конвертация, изменение игры/лота, взнос и запись результата сохраняются в одной транзакции; учётные данные не передаются через эту запись.

**Доступ:** Фоновый приём Twitch/DonationAlerts после настройки подключения.

**Условия и границы:** Twitch разрешает тип twitch_channel_points_redemption; DonationAlerts — donationalerts_donation.

**Код:** [streaming_manager/integrations.py строки 365–401 — IntegrationManager.accept_normalized_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L365-L401); [streaming_manager/db/services.py строки 742–780 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L742-L780); [streaming_manager/db/services.py строки 1048–1108 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1048-L1108); [streaming_manager/twitch.py строки 402–414 — TwitchAdapter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L402-L414); [streaming_manager/donationalerts.py строки 462–473 — DonationAlertsAdapter](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L462-L473).

### INT-009 Защита от повторного начисления внешнего события

**Состояние:** При условиях.

Уникальность пары источник + внешний ID закреплена и для external_events, и для contributions. Повтор возвращает уже сохранённый исход, не создавая новое начисление или pending; операции каждого сервиса сериализуются. Это также позволяет повторить удалённое подтверждение Twitch после локального успешного начисления без повторного увеличения баллов. Отклонённый pending также остаётся защищён от повторного воспроизведения.

**Доступ:** Автоматически при повторной доставке, восстановлении потока или ручном решении pending.

**Условия и границы:** Уникальный ID относится к конкретному источнику; DonationAlerts дополнительно использует свой числовой курсор.

**Код:** [streaming_manager/db/schema.py строки 109–138 — contributions / external_events schema](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/schema.py#L109-L138); [streaming_manager/integrations.py строки 191–208 — IntegrationManager._operation_lock / _save_credential_immediately](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L191-L208); [streaming_manager/db/services.py строки 545–585 — ServicesMixin._existing_external_event_result_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L545-L585); [streaming_manager/db/services.py строки 757–777 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L757-L777); [streaming_manager/db/services.py строки 1557–1564 — ServicesMixin.reject_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1557-L1564).

## Twitch и награды канала

### INT-010 Официальный вход Twitch по коду устройства

**Состояние:** При условиях.

Используется встроенный публичный Twitch Client ID и Device Code flow без ввода пароля или Client Secret в приложении. Диалог показывает код, адрес Twitch и оставшееся время, позволяет открыть Twitch, скопировать код и отменить вход. Программа ожидает разрешение в фоне; «Переподключить» запускает новый grant, а «Подключить» сначала пробует сохранённый.

**Доступ:** Настройки → Интеграции → Twitch → «Подключить Twitch» / «Переподключить».

**Условия и границы:** Нужен аккаунт Twitch и подтверждение доступа на странице Twitch.

**Код:** [streaming_manager/twitch.py строки 30–47 — Twitch constants](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L30-L47); [streaming_manager/twitch.py строки 715–799 — TwitchAdapter._device_flow / connect / reconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L715-L799); [streaming_manager/views/settings.py строки 2061–2142 — SettingsTab._show_twitch_device_code](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2061-L2142).

### INT-011 Профиль и фактическая доступность Custom Rewards

**Состояние:** При условиях.

Проверка получает ID, login, display name, аватар, тип канала и разрешения; отдельным запросом определяет доступность Custom Rewards и их число. Отказ 403 по наградам сохраняет подключение аккаунта, но показывает недоступность наград для канала, которому нужен Affiliate или Partner. Токен проверяется на соответствие встроенному приложению; истекающий токен обновляется, новая пара сохраняется до последующих сетевых запросов.

**Доступ:** Карточка Twitch и «Проверить соединение».

**Условия и границы:** Обычное подключение аккаунта не означает доступность управления Channel Points.

**Код:** [streaming_manager/twitch.py строки 455–507 — TwitchAdapter._refresh / _validate_with_refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L455-L507); [streaming_manager/twitch.py строки 509–574 — TwitchAdapter._profile_and_capability](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L509-L574); [streaming_manager/twitch.py строки 976–1006 — TwitchAdapter.view_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L976-L1006).

### INT-012 Отдельное согласие на управление наградами

**Состояние:** При условиях.

Первичный вход запрашивает чтение погашений. Если подключённый подходящий канал ещё не выдал channel:manage:redemptions, карточка предлагает «Подтвердить права на награды» и запускает дополнительный Device Code flow. Синхронизация, переключение и удаление блокируются, пока нет подключения, доступности наград и разрешения управления. Переподключение с уже зарегистрированными наградами сохраняет запрос manage scope.

**Доступ:** Настройки → Интеграции → Twitch → «Подтвердить права на награды».

**Условия и границы:** Канал должен поддерживать Custom Rewards; требуется отдельное подтверждение Twitch.

**Код:** [streaming_manager/twitch.py строки 413–414 — TwitchAdapter.required_scopes](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L413-L414); [streaming_manager/twitch.py строки 797–848 — TwitchAdapter.reconnect_for_channel_points / ensure_manage_scope / _managed_snapshot](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L797-L848); [streaming_manager/views/settings.py строки 1750–1786 — SettingsTab._build_twitch_b4_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1750-L1786); [streaming_manager/views/settings.py строки 2311–2315 — SettingsTab._run_integration_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2311-L2315).

### INT-013 Редактор набора Twitch-наград

**Состояние:** Доступно по коду.

Форма задаёт общее название и строки наград со стоимостью Channel Points, цветом #RRGGBB, пипеткой с экрана и неизменяемым ID Twitch. Строки можно добавлять и убирать; новая строка начинается со стоимости 100 и фиолетового цвета #9146FF. Поле стоимости принимает целое от 1 до 2 147 483 647.

**Доступ:** Настройки → Интеграции → Twitch → «Channel Points — пополнение игр».

**Код:** [streaming_manager/views/settings.py строки 1706–1745 — SettingsTab._build_twitch_b4_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1706-L1745); [streaming_manager/views/settings.py строки 1837–1883 — SettingsTab._populate_twitch_reward_row / _pick_twitch_reward_color](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1837-L1883); [streaming_manager/views/settings.py строки 1909–1950 — SettingsTab._add_twitch_reward_row / _collect_twitch_reward_form](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1909-L1950).

### INT-014 Проверка стоимости, цвета и названия наград

**Состояние:** При условиях.

Перед сохранением проверяются непустое общее название, положительная стоимость, корректный цвет, уникальность стоимости каждой строки, не более 50 локальных определений и длина полного Twitch-названия не больше 45 символов. Полное имя формируется как «общее название - стоимость». Ошибка формы не запускает сетевые изменения.

**Доступ:** Кнопка «Сохранить и синхронизировать награды».

**Условия и границы:** Дополнительные лимиты и ошибки самого Twitch могут проявиться при реальном API-запросе.

**Код:** [streaming_manager/twitch_b4.py строки 43–56 — TwitchRewardDefinition.normalized](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L43-L56); [streaming_manager/twitch_b4.py строки 124–148 — TwitchChannelPointsService.reward_title / _validate_configuration](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L124-L148); [streaming_manager/views/settings.py строки 1991–2001 — SettingsTab._sync_twitch_rewards_from_form](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1991-L2001).

### INT-015 Создание и синхронизация реальных Twitch Custom Rewards

**Состояние:** При условиях.

Сохранение сначала проверяет право управления, записывает локальные настройки, затем обращается к Twitch. Доступные приложению награды ищутся по сохранённому ID, затем точному полному имени; существующие обновляются, недостающие создаются, полученные ID сохраняются. Награда требует ввода названия игры/лота, не пропускает очередь запросов, получает общие имя, стоимость, цвет и состояние включения. Удалённая синхронизация последовательная; при частичной ошибке UI прямо сообщает, что локальные настройки сохранены и часть удалённых наград могла измениться.

**Доступ:** Настройки → Интеграции → Twitch → «Сохранить и синхронизировать награды».

**Условия и границы:** Нужно включённое подключение, доступные Custom Rewards и manage scope. Это реальные изменения Twitch; общей транзакции с удалённым сервисом нет.

**Код:** [streaming_manager/twitch.py строки 850–877 — TwitchAdapter.list_manageable_rewards / create_managed_reward](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L850-L877); [streaming_manager/twitch_b4.py строки 262–283 — TwitchChannelPointsService._reward_body](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L262-L283); [streaming_manager/twitch_b4.py строки 285–354 — TwitchChannelPointsService.sync_rewards](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L285-L354); [streaming_manager/views/settings.py строки 2003–2027 — SettingsTab._sync_twitch_rewards_from_form](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2003-L2027).

### INT-016 Убрать строку награды без удаления на Twitch

**Состояние:** При условиях.

«Убрать» изменяет только черновик таблицы. После сохранения и синхронизации исключённый зарегистрированный ID записывается как retired и удалённая награда выключается; окончательное удаление возможно отдельным подтверждаемым действием «Удалить награды».

**Доступ:** Строка таблицы наград → «Убрать» → «Сохранить и синхронизировать награды».

**Условия и границы:** До явного сохранения изменение списка остаётся черновиком.

**Код:** [streaming_manager/views/settings.py строки 1870–1877 — SettingsTab._populate_twitch_reward_row](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1870-L1877); [streaming_manager/views/settings.py строки 1920–1928 — SettingsTab._remove_twitch_reward_button_row](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1920-L1928); [streaming_manager/twitch_b4.py строки 150–175 — TwitchChannelPointsService.save_configuration](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L150-L175); [streaming_manager/twitch_b4.py строки 335–348 — TwitchChannelPointsService.sync_rewards](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L335-L348).

### INT-017 Включить и выключить награды независимо от аукциона

**Состояние:** При условиях.

Кнопка переключает доступность зарегистрированных удалённых наград. При включении требуется сохранённый положительный курс Twitch Channel Points и право управления. Начало, пауза или завершение аукциона больше не переключают награды; подключённый источник работает постоянно, а старые отдельные флаги учёта и привязки не используются.

**Доступ:** Настройки → Интеграции → Twitch → «Включить награды» / «Отключить награды».

**Условия и границы:** Нужен хотя бы один зарегистрированный активный reward ID, подключение и manage scope.

**Код:** [streaming_manager/views/settings.py строки 1802–1835 — SettingsTab._build_twitch_b4_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1802-L1835); [streaming_manager/twitch_b4.py строки 192–239 — TwitchChannelPointsService._require_positive_rate / set_manual_rewards_enabled](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L192-L239); [streaming_manager/twitch_b4.py строки 256–259 — TwitchChannelPointsService.desired_rewards_enabled](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L256-L259); [streaming_manager/twitch_b4.py строки 356–369 — TwitchChannelPointsService.sync_reward_enabled_state](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L356-L369).

### INT-018 Отдельное удаление зарегистрированных Twitch-наград

**Состояние:** При условиях.

После подтверждения удаляются из Twitch все записанные активные и retired ID. Локальные стоимости и цвета сохраняются, но их ID очищаются; список retired очищается и награды становятся выключенными. Подключение и история событий остаются. Уже отсутствующий на Twitch ID с ответом 404 считается удалённым.

**Доступ:** Настройки → Интеграции → Twitch → «Удалить награды» → подтверждение.

**Условия и границы:** Кнопка показана при наличии активных или retired ID и доступна с подключением/правами управления.

**Код:** [streaming_manager/views/settings.py строки 1817–1823 — SettingsTab._build_twitch_b4_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1817-L1823); [streaming_manager/views/settings.py строки 2038–2059 — SettingsTab._confirm_delete_twitch_rewards](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2038-L2059); [streaming_manager/twitch_b4.py строки 371–402 — TwitchChannelPointsService.delete_managed_rewards](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L371-L402); [streaming_manager/twitch.py строки 891–900 — TwitchAdapter.delete_managed_reward](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L891-L900).

### INT-019 Сохранение черновика наград и явный сброс при смене аккаунта

**Состояние:** Доступно по коду.

Несохранённые имя, стоимости, цвета и строки переживают обновление карточек и обычную навигацию; это не автосохранение. Во время синхронизации или удаления форма замораживается и затем перечитывает сохранённые ID. При подключении, переподключении или удалении подключения с черновиком показывается подтверждение сброса; удаление наград также предупреждает о сбросе.

**Доступ:** Редактор Twitch-наград, навигация настроек и действия с подключением.

**Условия и границы:** Черновик хранится только в памяти текущего процесса.

**Код:** [streaming_manager/views/settings.py строки 1432–1441 — SettingsTab._twitch_reward_unsaved_draft](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1432-L1441); [streaming_manager/views/settings.py строки 1478–1484 — SettingsTab._refresh_integrations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1478-L1484); [streaming_manager/views/settings.py строки 1952–1988 — SettingsTab._run_twitch_b4_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1952-L1988); [streaming_manager/views/settings.py строки 2279–2296 — SettingsTab._run_integration_action](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2279-L2296).

### INT-020 Поток EventSub и восстановление непогашенных запросов

**Состояние:** При условиях.

При включённом подключении и зарегистрированных reward ID фоновый WebSocket создаёт подписки только для них. После соединения восстанавливается состояние включения наград и запрашиваются UNFULFILLED погашения; при разрыве выполняются повторные подключения, при смене ID пересоздаётся набор подписок, поддерживается передача на reconnect URL Twitch. REST-восстановление ограничено 10 страницами по 50 записей на награду за один проход.

**Доступ:** Автоматически после запуска приложения/настройки Twitch; состояние видно в индикаторе интеграций.

**Условия и границы:** Нужны корректный OAuth grant с управлением погашениями, сеть и хотя бы один app-managed reward ID. Ограничение 500 записей на награду за проход — предел реализованного catch-up, а не обещание полного импорта всей истории.

**Код:** [streaming_manager/views/main_window.py строки 299–305 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L299-L305); [streaming_manager/twitch_b4.py строки 596–624 — TwitchEventSubRuntime._run](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L596-L624); [streaming_manager/twitch_b4.py строки 638–710 — TwitchEventSubRuntime._run_connection](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L638-L710); [streaming_manager/twitch.py строки 937–961 — TwitchAdapter.list_unfulfilled_redemptions](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L937-L961).

### INT-021 Фильтрация и проверка погашений Twitch

**Состояние:** При условиях.

Обрабатываются только ID зарегистрированных наград, остальные игнорируются. Для известной награды обязательны ID события/награды, положительная стоимость и корректное redeemed_at с часовым поясом. Без положительного настроенного курса или при некорректной дате/стоимости отправляется CANCELED; Twitch-погашение без курса не оставляется оператору в обычной очереди неизвестных валют. Количество Channel Points берётся из стоимости награды в событии.

**Доступ:** Автоматический приём EventSub и восстановление UNFULFILLED.

**Условия и границы:** Приложение должно быть подключено; CANCELED выполняется настоящим запросом Twitch и может завершиться сетевой ошибкой.

**Код:** [streaming_manager/twitch_b4.py строки 417–465 — TwitchChannelPointsService._normalize_redemption / process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L417-L465); [streaming_manager/twitch_b4.py строки 469–494 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L469-L494).

### INT-022 Начисление Twitch с выполнением или отменой запроса

**Состояние:** При условиях.

Имя зрителя и текст user_input нормализуются в общий вклад: текст служит названием игры/лота, стоимость — исходным количеством Twitch Channel Points. По сохранённому processed результату запрос помечается FULFILLED, по inapplicable — CANCELED; при повторной доставке общий движок возвращает сохранённый результат. В метаданных сохраняются reward ID/title/cost, данные зрителя, redeemed_at и идентификаторы EventSub, но не OAuth credential.

**Доступ:** Автоматически для допустимого погашения зарегистрированной награды.

**Условия и границы:** Источник-аукцион определяется по redeemed_at, а не по моменту доставки; дальнейшее сопоставление игры выполняет общий движок.

**Код:** [streaming_manager/twitch_b4.py строки 466–506 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L466-L506); [streaming_manager/twitch.py строки 902–921 — TwitchAdapter.update_redemption_status](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L902-L921); [streaming_manager/db/services.py строки 545–585 — ServicesMixin._existing_external_event_result_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L545-L585).

## DonationAlerts и пожертвования

### INT-023 Вход DonationAlerts через браузер и локальный callback

**Состояние:** При условиях.

Встроен публичный Client ID 20915; обычная сборка не требует ручной регистрации OAuth-приложения. Подключение запускает Implicit OAuth с правами профиля, подписки и истории пожертвований, открывает обычный браузер и ждёт до 5 минут. Диалог показывает ссылку, Redirect URI, отсчёт, повторное открытие, копирование ссылки и отмену. Callback слушает 127.0.0.1:17643; локальная страница передаёт URL-фрагмент в процесс, удаляет его из адреса/истории и проверяет одноразовый локальный nonce, а при наличии — provider state.

**Доступ:** Настройки → Интеграции → DonationAlerts → «Подключить DonationAlerts» / «Переподключить».

**Условия и границы:** Нужны аккаунт DonationAlerts, свободный loopback-порт 17643 и подтверждение в браузере.

**Код:** [streaming_manager/donationalerts.py строки 37–63 — DonationAlerts constants](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L37-L63); [streaming_manager/donationalerts.py строки 292–326 — DonationAlertsOAuthReceiver._callback_html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L292-L326); [streaming_manager/donationalerts.py строки 380–420 — DonationAlertsOAuthReceiver.start.Handler.do_POST](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L380-L420); [streaming_manager/donationalerts.py строки 616–677 — DonationAlertsAdapter._oauth_flow / connect / reconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L616-L677); [streaming_manager/views/settings.py строки 1580–1595 — SettingsTab._build_donationalerts_connection_controls](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1580-L1595); [streaming_manager/views/settings.py строки 2144–2239 — SettingsTab._show_donationalerts_oauth](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2144-L2239).

### INT-024 Сохранённый аккаунт и повторный вход DonationAlerts

**Состояние:** При условиях.

Карточка показывает имя/код аккаунта и ID пользователя. «Подключить» сначала проверяет сохранённый credential, «Проверить соединение» читает профиль, «Переподключить» создаёт новый browser grant. Истёкший токен или иной Client ID требуют входа; автоматическое обновление через refresh token в этом Implicit flow не реализовано. Отключение прекращает локальное использование, удаление убирает локальный credential; удалённый revoke endpoint не вызывается.

**Доступ:** Карточка DonationAlerts, её диагностические и lifecycle-кнопки.

**Условия и границы:** Проверка истечения применяется, если провайдер сообщил expires_in; окончательная действительность также проверяется API.

**Код:** [streaming_manager/donationalerts.py строки 575–614 — DonationAlertsAdapter._result_for_profile / _check](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L575-L614); [streaming_manager/donationalerts.py строки 665–696 — DonationAlertsAdapter.connect / check_connection / reconnect / disconnect](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L665-L696); [streaming_manager/donationalerts.py строки 752–761 — DonationAlertsAdapter.view_details](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L752-L761).

### INT-025 Новая связь DonationAlerts начинается с текущей истории

**Состояние:** При условиях.

При первом активном подключении программа получает максимальный удалённый donation ID и записывает начальный курсор, не начисляя старый архив. Намеренное отключение/удаление сбрасывает курсор, поэтому следующее включение снова начинает с текущего состояния. Временный сетевой сбой сохраняет курсор для восстановления пропущенного.

**Доступ:** Автоматическая инициализация фона DonationAlerts.

**Условия и границы:** Это приём новых событий после начальной отметки, а не пользовательский импорт всей истории DonationAlerts.

**Код:** [streaming_manager/donationalerts_runtime.py строки 28–40 — DonationAlertsDonationService](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L28-L40); [streaming_manager/donationalerts_runtime.py строки 90–140 — DonationAlertsDonationService.ensure_cursor_initialized / on_connection_removed / mark_seen](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L90-L140); [streaming_manager/views/settings.py строки 2307–2310 — SettingsTab._run_integration_action.perform_operation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L2307-L2310).

### INT-026 Реальный поток Centrifugo и REST-восстановление DonationAlerts

**Состояние:** При условиях.

Программа получает socket token, подключается к Centrifugo и приватному $alerts:donation_&lt;user_id&gt;, ожидает подтверждения и только после подписки делает REST catch-up. События, пришедшие во время handshake, накапливаются и обрабатываются по ID после восстановления. При ошибке цикл переподключается. Catch-up выбирает новые ID, сортирует по возрастанию и ограничен 50 страницами за проход с паузами 1,05 секунды между страницами.

**Доступ:** Автоматически при включённом подключении DonationAlerts; realtime-статус в аукционе.

**Условия и границы:** Нужны сеть, рабочая авторизация и данные socket connection token в профиле. Предел 50 страниц за проход не является обещанием неограниченного импорта архива.

**Код:** [streaming_manager/donationalerts.py строки 685–739 — DonationAlertsAdapter.runtime_snapshot / subscribe_centrifugo](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L685-L739); [streaming_manager/donationalerts_runtime.py строки 215–251 — DonationAlertsDonationService.catch_up](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L215-L251); [streaming_manager/donationalerts_runtime.py строки 369–446 — DonationAlertsRuntime._queue_handshake_donation / _flush_pending_donations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L369-L446); [streaming_manager/donationalerts_runtime.py строки 463–572 — DonationAlertsRuntime._run / _run_connection](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L463-L572).

### INT-027 Пожертвование DonationAlerts превращается во вклад по сообщению

**Состояние:** При условиях.

Проверяются положительный уникальный числовой ID, конечная неотрицательная сумма и трёхбуквенный ASCII-код валюты. Имя отправителя становится contributor, текст message — названием игры/лота, сумма и валюта передаются в общий движок без валютного пересчёта провайдером. По created_at ищется исходный аукцион; некорректное/отсутствующее время безопасно относит событие к постоянному списку вне аукциона. ID не выше сохранённого курсора отсекаются.

**Доступ:** Автоматический приём DonationAlerts.

**Условия и границы:** Нулевая сумма проходит нормализацию, но общий движок не начисляет неположительный итог. Без пригодного названия вне аукциона событие не зачисляется.

**Код:** [streaming_manager/donationalerts_runtime.py строки 142–213 — DonationAlertsDonationService._normalize_donation / process_donation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L142-L213); [streaming_manager/db/services.py строки 988–1001 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L988-L1001).

### INT-028 Валюты DonationAlerts доступны для отдельной настройки курсов

**Состояние:** При условиях.

Подключённый адаптер объявляет RUB, USD, EUR, BYN, KZT, UAH, BRL и TRY. Другая корректная трёхбуквенная валюта из реального пожертвования регистрируется общим движком и при отсутствии курса попадает в pending. Курсы одной валюты глобальны для программы, а не отдельны для аккаунта DonationAlerts.

**Доступ:** Настройки → Конвертация после подключения DonationAlerts; появление неизвестной валюты во входящем событии.

**Условия и границы:** Объявление валюты добавляет строку курса, но не задаёт сам курс автоматически, кроме базового RUB.

**Код:** [streaming_manager/donationalerts.py строки 64–73 — DONATIONALERTS_CURRENCIES](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L64-L73); [streaming_manager/donationalerts.py строки 741–750 — DonationAlertsAdapter.conversion_units](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L741-L750); [streaming_manager/db/services.py строки 283–319 — ServicesMixin._register_conversion_unit_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L283-L319); [streaming_manager/db/services.py строки 780–780 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L780-L780).

## Конвертация и ожидающие поступления

### CONV-001 Доступные строки курсов и их видимость

**Состояние:** Доступно по коду.

RUB всегда остаётся базовой валютой с курсом по умолчанию 1 балл за RUB. Другие валюты появляются от подключённого сервиса, первого принятого события или сохранённого курса. Сохранённые валюты остаются видимыми; сервисные неденежные единицы, включая Twitch Channel Points, видны при включённом подключении с состоянием «Подключено». Их сохранённый курс не удаляется при отключении.

**Доступ:** Настройки → Конвертация → «Курсы конвертации».

**Код:** [streaming_manager/views/settings.py строки 632–686 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L632-L686); [streaming_manager/db/services.py строки 356–359 — ServicesMixin.get_conversion_rate](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L356-L359); [streaming_manager/db/services.py строки 480–520 — ServicesMixin.visible_conversion_units](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L480-L520); [streaming_manager/integrations.py строки 468–475 — IntegrationManager.conversion_units](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L468-L475); [streaming_manager/twitch.py строки 963–971 — TwitchAdapter.conversion_units](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L963-L971).

### CONV-002 Редактирование и атомарное сохранение набора курсов

**Состояние:** Доступно по коду.

Каждая строка задаёт «1 исходная единица = … баллов». При «Сохранить курсы» сначала проверяется весь видимый набор, затем курсы и состояния pending записываются одной транзакцией; ошибка оставляет введённые поля. Курс должен быть конечным положительным числом. Пустой RUB восстанавливает 1, пустая другая строка очищает её курс. Сохранение курса переводит ожидающие события в состояние ручного применения, но не начисляет их автоматически.

**Доступ:** Настройки → Конвертация → поля курсов → «Сохранить курсы».

**Код:** [streaming_manager/views/settings.py строки 1224–1249 — SettingsTab._refresh_conversion_rate_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1224-L1249); [streaming_manager/views/settings.py строки 1402–1429 — SettingsTab.save_conversion_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1402-L1429); [streaming_manager/db/services.py строки 361–388 — ServicesMixin._update_pending_rate_status_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L361-L388); [streaming_manager/db/services.py строки 394–449 — ServicesMixin.set_conversion_rates_atomic](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L394-L449).

### CONV-003 Черновики курсов при переключении подключения

**Состояние:** Доступно по коду.

Несохранённые значения сохраняются в памяти при переходе между вкладками, обновлении карточек и исчезновении сервисной строки из-за отключения. При возвращении единицы поле восстанавливает черновик. Запись происходит только по «Сохранить курсы»; успешно сохранённые видимые черновики очищаются, скрытые остаются до возвращения строки или закрытия программы.

**Доступ:** Поля Настройки → Конвертация и переключение интеграций.

**Условия и границы:** Черновики не переживают завершение процесса.

**Код:** [streaming_manager/views/settings.py строки 667–682 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L667-L682); [streaming_manager/views/settings.py строки 1200–1243 — SettingsTab._remember_conversion_rate_draft / _refresh_conversion_rate_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1200-L1243); [streaming_manager/views/settings.py строки 1253–1260 — SettingsTab._handle_settings_page_changed](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1253-L1260); [streaming_manager/views/settings.py строки 1415–1425 — SettingsTab.save_conversion_settings](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1415-L1425).

### CONV-004 Точное десятичное умножение и округление вверх

**Состояние:** Доступно по коду.

Сумма умножается на индивидуальный курс через Decimal, затем любой положительный дробный результат округляется вверх до целого; целое и ноль не меняются. Например, 100,85 RUB × 1 = 101 балл. Ввод понимает запятую/точку и разделительные пробелы; отрицательные и бесконечные суммы не допускаются, курс должен быть больше нуля. Обратная конвертация баллов в исходную валюту не выполняется.

**Доступ:** Автоматическое начисление и предпросмотр/применение ожидающего события.

**Код:** [streaming_manager/conversion.py строки 120–180 — parse_decimal / parse_positive_rate / convert_source_to_sm_points](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/conversion.py#L120-L180); [streaming_manager/views/settings.py строки 641–646 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L641-L646); [streaming_manager/views/settings.py строки 688–692 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L688-L692).

### CONV-005 Контекст аукциона выбирается по времени события

**Состояние:** При условиях.

Подключённые источники работают постоянно. Twitch использует redeemed_at, DonationAlerts — created_at: по журналу переходов определяется аукцион, принимавший ставки в тот момент. Событие вне периода running направляется в постоянный список, даже если к доставке запущен новый аукцион. Если найденный исходный аукцион уже не running при первом приёме, событие помечается неприменимым и не переносится в новый; поздний pending имеет отдельные правила.

**Доступ:** Автоматический приём Twitch/DonationAlerts.

**Условия и границы:** Пауза не является периодом running. Для DonationAlerts отсутствие корректной даты даёт внешний к аукциону контекст; Twitch с некорректной датой отменяется раньше.

**Код:** [streaming_manager/db/auction_session.py строки 124–182 — AuctionSessionMixin.find_running_auction_at](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L124-L182); [streaming_manager/twitch_b4.py строки 466–494 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L466-L494); [streaming_manager/donationalerts_runtime.py строки 182–209 — DonationAlertsDonationService.process_donation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L182-L209); [streaming_manager/db/services.py строки 781–808 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L781-L808).

### CONV-006 Сообщение зрителя служит точным названием цели

**Состояние:** При условиях.

Для текущих провайдеров user_input Twitch или message DonationAlerts обозначает игру/лот целиком. Названия сравниваются после Unicode NFKC, нормализации пробелов и casefold; похожие названия автоматически не угадываются. Во время аукциона существующий лот пополняется, существующая игра подключается к сессии, новая создаётся временной auction_only. Вне аукциона существующая постоянная игра пополняется, новая создаётся постоянной только при действительном начислении.

**Доступ:** Текст зрителя во внешнем событии; общего пользовательского редактора привязок нет.

**Условия и границы:** Содержательное название обязательно вне running-аукциона. Новая неизвестная валюта обычно не создаёт игру до ручного применения.

**Код:** [streaming_manager/db/common.py строки 80–90 — normalize_text_key / normalize_title_key](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py#L80-L90); [streaming_manager/twitch_b4.py строки 469–478 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L469-L478); [streaming_manager/donationalerts_runtime.py строки 186–197 — DonationAlertsDonationService.process_donation](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L186-L197); [streaming_manager/db/services.py строки 873–913 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L873-L913); [streaming_manager/db/services.py строки 1003–1046 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1003-L1046); [streaming_manager/db/auction_session.py строки 1681–1701 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1681-L1701); [streaming_manager/db/auction_session.py строки 1800–1848 — AuctionSessionMixin._add_or_increment_auction_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1800-L1848).

### CONV-007 Пустое сообщение внутри аукциона создаёт нумерованный лот

**Состояние:** При условиях.

Обычное внешнее событие без game_id и текста в running-аукционе получает имя «Без текста N». Номер хранится в исходном событии и считается в пределах сессии, поэтому переименование или удаление лота не освобождает его. При неизвестном курсе создаётся видимый лот с нулевым начислением и pending; исходное пустое сообщение остаётся пустым в нормализованной записи. Вне аукциона пустая цель неприменима.

**Доступ:** Автоматически для пустого сообщения во время running-аукциона.

**Условия и границы:** Нумерация и исходная запись относятся к конкретной сессии; общий алгоритм сопоставления названий сохраняется.

**Код:** [streaming_manager/db/services.py строки 629–668 — ServicesMixin._reserve_blank_auction_lot_title_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L629-L668); [streaming_manager/db/services.py строки 810–817 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L810-L817); [streaming_manager/db/services.py строки 861–872 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L861-L872); [streaming_manager/db/services.py строки 920–936 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L920-L936); [streaming_manager/db/services.py строки 1005–1009 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1005-L1009).

### CONV-008 Неприменимое событие сохраняется без начисления

**Состояние:** При условиях.

Общий движок фиксирует неприменимость для отсутствующей/архивной явной цели, временного лота вне running-аукциона, пустой цели вне аукциона, уже не принимающего ставки исходного аукциона или неположительного итога. Исходная запись с причиной остаётся и защищает от повторного начисления; новая игра или вклад при этих исходах не создаются.

**Доступ:** Автоматическая проверка внешнего события.

**Условия и границы:** Для Twitch неприменимость затем приводит к запросу CANCELED; денежное пожертвование DonationAlerts автоматически не возвращается приложением.

**Код:** [streaming_manager/db/services.py строки 587–627 — ServicesMixin._mark_external_event_inapplicable_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L587-L627); [streaming_manager/db/services.py строки 787–800 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L787-L800); [streaming_manager/db/services.py строки 819–913 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L819-L913); [streaming_manager/db/services.py строки 988–1001 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L988-L1001); [streaming_manager/twitch_b4.py строки 495–506 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L495-L506).

### CONV-009 Неизвестный курс откладывает событие без начисления

**Состояние:** При условиях.

Допустимое событие с отсутствующим курсом регистрирует исходную единицу, сохраняет внешнее событие и pending со статусом awaiting_rate, не прибавляя баллы. Сохраняются исходная сумма, единица, отправитель, указание игры/названия и исходный аукцион. Для обычного нового названия создание игры откладывается до применения; отдельное исключение — нулевой лот «Без текста N». После установки курса нужен ручной выбор.

**Доступ:** Автоматически; затем Настройки → Конвертация → «Ожидают применения».

**Условия и границы:** В реальном Twitch-потоке отсутствие курса отменяется до этого общего механизма; типичный текущий путь — DonationAlerts с новой валютой.

**Код:** [streaming_manager/db/services.py строки 706–738 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L706-L738); [streaming_manager/db/services.py строки 915–986 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L915-L986); [streaming_manager/db/services.py строки 361–388 — ServicesMixin._update_pending_rate_status_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L361-L388); [streaming_manager/twitch_b4.py строки 460–464 — TwitchChannelPointsService.process_redemption](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L460-L464).

### CONV-010 Таблица ожидания с расчётом и контекстом

**Состояние:** Доступно по коду.

Очередь показывает источник и отправителя, локальное время приёма исходной записи, внешний ID, название игры/сохранённую цель, исходное значение, рассчитанные целые баллы и множитель либо «Курс не задан». Подсказка добавляет исходный аукцион. Для каждой строки доступны «Применить» при допустимых условиях и «Не применять»; завершённые решения исчезают из очереди, сохраняя историю.

**Доступ:** Настройки → Конвертация → «Ожидают применения»; очередь обновляется при открытии этой вкладки.

**Условия и границы:** Колонка «Время» использует external_events.created_at, то есть локальное время приёма записи, а не обязательно исходное provider created_at/redeemed_at.

**Код:** [streaming_manager/views/settings.py строки 698–733 — SettingsTab.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L698-L733); [streaming_manager/views/settings.py строки 1262–1316 — SettingsTab._refresh_pending_conversion_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1262-L1316); [streaming_manager/db/services.py строки 1246–1274 — ServicesMixin._pending_conversion_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1246-L1274); [streaming_manager/db/services.py строки 1456–1546 — ServicesMixin._pending_row_to_dict](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1456-L1546).

### CONV-011 Ручное применение с подтверждением суммы и курса

**Состояние:** При условиях.

«Применить» показывает цель, источник, исходное значение, текущий сохранённый курс и итог; подтверждение по умолчанию отрицательное. При применении курс заново читается в транзакции, создаётся один взнос и фиксируется applied_rate/credited_sm_points, а внешнее событие становится processed. Повторное применение обработанной строки отклоняется. Изменение курса позже не пересчитывает зафиксированное начисление.

**Доступ:** Очередь конвертации → «Применить» → подтверждение.

**Условия и границы:** Нужны сохранённый курс, положительный результат и доступная цель. Непосредственный метод применения использует актуальный курс из БД; подтверждение не резервирует показанный курс на время открытого диалога.

**Код:** [streaming_manager/views/settings.py строки 1358–1400 — SettingsTab._apply_pending_conversion](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1358-L1400); [streaming_manager/db/services.py строки 1635–1671 — ServicesMixin.apply_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1635-L1671); [streaming_manager/db/services.py строки 1773–1833 — ServicesMixin.apply_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1773-L1833); [streaming_manager/db/services.py строки 1459–1470 — ServicesMixin._pending_row_to_dict](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1459-L1470).

### CONV-012 Окончательно не применять pending

**Состояние:** При условиях.

«Не применять» требует подтверждения с источником, ID, целью и исходной суммой. Решение без начисления переводит обе связанные записи в cancelled, сохраняет исходные данные и журнал, не создаёт взнос и не меняет аукцион. Восстановление через очередь не предусмотрено; смена курса не возвращает cancelled в ожидание.

**Доступ:** Очередь конвертации → «Не применять» → подтверждение.

**Условия и границы:** Доступно только awaiting_rate / awaiting_manual_apply. Это локальное решение о начислении, не возврат денежного пожертвования провайдером.

**Код:** [streaming_manager/views/settings.py строки 1318–1356 — SettingsTab._reject_pending_conversion](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1318-L1356); [streaming_manager/db/services.py строки 1557–1617 — ServicesMixin.reject_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1557-L1617); [streaming_manager/db/services.py строки 362–388 — ServicesMixin._update_pending_rate_status_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L362-L388).

### CONV-013 Очередь учитывает жизненный цикл исходного лота

**Состояние:** При условиях.

Кнопка применения разрешена только для ожидающей строки с положительным расчётом и безопасной целью. Архивная/удалённая игра и временный лот вне подходящего аукциона блокируют применение. Событие с сохранённым исходным аукционом не перебрасывается интерфейсом в новую сессию; допускаются running-источник и отдельная предварительная коррекция Max Amount после нуля. Внешнее к аукциону событие применяется к постоянной игре/названию.

**Доступ:** Состояние кнопки «Применить» в очереди.

**Условия и границы:** Привязка определяется сохранёнными game_id, auction_id и исходным нормализованным названием, а не ручным выбором нового адресата в таблице.

**Код:** [streaming_manager/db/services.py строки 1471–1525 — ServicesMixin._pending_row_to_dict](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1471-L1525); [streaming_manager/db/services.py строки 1660–1736 — ServicesMixin.apply_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1660-L1736); [streaming_manager/views/settings.py строки 1301–1308 — SettingsTab._refresh_pending_conversion_rows](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1301-L1308).

### CONV-014 Pending может исправить предварительный исход Max Amount после 00:00

**Состояние:** При условиях.

Если исходная сессия Max Amount находится в winner_selected или tie_break_required и wheel_spin_id ещё отсутствует, pending может пополнить её сохранившийся лот или добавить допустимое новое исходное название. Пересчитываются сумма/вес, лидер или ничья; таймер не запускается. Удалённые временные лоты и архивные/недоступные цели не восстанавливаются. Подтверждённый/отменённый аукцион и уже зафиксированный розыгрыш этим путём не исправляются.

**Доступ:** Очередь конвертации → допустимое событие исходного Max Amount → «Применить».

**Условия и границы:** Нужен именно исходный незакрытый предварительный результат; проверяются mode, status и отсутствие wheel_spin_id.

**Код:** [streaming_manager/db/services.py строки 1305–1375 — ServicesMixin._post_expiry_title_lot_allowed_conn / _create_post_expiry_title_lot_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1305-L1375); [streaming_manager/db/services.py строки 1377–1454 — ServicesMixin._apply_post_expiry_source_entry_conn](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1377-L1454); [streaming_manager/db/services.py строки 1481–1504 — ServicesMixin._pending_row_to_dict](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1481-L1504); [streaming_manager/db/services.py строки 1673–1722 — ServicesMixin.apply_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1673-L1722).

### CONV-015 Сохранение происхождения и применённого курса

**Состояние:** Доступно по коду.

Применённый вклад сохраняет источник, внешний ID, отправителя, исходную сумму/единицу, конкретный курс и целые зачисленные баллы. Внешнее событие хранит нормализованную цель и безопасные метаданные провайдера; результат журналируется. last_event_at карточки обновляется при успешном автоматическом или ручном начислении, поэтому не означает время любого необработанного/отклонённого входящего сообщения.

**Доступ:** Автоматическое сохранение; сведения доступны дальнейшим экранам истории/журнала.

**Код:** [streaming_manager/db/services.py строки 720–739 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L720-L739); [streaming_manager/db/services.py строки 1048–1099 — ServicesMixin.process_normalized_integration_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1048-L1099); [streaming_manager/db/services.py строки 1773–1823 — ServicesMixin.apply_pending_conversion_event](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1773-L1823); [streaming_manager/views/settings.py строки 1544–1549 — SettingsTab._refresh_integrations](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1544-L1549).

## Локальный HTTP API и медиа

### API-001 Локальный HTTP-сервер и состояние подключения

**Состояние:** Доступно по коду.

При запуске приложения поднимается локальный HTTP-сервер на 127.0.0.1 и сохранённом api_port, обычно 8765. Все адреса OBS строятся от его base_url. Вкладка показывает «РАБОТАЕТ» либо причину ошибки запуска.

**Доступ:** Запуск приложения; Стрим / OBS → Состояние

**Условия и границы:** Порт должен быть свободен; сервер работает, пока запущено приложение.

**Код:** [streaming_manager/views/main_window.py строки 122–126 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L122-L126); [streaming_manager/api_server.py строки 75–96 — LocalApiServer.__init__ / base_url](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L75-L96); [streaming_manager/api_server.py строки 716–723 — LocalApiServer.start](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L716-L723); [streaming_manager/views/stream.py строки 2755–2758 — StreamTab.refresh](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2755-L2758).

### API-002 JSON текущего стрима

**Состояние:** Доступно по коду.

GET /api/data (или /data) отдаёт текущую игру, обычный список, допущенный аукционный список, текст информации, формат, фон, рамки, типографику и политику видимости. Это источник главного и отдельного списочного оверлеев.

**Доступ:** Локальный HTTP GET /api/data

**Код:** [streaming_manager/api_server.py строки 598–600 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L598-L600); [streaming_manager/db/services.py строки 2455–2519 — ServicesMixin.current_stream_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L2455-L2519).

### API-003 JSON публичного списка

**Состояние:** Доступно по коду.

GET /api/public или /public отдаёт объект games с данными публичного списка, определёнными db.public_games().

**Доступ:** Локальный HTTP GET /api/public

**Код:** [streaming_manager/api_server.py строки 601–606 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L601-L606).

### API-004 Экспорт допущенных игр для аукциона

**Состояние:** Доступно по коду.

GET /api/auction-export или /auction-export отдаёт games с id, title, sm_points и совместимым полем sum. Сохранены прежние псевдонимы /api/pointauc и /pointauc. Это выгрузка текущих допущенных игр, а не импорт ставок или удалённое управление.

**Доступ:** Локальный HTTP GET /api/auction-export

**Код:** [streaming_manager/api_server.py строки 25–26 — _LEGACY_AUCTION_EXPORT_SLUG](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L25-L26); [streaming_manager/api_server.py строки 607–622 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L607-L622).

### API-005 JSON состояний специализированных виджетов

**Состояние:** Доступно по коду.

GET /api/wheel, /api/auction-lots, /api/timer и /api/music-player отдают актуальное состояние и оформление соответствующих виджетов; доступны также короткие варианты без /api. Режим, автопрокрутка и звук читаются у владельцев состояния приложения через подключённые провайдеры.

**Доступ:** Локальные GET /api/wheel /api/auction-lots /api/timer /api/music-player

**Код:** [streaming_manager/api_server.py строки 98–126 — LocalApiServer state providers](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L98-L126); [streaming_manager/api_server.py строки 623–658 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L623-L658); [streaming_manager/views/main_window.py строки 177–190 — MainWindow.__init__](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L177-L190).

### API-006 JSON рабочих правил и явного предпросмотра

**Состояние:** Доступно по коду.

GET /api/rules или /rules читает рабочие сохранённые правила. Выбор другого template_id либо follow_token действует только при preview=1; неверный идентификатор/токен даёт 400, отсутствующий шаблон или истёкшая ссылка — 404. Обычный OBS-запрос не может сменить активный шаблон.

**Доступ:** Локальный GET /api/rules; предпросмотр с query-параметрами

**Код:** [streaming_manager/api_server.py строки 660–709 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L660-L709); [streaming_manager/db/rules.py строки 639–699 — RulesMixin.current_rules_payload](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py#L639-L699).

### API-007 Локальная отдача зарегистрированных медиа и обложек

**Состояние:** Доступно по коду.

GET/HEAD /media/&lt;id&gt; выдаёт зарегистрированное медиа разрешённого для категории расширения; абсолютный путь в URL не принимается. Для видео есть byte ranges (206/416). /music-cover/&lt;id&gt; отдаёт извлечённую обложку, /music-placeholder — штатную заглушку; старый /overlay-background/&lt;basename&gt; ограничен отдельной папкой фонов.

**Доступ:** Локальные HTTP-ресурсы виджетов

**Условия и границы:** Файл должен быть зарегистрирован, иметь допустимый тип и оставаться доступным.

**Код:** [streaming_manager/api_server.py строки 236–319 — Handler._send_local_media_path](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L236-L319); [streaming_manager/api_server.py строки 324–409 — Handler._send_background_file / _send_registered_media / _send_music_cover](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L324-L409); [streaming_manager/api_server.py строки 411–438 — Handler.do_HEAD](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L411-L438); [streaming_manager/media.py строки 93–119 — resolve_media_asset_path](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/media.py#L93-L119).

### API-008 Совместимые URL и удобство чтения JSON

**Состояние:** Доступно по коду.

Сервер сохраняет псевдонимы /obs-overlay, /obs-list, /obs-wheel, /obs-auction-lots, /obs-rules, /obs-timer, /obs-music-player и варианты /overlay/&lt;widget&gt;. Query pretty=1/true/yes/on включает форматированный JSON. JSON разрешает чтение из других origin и выдаётся без кэширования.

**Доступ:** Прямое обращение по HTTP к URL источников или JSON

**Код:** [streaming_manager/api_server.py строки 195–219 — Handler._send_json](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L195-L219); [streaming_manager/api_server.py строки 440–474 — Handler.do_OPTIONS / do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L440-L474); [streaming_manager/api_server.py строки 476–565 — Handler.do_GET overlay aliases](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L476-L565).

### API-009 Проверка доступности HTTP-службы

**Состояние:** Доступно по коду.

GET /health или /api/health возвращает ok, имя службы и версию приложения. Неизвестный маршрут возвращает JSON not_found с кодом 404.

**Доступ:** Локальный GET /health

**Код:** [streaming_manager/api_server.py строки 588–597 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L588-L597); [streaming_manager/api_server.py строки 711–711 — Handler.do_GET](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L711-L711).

## Границы текущего интерфейса

Ниже собраны существенные отсутствующие или недоступные входы. Они не включены в 265 записей реализованных возможностей. Служебный метод, тестовый клиент или оставшийся ключ базы сам по себе не означает готовую функцию интерфейса.

### X-001 Ручной порядок музыки и редактирование аудиотегов

В MusicTab есть только алфавитный и перемешанный режимы; UI для drag-and-drop порядка, редактирования тегов, удаления трека и ремонта внешнего пути не создаётся.

Код: [streaming_manager/views/music.py:42](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py#L42-L176).

### X-002 Плейлист и YouTube для саундтрека аукциона

Текущий обработчик _resolved_auction_soundtrack_playlist возвращает один выбранный локальный файл. Старые настройки и более общий движок не дают отдельной действующей пользовательской функции playlist/YouTube.

Код: [streaming_manager/views/auction_parts/audio.py:1242](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py#L1242-L1250).

### X-003 Автоматическое обновление приложения

В стартовой последовательности и текущем интерфейсе не найдено проверки новых выпусков или встроенной установки обновления; установщик и файлы GitHub Actions являются отдельной поставкой.

Код: [app.py:91](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py#L91-L165); [streaming_manager/views/main_window.py:812](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L812-L821).

### X-004 Произвольная ручная сортировка основного списка

В QTableWidget установлен setSortingEnabled(False), предусмотрен фиксированный общий порядок. Кнопка «Правила сортировки» информирует, не редактирует правила.

Код: [streaming_manager/views/games.py:610](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L610-L621); [streaming_manager/views/games.py:968](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L968-L995).

### X-005 Редактирование независимой публичной базы / обратный импорт публичного XLSX

Публичная таблица только для чтения, берёт данные из games; public_xlsx write-only. Подключение публичного XLSX является выбором назначения и перезаписывает содержимое.

Код: [streaming_manager/views/public.py:54](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L54-L58); [streaming_manager/views/public.py:118](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L118-L122); [streaming_manager/views/public.py:152](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L152-L154); [streaming_manager/views/public.py:264](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py#L264-L276); [streaming_manager/public_xlsx.py:78](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L78-L83).

### X-006 Прямой встроенный Google Sheets/Drive API совместной работы

В проверенной цепочке читается/пишется обычный локальный XLSX; Google Drive Desktop/Google Таблицы описаны как способ внешней доставки/редактирования файла. Код этих файлов не даёт основания заявлять серверное совместное редактирование, блокировку или разрешение конфликтов.

Код: [streaming_manager/views/games.py:802](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L802-L807); [streaming_manager/shared_xlsx.py:203](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L203-L208); [streaming_manager/shared_xlsx.py:297](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L297-L308).

### X-007 Полный импорт основной базы из JSON/любого XLSX и UI-режим merge=False

Кнопка «Импорт CSV» всегда вызывает merge=True; JSON присутствует только как публичный экспорт, XLSX-вход ограничен схемой «Совместной таблицы».

Код: [streaming_manager/views/games.py:1529](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py#L1529-L1552); [streaming_manager/exporters.py:26](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py#L26-L34); [streaming_manager/shared_xlsx.py:330](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py#L330-L341).

### X-008 Позиции в разовых публичных CSV/Excel/JSON

CSV/Excel имеют четыре PUBLIC_HEADERS без позиции; JSON games имеет id/title/sm_points/sum/review/status. ПОЗИЦИЯ присутствует в интерфейсе и отдельном автоматически обновляемом публичном XLSX-зеркале.

Код: [streaming_manager/exporters.py:13](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py#L13-L57); [streaming_manager/db/games.py:590](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py#L590-L599); [streaming_manager/public_xlsx.py:15](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py#L15-L21).

### X-009 Экспорт, очистка, откат или редактирование Журнала/Истории из их вкладок

В проверенных UI есть поиск/фильтры/пагинация/чтение/проверка результата, без пользовательских кнопок экспорта, удаления событий или восстановления состояния из журнала.

Код: [streaming_manager/views/log.py:123](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py#L123-L170); [streaming_manager/views/completed_auction_history.py:50](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L50-L231).

### X-010 Точная проверка старого результата без snapshot или новая жеребьёвка из Истории

Отсутствующие snapshot-входы намеренно не реконструируются; verify_wheel_result выполняет только детерминированный пересчёт сохранённых данных без RNG/сети/записей.

Код: [streaming_manager/views/completed_auction_history.py:379](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py#L379-L391); [streaming_manager/db/wheel.py:697](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py#L697-L725).

### X-011 Неиспользуемый отдельный диалог выбора времени

AuctionTimeDialog определён и импортирован, но его вызовов в актуальном приложении нет. Время вводится в общем поле таймера; этот класс не считать отдельной доступной возможностью.

Код: [streaming_manager/views/auction_dialogs.py:10](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_dialogs.py#L10-L58); [streaming_manager/views/auction.py:119](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L119-L119).

### X-012 Приём ставок перед взвешенным колесом — backend-only вариант

create_auction_session допускает weighted_wheel без start_in_wheel_mode и finish_auction переводит такую сессию к колесу, но текущая кнопка запуска для weighted_wheel всегда передаёт start_in_wheel_mode=True и duration_ms=0. Не описывать отдельный период приёма ставок прямого колеса как достижимую UI-функцию.

Код: [streaming_manager/db/auction_session.py:219](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L219-L303); [streaming_manager/db/auction_session.py:3219](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L3219-L3222); [streaming_manager/views/auction_parts/actions.py:151](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L151-L160).

### X-013 Предварительные данные проверки max_amount-тай-брейка скрыты родителем

show_pre_spin_verification умеет читать awaiting_wheel любой сессии, однако кнопка живёт в setup_widget, который для активного max_amount скрыт. Отдельного видимого входа для tie-preview в этой версии не найдено.

Код: [streaming_manager/views/auction.py:408](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L408-L413); [streaming_manager/views/auction_parts/rng.py:310](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L310-L315); [streaming_manager/views/auction_parts/state.py:246](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py#L246-L253).

### X-014 Перегенерация при остановке, пауза колеса и ручная сортировка не заявлены

Видимые действия позволяют остановить анимацию и повторить тот же сохранённый результат либо остановить всю сессию. Отдельного UI для паузы колеса или свободного reroll обычного результата не найдено; у таблицы не включён пользовательский sort по заголовкам. Это границы текущего интерфейса, а не будущие возможности.

Код: [streaming_manager/views/auction_parts/actions.py:14](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py#L14-L29); [streaming_manager/views/auction_parts/rng.py:141](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py#L141-L152); [streaming_manager/views/auction.py:887](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py#L887-L937).

### X-015 HTTP API изменения данных не реализован

В Handler определены GET, HEAD и OPTIONS, разрешённые CORS-методы — GET/OPTIONS. Нет POST/PUT/PATCH/DELETE для создания игр, импорта ставок, активации правил, управления музыкой или колесом. Python-методы сохранения и callback-провайдеры не являются публичными write endpoints.

Код: [streaming_manager/api_server.py:411](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L411-L447); [streaming_manager/api_server.py:713](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py#L713-L715).

### X-016 Файловый импорт/экспорт текста правил не найден

В доступном редакторе есть создание, переименование, удаление, активация и сохранение/сохранение копии шаблона. Кнопок или обработчиков загрузки/выгрузки правил в HTML/JSON/TXT нет. «Добавить фон» импортирует медиа, /api/rules читает JSON, но это не файловый импорт/экспорт шаблонов.

Код: [streaming_manager/views/rules_editor.py:127](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L127-L140); [streaming_manager/views/rules_editor.py:440](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L440-L445); [streaming_manager/views/rules_editor.py:1130](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1130-L1186).

### X-017 Переключатель скрытия главного оверлея не доступен

Политика overlay_show_mode оставлена внутри кода, но UI отсутствует, show_mode принудительно возвращает always, save сохраняет always. Нельзя учитывать её как доступную пользовательскую настройку.

Код: [streaming_manager/views/stream.py:232](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L232-L233); [streaming_manager/obs_visibility.py:33](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py#L33-L58); [streaming_manager/views/stream.py:2768](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py#L2768-L2771).

### X-018 Ручной внутренний отступ правил не доступен

Legacy padding хранится и проверяется в модели ради совместимости. В редакторе регулятора нет, фактический отступ вычисляется автоматически и в Qt, и в CSS.

Код: [streaming_manager/views/rules_editor.py:608](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L608-L612); [streaming_manager/views/rules_editor.py:1016](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py#L1016-L1027); [streaming_manager/web/rules_overlay.html:52](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html#L52-L59).

### X-019 Демонстрационные данные предпросмотра не реальные события

Пример колеса при отсутствии состояния и пример музыкального заголовка без играющего трека служат только визуальной проверке; они не создают лоты или результаты в базе.

Код: [streaming_manager/web/wheel_overlay.html:193](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html#L193-L198); [streaming_manager/web/music_player_overlay.html:654](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html#L654-L659).

### X-020 Ручной DonationAlerts Client ID не показан в текущей обычной сборке

Редактор numeric Client ID, кнопка сохранения и копирование Redirect URI существуют как условная ветка для адаптера без встроенного ID. В проверенном main_window создаётся DonationAlertsAdapter() со встроенным 20915, и UI возвращается до построения этой формы. Не считать текущей общей возможностью пользователя менять Client ID.

Код: [streaming_manager/donationalerts.py:51](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L51-L54); [streaming_manager/donationalerts.py:475](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L475-L486); [streaming_manager/views/main_window.py:95](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L95-L99); [streaming_manager/views/settings.py:1589](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1589-L1636).

### X-021 Устаревшие локальные переключатели приёма и привязки к аукциону

twitch_channel_points_enabled, twitch_rewards_link_to_auction, donationalerts_tracking_enabled и donationalerts_target_auction_id сохранены для совместимости, но текущий приём не использует их как разрешение. Отдельных соответствующих UI-переключателей нет; доступность наград Twitch управляется вручную.

Код: [streaming_manager/twitch_b4.py:28](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L28-L35); [streaming_manager/twitch_b4.py:70](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L70-L76); [streaming_manager/twitch_b4.py:212](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L212-L239); [streaming_manager/donationalerts_runtime.py:18](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L18-L25); [streaming_manager/views/settings.py:1710](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1710-L1715).

### X-022 Симулятор и тестовые пожертвования/погашения не подтверждены как UI-функция

В проверенных production-путях настроек, аукциона и локального API нет действия генерации искусственного события Twitch/DonationAlerts. Fake-клиенты/сокеты предусмотрены через инъекцию для тестов и не являются продуктовым подключением. Проверка соединения читает реальный профиль/права; RANDOM.ORG getUsage диагностирует ключ. Ручное добавление лота/баллов относится к локальному аукциону и не проверяет сервис.

Код: [streaming_manager/views/settings.py:1456](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1456-L1476); [streaming_manager/twitch.py:416](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L416-L434); [streaming_manager/twitch_b4.py:531](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L531-L552); [streaming_manager/donationalerts.py:475](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L475-L491); [streaming_manager/db/auction_session.py:1479](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py#L1479-L1514); [streaming_manager/random_sources.py:127](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py#L127-L128).

### X-023 Другие источники и типы событий не включены в список реализованных сервисов

Основное окно регистрирует Twitch и DonationAlerts. У Twitch разрешён только Channel Points redemption, у DonationAlerts — donation; отдельные адаптеры подписок, Bits, Twitch chat-команд, YouTube, Boosty, DonatePay и других донат-провайдеров этим реестром не зарегистрированы. Возможности базового IntegrationAdapter — контракт расширения, а не готовые сервисы.

Код: [streaming_manager/views/main_window.py:95](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py#L95-L100); [streaming_manager/twitch.py:402](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L402-L414); [streaming_manager/donationalerts.py:462](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L462-L473); [streaming_manager/integrations.py:87](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L87-L115).

### X-024 Произвольные чужие награды и ручные привязки событий не реализованы

Продуктовый Twitch-редактор не принимает произвольный reward ID: колонка ID только для чтения, API управляет only_manageable_rewards, поток подписан на записанные app-managed ID. Отдельного редактора соответствий event/reward → game нет; оба провайдера используют полный текст зрителя как цель с точным нормализованным сравнением, без fuzzy/AI.

Код: [streaming_manager/views/settings.py:1870](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1870-L1873); [streaming_manager/twitch.py:850](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py#L850-L858); [streaming_manager/twitch_b4.py:444](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L444-L446); [streaming_manager/integrations.py:58](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py#L58-L64); [streaming_manager/donationalerts_runtime.py:195](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py#L195-L197).

### X-025 Возврат денег DonationAlerts, refresh-token и удалённый отзыв доступа не заявлены

DonationAlerts использует access token Implicit grant, при истечении требует новый вход; disconnect локальный и не вызывает revoke endpoint. Удалённого возврата денежного пожертвования по неприменимому событию/отказу оператора в реализованном адаптере нет. Twitch CANCELED относится к погашению Channel Points и не является общим денежным возвратом.

Код: [streaming_manager/donationalerts.py:90](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L90-L95); [streaming_manager/donationalerts.py:602](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L602-L614); [streaming_manager/donationalerts.py:679](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py#L679-L683); [streaming_manager/twitch_b4.py:495](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py#L495-L506).

### X-026 Произвольное ручное создание единицы и очереди не является кнопкой настроек

register_conversion_unit, set_conversion_rate и queue_external_conversion_event доступны как программные DB helpers. В production-настройках пользователь видит единицы от подключённых адаптеров/сохранённого реестра и принятых событий, но не свободную кнопку «добавить валюту/сервис/событие». queue_external_conversion_event не вызывается production UI или текущими адаптерами.

Код: [streaming_manager/db/services.py:321](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L321-L338); [streaming_manager/db/services.py:451](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L451-L470); [streaming_manager/db/services.py:1111](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1111-L1134); [streaming_manager/views/settings.py:1187](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L1187-L1249).

### X-027 Автоматический валютный рынок, обратная конвертация и пересчёт всей истории не реализованы

Курс вводится оператором как баллы за единицу; сетевого получения FX-курсов в этом механизме нет. Конвертация односторонняя, а применённые вклады хранят исходный курс/итог. Изменение курса влияет на ожидающие и будущие события, не переписывая уже применённые.

Код: [streaming_manager/views/settings.py:641](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L641-L646); [streaming_manager/views/settings.py:702](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py#L702-L706); [streaming_manager/db/services.py:394](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L394-L449); [streaming_manager/db/services.py:1459](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py#L1459-L1470).

## Наблюдения для последующего сравнения

### Номер версии не определяет весь срез

APP_VERSION остаётся 1.0.8, а код схемы содержит 21 и миграции до 21. Идентификатором этого реестра служит полный коммит. Сравнение только по строке версии может пропустить изменения.

### Минимум вращения колеса

Реальные ограничения времени позволяют вращение от 1 секунды до 24 часов. Встроенный текст справки с минимумом 3 секунды отстаёт от обработчиков. См. AUC-005 и WHL-004.

### Два входа задают разные начальные статусы

Новая карточка в форме начинает с ПРОХОДИТСЯ, а новая запись импорта CSV или пустой статус совместной таблицы — с НЕ ИГРАЛ. См. LIST-007, LIST-017 и LIST-022.

### Дробные баллы при импорте

Форма карточки вводит целое число, но числовой парсер импортов допускает неотрицательную дробь и округляет положительный результат вверх. Текст CSV-справки про исключительно целое число уже этого контракта. См. LIST-019 и CONV-004.

### Разная сохранность истории при удалении

Одиночное удаление записи убирает связанные auction_entries и прежние подробные записи её журнала; массовая очистка сохраняет закрытые снимки и общий журнал. Эти действия нельзя считать равнозначными. См. LIST-014 и LIST-015.

### Черновик правил и рабочий источник

Предпросмотр редактора по токену следует несохранённому тексту и оформлению; рабочий OBS-источник читает сохранённые правила. Подсказка про только сохранённый предпросмотр не совпадает с реализацией. См. RUL-014.

### Прямой импорт фона правил

Редактор правил умеет выбрать GIF или видео из общей библиотеки, но его собственная кнопка импорта фактически пропускает только статические PNG JPG JPEG WEBP. Более широкая подсказка не расширяет этот вход. См. RUL-012.

### Разные виды снимков аукциона

Стартовый состав сессии, живые баллы игры, правила открытого аукциона и проверочный снимок отдельного вращения имеют разные правила изменения. В частности, правила могут обновляться из редактора, а уже определённый результат вращения воспроизводится из сохранённых данных. См. AUC-003, RUL-015 и WHL-013.

### Ожидание конвертации и поздние правки

После нуля ручные прибавка, уменьшение и новый лот имеют другие блокировки, чем удаление, исключение, переименование и подтверждение результата. Интерфейс применения pending также строже некоторых программных помощников базы. Условия сохранены в AUC-024–029, AUC-033 и CONV-013–014.

### Два XLSX решают разные задачи

Совместная таблица заменяет полное состояние постоянного списка в обе стороны; публичная таблица — одностороннее зеркало. Это локальные файлы, а не встроенное серверное совместное редактирование. См. LIST-021–024 и PUB-006–010.

## Карта исходных файлов

Перечень текстовых runtime-файлов зафиксирован ниже. Пустые __init__.py, совместимый AuctionMixin и SVG-заглушка учтены как структурные ресурсы. Бинарные картинки не содержат отдельной бизнес-логики; tools и GitHub Actions относятся к проверке и поставке, а не к дополнительным пользовательским функциям.

| Файл | Строк | SHA256 |
|---|---:|---|
| [app.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/app.py) | 170 | `7a903805e17ac41f15824a04bd43358349c2a6d417a498d151cb421cec4604b4` |
| [streaming_manager/__init__.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [streaming_manager/api_server.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/api_server.py) | 732 | `a27dd0c43b8698acc1d84f8d354e41fb750aa5026f7cc8f9d06d99025d419633` |
| [streaming_manager/app_paths.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/app_paths.py) | 71 | `42d796c3fa2ab58523264811a530a73bf535b9f10be236d8839212e83a5b701e` |
| [streaming_manager/audio.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/audio.py) | 531 | `93ed2f57cbfecc18e20a6b137cbfdfe7da63baf47ff77b8e5794708f38de830a` |
| [streaming_manager/backup_restore.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/backup_restore.py) | 1184 | `d599b5daf588133e5d7484ebd3c2712d83a64a5b95f8ac0011ad48f4587c28ae` |
| [streaming_manager/constants.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/constants.py) | 269 | `64a5acd18263e737d091a133cdf2ff8f1d3e125f3fdf10d5c554253a966bdb87` |
| [streaming_manager/conversion.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/conversion.py) | 180 | `1ae561d5d76e351d9f38ac7d9dbbbac76d3d49149b27ddbcbcbda5bad8583bb0` |
| [streaming_manager/credentials.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/credentials.py) | 230 | `d51052233ce8da3f888da1f748b457d8bb7d9d7e24f28305e594f14fd79e200a` |
| [streaming_manager/database.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/database.py) | 58 | `621f6ea248c629758a081ded167145e0c9df565cc75e8cb394c98bc0bcbf0034` |
| [streaming_manager/db/__init__.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [streaming_manager/db/auction.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction.py) | 10 | `5872910fe213a12c0f2172248ec6432794665470e326a4077abcb76e29d25a5c` |
| [streaming_manager/db/auction_session.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/auction_session.py) | 3642 | `20869bb0633226dda8b3b89685f2a9b918d95408e78f3cfbf784373651f79565` |
| [streaming_manager/db/common.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/common.py) | 209 | `103a1a4682261f5a809c6a5cb5adc0740b00ad8b8c0446739af940ec0a1bef1e` |
| [streaming_manager/db/games.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/games.py) | 637 | `a05df4cb14e22a408a30c3d650935de7772b562f91362fa5d15a2d6268bac04f` |
| [streaming_manager/db/integrations.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/integrations.py) | 198 | `e145dab2412a2b24b96234ca503ea352407156882f3e33c28a7c879371261a90` |
| [streaming_manager/db/media.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/media.py) | 605 | `cb5e6b8bb62210ea8849402bb4577d32d10bf49938a4f792b705403f8158f558` |
| [streaming_manager/db/rules.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/rules.py) | 774 | `382a4b5a9d7c9ae62ff91635ade9fa108f23db551b9ce01b208c30f681b759b9` |
| [streaming_manager/db/schema.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/schema.py) | 1369 | `cde2388666fe1ff245039d7dfcb9e56cfdd2747594b03a154b0d6e0476b4d0b6` |
| [streaming_manager/db/services.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/services.py) | 2920 | `b0e5eff605854997592f11cb3f78cc393297e8e8a4ec9ce167a3ceb2fc23937f` |
| [streaming_manager/db/wheel.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/db/wheel.py) | 1357 | `e12ac695b2a9afc4676187c5279d7829691a0190fe679d4079daddb98f1f5d83` |
| [streaming_manager/default_wheel_icon.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/default_wheel_icon.py) | 116 | `36f36ba9b04b7d74bd1099d5a7dc7481b128c9d1d17699272ea01cfb67b38100` |
| [streaming_manager/diagnostic_logs.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/diagnostic_logs.py) | 102 | `0870f42b83226c75d20ae4f1bf804d061e8efab6a43181a9ebbcfd1d87614ca3` |
| [streaming_manager/donationalerts.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts.py) | 784 | `40022b099c614ce6d94ff8fba77249af1003655e331b03fb72e180b2613d4672` |
| [streaming_manager/donationalerts_runtime.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/donationalerts_runtime.py) | 589 | `048e2b32c050faaacf456c95883ce434d00e697a042955091f222541cb31c8fc` |
| [streaming_manager/emote_catalog.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/emote_catalog.py) | 295 | `2874e413b2e7bd9434a7b1c0900ea7a1a39be374ee486a6df3b9c6d16cfe29b4` |
| [streaming_manager/exporters.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/exporters.py) | 57 | `39e2b3bc1c0fa54ee121a5408ce2b85cfa04dfea8849c7f99237118a93afc9a6` |
| [streaming_manager/input_guard.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/input_guard.py) | 137 | `69847996db0006deec7bebca07bb1bbd60f445f1b4a9589f6408ef70ee8cb88e` |
| [streaming_manager/integrations.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/integrations.py) | 495 | `600b74976395594b9e1787dca19a05a3fb86a1761b8c5fb2de105c23c4a4208c` |
| [streaming_manager/media.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/media.py) | 127 | `6db2e8eb21a12c4671da57cff5d7ae501eca6b2b1861e71425e2524f6cdabec3` |
| [streaming_manager/music_player.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/music_player.py) | 914 | `e8aff7fe0945aaf865d1c7567c95e3c6495c0c552711a41ecdca763a4e1c9e22` |
| [streaming_manager/obs_visibility.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/obs_visibility.py) | 108 | `8865ca281ec2c852e0758ca6e97e519e0d457f554e3a08a572a1f071c6c4dfb2` |
| [streaming_manager/position_policy.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/position_policy.py) | 50 | `7780fa2e144f290794fd4aebe4ec963a722b2c6361799efb13793640bcfdbee8` |
| [streaming_manager/public_xlsx.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/public_xlsx.py) | 168 | `2618951ec90d9fe1e9bbe43f868061e86d4b7f32b87616873d41352df4333f46` |
| [streaming_manager/random_sources.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/random_sources.py) | 264 | `a2ba8b31f863264edf0cd68802aa25802cd8cf3f5a86d729b6614e6dc938bd38` |
| [streaming_manager/remote_image.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/remote_image.py) | 410 | `ff1c222ba8876ad4e4e777535da3a10f2b7e567d0e5f979ce1c3f310d95d5640` |
| [streaming_manager/rules_html.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/rules_html.py) | 104 | `e5081cc0983e13299956e45e1ba5ddc71457d98e0a60791299e6c765746c8182` |
| [streaming_manager/shared_xlsx.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/shared_xlsx.py) | 410 | `5754a56cb1f0320e1187716dcb789ac43bea3f44ffa568c37eb87e40e1625383` |
| [streaming_manager/single_instance.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/single_instance.py) | 19 | `7484185d85290ec915efa68f8aee7252fe9e4b77d6843ba525cf3b0488faf2b5` |
| [streaming_manager/time_input.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/time_input.py) | 62 | `d696c3b8873f4d2801f1fc1e3beca621dd669a9a85b0e1eb926ac5a6d8823065` |
| [streaming_manager/twitch.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch.py) | 1030 | `862c1aeca73d24dbaeeb2dabbe39a5a7cf3f7e9afd633ec8df206225007226fe` |
| [streaming_manager/twitch_b4.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/twitch_b4.py) | 735 | `7f242323fef191059b1c3754ba582cb85834ed0366a0e1ea0a01c18423f6064b` |
| [streaming_manager/ui.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/ui.py) | 24 | `0253a9e4b25ffa6735dd3a7829bca5ceffe8eac7c22ba34efa466638f63b9af2` |
| [streaming_manager/ui_settings.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/ui_settings.py) | 180 | `81c055a0ba855918954d58ed05030c7a8503e78215395c9b8a85f4c578e1dc88` |
| [streaming_manager/views/__init__.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [streaming_manager/views/auction.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction.py) | 2742 | `146c7bf4249f7d62f7bf6a9c3c5fcf87888bcc7952c76fbe44c48cbf9b9f080a` |
| [streaming_manager/views/auction_bets.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_bets.py) | 60 | `b868930e49a3d3e9d10ed99dc0ed226af086178e004d47cb1d224d8914b5c203` |
| [streaming_manager/views/auction_dialogs.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_dialogs.py) | 58 | `7b614c683e299b052e1f39a9f40e6a7fd514c14fed5c0bb5fe3a93e72b0cabd9` |
| [streaming_manager/views/auction_history.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_history.py) | 441 | `6bd7dbf7ab811f70cfa6312b5dc4113739eb6a3ffd83dbfeba6b4b47d51162d8` |
| [streaming_manager/views/auction_parts/__init__.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [streaming_manager/views/auction_parts/actions.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/actions.py) | 963 | `8980a2d7ae57789cefff71453a8d345add19eef29ec154afb9df886f49b04fac` |
| [streaming_manager/views/auction_parts/audio.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/audio.py) | 1480 | `766f87aa4e86a83f7b36ecd5bb5a0e76577bd7c5417a793227876a04abf3effe` |
| [streaming_manager/views/auction_parts/rng.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/rng.py) | 463 | `a749580f78c4a6b3477b4b7416eb3bfdf85fc7e7f86d307b9441f455a49c4676` |
| [streaming_manager/views/auction_parts/search.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/search.py) | 120 | `9302ca6ea77481efb605b0eeff707555a4722a36b730565eebd00601add0c7a8` |
| [streaming_manager/views/auction_parts/state.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/auction_parts/state.py) | 944 | `9b353fc06dd6068e48ba979087be4256b8dd2d6548ebdba291af849f9e21aaf0` |
| [streaming_manager/views/common.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/common.py) | 776 | `5444a50ac6d44d3dd6997b4586928fd9acd9735bf7ac79267baa41262746cd13` |
| [streaming_manager/views/completed_auction_history.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/completed_auction_history.py) | 600 | `ceb0b47779892fe24e32f22bc053dd49ab60c1ccc53a04f955cc347080e67bd0` |
| [streaming_manager/views/games.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/games.py) | 1596 | `a7ee1b580bf5086d5af0a73e31ddf9a62510a4831e3539daf1f5122ecb0b013b` |
| [streaming_manager/views/log.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/log.py) | 528 | `3cf83b35b1c9226c19961bdbfbd0b425a78d6d6291512e72802f3cc249e5f679` |
| [streaming_manager/views/main_window.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/main_window.py) | 956 | `75c6b4d581838a55c40a69958553b30765c206516fc76ca3dfa65ec7603382cd` |
| [streaming_manager/views/music.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/music.py) | 600 | `5f6205030733b04cc0fb2b4e272abd9cb1b12164f67732c3a83d0f5181aaf234` |
| [streaming_manager/views/public.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/public.py) | 577 | `bd1c7ee5d99b84fd4deeb3656b6ae3e5f6a51a488f24b88c2d2cb3a29fb83454` |
| [streaming_manager/views/rules_editor.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/rules_editor.py) | 1417 | `f86d3c6e953bfba559f82fb88b5316e796a4ad79d0c32c9de8b8fa7e276c6684` |
| [streaming_manager/views/settings.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/settings.py) | 2816 | `5a5c11c38264d52c177c89258bfdf00778dbf15a2526dfe3c897635eb1064f77` |
| [streaming_manager/views/stream.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/stream.py) | 2803 | `6a804084f29f7c56dbad3c1412276e701096c5241f20f3c4df1479c4d01081f6` |
| [streaming_manager/views/wheel.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel.py) | 674 | `9564381ca37c1ce296523126b7c2bc2cee877657f1534264eaeb78ea00d99490` |
| [streaming_manager/views/wheel_center_picker.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/wheel_center_picker.py) | 250 | `7be00cc1d23f929992c19cb0be7659ea50237aa43aee00288f9ca4608e6d5016` |
| [streaming_manager/views/winner_verification.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/views/winner_verification.py) | 120 | `7dc60d6a48cabd4d860baac47df49263d1c8a9a51a92101fb496a9315950a918` |
| [streaming_manager/web/auction_lots_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/auction_lots_overlay.html) | 595 | `7f8b35599b153ff1f6f8abcf32ed520129d087a1628a5bee85d65faeba7e8205` |
| [streaming_manager/web/list_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/list_overlay.html) | 403 | `f4bbe3b23d3b623a3925498db8d08a1a8fa90f3671a4d2a7f9c75e514b98df11` |
| [streaming_manager/web/music_placeholder_note.svg](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_placeholder_note.svg) | 8 | `4cbd39cf9536e3dc876aba456287bd7cbff321df83dd778d6d331c40762b94d9` |
| [streaming_manager/web/music_player_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/music_player_overlay.html) | 701 | `ac130a8fb45652354ded9b8f7cd8d29ffb655ddb97dee4e2ed918d6173b1ecd2` |
| [streaming_manager/web/obs_visibility.js](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/obs_visibility.js) | 30 | `7a048810ee7a8873cfafa0520cd42d620c41fd70322ec789d3b1d2437d83e949` |
| [streaming_manager/web/overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/overlay.html) | 1134 | `4579111f803daccd86c6ef2d3672b4ca372a7a5fee91e24385f433b2e9655d17` |
| [streaming_manager/web/rules_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/rules_overlay.html) | 334 | `ae5c054f5511bb0dcf8942c480352ff9310d412bd198e5070417df4a098e7fea` |
| [streaming_manager/web/timer_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/timer_overlay.html) | 439 | `f453bc7b11e620505bcf817c8c0b8999a0beca7dfbab2eef4ef0a753a7ebb32a` |
| [streaming_manager/web/wheel_overlay.html](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/web/wheel_overlay.html) | 379 | `a4c8824e84f8468ef7f7cc7aa898267181554c592f5c06af2e7268e9f7c6261b` |
| [streaming_manager/wheel_center_media.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/wheel_center_media.py) | 71 | `7def8c5cbd0f40d5c8012271641693155211fec0214e23ed4e50976338771c27` |
| [streaming_manager/wheel_motion.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/wheel_motion.py) | 59 | `e5394f24149aa3ed8d79b9a374ae1141d91f10b6a8095fc42e44c02c73e53d11` |
| [streaming_manager/windows_long_path.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/windows_long_path.py) | 191 | `6a645777c5c41c23ab5e9660fae9001cb67236f97b8e068a138bdda718e0f357` |
| [streaming_manager/workers.py](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/streaming_manager/workers.py) | 46 | `fd162de69d90f9f4f2360f73ad90ea7aba2980c6b83a9ba5ca4ba2fa2adfc742` |

Установщик: [installer/InOneLine.iss](https://github.com/ALL-EX-E/InOneLine/blob/5101439b2e0177a7e7b248955e7438084352d95b/installer/InOneLine.iss).

Конец реестра — 265 записей функций и 27 записей границ интерфейса.
