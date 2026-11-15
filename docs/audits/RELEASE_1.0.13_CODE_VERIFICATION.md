# Проверка выпуска InOneLine 1.0.13

## Граница выпуска

Версия 1.0.13 публикует уже принятые исправления журнала: чистая первая установка не создаёт служебные строки начальной настройки, реальные изменения музыкального плеера видны при открытии журнала, а явные действия Twitch и DonationAlerts записываются без секретов. Схема базы остаётся 21.

## Приёмка

15.11.2026 пользователь установил точный кандидат из [PR №436](https://github.com/ALL-EX-E/InOneLine/pull/436) и ответил: «Всё работает. Принимаю.» Принят HEAD `fa57f4f587caee7ccea0440156e417fdb956327b`, Windows CI `43660818230` и artifact `14140218736`.

- QA ZIP: 53 135 943 байта, SHA-256 `af4d03237223c6b115d164638a60c56c3605e7465909e816399891db576bd7d4`.
- `InOneLine_Setup_1.0.13.exe`: 48 691 966 байт, SHA-256 `919357852384e69b723c6b5eecea8cb0873220bd3b94f3d955c1699989261012`.
- `InOneLine_Source_1.0.13.zip`: 4 440 115 байт, SHA-256 `bea6076e656f14cb8da88daabaf6d7c2dd233638a30b4239fcef70af15721dce`.

Drive-readback подтвердил размеры и SHA-256 QA ZIP и установщика. Независимая финальная проверка ветки не нашла Critical, Important или Minor замечаний.

## Публикация

PR №436 слит merge-коммитом `1027aa953077fca9f3c07734b5f9074bef1743b4`. Независимые push-проверки [Windows CI 43711650895](https://github.com/ALL-EX-E/InOneLine/actions/runs/43711650895) и [wording gate 43711650922](https://github.com/ALL-EX-E/InOneLine/actions/runs/43711650922) завершены SUCCESS.

Immutable request `.github/release/requests/v1.0.13.json` добавлен коммитом `7f2d2f5632b3a3333abf158db5800bef36139ead`. [Publisher 43713623030](https://github.com/ALL-EX-E/InOneLine/actions/runs/43713623030) скачал принятый artifact, проверил хеши, создал [GitHub Release v1.0.13](https://github.com/ALL-EX-E/InOneLine/releases/tag/v1.0.13) и повторно скачал оба asset. Релиз не является draft/prerelease, target — `1027aa953077fca9f3c07734b5f9074bef1743b4`. Независимое публичное скачивание подтвердило те же размеры и SHA-256. Выпуск v1.0.12 и его assets сохранены без изменений.
