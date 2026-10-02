# Durable Decisions

Этот файл содержит решения, которые должны переживать отдельные чаты и релизы.

## 2026-09-30 — GitHub становится source of truth

- Текущие Project State, Roadmap, Decisions, Workflow и QA ведутся в GitHub.
- Google Drive остаётся резервным/историческим архивом и не определяет CURRENT.
- Существенное решение из чата должно быть перенесено в GitHub-документацию, а не существовать только в истории чата.
- Официальные бинарные релизы хранятся в GitHub Releases.
- Candidate/FIX artifacts могут существовать в Actions/Drive как временные или резервные копии, но не являются CURRENT.

## Release rule

- В release cadence считаются только принятые CURRENT/released версии.
- Candidate/FIX версии не считаются.
- После manual acceptance официальные installer/source bytes не пересобираются.
- Release metadata может быть добавлена отдельным commit, если runtime/source принятых bytes не меняются.

## Accepted release publication

- Исторические per-release publication workflows не являются текущим источником истины и хранятся только в Git history.
- Для будущих принятых релизов используется единый `.github/workflows/publish-accepted-release.yml`.
- Нормальная публикация начинается только с добавления нового immutable request в `.github/release/requests/`.
- Request обязан фиксировать exact accepted Actions artifact ID, exact target commit, release metadata, final asset names и SHA-256.
- После manual acceptance публикация не пересобирает installer/source: она только проверяет, переименовывает/стейджит и публикует exact accepted bytes.
- Существующие tag/GitHub Release никогда не перезаписываются общим publisher.
- Старые release notes сами по себе не запускают публикацию.
- После публикации assets скачиваются повторно и проверяются по exact name/SHA-256.
- Полный контракт: `docs/RELEASE_PUBLICATION.md`.

## Public naming rule

В публичных материалах функции называются по назначению, а не по стороннему продукту, использованному как внутренний референс. Сторонние названия допустимы только для объективно нужной интеграции/API/protocol/dependency/license/legacy compatibility.

## D43 / D26 audio architecture

- InOneLine остаётся авторитетом для playback state.
- Browser Source — renderer/transport, а не второй business-logic engine.
- Auction и wheel soundtrack используют Timer Browser Source.
- Music Player использует отдельный Music Player Browser Source.
- AudioCoordinator определяет слышимого владельца.
- Music Player уступает ownership только активному событию с реально доступным незаглушённым soundtrack.
- После события Music Player возвращается на сохранённую позицию.

## D26 Music Player

- Managed music: `data\music`; supported MP3/WAV/OGG.
- Managed soundtrack: общий `data\soundtrack`; выбор auction/wheel независим.
- После перезапуска текущий трек/позиция восстанавливаются в Pause; autoplay запрещён.
- Search меняет только видимость списка, не очередь.
- Show mode, animation, artwork, colors и Spectrum относятся к OBS Music Player Overlay.
- Preview не создаёт дополнительный слышимый звук.

## D21 Elimination

Released behavior имеет приоритет над ранними draft-описаниями: каждое elimination spin использует настоящий weighted RNG по текущим активным лотам; выбранный лот архивируется только после явного `В архив`; последний лот тоже проходит spin; нулевой список завершает режим без final winner.

## Post-D26 UX rules

Из двух post-D26 UX patch items один уже закрыт:

1. **Conditional UI Visibility** — RELEASED in 1.0.8. Логически неприменимые controls скрываются; временно недоступные, но применимые controls остаются visible + disabled.
2. **Global Multi-File Import** — остаётся eligible for selection. Требование: распространить стандартный Windows Ctrl/Shift multi-file import на все применимые `Добавить файл…` flows, переиспользуя уже реализованный D26 multi-select механизм Music Player.


## 2026-10-02 — Roadmap reconciliation

После повторной сверки чатов 1–31, исторических Drive-roadmap/audit records, GitHub Issues, release notes и current runtime зафиксированы durable rules:

- Короткий post-D26 GitHub roadmap `#4 -> D22` был неполным documentation drift, а не новым решением пользователя удалить остальной backlog.
- GitHub Issues — tracking для выбранных/выделенных задач, а не полный реестр будущих идей; отсутствие Issue не означает удаление пункта из canonical roadmap.
- Global Multi-File Import / #4 остаётся eligible for fresh review, но не выбран автоматически.
- D22 / #5 остаётся explicitly deferred и не является автоматическим следующим scope.
- Retained dependency/complexity chain после released D26 сохраняет D40 -> D34 -> D41 -> older YouTube integration candidate -> D38 -> Public Web -> D27 -> D7.
- D23, D24, D25 и D42 остаются сохранёнными post-completion items.
- D16, D17, D18 и D20 сохраняют более поздние direct-user defer/skip статусы.
- Games/List shared Autoscroll из старого PASS13 не восстанавливается: более позднее прямое решение пользователя — не добавлять его; Compact presentation отложен до реальной необходимости.
- D15 не является подтверждённым InOneLine roadmap item.
- D39 остаётся historical assistant-proposed possibility / NOT ACTIONABLE без нового прямого решения пользователя.
- Historical W3 YouTube soundtrack-source wording не является утверждённым roadmap scope; «Трейлер (YouTube)» закрыт.
- Старые stale-OBS-page reload и wheel infinite-RAF candidates не являются открытыми задачами: их соответствующие runtime concerns уже закрыты текущей реализацией.
- При конфликте более позднее прямое пользовательское решение и released/current behavior имеют приоритет над более ранними assistant-authored cumulative planning blocks.
- Полный survivable inventory хранится в `docs/ROADMAP.md`; подробный reconciliation — `docs/history/ROADMAP_RECONCILIATION_2026-10-02.md`.

Этот reconciliation не выбирает следующий implementation scope.


## 2026-10-02 — Full user-idea inventory

- `docs/IDEA_INVENTORY.md` is the canonical exhaustive historical inventory of user-proposed/accepted/deferred/rejected/superseded ideas.
- `docs/ROADMAP.md` is the shorter current/future selection view and must not be treated as a complete history of everything the user ever proposed.
- GitHub Issues are tracking aids only; they are not the full idea inventory.
- Product A1–A8/A6.1 and Maintenance A1–A10 are separate namespaces and must always be labelled accordingly.
- Direct user dialogue has priority over later assistant-authored status compression. In particular, advanced History analytics (heatmap, weekdays, participant rankings, points/donations analytics, record cards, most expensive winning lot) remains USER-ACCEPTED post-completion/post-integration work.
- Backup-retention last-N/N-days remains non-roadmap because no direct user proposal/acceptance was recovered; do not promote assistant audit suggestions into the user inventory.
- Before declaring an old idea “missing” or “next”, check IDEA_INVENTORY + later direct decisions + released/current behavior.


## 2026-10-02 — Third-pass recovered product invariants

A third independent comparison of old chats/Drive dedicated reviews against `docs/IDEA_INVENTORY.md` recovered several durable details:

- DonationAlerts/I1 uses the later permanent-source model: enabled connection is intake permission; provider source timestamp routes an event to the auction that was running at source time or to the persistent game list outside auctions. The old auction-only intake toggle/target binding is retired compatibility state, not current product behavior.
- Twitch Channel Points likewise are not gated by an auction-only intake switch; contribution routing may occur both inside and outside auctions according to the accepted B3/B4 rules.
- Integration connection UX should avoid user-managed client secrets where the provider supports public/native application authorization; use browser/device authorization and protected local tokens.
- Auction/game mutations obey a cross-surface synchronization invariant: authoritative DB mutation must propagate to Games/Public/Auction/Journal and relevant OBS/API views without manual F5.
- The default weighted wheel remains RNG-first: the winner is determined before animation, hidden until animation completes, and persisted spin/result state is recovered after restart. D27 remains a separate future alternative.
- Main OBS transparency remains cutout-only for game/webcam interiors; a second whole-overlay transparent mode was explicitly rejected.
- The initial public-GitHub-without-source publication plan was superseded by the later official SOURCE+INSTALLER publication and custom license decision.

These are historical/current invariants, not new implementation scopes.
