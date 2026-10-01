# Документация InOneLine

С 2026-09-30 этот каталог является канонической проектной документацией InOneLine.

## Читать в начале нового рабочего чата

1. [PROJECT_STATE.md](./PROJECT_STATE.md) — точное текущее состояние проекта.
2. [ROADMAP.md](./ROADMAP.md) — реализованные, отложенные, возможные и отклонённые идеи.
3. [DECISIONS.md](./DECISIONS.md) — долговременные продуктовые и процессные решения.
4. [WORKFLOW.md](./WORKFLOW.md) — обязательный порядок разработки, проверки и выпуска.
5. [SOURCE_OF_TRUTH.md](./SOURCE_OF_TRUTH.md) — иерархия источников и правила разрешения конфликтов.

## QA

- [qa/1.0.8-conditional-ui.md](./qa/1.0.8-conditional-ui.md) — полный ручной gate 1.0.8 / Global Conditional UI Visibility.
- [qa/1.0.8-regression-foundation.md](./qa/1.0.8-regression-foundation.md) — восстановленный постоянный regression foundation exact 1.0.8: DB, GUI, frozen EXE и installer.
- [qa/1.0.8-filesystem-maintenance.md](./qa/1.0.8-filesystem-maintenance.md) — принятый filesystem/source cleanup maintenance: legacy media, backup compatibility, clean install и duplicate audit.
- [qa/1.0.7-D26.md](./qa/1.0.7-D26.md) — полный ручной gate D26 / Music Player.

## Аудиты

- [audits/CODEBASE_AUDIT_2026-10-01.md](./audits/CODEBASE_AUDIT_2026-10-01.md) — контрольный аудит exact CURRENT 1.0.8: dead code, reuse-first, performance, QA/release infrastructure.
- [audits/FILESYSTEM_AUDIT_2026-10-01.md](./audits/FILESYSTEM_AUDIT_2026-10-01.md) — полный аудит установочных/runtime-файлов, каталогов, временных объектов и exact-дубликатов.

## История

- [history/RECONCILIATION_2026-09-27.md](./history/RECONCILIATION_2026-09-27.md) — итог последнего полного аудита старой документации/решений.
- [MIGRATION_2026-09-30.md](./MIGRATION_2026-09-30.md) — переход от Google Drive к GitHub как source of truth.
- Release-specific факты находятся в корневых `RELEASE_NOTES_*.md`, тегах и GitHub Releases.

Документы в `docs` должны обновляться одновременно с изменением соответствующего состояния. Старые candidate/FIX-сборки не считаются релизами.
