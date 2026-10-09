R1.0.4 installer source

- Inno Setup 7.1.0 x64 compiler remains pinned for the first 1.0.0 release candidate.
- Default directory: C:\InOneLine. The user may choose another local drive/folder.
- The full InOneLine.exe launch path must remain shorter than 260 characters.
- Reinstall/update removes only InOneLine.exe and _internal before replacing runtime files; data/, backups/ and logs/ are preserved.
- Final uninstall policy is active in R1.0.4: before removal the uninstaller presents an explicit destructive-data warning with No as the default choice.
- If the user confirms, data/, backups/ and logs/ are deleted together with the runtime. Current UI state is stored as data/ui_state.ini and is removed with data/.
- The warning directs the user to create a full external .iolbackup via Settings -> General -> Full program backup -> «Создать полную резервную копию…» before continuing. Store the backup outside the InOneLine installation root.
- External files merely referenced by InOneLine are never deleted by the uninstaller.
- App/Setup/shortcut icon design remains the approved transparent FIX4 icon from assets/InOneLine_icon_master.png and assets/InOneLine.ico.
- Installed Apps display name remains explicitly registered as "In one line".

- A9 moves MainWindow QSettings from HKCU into app-owned data/ui_state.ini. Frozen Windows builds inspect both 64-bit and 32-bit per-user Registry views, prefer the newest Streaming Manager source, backfill only missing keys, save data/legacy_ui_state_backup.ini for recovery/audit, then clear only the current user's legacy stores after a successful copy. The administrative installer no longer reads, creates or deletes HKCU keys. A per-install single-instance lock prevents concurrent InOneLine windows from overwriting the same UI state. The post-install launch is explicitly run as the original user.
