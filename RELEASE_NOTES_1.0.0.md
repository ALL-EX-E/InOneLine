# InOneLine 1.0.0

Первый стабильный публичный релиз InOneLine.

## Что входит в 1.0.0

- единое Windows-приложение для управления играми, публичным списком и аукционом;
- проведение аукциона в режимах max amount и weighted wheel;
- отображение шанса победителя по зафиксированному результату wheel run;
- таймеры и дополнительное время при ничьей;
- Twitch и DonationAlerts integrations;
- пять OBS Browser Sources;
- CSV / JSON / Excel export;
- backup / restore;
- installer с сохранением данных при reinstall/update;
- исправления UI для минимального окна 1100×700.

## Проверка релиза

Финальная R1.0.10 прошла:

- Windows build/installer QA: **12/12 PASS**;
- cold-start UI gate 1100×700;
- frozen startup/API;
- все 5 Browser Sources;
- SQLite schema 18 / 14 named migrations;
- backup/restore;
- reinstall/update;
- shortcuts / Installed Apps;
- uninstall workflow;
- ручную UI-проверку.

## Официальные артефакты

### Installer

`InOneLine_Setup_1.0.0.exe`

- Размер: `45 457 945` байт
- SHA-256: `7a2ff7575574898622ceff041bb0ef0ddb85dd7a16190a5bdb6ae7b261b3c8fd`
- FileVersion: `1.0.0.0`
- Authenticode: `NotSigned` — проект не использует платный сертификат Authenticode публичного доверия; Windows может показать предупреждение SmartScreen/«Неизвестный издатель»

### Exact accepted source archive

`InOneLine_Source_1.0.0.zip`

- Размер: `1 264 987` байт
- Файлов: `76`
- SHA-256: `3ffdc14c164fe8e59e1c057e2917d219a6ffe01e4b2d785d38bd8dd72d78a8b8`
- ZIP CRC: PASS

GitHub автоматически формирует `Source code (zip)` и `Source code (tar.gz)` из дерева репозитория на теге `v1.0.0`. Они не являются byte-identical копией принятого SOURCE ZIP; для точной воспроизводимости используется отдельный `InOneLine_Source_1.0.0.zip`.

`InOneLine_Source_1.0.0.zip` сохранён byte-identical с принятым SOURCE и может не содержать более поздние публичные метаданные репозитория, включая `LICENSE`. Условия текущего файла `LICENSE` применяются к InOneLine и его исходному коду.

## Разработка с использованием ИИ

InOneLine разрабатывался автором при помощи **ChatGPT от OpenAI**. ChatGPT использовался в процессе проектирования, написания и проверки кода, отладки, подготовки тестов и документации.

Другие нейросети при создании InOneLine не использовались. Окончательные решения по проекту, запуск сборок, ручное тестирование и приёмка релиза выполнялись автором проекта.

## Лицензия

InOneLine можно бесплатно использовать, копировать, изменять, переписывать и распространять бесплатно. Платное распространение оригинальной или модифицированной/производной версии запрещено.

Полные условия находятся в файле [LICENSE](./LICENSE).
