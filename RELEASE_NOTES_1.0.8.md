# InOneLine 1.0.8

Candidate after accepted/released 1.0.7. CURRENT remains 1.0.7 until native Windows manual QA and explicit user acceptance.

## Conditional UI Visibility

The UI now distinguishes two different states:

- **semantically inapplicable** controls are hidden;
- controls that are still valid but only **temporarily unavailable** stay visible and disabled.

This avoids permanent grey clutter without making short worker/RNG/connection locks jump around.

### Stream / OBS

- Timer: “Цвет фона” is shown only for the Color background mode.
- Auction Lots: “Цвет фона” is shown only for Color; “Свой фон” is shown only for Custom.
- Rules: background color and opacity are shown only for Color.
- Main overlay:
  - webcam position is hidden while the webcam block is disabled;
  - list side is hidden while the list block is disabled;
  - information position is hidden while the information block is disabled;
  - frame-color rows for webcam/list/info are hidden with the corresponding block;
  - Top-1/Top-2/Top-3/list typography is hidden with the list block;
  - information typography is hidden with the information block.
- Existing D26 Music Player conditional rows are preserved unchanged.

### Auction settings

For timer auto-extension:

- each reason duration is hidden while that reason is OFF;
- “Также учитывать неденежные единицы интеграций” is hidden while External donation is OFF;
- the threshold duration is hidden while the threshold is OFF.

Saved values are not deleted when their controls are hidden.

### Games

- For an active selected game, only “В архив” is shown.
- For an archived selected game, only “Восстановить” is shown.
- With no selected game, neither mutually exclusive action is shown.
- If an applicable action is temporarily blocked by a worker, it stays visible but disabled.

### XLSX connections

- Public-list XLSX: “Отключить” is hidden when no table is connected.
- Shared main-list XLSX: “Отключить” is hidden when no table is connected.
- During a transient worker operation, an existing Disconnect action remains visible and may be temporarily disabled.

### Auction and history actions

- Current-auction “Удалить лот” is visible only when the auction is running **and** the selected row is a temporary auction-only lot.
- Completed-auction verification actions are hidden when no verification snapshot exists.
- The Random.org+ proof action keeps its existing conditional visibility.

## Deliberately unchanged

Temporary/safety locks remain disabled rather than hidden:

- active file copy/import/backup/restore workers;
- RNG preparation, active spin and timer safety states;
- integration actions unavailable because a provider is disconnected;
- concurrent/destructive mutation locks.

## Compatibility

- SQLite schema: **19**
- Named migrations: **15**
- No database migration.
- No RNG/winner-selection change.
- Updating from 1.0.7 preserves all saved values; hidden controls continue using their saved state when they become applicable again.

## Acceptance gate

Candidate must pass:

- compile/static/semantic checks;
- protected RNG-source diff;
- PyInstaller + Inno Setup Windows build;
- frozen startup/API smoke;
- publication wording gate;
- focused native Windows manual verification;
- explicit user acceptance.

Until then **1.0.7 remains CURRENT / RELEASED**.
