# YouTube multichat candidate — manual check

Candidate date: 13 November 2026. [QA ZIP on Google Drive](https://drive.google.com/file/d/1dH7LW5H9a_C1W8YBZ40VfMml4spdVQHI/view), size 68,648,082 bytes, SHA-256 `DF5310C8266B37D90B8CD218A4788938CBE3A8455236C8A48B66010FE3ADCBE3`.

Extract the portable ZIP into a new directory, then run `InOneLine.exe` from that directory. The candidate keeps its own `data` directory. Do not place it over the installed application.

1. Open the chat tab, paste the YouTube Studio live chat URL, and click **Подключить YouTube**. Wait for the status **Подключено · Все сообщения**.
2. Send one ordinary YouTube message and one native emoji. Confirm that text, author, avatar, emoji and the YouTube logo appear in the app and the local OBS page. Try a viewer without an available avatar; no substitute or empty avatar slot should appear.
3. Send a Twitch message between two YouTube messages. With delay 0, verify order of arrival; with a positive delay, verify available source timestamps determine order within the common buffer.
4. Send two identical YouTube texts. Both must appear. Delete one on YouTube; only that row should disappear in both views.
5. Disconnect YouTube and confirm Twitch continues; reconnect YouTube and confirm old rows do not duplicate.
6. Change only YouTube message appearance. All existing and new YouTube rows in the app should update immediately, while Twitch stays unchanged. OBS should retain its previous style until **Сохранить**, then update its existing rows. Repeat for Twitch.
7. Turn off only the YouTube OBS checkbox. Old YouTube rows must remain there; new YouTube messages appear only in the app. Twitch continues in both places. Turn YouTube back on and verify that messages sent while it was off do not appear retroactively.
8. With a nonzero common delay, switch the YouTube OBS checkbox while a message is waiting. Its OBS destination is decided when the delay expires. Confirm the same independent behavior for Twitch.
9. Restart the isolated candidate after connecting YouTube. The saved link should reconnect automatically. Explicitly disconnect and restart; it should remain disconnected until you connect it again.
10. Set the app width to 520 px and check that the message feed and all platform controls remain usable. Check the same OBS URL in two browser sources and after hiding/restoring a scene.

The direct-link YouTube reader does not implement the older Google OAuth and automatic active-stream selection requirements D41-REQ-54–63. This link-based method was separately exercised by the user and remains a candidate implementation until the documentation is reconciled and full manual QA passes.
