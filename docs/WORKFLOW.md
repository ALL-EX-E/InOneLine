# Development and Release Workflow

## Основной цикл

1. Выбрать ровно один scope.
2. Выполнить fresh review против exact CURRENT.
3. Зафиксировать точный scope и получить явное одобрение пользователя.
4. Реализовать изменение в candidate-ветке, reuse-first.
5. Прогнать automated gates.
6. Собрать Windows candidate.
7. Провести сфокусированную ручную Windows-проверку.
8. При дефекте исправлять только candidate, выпускать новый FIX и повторять только нужные проверки плюс regression gates.
9. После полного PASS получить явную пользовательскую приёмку.
10. Продвигать **точно проверенные bytes**, не пересобирая installer/source после ручной приёмки.
11. Source ZIP собирать только из Git-tracked файлов через `tools/create_source_snapshot.py`; запрещено архивировать post-build workspace копированием каталога.
12. Для публикации создать новый immutable request в `.github/release/requests/` с exact artifact ID, target commit, именами файлов и SHA-256; единый `publish-accepted-release.yml` проверяет bytes, запрещает overwrite существующего tag/release, публикует без пересборки и повторно проверяет опубликованные SHA-256.
13. Обновлять `docs/PROJECT_STATE.md`, `docs/ROADMAP.md`, QA и решения.
14. Только после этого считать версию CURRENT/released.

## Active Review Ledger — текущий режим

Пока пользователь не отменит этот режим, разработка новых product features приостановлена. Работа по багам, UI и уже существующим функциям ведётся через `docs/ACTIVE_REVIEW_LEDGER.md`.

Перед ответом по текущей работе InOneLine сначала сверяться с `ACTIVE_REVIEW_LEDGER.md`. Замечания со скриншотов сначала только фиксируются в ledger; runtime не меняется до прямой команды пользователя **«всё делаем»**. После этой команды накопленные пункты сначала проверяются на дубли/зависимости и сортируются по сложности/безопасности, затем выполняются строго по одному с обязательной ручной проверкой пользователя после каждого исправления.

## Инженерные инварианты

Эти правила действуют для любых future feature, maintenance, optimization и cleanup scope:

- **Reuse first → minimal diff → no parallel logic → no new persistence unless unavoidable.** Существующие механизмы, данные, UI, settings, calculations, APIs и storage paths переиспользуются прежде, чем вводить новую сущность/ветку/backend.
- Новый механизм/сущность допустим только если существующий объективно непригоден для **корректности, надёжности или требуемой производительности**; удобство рефакторинга само по себе недостаточно.
- **Стабильность и работоспособность важнее ускорения/уменьшения размера.** Оптимизация не должна повышать риск зависаний, вылетов, потери данных, нарушения RNG/verification/business semantics или чрезмерного RAM/package growth.
- Любой performance/size/RAM cleanup должен быть измеримым и локальным; удаление кода/зависимостей/файлов без доказательства безопасности запрещено.
- Перед рискованным cleanup/refactor должна существовать постоянная regression/Windows QA foundation. Если проблема находится в QA/build harness, сначала исправляется QA/build слой, а runtime не меняется без отдельного approved scope.
- Вне утверждённого scope запрещено менять runtime behavior, schema/migrations, RNG/weights/probabilities, persistence ownership или пользовательские данные.

## Версии

- Candidate/FIX не считаются релизами.
- Candidate/build staging проверяется **до** замены/продвижения безопасного артефакта; failed build/validation не должен уничтожать или перезаписывать последний принятый/безопасный archive/artifact. Historical A1 использовал temporary `.building` + fail-closed validation; current GitHub publication uses immutable accepted artifacts/requests, but safety invariant remains the same.
- Номинальный APP_VERSION candidate не увеличивает release cadence.
- Rollback — предыдущий реально принятый CURRENT.
- При release-финализации допустим отдельный metadata-only commit; он не должен менять принятые runtime/source bytes.

## QA

Автоматические тесты не заменяют ручную Windows-проверку там, где поведение зависит от Qt, браузера, OBS, Windows media stack или реального UI.

Если пользователь сообщает `Работает`, закрывается только явно проверенный сценарий; уже пройденные сценарии не повторяются без причины.

Ручные Windows/PowerShell проверки пользователю даются **только когда они реально добавляют проверку** и по возможности **по одной проверке/команде за раз**. Не перегружать пользователя длинной пачкой ручных команд, если тот же факт уже надёжно покрыт automated gate или ранее пройденным Windows-сценарием.

### Идентификаторы QA

- Release/reconciliation defects and accepted-scope omissions use **`QA-<version>-NN`** identifiers.
- Permanent roadmap/product identifiers such as D/A/W/B/E/R must not be reused for temporary release defects or QA findings.
- A QA finding can point to an older accepted roadmap contract, but it remains a QA finding until the user explicitly approves and accepts the runtime correction.

## Документация

После каждого долговременного решения:

- текущее состояние → `PROJECT_STATE.md`;
- очередь/идея/статус → `ROADMAP.md`;
- долговременное правило → `DECISIONS.md`;
- release QA → `docs/qa/`;
- публичное пользовательское изменение → release notes/README при необходимости.

Нельзя полагаться на единственный старый cumulative-файл, в который бесконечно дописывались предыдущие версии. Git history теперь выполняет роль истории изменений документа.

Исторические audit/reference/release материалы при очистке активного дерева **не уничтожаются как единственный экземпляр**: retire/cleanup допустим только когда соответствующая история уже сохранена в Git history, canonical history docs или архиве Drive. Нельзя заявлять, что утраченный исходный артефакт архивирован, если доступна только поздняя текстовая реконструкция.

## Публичная документация

Сторонние продукты нельзя использовать как публичные design/UX references. Название стороннего продукта допустимо только когда оно объективно необходимо для фактической интеграции, API/протокола, зависимости, лицензии/атрибуции или legacy-совместимости.

Перед публикацией действует `publication-wording` gate.


## Publication requests

- Publication requests после создания не редактируются и не переиспользуются.
- Изменение старого `RELEASE_NOTES_*.md` само по себе никогда не должно запускать публикацию.
- Исторические release-specific workflows хранятся только в Git history; active CI использует единый publisher.
- Для уже существующего tag или GitHub Release publisher обязан завершаться отказом до загрузки/публикации новых assets.
