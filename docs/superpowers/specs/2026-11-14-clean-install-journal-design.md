# Clean-install journal design

## Intent

On the first launch of a clean InOneLine 1.0.12 installation, automatic default initialization must not appear in the operator journal as if the user changed settings.

## Scope

- Seed only absent settings without creating `change_log` rows.
- Use the silent seed path only while Music Player and Multichat construct their initial state.
- Keep ordinary `set_setting` and `set_settings_bulk` behavior unchanged, so later user and runtime changes remain audited.
- Do not change the application version, installer version, database schema, published GitHub release, or installed copy in `C:\InOneLine`.

## Approach

Add an explicit database method that inserts missing settings and never overwrites existing values or writes audit entries. Music Player initialization uses it for queue and state persistence while its constructor is active; Multichat uses it for the initial normalized delay. After construction, both components continue through the existing audited setters.

Alternatives rejected: filtering rows in the Journal would leave misleading data in SQLite and full search; globally suppressing all first writes would also hide a user's legitimate first change.

## Verification

A real temporary SQLite database must show zero journal rows after automatic default seeding, preserve existing values, and produce an audit row when the same setting is subsequently changed through the normal setter. Qt integration tests must cover clean Music Player and Multichat construction.
