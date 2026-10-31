InOneLine AutoTest v1: Windows 11, Python installation is NOT required.

INSTALL:
1. Install the matching candidate InOneLine_Setup_1.0.8.exe first.
2. Copy Start_InOneLine_AutoTest.cmd and InOneLine_AutoTest.ps1 beside installed InOneLine.exe (e.g. C:\InOneLine).
3. Close InOneLine if it is open.
4. Double-click Start_InOneLine_AutoTest.cmd.
5. Follow the on-screen instructions for optional Twitch message and normal window closing.
6. Send InOneLine_AutoTest_yyyyMMdd_HHmmss.zip from the desktop to the developer.

SAFETY:
- Sandbox creates a new temporary database and simulates DonationAlerts RUB/EUR donations locally.
- No simulated donations enter your real account/database, XLSX, OBS, or auction.
- Real Twitch channel points tests are SKIP because this feature is unavailable on your channel.
- Live DonationAlerts payment event tests are SKIP.
- The tester does not create/delete rewards or send chat messages on its own.
- It never includes your database, token files, chat message text, passwords or credential payloads in the ZIP.
- Read-only HTTP route probes do not mean each UI function was exhaustively tested.

COVERAGE:
- Main app launch, local HTTP API/overlay routes, normal process close.
- Nine main tabs in a separate offscreen GUI sandbox.
- Genuine DonationAlerts mapping and duplicate/conversion/invalid payload scenarios in temp DB.
- Optional real Twitch message with unique marker.
- Remaining UI button interactions and actual OBS rendering need future coverage.

KNOWN LIMITATIONS:
- Get-NetTCPConnection is needed to discover the HTTP port owned by the actual launched PID. If Windows restricts that query, API checks report FAIL rather than claiming a result from a different program.
- Program may legitimately need time to finish an active backup or XLSX write before its process disappears.
- If the script is stored under Program Files, reports are still written to your desktop, not the protected install folder.
- This is an opt-in test utility, not unattended production monitoring.
