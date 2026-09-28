# InOneLine 1.0.3

Патч-релиз после принятой 1.0.2.

## Что изменилось

- В «Настройки → Аукцион → Автопродление таймера» активирована ранее подготовленная причина **«Внешнее пожертвование»**.
- У причины используется существующее настраиваемое время продления.
- Добавлена сохраняемая галочка **«Также учитывать неденежные единицы интеграций»**.
- По умолчанию дополнительная галочка выключена.
- При выключенной дополнительной галочке внешнее автопродление учитывает денежные/currency события.
- При включённой — дополнительно учитывает provider-neutral service units: Twitch Channel Points, будущие баллы/очки VK и аналогичные единицы других интеграций.
- Денежная причина и service-unit причина разделены в audit trail как `external_donation` и `external_service_unit`.
- Для обеих причин используется существующий общий S2 timer-extension backend, threshold/collision rules и 24-часовой ceiling.
- Pending conversion events сохраняют правильную currency/service семантику после последующего применения курса.

## Совместимость данных

- SQLite schema: **18**;
- named migrations: **14**;
- новой миграции нет;
- новая настройка хранится в существующей таблице settings;
- обновление поверх 1.0.2 сохраняет пользовательские данные.

## Проверка

Точный кандидат `0ca60eb11f3e33c3ed6d5f52f80d84fb3c2145c7` прошёл:

- source/DB/UI regression gate;
- currency-event auto-extension;
- service-unit OFF;
- service-unit ON;
- pending currency;
- pending service unit;
- parent external reason OFF;
- persistence/UI enable/disable behavior;
- PyInstaller build;
- Inno Setup build;
- silent install;
- frozen startup/API smoke;
- ручную Windows-проверку пользователем: PASS.

После ручной приёмки installer не пересобирался.

## Официальные артефакты

### Installer

`InOneLine_Setup_1.0.3.exe`

- Размер: `46878242` байт
- SHA-256: `b36f56743aec734c628abe45bbc37fc6ce2beb6cee867591fc7421a6f679b44e`
- Authenticode: `NotSigned`

### Exact accepted source snapshot

`InOneLine_Source_1.0.3.zip`

- Размер: `1265529` байт
- Файлов: `77`
- SHA-256: `12e0981b4b13953654d78656e1f514a88ec44d6dd0d2470c7e2f4dc685a2c6df`
- ZIP CRC: PASS

SOURCE сформирован из канонического exact SOURCE 1.0.2 с заменой только пяти файлов, реально изменённых и прошедших проверку в принятом 1.0.3 candidate commit. Служебный candidate-workflow и более поздние публичные release-метаданные не входят в официальный SOURCE ZIP.

## Разработка с использованием ИИ

InOneLine разрабатывался автором при помощи **ChatGPT от OpenAI** для проектирования, написания и проверки кода, отладки, тестов и документации. Окончательные решения, сборка, ручная проверка и приёмка релиза выполнялись автором проекта.

## Лицензия

Полные условия находятся в файле [LICENSE](./LICENSE).
