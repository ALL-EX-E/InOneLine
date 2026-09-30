# InOneLine — Current Project State

Обновлено: **2026-09-30**

## CURRENT / RELEASED

- Version: **1.0.7**
- Scope: **D26 — Music Player**
- Status: **RELEASED / MANUALLY ACCEPTED**
- SQLite schema: **19**
- Named migrations: **15**
- Accepted candidate commit: `8f58f8561ecd9832cf575a2bc0fdaf102375f298`
- Final release commit on `main`: `5ee92aaa19472fa81f1b844886c9f999662c9674`
- Final D26 Windows gate: `36715896504` — SUCCESS
- Publication wording gate: `36725498488` — SUCCESS
- GitHub publication workflow: `36725498493` — SUCCESS
- Accepted artifact: `11097065150`
- Manual Windows QA: **PASS**

## Официальные артефакты 1.0.7

Installer: `InOneLine_Setup_1.0.7.exe`

- Size: `47,618,359` bytes
- SHA-256: `f89e0e713ca53354cda603c1e4748c064c96570edfeef5aa28fbfe1548106dc1`

Source: `InOneLine_Source_1.0.7.zip`

- Size: `13,802,881` bytes
- Files: `182`
- SHA-256: `33e11f6590089d479eb9e9a64bde49dfef2858d4caefeab858a000a3e22ee20b`
- ZIP CRC: PASS

## Последние принятые функциональные релизы

- **1.0.4 / D19** — пользовательское/анимированное изображение в центре колеса и быстрый выбор.
- **1.0.5 / D43** — OBS Browser Audio Transport через Timer Browser Source + AudioCoordinator foundation.
- **1.0.6 / D21** — формат weighted wheel «Выбывание» + multi-spin verification.
- **1.0.7 / D26** — полноценный Music Player, shared soundtrack library, AudioCoordinator ownership и отдельный OBS Music Player Overlay.

Подробности каждой версии находятся в `RELEASE_NOTES_<version>.md`.

## Текущая рабочая очередь

Новый implementation scope **не выбран автоматически** после 1.0.7.

Первым отдельным post-D26 patch разрешено рассматривать:

1. Global Conditional UI Visibility.
2. Global Multi-File Import.

Отдельно остаётся отложенный approved post-completion item:

- **D22 — Battle Royale**.

Выбор следующего scope требует отдельного решения пользователя и fresh exact-CURRENT review.

## Release cadence

В счёт cadence входят только версии, которые прошли финальную пользовательскую приёмку и стали CURRENT/released. Candidate/FIX версии не считаются.

Последняя явно зафиксированная отметка после 1.0.3 была 16/25; с принятыми 1.0.4–1.0.7 текущая арифметическая отметка — **20/25**. Перед фактическим C1 gate счётчик нужно сверить с release history, а не с candidate APP_VERSION.
