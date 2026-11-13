# Multichat Settings Groups Design

**Intent:** Reopen the accepted Twitch + YouTube multichat candidate only for the operator settings layout requested after manual testing.

**Goal:** Present exactly three top-level settings groups in this order: common, Twitch, YouTube.

**Common group:** Keep delay, limit, time and platform-icon controls. Rename «Чат Twitch в OBS» to «Мультичат в OBS» and move the shared visibility selector, shared OBS URL/actions, common background and common outline here.

**Twitch group:** Keep Twitch connection status visible. Show Twitch OBS admission and Twitch appearance only while Twitch chat is connected.

**YouTube group:** Keep URL, connect/disconnect actions and connection status visible. Show YouTube OBS admission and YouTube appearance only while YouTube chat is connected.

**Persistence:** Reuse every existing settings key. Split appearance editors must save only their owned section so saving common, Twitch or YouTube cannot overwrite a newer value owned by another section.

**Non-goals:** No message delivery, ordering, deletion, reconnect, OBS rendering, appearance schema, database schema or auction behavior changes.

**Acceptance:** Native Qt tests prove top-level order, labels, conditional visibility, independent drafts/saves and unchanged settings keys. Existing multichat, appearance, GUI and browser regressions remain green; a new Windows installer is issued for focused manual QA.

