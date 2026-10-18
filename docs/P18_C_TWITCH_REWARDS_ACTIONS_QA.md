# P18-C / UI-084 — управление Twitch-наградами по состоянию канала

Дата: 2026-10-18. Основа: принятый P18-B (Windows ручная приёмка 5/5, clean PR #250, merge main `3ee23a6f74025551290af232fedcfd9c47807e6a`, контрольный Windows Regression Foundation #39130925566 и Publication wording #39130925582 — SUCCESS).

## Изолированный объём P18-C

Только отображение и доступность операторских действий с Twitch Channel Points / Custom Rewards внутри существующей карточки Twitch:

- Использовать **текущий** B1 provider_config (`channel_points_custom_rewards_available`, `channel_points_custom_rewards_reason`, `granted_scopes`), не создавать второй state store.
- Сохранить существующие backend guards `TwitchChannelPointsService.ensure_manage_scope()`, `connection_ready()` и API provider.
- `Сохранить и синхронизировать награды` доступно лишь когда Twitch подключён и включён, Channel Points Custom Rewards доступны этому каналу, и сохранена scope `channel:manage:redemptions`.
- Если отсутствует manage scope, показать причину и **отдельное явное** действие `Подтвердить права на награды` через прежний асинхронный OAuth/Device Code path. Не просить повторный вход автоматически при обычном открытии страницы; не выполнять provider work в GUI thread.
- `Включить награды` и `Отключить награды` взаимоисключающие в зависимости от существующего `manual_rewards_enabled` и не связаны с состоянием аукциона; реальное дистанционное действие доступно только при наличии зарегистрированных reward ID, подходящего канала, scope и активного подключения.
- `Удалить награды` присутствует только при наличии зарегистрированных или retired ID; прежнее подтверждение и отдельное удаление сохранены.
- При недоступности Custom Rewards причина объясняется прямо в карточке, remote-модифицирующие кнопки недоступны. `Добавить награду` остаётся локальным изменением черновика и допустимо даже без активного Twitch.
- Завершение других фоновых операций не имеет права случайно активировать ранее недоступные кнопки.

Файлы: `streaming_manager/views/settings.py`, отдельный native Windows Qt smoke `tools/twitch_reward_eligibility_smoke.py`, и CI gate. Не менять адаптер Twitch, токены, EventSub, базу данных, существующие reward IDs, конвертацию, историю, бизнес-логику колеса/таймеров.

Статус: **DRAFT QA / НЕ ПРИНЯТО / НЕ MERGED**. Только после успешных native Windows CI и wording, точного QA ZIP на Google Drive, и поэтапной ручной приёмки пользователь может принять P18-C. Следующая отдельно P18-D — сохранность несохранённого reward draft при навигации и failure boundary save/sync, как предписано UI-084.
