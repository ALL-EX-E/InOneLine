# InOneLine 1.0.8

Функциональный patch после принятой 1.0.7. Global Conditional UI Visibility candidate прошёл автоматические Windows-gates и полный focused manual QA перед публикацией.

## Conditional UI Visibility

Интерфейс теперь различает два состояния:

- **логически неприменимые** элементы скрываются;
- элементы, которые всё ещё применимы, но **временно недоступны**, остаются видимыми и disabled.

Это убирает постоянный серый UI-мусор, но не заставляет интерфейс прыгать во время коротких worker/RNG/connection lock-состояний.

### Stream / OBS

- Timer: «Цвет фона» показывается только для режима Color.
- Auction Lots: «Цвет фона» показывается только для Color; «Свой фон» — только для Custom.
- Rules: цвет и непрозрачность фона показываются только для Color.
- Основной overlay:
  - положение веб-камеры скрывается, когда webcam block выключен;
  - сторона списка скрывается, когда list block выключен;
  - положение информации скрывается, когда info block выключен;
  - строки цвета рамки webcam/list/info скрываются вместе с соответствующим блоком;
  - Top-1/Top-2/Top-3/list typography скрывается вместе со списком;
  - typography дополнительной информации скрывается вместе с info block.
- Существующая D26 conditional visibility Music Player сохранена без изменений.

### Настройки аукциона

Для автопродления:

- время каждой причины скрывается, пока причина OFF;
- «Также учитывать неденежные единицы интеграций» скрывается, пока External donation OFF;
- поле threshold duration скрывается, пока threshold OFF.

Сохранённые значения не удаляются при скрытии.

### Игры

- Для активной выбранной игры показывается только «В архив».
- Для архивной выбранной игры показывается только «Восстановить».
- Без выбранной игры обе взаимоисключающие кнопки скрыты.
- Если применимое действие временно заблокировано worker-операцией, оно остаётся видимым, но disabled.

### XLSX connections

- Public XLSX: «Отключить» скрыта, если таблица не подключена.
- Shared XLSX: «Отключить» скрыта, если таблица не подключена.
- Во время временной worker-операции существующая Disconnect-кнопка остаётся видимой и может быть disabled.

### Аукцион и история

- «Удалить лот» видна только при running-аукционе и выборе временного auction-only lot.
- В истории завершённых аукционов verification actions скрыты, если snapshot отсутствует.
- Random.org+ proof action сохраняет прежнюю условную видимость.

## Намеренно не изменено

Временные/safety lock-состояния остаются disabled, а не hidden:

- активные file copy/import/backup/restore workers;
- RNG preparation, active spin и timer safety states;
- integration actions, временно недоступные из-за состояния provider;
- concurrent/destructive mutation locks.

## Compatibility

- SQLite schema: **19**
- Named migrations: **15**
- Database migration: **нет**
- RNG / winner selection: **без изменений**
- Обновление с 1.0.7 сохраняет все значения; скрытые controls продолжают использовать сохранённые данные при повторном появлении.

## Verification

Accepted candidate commit:

`af29d033d5d8cf6bcb774355771121c1bdc7d10f`

Automated Windows candidate gate:

`36739896076` — SUCCESS

Publication wording gate:

`36739896140` — SUCCESS

Manual Windows QA:

**PASS 1–10 / FINAL**
