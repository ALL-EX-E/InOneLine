# D41-04 — Windows manual QA checklist (Twitch native graphics)

Candidate ONLY, not accepted, not merged and not a release. Verify on the exact installer from this PR's SUCCESS Windows run. Use a controlled Twitch channel with authorized user:read:chat and the existing EventSub/Channel Points integration. Do not reveal OAuth tokens or private chats in reports.

For EVERY scenario, record PASS / FAIL / NOT TESTED, preserving the actual action and observed result. Browser/OBS tests require real Twitch messages, not the synthetic CI fixture.

1. **Installation and existing data:** install the candidate over the accepted InOneLine instance. Launch. **Expected:** existing database, auctions, Twitch authorization, Window settings and Channel Points unchanged; no migration.
2. **Live connection:** open «Чат Twitch» with an authorized channel; send one plain Twitch message. **Expected:** exactly one new message with the original nickname and content, no browser-chat polling.
3. **Native emote:** send a native static Twitch emote mixed with text. **Expected:** image appears at its position, remaining text/order intact in Qt and OBS.
4. **Animated Twitch emote:** send a Twitch animated emote. **Expected:** original animation moves in Qt and OBS (when image is available), no static-only replacement.
5. **Twitch GIF:** send a Twitch-supported GIF chat element in a test channel. **Expected:** original GIF animation displays in Qt and OBS if the EventSub GIF URL is supplied; no synthetic image when unavailable.
6. **Author avatar:** send a message by a Twitch user whose API profile picture is available. **Expected:** genuine avatar beside name once fetched asynchronously, preserving text and message position.
7. **Missing avatar:** test a failed/unavailable avatar resource. **Expected:** no placeholder, reserved blank square or crash.
8. **Role badges:** send from a moderator, VIP or subscriber account with chat badges. **Expected:** only genuine available Twitch badges in original EventSub order beside the nickname, same in Qt and OBS.
9. **Absent badges:** user has no accessible badge image. **Expected:** no invented role badge or reserved space.
10. **Twitch username color:** choose a nondefault Twitch chat name color, send a message. **Expected:** correct color in both views; other usernames untouched.
11. **Official Twitch icon ON:** ensure «Показывать значки платформ» checked. **Expected:** the official Twitch Glitch platform marker appears to the left of header/available avatar/name on every message.
12. **Global icon OFF:** uncheck «Показывать значки платформ». **Expected:** all platform markers disappear immediately in Qt and all OBS instances, with no empty space; avatars, role badges and emotes remain.
13. **Global icon ON again:** check it. **Expected:** icon returns on already displayed and new messages in both places; there is one global switch, no per-platform switch.
14. **Persistence:** disable markers, close and reopen InOneLine. **Expected:** unchecked state persists in the single setting; switch back and confirm persists.
15. **Show timestamp:** toggle «Показывать время» both directions. **Expected:** header time appears/disappears independently of global marker, on both views.
16. **OBS in several scenes:** add the exact existing local chat URL to two OBS browser sources. **Expected:** identical messages, emotes/GIF, icons and global visibility without a second Twitch connection.
17. **Automatic deletion:** send then moderate-delete a displayed Twitch message. **Expected:** removed from both Qt and OBS, even if it had an emote/avatar/badge; no resurrection from async media resolution.
18. **Clear messages:** use Twitch clear-user/clear-chat tools for a test account. **Expected:** only matching current rows cleared via original EventSub semantics; unrelated messages unaffected.
19. **Delay/buffering:** set 1–3 seconds delay, send graphical message, delete during delay, reduce delay to 0. **Expected:** no resurrected deleted message; other messages preserve order; no double delivery.
20. **Offline/reconnect:** interrupt network to Twitch, then restore. **Expected:** application stays responsive, pre-existing rendered messages remain (subject to RAM cap), new messages appear after reconnect; no historical replay claim.
21. **Fallback/security:** send literal markup `<script>alert(1)</script>`, unusual Unicode and a URL as text. **Expected:** literal content only, never executed, and links are not interactive.
22. **Heavy use:** rapidly send 100+ text/graphics events on a test stream. **Expected:** bounded RAM and image jobs, no GUI hang; 10–1000 existing message limits preserved, no crashes.
23. **Layouts:** resize main window to 520×360 and a medium width, then 2560×1440. **Expected:** message view and settings accessible, no overlap or forced main window resize.
24. **Twitch Channel Points:** redeem an already configured managed Twitch reward while chat receives graphical messages. **Expected:** unchanged reward and auction behavior, no duplicate EventSub subscriptions.
25. **No extra platforms:** review «Чат Twitch» and OBS. **Expected:** no active YouTube, no browser capture settings, no chat history written to database or a text file.

**Exit criteria:** all checked behaviors PASS or explicitly report NOT TESTED with reason; no partial PASS is represented as acceptance. On FAIL fix the same draft PR, issue a new exact Windows QA artifact and repeat affected scenarios. Only a direct user acceptance authorizes merging the tested blobs into main.


## QA-D41-04-01 — адресная повторная проверка FIX первой загрузки (26 октября 2026)

Первоначальные 25 сценариев выше относятся к общему D41-04 и уже оценены пользователем как «всё работает», за исключением задержки первой картинки. Для FIX достаточно выполнить затронутые проверки ниже и регрессию Twitch/OBS/Channel Points, а не произвольно повторять весь UX.

1. **Холодный запуск:** закрыть программу и OBS, затем запустить, открыть «Чат Twitch», дождаться «Twitch: чат подключён» и до отправки сообщения дать канальному профилю/каталогам завершить необязательную асинхронную загрузку. Отправить впервые ранее не использованный *канальный* emote и распространённый нативный Twitch emote. **Ожидается:** при доступности предварительно загруженного ресурса он сразу отображается картинкой без временного текстового кода; UI не блокируется во время загрузки.
2. **Обычное первое сообщение после запуска:** быстро отправить сообщение, не ожидая подготовки каталога. **Ожидается:** сам текст приходит немедленно; если CDN ещё не ответил, картинка добавляется позже без зависания и без дубля/потери текста.
3. **Первое сообщение владельца канала:** отправить сообщение со своего подключённого Twitch-аккаунта. **Ожидается:** если сохранённая оригинальная Twitch-аватарка доступна и заранее загружена, она появляется сразу.
4. **Впервые появившийся сторонний зритель:** отправить сообщение с прежде не участвовавшего Twitch-аккаунта. **Ожидается:** текст появляется немедленно; оригинальный аватар появляется после первого Twitch API/CDN-ответа. Мгновенность при первом знакомстве с таким зрителем технически не обещается.
5. **Повторный отправитель/смайлик:** отправить тот же эмот и сообщение повторно. **Ожидается:** изображения появляются без сетевой задержки из текущего RAM/браузерного кеша.
6. **OBS:** сравнить холодную загрузку в одной и двух браузерных сценах с локальным `/multichat-overlay`. **Ожидается:** ранее предзагруженные изображения Twitch показываются без повторной задержки, а переключатель платформенных значков и удаление сообщений продолжают работать.
7. **Неудачная загрузка:** временно сделать CDN недоступным или создать безопасную тестовую имитацию ошибки. **Ожидается:** сообщение не теряется, нет фиктивных аватаров/значков, не происходит вечного ожидания или блокировки вкладки.
8. **Channel Points и сеть:** погасить уже управляемую награду при поступлении чата, затем восстановить сеть после разрыва. **Ожидается:** прежний EventSub и награды функционируют, никаких новых подключений от браузера к Twitch нет.

**Статус:** FIX candidate не засчитывается за окончательный PASS, пока эти сценарии не подтверждены пользователем.
