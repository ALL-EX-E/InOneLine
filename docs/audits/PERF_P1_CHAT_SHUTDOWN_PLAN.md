# PERF P1: завершение чата и его сетевых загрузок — план реализации

> Исполнитель: текущая сессия, последовательно; superpowers:executing-plans, TDD и один независимый обзор всего пакета. Пользователь подтвердил первый пакет ответом «Делаем» 31.10.2026. Дополнительные runtime-пакеты аудита не выполнять.

**Goal:** после подтверждённого закрытия прекратить задачи ChatRichFeed и освободить его сетевые процессы, в том числе при зависшем DNS; сохранить текущие картинки, анимации, UI, настройки и R06 ZERO.
**Architecture:** существующие executor (3 задачи), кеши и Qt-декодирование остаются. Блокирующий stdlib HTTP/DNS одной картинки выполняется внутренним app.py helper без Qt/SQLite/секретов. Родитель ждёт его с общим deadline и Event cancellation; по завершении или отмене обязательно собирает только свой дочерний процесс. Повторно используется неизменная логика URL/DNS/redirect/bytes и подготовки изображения.
**Tech Stack:** Python 3.12, PySide6 6.11.2, subprocess, urllib; версии зависимостей прежние.
**Spec:** основной рабочий документ, запись «СОГЛАСОВАНО — PERF P1», и PERFORMANCE_AUDIT_2026-10-31.md, пакет 1.

## Global Constraints

- Один пакет за раз; main, R06 PR №383 и новые анимации не продвигать.
- Внешний вид, настройки, сообщения, OBS API, аукционные правила и пользовательские данные не менять.
- Не убивать основной процесс; сетевой helper владеет только временными сетевыми ресурсами и не пишет пользовательские данные.
- Не отключать URL/DNS/redirect/размер/формат проверки, TLS-проверку и защиту Windows.
- Полный сетевой запрос ≤15 с, включая запуск/DNS/redirect/body; проверка cancellation каждые ≤100 мс; уборка своего helper ≤1 с; frozen EXE на чистом QA обычным WM_CLOSE ≤10 с.
- Не более 3 сетевых helpers одновременно, в простое и после закрытия 0; существующий executor не создавать заново после shutdown.
- Windows CI и реальная загрузка установщика на Google Диск обязательны до запроса ручного PASS.

## Review Focus

- Отмена выхода и неуспешное Save: работоспособность чата, таймеров, соединений сохраняется.
- DNS без ответа, медленно поступающее тело и redirect: deadline общий, child всегда собран, GUI не ждёт DNS.
- Приватный/смешанный DNS, redirect в локальную сеть, неверный MIME и превышение размера: прежние guards работают.
- Гонка close/enqueue/finished: новых задач/потомков после shutdown нет, QMovie не возобновляется.
- Frozen onedir и длинный путь Windows: internal helper запускается без GUI/instance lock и не оставляет процессов.

## Approaches and ruling

Исправить только shutdown executor недостаточно: уже выполняющийся urllib/getaddrinfo остаётся. QtNetwork тоже использует QHostInfo thread pool, ожидаемый при destruction (проверен Qt 6.11.2 qhostinfo.cpp). Выбран короткоживущий изолированный сетевой helper по существующему internal-helper шаблону backup. Постоянный IPC-сервис добавил бы вторую долгоживущую подсистему, поэтому здесь не вводится. Это технический выбор исполнителя в согласованном первом пакете; его стоимость запуска и число процессов проверяются.

### Task 1: отменяемая ограниченная загрузка

**Files:** создать streaming_manager/remote_image_http.py (перенос существующей чистой HTTP-логики), streaming_manager/chat_image_download.py; изменить remote_image.py только на переиспользование HTTP-модуля и app.py internal-helper dispatch. Тесты tools/shutdown_lifecycle_smoke.py и tools/chat_image_network_fixture.py.
**Interfaces:** fetch_chat_image_bytes(url: str, *, cancel_event: Event | None = None, timeout: float = 15.0) -> tuple[bytes, str, str]; результат raw image, display name и final URL. run_chat_image_helper() -> int читает один bounded JSON request из stdin и пишет bounded JSON header + raw bytes; URL не передаётся в argv. Существующие public remote_image функции и типы сохраняются.

- [ ] Записать воспроизводящие тесты: pending queue after parent close; real child blocked in DNS; slow body total deadline; cancel before spawn; normal payload bytes; MIME/private URL/redirect/size отказ; helper ownership cleanup.
- [ ] Выполнить RED на исходных байтах: увидеть дефект очереди/отсутствие отменяемого backend, сохранить лог.
- [ ] Перенести чистые HTTP-функции без изменения условий в remote_image_http; добавить helper dispatch до Qt GUI импорта.
- [ ] Реализовать ограниченное ожидание subprocess.communicate, cancellation и finally cleanup; старые remote_image функции используют те же HTTP-функции.
- [ ] GREEN адресных тестов: реальные дочерние процессы и локальный сервер, без внешних сервисов/credentials.
- [ ] Коммит логически завершённого backend/тестов; результат и отклонения в ledger.

### Task 2: жизненный цикл feed и родителя

**Files:** streaming_manager/views/chat_rich_feed.py, views/multichat.py, views/main_window.py; тесты shutdown_lifecycle_smoke.py и существующие chat smoke.
**Interfaces:** ChatRichFeed.shutdown() -> None, MultichatTab.shutdown() -> None идемпотентны. _fetch_chat_image(url, cancel_event=None) сохраняет прежний формат результата (RemoteImageResult, scaled QImage). closeEvent feed делегирует shutdown; MainWindow вызывает tab.shutdown только после успешного решения Save/Discard; aboutToQuit также останавливает владельца.

- [ ] RED реального родительского окна с 9 задачами: оставшиеся 6 queued должны отменяться, active загрузки получать cancellation, таймеры и movies остановлены; закрытие не запускает новые tasks.
- [ ] Подключить backend из Task 1, Event и запрет поздних enqueue/prefetch/display/result после shutdown.
- [ ] Добавить явное завершение владельца из MainWindow и aboutToQuit, сохранив Cancel/Save guards.
- [ ] GREEN сценариев Cancel, Save failure/success, Discard, repeated shutdown и GUI/картинок/анимаций/OBS; проверить реальный process exit с slow DNS/HTTP.
- [ ] Запустить полную применимую исходную regression-suite; Windows-specific проверки выполняет native CI. Коммит и ledger.

### Task 3: Windows frozen gate, сборка и ручной кандидат

**Files:** tools/shutdown_lifecycle_smoke.py, .github/workflows/regression-foundation-1.0.8.yml, docs/qa/PERF_P1_manual_checklist.md, основной документ.

- [ ] Добавить native frozen режим: обычный WM_CLOSE, ожидание выхода root PID, отсутствие его потомков и освобождение порта; force используется только для уборки уже проваленного теста.
- [ ] Включить адресный shutdown smoke и frozen gate в прежний Windows workflow; push только candidate/perf-p1-chat-shutdown, отдельный candidate artifact с BUILD_INFO и хешами.
- [ ] Один независимый обзор всего diff; устранить существенные замечания с RED→GREEN.
- [ ] Выполнить native Windows CI существующим toolchain и существующую сборку Inno Setup. Не считать успехом одно лишь создание файла.
- [ ] Скачать artifact, CRC/SHA сверить с BUILD_INFO, загрузить тот же installer на Google Drive и проверить обратным чтением байтов.
- [ ] Основной документ и Drive синхронизировать; отметить WAITING MANUAL QA, выдать короткую полную инструкцию этого пакета. До ручного PASS не переходить к PERF P2.
