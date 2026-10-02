R1.0.4 installer source

- Inno Setup 7.1.0 x64 compiler remains pinned for the first 1.0.0 release candidate.
- Default directory: C:\InOneLine. The user may choose another local drive/folder.
- The full InOneLine.exe launch path must remain shorter than 260 characters.
- Reinstall/update removes only InOneLine.exe and _internal before replacing runtime files; data/, backups/ and logs/ are preserved.
- Final uninstall policy is active in R1.0.4: before removal the uninstaller presents an explicit destructive-data warning with No as the default choice.
- If the user confirms, data/, backups/ and logs/ are deleted together with the runtime. Current UI state is stored as data/ui_state.ini and is removed with data/.
- The warning directs the user to create a full external .iolbackup via Settings -> General -> Local data before continuing. The backup must be stored outside the InOneLine installation root.
- External files merely referenced by InOneLine are never deleted by the uninstaller.
- App/Setup/shortcut icon design remains the approved transparent FIX4 icon from assets/InOneLine_icon_master.png and assets/InOneLine.ico.
- Installed Apps display name remains explicitly registered as "In one line".

- A9 moves MainWindow QSettings from HKCU into app-owned data/ui_state.ini. Frozen Windows builds migrate the current user's legacy Streaming Manager/InOneLine native QSettings once, then clear those legacy keys from the same interactive user context. The administrative installer no longer reads, creates or deletes HKCU keys; old settings belonging to another Windows profile are intentionally left untouched rather than risking deletion under the wrong UAC account.
