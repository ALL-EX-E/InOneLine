# InOneLine Roadmap

Обновлено: **2026-09-30**

## CURRENT

- Released: **1.0.7 / D26 Music Player**
- Новый implementation scope после релиза автоматически не выбран.

## Ближайшие eligible items

1. **Global Conditional UI Visibility** — отдельный post-D26 patch. Перед реализацией нужен полный UI-аудит; логически неприменимые controls должны скрываться вместо постоянного disabled/серого состояния. Tracking: **#3**.
2. **Global Multi-File Import** — отдельный post-D26 patch. Распространить стандартный Windows Ctrl/Shift multi-select на применимые потоки «Добавить файл…». Music Player уже поддерживает это в D26. Tracking: **#4**.
3. **D22 — Battle Royale** — approved post-completion item, отложен и требует fresh design/review перед реализацией. Tracking: **#5**.

Ни один из этих пунктов не выбран автоматически.

## Недавние закрытые roadmap items

- **D19** — custom center image + quick picker — RELEASED in 1.0.4.
- **D43** — OBS Browser Audio Transport — RELEASED in 1.0.5.
- **D21** — Elimination wheel — RELEASED in 1.0.6.
- **D26** — Music Player + OBS overlay — RELEASED in 1.0.7.

## Правило для оставшегося legacy backlog

Старый backlog до границы GitHub source-of-truth не должен автоматически становиться активным только потому, что встречается в историческом документе. Перед возвратом любого такого пункта требуется:

1. сверить его с последним canonical status;
2. убедиться, что он не был реализован, отклонён или superseded;
3. провести fresh exact-CURRENT review;
4. получить явное решение пользователя о выборе scope.

Итог последнего reconciliation-аудита хранится в `docs/history/RECONCILIATION_2026-09-27.md`.
