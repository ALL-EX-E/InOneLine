# Документация InOneLine

С 2026-09-30 этот каталог является канонической проектной документацией InOneLine.

[Главный документ разработки](./MASTER_DEVELOPMENT.md) — обзор архитектуры, требований, структуры и очереди. Перед текущей работой обязательно сверяться с [ACTIVE_REVIEW_LEDGER.md](./ACTIVE_REVIEW_LEDGER.md); обзор не подменяет журнал приёмки.

## Читать в начале нового рабочего чата

1. [PROJECT_STATE.md](./PROJECT_STATE.md) — точное текущее состояние проекта.
2. [ROADMAP.md](./ROADMAP.md) — реализованные, отложенные, возможные и отклонённые идеи.
3. [IDEA_INVENTORY.md](./IDEA_INVENTORY.md) — полный реестр пользовательских идей: реализованные, принятые, отложенные, условные, отклонённые и superseded.
4. [DECISIONS.md](./DECISIONS.md) — долговременные продуктовые и процессные решения.
5. [WORKFLOW.md](./WORKFLOW.md) — обязательный порядок разработки, проверки и выпуска.
6. [SOURCE_OF_TRUTH.md](./SOURCE_OF_TRUTH.md) — иерархия источников и правила разрешения конфликтов.

## QA

- [qa/1.0.8-conditional-ui.md](./qa/1.0.8-conditional-ui.md) — полный ручной gate 1.0.8 / Global Conditional UI Visibility.
- [qa/1.0.8-regression-foundation.md](./qa/1.0.8-regression-foundation.md) — восстановленный постоянный regression foundation exact 1.0.8.
- [qa/1.0.8-filesystem-maintenance.md](./qa/1.0.8-filesystem-maintenance.md) — filesystem/source cleanup maintenance.
- [qa/1.0.8-media-sync-maintenance.md](./qa/1.0.8-media-sync-maintenance.md) — A4 Managed Media Sync.
- [qa/1.0.8-unused-import-maintenance.md](./qa/1.0.8-unused-import-maintenance.md) — A5 Verified Unused Imports.
- [qa/1.0.8-dead-helper-maintenance.md](./qa/1.0.8-dead-helper-maintenance.md) — A6 Dead Private Helpers.
- [qa/1.0.8-publication-ci-maintenance.md](./qa/1.0.8-publication-ci-maintenance.md) — A7 Publication CI Consolidation.
- [qa/1.0.8-actions-version-maintenance.md](./qa/1.0.8-actions-version-maintenance.md) — A8 GitHub Actions Version Refresh.
- [qa/1.0.8-installer-user-state-maintenance.md](./qa/1.0.8-installer-user-state-maintenance.md) — A9 Installer User-State / HKCU Ownership.
- [qa/1.0.7-D26.md](./qa/1.0.7-D26.md) — полный ручной gate D26 / Music Player.

## Аудиты

- [Аудит 2026-10-08](./audits/PROJECT_AUDIT_2026-10-08.md) — инвентаризация материалов, совпадения, исправления CI/настроек и ограничения полноты чатов.

- [audits/CODEBASE_AUDIT_2026-10-01.md](./audits/CODEBASE_AUDIT_2026-10-01.md) — контрольный аудит exact CURRENT 1.0.8: dead code, reuse-first, performance, QA/release infrastructure.
- [audits/FILESYSTEM_AUDIT_2026-10-01.md](./audits/FILESYSTEM_AUDIT_2026-10-01.md) — полный аудит установочных/runtime-файлов, каталогов, временных объектов и exact-дубликатов.

## История

- [history/RECONCILIATION_2026-09-27.md](./history/RECONCILIATION_2026-09-27.md) — предыдущий полный reconciliation старой документации/решений.
- [history/ROADMAP_RECONCILIATION_2026-10-02.md](./history/ROADMAP_RECONCILIATION_2026-10-02.md) — повторная сверка чатов/Drive/GitHub и восстановление полного survivable roadmap inventory с поздними defer/status corrections.
- [MIGRATION_2026-09-30.md](./MIGRATION_2026-09-30.md) — переход от Google Drive к GitHub как source of truth.
- Release-specific факты находятся в корневых `RELEASE_NOTES_*.md`, тегах и GitHub Releases.

Документы в `docs` должны обновляться одновременно с изменением соответствующего состояния. Старые candidate/FIX-сборки не считаются релизами.
