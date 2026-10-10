# InOneLine Roadmap

Обновлено: **2026-10-10**

Этот файл — короткий канонический inventory будущей работы. Он восстановлен после повторной сверки чатов «Программа для стрима» 1–31, исторических Drive-roadmap/reconciliation-файлов, GitHub Issues, release notes и exact current source.

## CURRENT

- Released product version: **1.0.8 / Global Conditional UI Visibility**.
- Latest accepted 1.0.8 maintenance baseline includes the filesystem/codebase maintenance accepted through **A9**.
- SQLite schema: **19**.
- Named migrations: **15**.
- Все A1–A10 findings контрольного codebase audit 2026-10-01 закрыты.
- Новый product implementation scope после maintenance-аудита **не выбран автоматически**.
- **QA-1.0.8-01 — Conduct integration last-event visibility** — новый reconciliation/QA finding: ранее принятый B1 contract требует показывать время последнего принятого integration event в компактном `Аукцион → Проведение` status UI. Current 1.0.8 сохраняет `last_event_at` и показывает последнюю активность в Settings, но не в Conduct status/dialog. Статус: **ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT FIXED / NOT AUTO-AUTHORIZED**.
- GitHub Issues используются для отдельных tracking-задач, но **не являются исчерпывающим backlog**; полный survivable future inventory находится в этом файле. Полная история пользовательских идей и их статусов — `docs/IDEA_INVENTORY.md`.

## Известный accepted-requirement QA finding

- **QA-1.0.8-01 — Conduct integration last-event visibility**. Это не новая feature idea и не меняет retained future dependency order. Перед runtime fix нужен fresh exact-CURRENT review и отдельное approval; исправление должно переиспользовать существующий `integration_connections.last_event_at`/B1 status infrastructure, без второго event/history backend.
- **QA-1.0.8-02 — accepted B2 test-event safety contract is not represented generically in current normalized-event core**. Direct user acceptance exists: provider events explicitly marked test/sandbox/demo must never credit points, create/increment game/lot, change leader, extend timer or affect wheel/winner; diagnostics/history-only is allowed. Current 1.0.8 has no explicit normalized test-event field/gate. Classification: **ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / PROVIDER-CAPABILITY-DEPENDENT / NOT AUTO-AUTHORIZED**. No current supported-provider reproduction was established; implement only through fresh exact-current review and common B2/B3 reuse.
- **QA-1.0.8-03 — B3 empty-message current-runtime gap — TARGET APPROVED IN UI-087 / AWAITS REVIEW-BATCH IMPLEMENTATION**. The earlier generic manual `Требует привязки` target is superseded for an ordinary accepted external event received during a running auction with empty message. UI-087 requires an automatic temporary lot `Без текста N`: each accepted empty-message event gets its own sequential placeholder within that auction session; a known-rate event credits it immediately, while an unknown-rate event creates the placeholder immediately but keeps the credit in `Ожидают применения` until the rate is saved and the operator presses `Применить`. Current 1.0.8 still marks `missing_target` as `inapplicable`, so runtime remains out of contract until the approved review batch is implemented after the user's future `«всё делаем»` command. A separate `Требует привязки` workflow must not be created just for standard empty-message donations; provider-specific events that cannot safely map to an ordinary lot-targeted credit remain separate edge cases.


## Текущий утверждённый review-batch — не реализован

Полный UI/function review завершён 2026-10-07. Детальный source of truth для накопленных решений — `docs/ACTIVE_REVIEW_LEDGER.md`.

- Runtime/source остаётся **1.0.8 / schema 19 / 15 named migrations**.
- Это уже не fresh-review candidate list: большинство UI/BUG-пунктов имеют принятый target и ждут общей команды пользователя `«всё делаем»`.
- До этой команды **код не менять**.
- Главные cross-cutting supersession текущего batch:
  - UI-074: локальный список аукциона без автопрокрутки; persisted autoscroll только для Auction Lots OBS overlay;
  - UI-087: empty message во время running auction → `Без текста N`;
  - UI-088/UI-090: CSV/JSON/Excel file export переносится на `Публичный список`; legacy compatible export и внутренняя вкладка `Настройки → Экспорт` удаляются;
  - UI-044 в прежнем виде не реализуется, потому что target `Настройки → Экспорт → Публичный API` исчезает вместе с вкладкой; `/api/public` сохраняется.
- Не считать released 1.0.8 layout/behavior в исторических записях более поздним target, если оно явно superseded текущим ledger.
- UI-053 закрыт 2026-10-07: на странице `Аукцион` рядом с `Копировать URL таймера` добавить `Открыть предпросмотр таймера`; действие работает и для Max Amount, и для wheel context и переиспользует существующий `/timer-overlay?preview=1`.
- AUCTION-TIMER-REVIEW-002 закрыт решением пользователя 2026-10-07: tie overtime Max Amount использует saved Max Amount duration default; pending-overtime reset возвращает тот же default; отдельной overtime-настройки нет. Current 1.0.8 требует изменения, потому что сейчас использует wheel default.
- AUCTION-TIMER-REVIEW-003 закрыт решением пользователя 2026-10-07: сохранить ~1.2 s как отдельный preparation lead-in; до его окончания установленная длительность не расходуется, затем timer / применимое wheel motion / soundtrack стартуют одновременно от общей authoritative start boundary; repeated Start/Spin during lead-in must be re-entry protected.
- После этого неразрешённых timer-behavior вопросов перед dependency sorting не осталось.
- QA-1.0.8-01 и QA-1.0.8-02 остаются documented findings и **не включаются автоматически** в batch без отдельного решения пользователя. QA-1.0.8-03 уже покрыт UI-087.

## Dependency reconciliation — point 2 COMPLETE

- All accepted current-review decisions have been cross-checked against each other and exact CURRENT 1.0.8.
- Supersession/precedence is now explicit in `docs/ACTIVE_REVIEW_LEDGER.md`; no unresolved logical conflict remains in the approved review target.
- Critical shared boundaries: one position policy, one media library/availability path, one OBS visibility policy, one auction session state machine, one integration/conversion provenance pipeline, one authoritative timer/wheel start boundary.
- Rules Overlay is the main resolved exception case: UI-060 composite template owns Rules text/appearance; GLOBAL-OBS-VISIBILITY-001 later owns widget-level show-mode; Stream/OBS does not host a second Rules settings/save copy.
- Stop with unresolved source-auction pending does not auto-discard it: Stop closes without winner/materializes lots; later explicit Apply can credit the corresponding persistent target exactly once without reopening session state.
- Next plan step is point 3: sort implementation so shared foundations are changed before dependent UI and each accepted change can be manually verified in isolation.
## P01 progress — A/B/C/D source + regression assertion complete

- Candidate `candidate/p01-mainwindow-shell-cleanup`.
- A: remove `Файл` menu/actions — source check PASS.
- B: remove `Вид` menu; keep one direct F5 → `refresh_all()` — source check PASS.
- C: add exact non-clickable hint `F5 — обновить данные во всех разделах` in existing top menu-bar area — source check PASS.
- D: lock the shell contract in the existing GUI regression smoke — commit `4dfd487f700ab1c1cd456df9ee9d34dcf582397c`; source/diff check PASS.
- Candidate now changes `streaming_manager/views/main_window.py` plus the regression assertion in `tools/gui_regression_smoke.py`; runtime behavior change remains isolated to MainWindow.
- E: draft PR #19 opened as QA-only trigger; Windows regression run `37582729729` / job `112665869659` against candidate SHA `4dfd487f700ab1c1cd456df9ee9d34dcf582397c` — **SUCCESS**.
- P01-focused Native GUI regression, frozen build/startup, installer build and silent-install regression all passed.
- Separate publication-wording gate failed only on pre-existing docs wording; keep outside P01 runtime scope unless separately selected.
- Temporary installer-artifact PR #20 was closed unused/no-merge after its newly added QA workflow did not trigger; P01 runtime candidate was not changed.
- Manual QA installer produced successfully by Windows regression run `37583488177`; artifact `11465802252`.
- Google Drive package ready for user QA: `InOneLine_P01_CANDIDATE_1.0.8_WINDOWS_QA.zip`, file ID `1VvMjue9GOFet2XSN8PpttBkX1nyB03Gk`, verified size `46756638` bytes.
- Installer SHA-256: `c931ae5d7abba8ac8ae3d0f43e61fcacb1dc4344e746c028551c3eafec32ce82`.
- P01 manual QA accepted by user on 2026-10-07.
- PR #19 merged to `main` as `d40c0dc7798aae3c9d7a8d7b8faab97756e06512`.
- Post-merge verification run `37586507639` — **SUCCESS**; QA-only PR #21 closed without merge.
- Separate Publication wording gate `37586507550` remains an unrelated known documentation finding.
- **P01 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- **P02 is next and unblocked.**
- P02-A / UI-010 complete on `candidate/p02-list-public-labels`: main tab `Игры` -> `Список`; implementation `f6481b6668019b45af3d9d11040117baf2868f4c`, regression expectation `cc1bad8b3e6a0d882dec429f043997b64fcb11cf`.
- P02-B / UI-011 complete: button `Добавить игру` -> `Добавить`; implementation `1ccc1ad65ad6a050380ce469f99ae307976b2dbd`, GUI assertion `772af23741caa81ddc8ad8f8562dad0ec65d6b9e`.
- P02-C / UI-012 complete: GameDialog titles -> `Добавить` / `Изменить`, internal headings removed; implementation `dc4197fc05f9eec7885705f77eda1ed7053962b3`, GUI regression `57789c7dbbc1202f000cf8c74f04239f8772c4d9`.
- P02-D / UI-013 complete: `Название игры:` -> `Название:`; `Дата выхода:` -> `Дата:`; implementation `e62c0b08de7bd358e85eaf3d6354816dbb3d7063`, GUI regression `e7b90528e3b17ac3b16a4e846a5dec98ba8c4915`.
- P02-E / UI-015 complete: `Дата`, `Баллы`, `Отзыв` explicitly marked `(необязательно)`; `Кооператив/Статус` unchanged. Implementation `635e4405ffd12ed35f8c0385616ff1f1193a689f`, GUI regression `1f73618165e5e3f1cd3acad833209cc4cef58f45`.
- P02-F / UI-022 complete: full-list clear UI now uses `Очистить список`, `Будут удалены все записи: N`, `УДАЛИТЬ ЗАПИСИ`, `Удалить записи`; worker completion preserves the new button label. Implementation `8781b4bafbfdfdafcbfd960f6d667924ca08f822` + `6a7746c956460ca9464951551f5b7242af174958`; GUI regression `7ac2eb591a9af5c93aa5a542d07f3c049dcac3ab` + `00abccc2301d72076ad4caa1a36f32440c23bd73`.
- P02-G / UI-024 complete: sorting-rules window wording simplified without changing sort semantics. Implementation `99ecc55ef2556957f0957c61098a4ae6df03c2d6`; GUI regression `7b03ca8786ec81b507a0ad4c265dcf07928cc4bd`.
- P02-H / UI-029 complete: Public List explanatory text and read-only table header now use `НАЗВАНИЕ`; data/API/XLSX/export semantics unchanged. Implementation `282ca506ad6376c5ee165009bff8bfa1c9969f44`; GUI regression `6566370f056feaa2063f0bed5f6164877d62b34a`.
- P02-I / UI-030 complete: visible `Открыть локальный JSON` button removed from Public List; `/api/public` remains unchanged. Implementation `a82154e53ad61a25c7026de64592ad1ba422a802`; GUI regression `655dc42510cd726eaa3098ab00ded28e49958bb5`.
- P02 implementation items are complete as candidate.
- Draft PR #22 / candidate SHA `655dc42510cd726eaa3098ab00ded28e49958bb5`: candidate-wide regression run `37590831341` — **SUCCESS**, including Native GUI, frozen build/startup, installer and silent-install gates.
- Manual-QA ZIP uploaded to Drive: `InOneLine_P02_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1bRyJ2SJMvRIBadjwgSCOY12JjBp1Ajpp`; installer SHA-256 `8aaf388bb20b59b0c039f4a529b3298f7d3258002890498ee60dac7a74920647`.
- Separate wording gate failure remains the known docs-only finding.
- Manual QA found one remaining P02 issue only: user-facing game terminology. **P02 REOPENED**; all other checked P02 behavior is reported correct.
- GLOBAL-TERMINOLOGY-001 is now active across the project. P02-J1/J2 remove current List/Public/general fallback wording; CSV/import terminology moves with P03; export/XLSX P05/P07; Stream/OBS P09; Auction P12/P20; integrations P18/P19; Journal P22.
- P02-J1 commits: `a49e7a41134479675fb558df6960319f45129d3f`, `1748a31d8606a513cbcb67d9ba1035e5861d98b7`, regression `f2b9e9218d81aea5a0b533a2e8b629a4894e6b92`.
- P02-J2 commits: `a0ee0a764da4360cd93869295df67dc7cb9e4530`, `404919075f3b54e840a0cb277739abfeea318201`, `e75af0d0195a41665d5839ab6039314e46a33230`, `eba81eb4934984fd2ca1f85da0be3106f51b765b`; regression `4bf4c7e2a4b15837e172073098dcf5595c227e8c`.
- Previous P02 installer is superseded.
- Fresh P02-J head `4bf4c7e2a4b15837e172073098dcf5595c227e8c`; Windows regression `37594380334` — **SUCCESS**.
- V2 manual-QA ZIP: `InOneLine_P02_CANDIDATE_V2_1.0.8_WINDOWS_QA.zip`, Drive ID `1fGGNR1_2FZl1mgKwFAPexmE1HFzXKygt`; installer SHA-256 `39dc8bb825ff6d6b58cf880668d0fa687fc37708802c0a424357b76337dc42d6`.
- Repeat manual QA PASS 2026-10-07: P02 works as intended and J1/J2 terminology cleanup is accepted.
- `ИГРАЛ / НЕ ИГРАЛ` are explicitly protected because they participate in sorting/status mechanics; terminology changes must be context-checked and user-facing only.
- Clean accepted promotion PR #23 merged as `e89b178f4816b30e3a54e59ea5407eab2e782e6d`.
- Clean-promotion regression `37596838501` — **SUCCESS**; post-merge regression `37597234911` — **SUCCESS**. QA PR #24 and superseded PR #22 closed without merge.
- **P02 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- **P03 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- P03-A / UI-021 complete on `candidate/p03-csv-date-caret`: canonical CSV headers `НАЗВАНИЕ` + `ДАТА` are accepted while legacy `НАЗВАНИЕ ИГРЫ` + `ДАТА ВЫХОДА` remain aliases. Implementation `d6b8b30a1336f5b7864b1ca3f19c41c4473815f2`; regression `2ac0f44deaa3f6234af194d88b755e36fc729c72`.
- P03-B / UI-020 complete: CSV help rewritten to the accepted neutral/canonical wording while explicitly preserving legacy aliases and `ИГРАЛ / НЕ ИГРАЛ` status labels. Implementation `a70f00688650638ff2173ba942b418db26ba8201`; GUI regression `ec74bed827edaa675f6360dd703326e442f38ee9`.
- P03-C / UI-019 complete: CSV error messages now state the problem, source row/value and correction guidance; TEST-001 error scenarios + atomicity + backup-path preservation are automated in the existing GUI smoke. Implementation `0f7f8b24b3b702607b9c1ef4b167745f714230c7`; regression `2230c10a06a986389bff3ab546afbe011368730c` + `e7a32323fbe3f951f966b8a2d538961ed34f6fa6`.
- P03-D / BUG-002 complete: existing date auto-format now preserves logical caret position instead of jumping to the end. Implementation `7872121a09c740e99073053d9b1ee9e776296202`; regression `2fd76ae1260738fdf289b36de084ac2b15234e19` covers Add/Edit, Backspace, Delete, selection replacement and sequential input.
- P03 clean review branch `candidate/p03-review`, head `9fb64bc0d0867f439b0866f82826b406c22ef012`, draft PR #25; exactly 3 changed files.
- Candidate-wide Windows regression `37633288322` — **SUCCESS**, including Native GUI P03 checks, frozen build/startup, Browser Source, installer and silent-install gates.
- Manual-QA ZIP uploaded to Drive: `InOneLine_P03_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1Fpk09-w7nq22ao8qdgDMLyJBSJIwD9tu`; installer SHA-256 `5f82f276e36ab316b2f2bc9f130036791e2b3f0c7de2d9c7d067690e9a57086d`.
- **P03 automated gate PASS; complete user manual QA PASS / ACCEPTED («Работает. Идём дальше.»).** Merge and post-merge regression passed. **P04-A / UI-025 is CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS; P04-B / BUG-003 is next.**
## P00 baseline gate — PASS — 2026-10-07

- Exact CURRENT reconfirmed: **1.0.8 / schema 19 / 15 named migrations**.
- Accepted A9 runtime anchor `74ad16c5772d5cc191f7e307203b6a574af7815c`; subsequent `main` changes before P00 were docs/README only.
- Fresh rerun of permanent Windows regression: run `36972339831`, fresh job `112658659175` — **SUCCESS**.
- Compile, DB integrity, GUI, frozen Browser Source, backup/restore, A9 migration/single-instance, Inno Setup and silent-install regressions all passed.
- P00 changed no runtime/product behavior. **P01 is the next implementation package.**
## Final implementation queue — point 3 COMPLETE

Detailed source of truth: `docs/ACTIVE_REVIEW_LEDGER.md` §4.7.

Execution rule: each package below is one candidate/review gate. Do not start the next package before automated checks + user manual acceptance of the previous package. Exact CURRENT 1.0.8 remains rollback baseline until a candidate is accepted.

1. **P00** — exact baseline/regression gate.
2. **P01** — MainWindow shell/menu/F5 cleanup.
3. **P02** — low-risk List/Public labels/dialogs.
4. **P03** — CSV/import + date/caret correctness.
5. **P04** — search/filter/selection/hide-list cleanup + total points.
6. **P05** — Public file export relocation + remove Settings Export.
7. **P06** — window sizing/state/tab-order migration + full backup ui_state — **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**.
8. **P07** — one position policy + XLSX derived position — **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**.
9. **P08** — shared media dedup/availability foundation — **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**.
10. **P09** — Stream/OBS structural cleanup and API-control removal — **IN PROGRESS** (UI-033–UI-042 CLOSED, with UI-038 already satisfied by accepted UI-036/P08; UI-043 Windows candidate PASS / AWAITING MANUAL QA).
11. **P10** — common OBS show-mode + timer/music widget presentation/audio help.
12. **P11** — Rules composite editor/overlay.
13. **P12** — single Auction page + lot-search scope.
14. **P13** — Auction layout/timer contextual UI/quick actions.
15. **P14** — Auction Lots Overlay + OBS-only autoscroll/footer.
16. **P15** — Wheel OBS widget + appearance/center-image UX.
17. **P16** — authoritative timer/wheel/audio timing core.
18. **P17** — Auction Settings over final timer/wheel foundations.
19. **P18** — integration connection/state UX + Auction readiness/RNG navigation.
20. **P19** — conversion/pending-rate workflow.
21. **P20** — Max Amount/Wheel business state machine.
22. **P21** — source-time pending gate + `Без текста N`.
23. **P22** — integration transparency + final History/Journal presentation.
24. **FINAL GATE** — complete automated/manual regression and release acceptance.

Mechanical coverage: UI-001…UI-090 = 90/90 accounted for, no missing IDs, no duplicate package assignment. UI-014/016/017/018/023/026/027/031/044/057 are preserve/resolved/superseded validation-only items; QA-1.0.8-01/02 remain outside this batch; QA-1.0.8-03 is handled by P21/UI-087.
## Сохранённые future scope после текущего review-batch

Эти пункты сохранены для будущего и **не являются следующей автоматической очередью**, пока текущий review-batch не сверён по зависимостям и не реализован/закрыт. Для каждого из них позже всё равно требуется fresh exact-CURRENT review и отдельное решение пользователя.

1. **Global Multi-File Import** — текущий post-D26 candidate, tracking **#4**. Распространить стандартный Windows Ctrl/Shift multi-select на применимые потоки «Добавить файл…», переиспользуя уже работающий D26 multi-select и существующие managed/external/duplicate rules.
2. **D40 — ручной порядок soundtrack/music library** — сохранённая future-идея, не реализована D26. Должна переиспользовать D43/D26 audio/media/playback state, а не создавать второй player/library backend. Это **не восстановление** superseded pre-D26 Auction playlist/Loop-One модели: с D26 текущий Auction soundtrack — один выбранный зацикленный файл из shared soundtrack library.
3. **D34 — Tourniquet donation adapter** — possible/deferred integration; перед реализацией требуется свежая проверка официального API/event delivery/auth/currencies/security.
4. **D41 — кроссплатформенная агрегация чатов + отдельный OBS chat overlay** — user-requested post-completion idea; обычные сообщения чата сами по себе не меняют auction/SM-points/timer/wheel state.
5. **Older YouTube platform/integration candidate** — сохранённая отдельная integration-direction с неуточнённым scope. Не путать с историческим W3 YouTube soundtrack-source wording и не путать с закрытым «Трейлер (YouTube)».
6. **D38 — optional LAN access to standalone OBS widgets** — post-completion only; localhost остаётся default, Internet exposure по умолчанию запрещён.
7. **Public Web / ordinary site presentation** — сохранённое future/publication direction; exact hosting/security/update/UI scope не определён и не auto-authorized.
8. **D27 — «Честное колесо»** — optional physics/final-stop winner mode; default RNG-first wheel не меняется.
9. **D7 — whole-snapshot cryptographic verification hardening** — security hardening поверх уже реализованной verification model. Public Internet verification is not implied; any LAN/public viewer endpoint remains a separate D38/Public-Web/security decision.

Порядок 2–9 восстановлен из ранее принятого complexity/dependency planning. Он нужен, чтобы не потерять зависимости, но **не означает автоматического выбора следующей реализации**.

## Явно отложенные / пропущенные пользователем

Эти пункты живы, но не должны автоматически возвращаться в текущую очередь:

- **D16 — local-wheel hover highlight** — explicitly deferred.
- **D17 — random spin duration** — explicitly skipped for now.
- **D18 — wheel visual style selector** — explicitly skipped for now.
- **D20 — visual sector split** — explicitly deferred.
- **D22 — Battle Royale** — approved post-completion, explicitly deferred 2026-09-29; tracking **#5**.
- **W1 — Space -> existing «Крутить»** — ранее реализовывался, затем сознательно снят из MAIN и оставлен post-completion. If reopened, Space must reuse the existing Spin action, stay inactive while focus is in text/numeric/other controls with normal Space behavior, and be blocked during invalid/re-entrant/ongoing spin states.
- **Сохранённые аукционы** + зависимый полный **«Новый аукцион...»** — deferred reusable-auction workflow.
- **A8 compensating Undo** — только possible post-completion; прежний whitelist не считается pre-approved, fresh safety review обязателен. Retained invariants: compensation appends an auditable reversal event instead of deleting original history, is blocked after unsafe dependent changes, and remains operator-only/not viewer-facing.
- **B6 external auction-service API adapter contract** — deferred; fresh source-of-truth/conflict/ID/dedup/write-policy review обязателен. Provider token must use B1 protected credential storage; B6 must wrap the common integration/auction backend rather than create a second auction engine.
- Дополнительные provider adapters: **iHAQ Donate v2.0, ODA Digital/OpenDonationAssistant, DonateX, VK Video Live rewards/points, Kick Channel Points/Custom Rewards, Donate Helper, DonatePay** — deferred. Все используют общий B2/B3 dedup/conversion/history/matching path, official/reliable APIs only, no page/OBS/browser scraping; provider test flags obey QA-1.0.8-02 safety invariant. Kick/VK remain feasibility-conditional; Donate Helper/iHAQ feasibility-gated; DonatePay exact realtime payload/auth contract and DonateX delivery contract require fresh revalidation; ODA remains contract-blocked.
- Реальная Twitch Channel Points/Custom Rewards verification — eligibility-dependent, не потерянная feature-задача.

## Approved/retained post-completion wheel items, пока не выбранные

- **D23 — import custom participants**: destination «в текущий аукцион» через existing add/increment path либо temporary wheel-only participants; preview/confirmation и duplicate merge остаются частью сохранённого design.
- **D24 — отдельный OBS Browser Source со списком участников колеса**: независим от operator list и Wheel Overlay; должен использовать authoritative wheel state.
- **D25 — cumulative probability лотов с суммой <= сумме победителя**: approved only as post-completion / **не нужно сейчас**; считать по resolved weighted-wheel snapshot.
- **D42 — текущий лот/сектор под стрелкой во время вращения**: approved post-completion; local + OBS, включаемое/выключаемое отображение, без изменения RNG/weights/winner.

## Принятые/сохранённые future ideas, не выбранные в реализацию

Наличие здесь означает сохранённое пользовательское решение/идею, а не разрешение начать код.

- **D1** double timer / elapsed count-up — user-accepted as possible / deferred.
- **D2** pin/unpin lot — user-accepted as possible / deferred.
- **D5 advanced History analytics** — **USER-ACCEPTED POST-COMPLETION / POST-INTEGRATION**, а не assistant-only possibility: activity heatmap, weekdays distribution, participant rankings, separate points/donations analytics, record cards и «Самый дорогой победивший лот». Core History уже реализован. Fresh review must preserve the accepted identity/comparability rules: participant identity uses provider/source + stable external user ID rather than mutable nickname; cross-service accounts are not auto-merged by matching names; unlike point systems/currencies are not naively combined without an explicit comparable basis/base-currency rule; analytics reuse authoritative completed-history snapshots rather than a second backend.
- **D9** localization/languages — user-accepted / deferred post-completion; централизованная UI-localization, без автоматического перевода пользовательских данных, названий игр и History/Journal content.
- **D10** GitHub link — conditional future item; only the official InOneLine repository is valid. The public repo exists; placement still needs fresh review.
- **D11** Telegram link — conditional on an official project Telegram resource; official project link only.
- **D12** support/Boosty link — conditional on completion/publication and an official support resource; informational/project UI, not Auction business UI.
- **D13** optional Pending/manual-processing queue — user-accepted as possible post-completion; MAIN automatic acceptance не меняется.
- **D28** artificial/fixed probability mode — user-accepted as possible post-completion, only explicit artificial-chance mode.
- **D29** viewer names in viewer-facing table — user-accepted as possible / integration-dependent.
- **D30** blind/hidden viewer amounts — user-accepted as possible post-completion; authoritative values/RNG unchanged.
- **D31** Never/Match/Always auto-processing selector — user-accepted as possible extension of future D13.
- **D32** viewer name as order text — user-accepted, later narrowed to a separate future participant/viewer-based mode.
- **D33** alternative display sorts old/new/cheap/expensive — user-accepted as possible; default amount-desc stays.
- **D35** per-bet fortune multiplier — user-accepted as possible post-completion.
- **D36** viewer chooses lot — user-accepted as possible, dependent on D35 and fresh interaction review.
- **D37** presets export/import — user-accepted / deferred post-completion.
- **Games/List Compact presentation** — earlier accepted, 2026-09-28 explicitly postponed until a real future need appears.
- **Auction Lots Normal/Compact applicability** — only specification-reconciliation territory; not a confirmed defect.

## Неутверждённые / review-later только

- **D3** universal inline editing in all tables — possible post-completion; no current approval to implement.
- **Auction Lots Normal/Compact** remains specification-reconciliation territory unless separately selected.

## Важные status corrections

- Games/List shared persisted **Autoscroll** из старого PASS13 **не является живой задачей**: 2026-09-28 пользователь прямо решил не добавлять её, потому что автопрокрутка уже реализована там, где нужна.
- **D15 Twitch AI-bot/neural-network** — не подтверждён как InOneLine roadmap item; historical identifier only.
- **D39 per-scene widget style profiles** — historical assistant-proposed possibility; **NOT ACTIONABLE** без нового прямого решения пользователя.
- Historical W3 **YouTube URL/video-ID soundtrack source** — reference-only possibility, не direct-user-approved roadmap scope.
- Historical **«Трейлер (YouTube)»** — resolved/closed; не возвращать.
- **D4** separate top-level Wheel page, **D6** generic Widgets umbrella, **D8** video requests, **D14** old umbrella item — rejected/superseded; не возвращать автоматически.
- F-series rejected/superseded items не являются backlog.
- H-series — existing behavior to preserve, а не новые задачи.

## Недавние закрытые roadmap items

- **QA-1.0.2-01 / unified OBS onboarding** — CLOSED in 1.0.2.
- **QA-1.0.2-02 / external donation auto-extension completion** — CLOSED in 1.0.3.
- **D19 — custom center image + remote Twitch/7TV/BTTV/FFZ sources + quick picker** — RELEASED in 1.0.4.
- **D43 — OBS Browser Audio Transport** — RELEASED in 1.0.5.
- **D21 — Elimination wheel** — RELEASED in 1.0.6.
- **D26 — Music Player + shared soundtrack library + OBS overlay** — RELEASED in 1.0.7.
- **Global Conditional UI Visibility / #3** — RELEASED in 1.0.8.
- Старый deferred stale-OBS-page reload/version-handshake уже закрыт реализованным overlay handshake; отдельной roadmap-задачей больше не является.
- Старый wheel-overlay infinite RAF optimization также не является открытой задачей: current wheel overlay запускает animation RAF только во время реального wheel animation.
- Старые release-hygiene/unused-file cleanup темы закрыты maintenance-аудитом 2026-10-01/02.

## Process gate

Release cadence считает **только принятые CURRENT/released версии**; rejected candidate/FIX не считаются.

После принятых 1.0.4–1.0.8 текущая арифметическая отметка — **21/25**. Перед фактическим C1 gate счётчик всё равно сверяется с release history.

## Roadmap safety rule

Наличие идеи в этом файле не означает разрешения на реализацию. Перед product change:

1. сверить latest exact CURRENT code/data/UI;
2. проверить, не была ли идея позже реализована, отложена, отклонена или superseded;
3. выбрать ровно один scope;
4. определить минимальный reuse-first diff;
5. получить явное approval;
6. automated QA -> native Windows/manual gate -> explicit acceptance -> promotion exact tested bytes.

Подробный повторный reconciliation от 2026-10-02: docs/history/ROADMAP_RECONCILIATION_2026-10-02.md.

## Current implementation handoff

- P03: full manual checklist accepted, merged and post-merge regression passed. P04-A / UI-025 is unblocked.
- P04: first remove obsolete list hide/show state/hooks and fallback automatic selection, then implement the accepted search/Enter/deselect contract and total-points snapshot reuse. Keep individual implementation steps small.
- Manual checks for each current candidate package are delivered together as one complete checklist.

## P03 technical closure and P04-A start

- User accepted the complete P03 manual checklist: «Работает. Идём дальше.»
- Clean promotion PR #26 merged as `8a0ac384f2df7b2cbf526c14e62ae89b86586932`; all three accepted file blobs match candidate `9fb64bc0d0867f439b0866f82826b406c22ef012`.
- Pre-merge Windows regression `37647359158` and wording gate `37647358838` — **SUCCESS**.
- Exact merge-commit Windows regression `37647803098` and wording gate `37647803210` — **SUCCESS**. Historical QA PR #25 closed without merge. Accepted installer bytes were not replaced.
- **P03 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.**
- **P04-A / UI-025 = MANUALLY ACCEPTED / AWAITING CLEAN PROMOTION.** Accepted scope removes obsolete hide/show-list buttons, spacers, MainWindow/Enter visibility hooks and `lists/visible`, `games/list_visible`, `public/list_visible` UI-state keys while preserving tables/data, geometry/tab state and explicit search navigation. Selection/search/total-points remain separate later small steps.
- P04 remains open. Clean-promote, merge and pass exact post-merge regression before starting the next implementation step.

## P04-A / UI-025 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS

- Branch `candidate/p04-a-list-visibility`, head `3cdff95129d012729d1cfc8c7a74f4050f3231d0`, draft PR #27. Exactly four changed files: MainWindow, Games, Public and existing GUI regression smoke; 53 additions / 195 deletions. Published blobs match the locally tested files.
- Removed only obsolete hide/show controls, empty spacers and MainWindow/search visibility hooks. `_restore_ui_state()` removes `lists/visible`, `games/list_visible`, `public/list_visible`; save no longer recreates them. Window geometry/maximized/tab state and the native-QSettings migration backup remain intact. Existing tables, data, filters, explicit selection synchronization, statuses, schema and accepted P03 CSV/date behavior are preserved.
- Local compile, publication wording and full existing GUI smoke — **PASS**. New GUI cases cover upgrade from false visibility preferences, both tables visible, no hide/show buttons, Enter navigation and synchronized selection, unchanged window size and saved-tab/geometry persistence.
- Exact candidate Windows regression `37648861189` — **SUCCESS**, including Native GUI, frozen startup/Browser Source, installer build, silent install and artifact preservation. Publication wording gate `37648861211` — **SUCCESS**.
- Artifact `11495357287`, ZIP size 46,751,606 bytes, GitHub SHA-256 digest `1eb7e5f9589f71fae4cf778d6da90f06e5d08badea0fd67035fd8d3f900bfcee`. Installer CI SHA-256 `086ed75bf046036a0d7d74efff677626f460d6346c5a849249d3fd53d229bdc0`.
- Drive handoff: `InOneLine_P04_A_CANDIDATE_1.0.8_WINDOWS_QA.zip`, file ID `13AHiI075GQtGE5stmsQFUhUrnuDA9KRR`; uploaded directly from the GitHub artifact reference, verified Drive size 46,751,606 bytes.
- Complete manual checklist issued together: (1) both lists and existing records visible, hide/show buttons absent; (2) repeated tab switches do not resize the window or hide either table; (3) Enter search on both tabs selects/navigates to an active existing record and synchronizes selection; (4) F5 keeps both tables visible and data accessible; (5) restart restores window position/size and selected tab, both tables remain visible.
- **P04-A = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS. P04 remains open.** Clean promotion PR #28 passed regression `37652474014` + wording `37652474280`, merged as `fddf49014ffb34ff48c6871027a817f1453edb9e`, and exact post-merge regression `37653013085` + wording `37653013097` succeeded. Candidate PR #27 closed without merge. **P04-B / BUG-003 is the next isolated step.** Full search/filter/total-points changes remain later scopes.


## P04-B / BUG-003 — next isolated implementation step

- Remove only the implicit fallback that selects row 0 during ordinary refresh when the former selected record is no longer present.
- Preserve selection when the same record remains visible; preserve no-selection when there was none.
- Add empty-area click deselection to the main list without a new selection subsystem.
- Preserve explicit Enter-search and `focus_game()` selection.
- Do not include UI-007/UI-008/UI-009/UI-028 or UI-076 in P04-B.


## P04-B / BUG-003 candidate — AUTOMATED PASS / AWAITING MANUAL QA

- Candidate head `f3740181a9f161c3c56965d075a2d3c2ae3d0762`, draft PR #29; only main-list selection runtime + existing GUI regression changed.
- Removed implicit first-row fallback from ordinary refresh; still-visible selection is preserved, missing/no selection remains empty.
- Empty-area left click clears selection/current cell; explicit Enter search and `focus_game()` remain selection commands.
- Regression Foundation `37654068727` and wording gate `37654069253` = SUCCESS.
- Drive manual-QA build: `InOneLine_P04_B_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1eRIdxzl8ny6svzrZlgKeS-3nsDJI9IOu`.
- Do not start UI-007/UI-008/UI-009/UI-028/UI-076 until P04-B is manually accepted, clean-promoted, merged and post-merge verified.

## P04-B CLOSED / P04-C candidate gate — 2026-10-07

- P04-B / BUG-003 manually accepted by user («Работает. Идём дальше.»), promoted and merged as `f2cc6e9f0968eac1be75f7d5b91ead7afe7e76df`.
- Exact post-merge Regression Foundation `37655810706` and wording gate `37655810503` = **SUCCESS**. P04-B = **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**.
- P04-C / BUG-004 candidate: `candidate/p04-c-public-selection-v2`, head `68f11b92fe2dd5ebb91752cf8723a9d5c66a0e09`, draft PR #31.
- Scope remains isolated: Public empty-area deselection + existing GUI regression only. Public ordinary refresh has no implicit selection fallback; Enter and `select_synced_search_result()` remain explicit selection actions.
- Windows regression `37656101654` and wording checks = **SUCCESS**.
- Drive manual-QA build: `InOneLine_P04_C_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1M0ooksHuIEa0_50oJEcICJtkzzWCxK5L`.
- P04-C = **AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED**. Do not begin the next P04 scope until manual acceptance.

## GLOBAL-FOCUS-001 — единое снятие focus/selection во всей программе — DEFERRED / RECORDED — 2026-10-07

- Пользователь выявил общий UX-дефект после ручной проверки P04-C: если таблица полностью заполнена строками, для снятия selection может не существовать видимой пустой области; пользователь не должен прокручивать список до самого низа только ради deselect.
- Та же проблема шире таблиц: после клика в поле ввода focus визуально/логически остаётся на нём, пока пользователь не выберет другой focusable control.
- Это не дефект только Games/Public и не должен решаться набором локальных hacks по каждой вкладке.
- Целевое продуктовое правило: должен существовать единый естественный способ убрать focus с поля и снять selection с таблицы независимо от наличия видимой пустой строки/области. Пользователь не должен искать другое поле или прокручивать длинный список вниз.
- Предпочтительно сначала исследовать один общий механизм на уровне shared UI/MainWindow/event handling; не ломать обычный click/double-click, Enter-search, keyboard navigation, dialog validation, caret/selection semantics, buttons, combo/spin boxes и explicit programmatic focus/selection.
- Конкретный жест/реализацию (например neutral-background click и/или универсальный keyboard escape fallback) утвердить при отдельном global UI review после проверки влияния на существующие widgets.
- Не расширять текущий P04-C до глобального mouse/focus subsystem. Реализовывать отдельным изолированным шагом после сортировки зависимостей.

## P04-C / BUG-004 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-07

- User manual result: `Работает`. Separate cross-app focus/selection limitation was recorded as GLOBAL-FOCUS-001 and intentionally excluded from P04-C.
- Exact accepted candidate head: `68f11b92fe2dd5ebb91752cf8723a9d5c66a0e09`.
- Clean promotion PR #32 passed regression and wording gates, then merged as `7df4071088e8ef3f89b5f6d20caeab745a958d39`.
- Exact post-merge Regression Foundation `37658841462` = SUCCESS; wording gate `37658841402` = SUCCESS.
- P04-C remains limited to Public empty-area deselection and existing GUI regression. GLOBAL-FOCUS-001 remains DEFERRED / RECORDED as a later global UI task.

## P04-D / UI-007 candidate — AUTOMATED PASS / AWAITING MANUAL QA — 2026-10-07

- Branch `candidate/p04-d-search-scope`, head `943a26d76bbaf0784b9e38fed84076d9597e82e3`, draft PR #33; base at implementation start `948a577e558ac37d36a10679d12afc9dde3a4b79`.
- Scope is UI-007 only. A non-empty main-list search reuses `games_refresh_snapshot/_list_games_conn` with effective `status_filter="all"` + `include_archived=True`, while `active_filter` itself remains unchanged.
- Clearing search therefore immediately restores the currently selected statistic filter. Existing Unicode normalization and title/review matching are preserved; `auction_only=1` temporary lots remain excluded by the existing normal-list query.
- UI-008/UI-009/UI-028/UI-076 and GLOBAL-FOCUS-001 are not included.
- Exact diff: `streaming_manager/views/games.py` + existing `tools/gui_regression_smoke.py` only; 64 additions / 3 deletions.
- Regression Foundation `37660389855` = SUCCESS; wording gate `37660389867` = SUCCESS.
- Artifact `11501485064`, ZIP 46,756,657 bytes, SHA-256 `6e8d3d5d320c60fc75e882a7c53e00fefea6388fadae7081f3d97e29f812dad9`; contains exactly `InOneLine_Setup_1.0.8.exe`, 47,616,617 bytes, SHA-256 `2a6fa43681b535f14a4092693c975033863fe969b756e78cc994943fc6e682d7`.
- Drive handoff: `InOneLine_P04_D_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1o1BEOnoJqFCwkgTJVQoBgahGiVWYslSC`, verified 46,756,657 bytes.
- **P04-D = AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED.** Do not start UI-008/UI-009 or later P04 scopes before manual acceptance and technical closure.

## P04-D / UI-007 — завершение 2026-10-08

- **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS**. Пользователь подтвердил 6/6 сценариев. Изолированный поиск игнорирует статистический фильтр только при непустом запросе, включает обычный архив и возвращает выбранный фильтр после очистки.
- QA candidate `943a26d76bbaf0784b9e38fed84076d9597e82e3` / PR #33; чистый PR #35 переносит те же два Git blob; принят в `main` коммитом `e9e22d27d0f0101773c7016367f867e2bb61e7c8`. Pre-merge regression `37748280816`, wording `37748280794`, post-merge regression `37748751586`, wording `37748751519` — все SUCCESS.
- **Дальше P04 / UI-008** (убрать дублирующую кнопку `Найти`, сохранив live-search + Enter). Затем отдельными небольшими scope UI-009 / UI-028 / UI-076 в порядке согласованных зависимостей. P05 и далее пока не начаты.

## UI-008 — кандидат / ожидает ручной проверки 2026-10-08

- `UI-008` реализован изолированно на branch `candidate/p04-e-ui008-search-button`, draft PR #37, head `f8f03430d0ed77fddde18ba58e2db7b8030cead4`. **AUTOMATED PASS / AWAITING MANUAL QA / NOT MERGED**.
- Только убрать дублирующую кнопку `Найти` в основном списке; live-search/Enter сохраняются. UI-009, UI-028, UI-076 и GLOBAL-FOCUS-001 не включены.
- Windows CI run `37749509764` и publication wording `37749509711` = SUCCESS. QA ZIP сохранён на Drive: `1ME2RkaJSUpME4PQE3-mIXZHjpaUP9XMQ`, SHA-256 `44ef8a29606af13c7af3f4a9343a2c890e25a90bf43f67649a7499de21e0029d`.
- Следующий шаг: только ручная QA UI-008, затем чистый перенос в `main` + точная post-merge проверка при PASS. Другие P04 части пока не начинать.

## UI-008 — ручная QA выявила дефект / REOPENED — 2026-10-08

- На присланном скриншоте основного списка кнопка `Найти` всё ещё отображается; 4/5 остальных ручных проверок PASS, 1/5 FAIL. **UI-008 не принят; PR #37 не merge.**
- Candidate source `f8f03430d0ed77fddde18ba58e2db7b8030cead4` не содержит кнопку; проверка source GUI CI не равна проверке UI реально установленного EXE. Диагностика: путь/хэш активного процесса и использованного установщика, возможный старый экземпляр или альтернативный каталог, проверка упаковки/обновления той же 1.0.8.
- До устранения причины и повторного ручного PASS очередь остановлена на UI-008. UI-009 и дальнейшие пакеты не начинать.

## UI-008 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-08

- После первой QA (4/5 PASS, кнопка `Найти` осталась) пользователь повторно установил проверяемую сборку и прислал скриншот `Список` без этой кнопки. Суммарно **5/5 ручных сценариев PASS**. Первопричина первоначального отображения кнопки неизвестна; QA-наблюдение сохранить, не придумывать вывод об installer.
- Чистый перенос проверенных файлов: PR #40, merge `f5e244d04db63ddb421213d3ee1272ed77aee55c`; pre-merge Windows `37771721603` + wording `37771721591`, точный post-merge Windows `37772054443` + wording `37772054420` — все SUCCESS. PR #37 закрыт без merge; принятый installer не пересобирался.
- **Следующее по утверждённой очереди — UI-009**: удалить дублирующую кнопку `Сбросить фильтры` на основном списке, используя уже существующий крестик поля поиска, при этом сохранять выбранный statistic filter. UI-028 (Public `Найти`) и UI-076 (счётчик баллов) после отдельной приёмки.

## UI-009 — candidate / AWAITING MANUAL QA — 2026-10-08

- Exact candidate `2fd8fa5c31b94469e681aaf0d8b1f3699f0c354e`, PR #42 (draft). Removes redundant main-list `Сбросить фильтры`; existing native clear X removes search text without changing statistic filter. No new state/subsystem; Public `Найти` and subsequent P04 scope preserved.
- Windows regression `37772947602` + wording `37772947662` = SUCCESS; QA Drive ZIP `1I6wRbxVqhXPmG_wI4bm4NaY3ujK1f-C9`; SHA-256 `d0d4c0b4cf5a96d428c829e27b19d5c77cc7c58d78d9c7b9e78e509447c24bb7`.
- Status: **AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED**. UI-028/UI-076 and further scopes wait for separate manual approval and technical closure.

## UI-009 — завершение 2026-10-08

- **CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** Пользователь принял 5/5 сценариев. Убрана лишняя основная кнопка `Сбросить фильтры`, native крестик очистки поиска сохраняет активный фильтр; единственный лишний helper `reset_filters()` убран после проверки ссылок.
- Clean PR #44 merged `464136d144e054efcf38a10da8e075ed5fec8281`; pre-merge Windows `37778466982`, wording `37778467039`, exact post-merge Windows `37778963533`, wording `37778963540` — SUCCESS. Historical PR #42 closed without merge, accepted QA ZIP unchanged.
- **Следующий отдельный шаг P04 — UI-028 (публичный поиск без кнопки `Найти`)**, затем UI-076 по дорожной карте; не включать другие UI задачи в UI-028.

## UI-028 — candidate / AUTOMATED PASS / AWAITING MANUAL QA — 2026-10-08

- UI-028 isolated branch `candidate/p04-g-ui028-public-find-removal`, head `e23e4d2fea50cdc6f962c3486244d4a018279c77` (draft PR #46), изменены только Public GUI и существующий regression smoke. Удалена `Найти` из `Публичный список`, сохранены live-search/Enter, подсистема фильтров основного списка и API.
- Windows CI `37779716348` + wording `37779716372` SUCCESS. Drive QA ZIP `1INEdrDa7vnmkioU4C_DWswix-JVXJqfh`, SHA-256 `67e41ad6777bdea66b0f460998ad6014970d4c3b0e0e243bbcc93de3b43f1502`.
- Status **AUTOMATED PASS / AWAITING USER MANUAL QA / NOT MERGED**. UI-076 и дальнейшие шаги не начинать до ручной приёмки UI-028 и точной post-merge проверки.

## UI-028 — CLOSED / ACCEPTED / POST-MERGE PASS — 2026-10-08

- Ручной PASS 5/5. Чистый PR #48 объединил точно проверенные два файла: merge `974515f8065c8aa11e9b244d9b4841d346259a64`. Original draft PR #46 закрыт без повторного merge.
- Pre-merge CI Windows `37795531310`, wording `37795531399`; exact post-merge Windows `37796011497`, wording `37796011272` — SUCCESS.
- Следующий изолированный пункт `UI-076`: добавить справа информационный `Всего баллов: N` на основной статистической строке; существующий `_game_stats_conn` должен суммировать `sm_points` всех `auction_only=0` независимо от статуса/архива/фильтра. Без дополнительного SQL, Public, API, OBS и нового фильтра.

## UI-076 — candidate / AUTOMATED PASS / AWAITING USER MANUAL QA — 2026-10-08

- Точный candidate `ad6a913dceaa3ea05584211845a1c9755e5fdebf`, PR #50 (draft), основан на закрытом UI-028. Информационный счётчик справа в статистической строке через existing single-query `_game_stats_conn` + existing `games_refresh_snapshot -> _update_stats`. В сумме `sm_points` всех обычных записей с архивом независимо от фильтра; `auction_only=1` исключаются до materialization.
- Regression Windows `37797159783` и wording `37797159654` SUCCESS. QA ZIP [Google Drive](https://drive.google.com/file/d/1sRuOo4CX5ANiLBfnUMDSvCcWIvrlmKq5/view) (46 774 807 bytes; declared GitHub artifact digest `5796783f2b563c4348174c9e5bed4dc0d7f34b5b957432fbc645c0fe7628297d`).
- **NOT ACCEPTED / NOT MERGED**. Следующий шаг — ручная проверка UI-076. Не начинать следующий самостоятельный пункт до приёмки и clean promotion + точного post-merge PASS.

## UI-076 — REOPENED after MANUAL FAIL, fixed candidate AWAITING RETEST — 2026-10-08

- Пользовательские скриншоты: при 1100 px исходные фильтры и новый счётчик `Всего баллов: N` обрезались (пункт 6 FAIL; остальные 5 PASS). UI-076 **не принят**.
- В первоначальном draft PR #50 обновлён код до head `cbc0056daba456e9c5bf3792f979ca6e9b6877c7`: адаптивный перенос только информационного QLabel вниз вправо при узком окне с возвратом в первый ряд при расширении. Агрегат SUM и старые кнопки неизменны. Тест окна `1100→1600→1100` и фильтров включён в existing GUI smoke.
- Windows regression `37803969976` SUCCESS, wording SUCCESS; новый Drive ZIP `1XQ83iShKwVZapAxyhlp5neDIP5_Flu6I`, 46 772 444 байта, SHA-256 `c86caa20d0c7939997e15bd1d04bcbc741da34a92b8014238327a45139a63041`, проверка CRC PASS. Прежний `1sRuOo4CX5ANiLBfnUMDSvCcWIvrlmKq5` — FAILED/SUPERSEDED (сохранён).
- **Ожидается только повторная ручная QA исправленной сборки; не объединять с main до PASS.** Затем clean promotion и post-merge CI, после чего перейти по дорожной карте.

## UI-076 — layout на строке кнопок / AUTOMATED PASS / AWAITING MANUAL QA — 2026-10-08

- Пользователь не принял UX второго кандидата (счётчик сдвигался в третью строку при узком окне). Третий кандидат PR #50 head `9608b6c557953797779e95dfb0a08806600f5330`: счётчик **всегда на одном уровне** с `Правила сортировки`, `Копировать URL списка`, `Открыть предпросмотр списка`; правый край выравнивается с `Не кооп` на предыдущем ряду через реальную геометрию Qt. Сумма/фильтры/архив не изменены. Промежуточный off-by-spacing FAIL 9px исправлен, Windows CI `37808003241` SUCCESS.
- Новый QA ZIP [Drive](https://drive.google.com/file/d/1DMqTUTMv4slMcFiXMnx7sdAYFNDi38h8/view), SHA-256 `30ba79754efc53feafac86412184daea4f796f8d8735fff9ddf4a712a82a42bf`, CRC PASS, 46 785 061 байт. Два прежних ZIP historical/superseded. **Ожидать ручной PASS; UI-076 пока NOT MERGED**.
- **P06** — отдельно от UI-076 уменьшить минимальный размер окна ниже текущих 1100×700 и добавить горизонтальную прокрутку. Не вносить в UI-076 и проверить новый anchor badge в рамках P06 с горизонтальной прокруткой на меньших ширинах.

## UI-076 — stable position 2 / new QA candidate pending acceptance — 2026-10-08

- Пользователь выявил горизонтальное дёргание QLabel при перетаскивании границы окна из-за dynamic resize spacer. Исправление **не переносит позицию вручную**: QLabel стоит в `sorting_actions` непосредственно после третьей кнопки `Открыть предпросмотр списка` (вариант 2). Предыдущие `QSpacerItem`, `showEvent/resizeEvent`, выравнивание по `Не кооп` удалены как источник jitter. `Очистить список` и скрытые `В архив`/`Восстановить` не затронуты.
- GitHub [draft PR #50](https://github.com/ALL-EX-E/InOneLine/pull/50) head `220adcc78778a43265a855045bf694a5e5d75d03`. Windows regression `37810486613` SUCCESS (7 widths incl. 1100/1600); wording SUCCESS. Новый [Drive QA ZIP](https://drive.google.com/file/d/1Ohsul5NaTtGP7J_TCKMytBuY-E8N22dA/view), SHA-256 `18ae42c5e2544c62dfbd646d22828150823623d88ed49bb35ee6d4600b50189b`, 46 769 147 bytes, CRC PASS. Другие три UI-076 ZIP superseded/historical.
- **UI-076 не принят и не merged; ожидается ручная QA именно 4-го кандидата.** Затем clean promotion + exact post-merge Windows CI.
- Напоминание: **P06** остаётся отдельной утверждённой задачей уменьшить минимум окна ниже 1100 и добавить горизонтальную прокрутку. UI-076 не содержит P06.


## UI-076 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-08

- Ручной PASS пользователя: «Всё работает. Идём дальше» для кандидата со стабильной позицией 2 — счётчик сразу после «Открыть предпросмотр списка», без пересчёта геометрии при resize.
- QA ZIP `11564293733` / Drive `1Ohsul5NaTtGP7J_TCKMytBuY-E8N22dA`, 46 769 147 bytes, SHA-256 `18ae42c5e2544c62dfbd646d22828150823623d88ed49bb35ee6d4600b50189b`.
- Clean promotion PR #55 merged as `5d8ee1e2d7fb7be57246ff332cf603dc970b54fc`; exact candidate blobs are present. Original candidate PR #50 closed without merge.
- Pre-merge Windows `37814527293` + wording `37814527185`/`37814518804`; exact post-merge Windows `37814970241` + wording `37814970284` — all **SUCCESS**.
- **P04/UI-076 CLOSED.** Version 1.0.8, schema 19, 15 migrations, published release and rollback unchanged.
- Следующий пункт очереди: **P05 — Public file export + removal Настройки → Экспорт**. Перед runtime-изменением требуется fresh scope review exact CURRENT и отдельное явное одобрение пользователя.


## P05 — свежий review exact CURRENT завершён; ожидает batch approval — 2026-10-08

- Review проведён по `main` `eb123eb99d9913db2d6ee2694471dc99f8b9d569`. Runtime P05 не менялся.
- Объём UI-088/UI-089/UI-090 подтверждён: перенос трёх existing file-export actions на `Публичный список`; отдельное пояснение snapshot vs auto-update XLSX mirror; удаление legacy compatible-export controls и внутренней вкладки `Настройки → Экспорт`.
- Existing public exporters/data contract и `/api/public` сохраняются; старый импорт `Название|Баллы` остаётся совместимым. Regression gate должен проверять новые кнопки/отсутствие дублей, четыре оставшиеся вкладки настроек и сохранность зеркала/импорта.
- **READY AFTER BATCH APPROVAL / NOT IMPLEMENTED.** Код не менять до отдельного прямого одобрения пользователя.

## P05 status update — 2026-10-09

- Пользователь подтвердил: «Работает. Записывай и идём дальше». Initial manual PASS относится к Public CSV/JSON/Excel actions, обоим XLSX mirror flows, удалённому Settings Export UI и исчезновению пустого прямоугольника на `Аукцион`.
- Проверенный кандидат: `9eb8aae28a2d85709e4090dce4cb12badc4b6607`; QA ZIP `InOneLine_P05_AUCTION_HOST_FIX_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1TV2hvEz4-uVpk3ax07r9kCfnsmKQcz_y`, 46,762,701 bytes, SHA-256 `1d6df043f106d9656d4476d3cac77376d485cc4a87230a2c2ac076d48909060e`.
- Clean promotion PR #59 merged as `45bb317751e688054d201ee3d77d5bbe5199c82b`; original candidate PR #58 closed without merge. Promotion Regression Foundation `37883637947` and wording gate `37883637998` succeeded. No release/version/schema/migration changes.
- При сверке UI-088 обнаружено, что первый promotion изменил файловый заголовок `НАЗВАНИЕ ИГРЫ` на `НАЗВАНИЕ`; утверждённый формат CSV/XLSX и JSON `columns` требует сохранить старый заголовок. Follow-up PR #60 (`886eaa2d96dc1b9576f2e292e2a1af6e6ed2ccee`) восстанавливает его и проверяет все три экспорта. Windows regression `37883971211` и wording `37883971209` succeeded.
- Follow-up QA ZIP: `InOneLine_P05_HEADER_FIX_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1O6PmpJMW8Qqf3ST06YlwTkYZ-1zXfsy-`, 46,764,368 bytes; GitHub artifact SHA-256 `86d03f964c57de19c5fea0da2262d99cb9313709a06eab6c886009c52e57f7ad`.
- Follow-up manual retest: **PASS** for CSV, Excel and JSON headers; the user replied `PASS` on 2026-10-09 using the exact QA ZIP listed above.
- Clean promotion PR #62 reused both exact tested file blobs from candidate PR #60 and merged as `777ce8caed26ba05af97adebd0f6c56dd3c48886`. Promotion Regression Foundation `37886832208` and wording gate `37886832239`: **SUCCESS**.
- Candidate PR #60 and QA-only post-merge PR #63 were closed without merge. Exact post-merge Regression Foundation `37887212648` and wording gate `37887212487`: **SUCCESS**.
- **P05 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** App 1.0.8, schema 19, migrations 15, published release and rollback are unchanged.


## P06 — fresh review exact CURRENT complete — 2026-10-09

- Reviewed exact `main` `777ce8caed26ba05af97adebd0f6c56dd3c48886`; app 1.0.8 / schema 19 / migrations 15.
- P05 is closed with manual PASS, clean merge PR #62, and successful post-merge Regression Foundation `37887212648` plus wording gate `37887212487`. Candidate PR #60 and QA-only PR #63 are closed without merge.
- The next package is P06: responsive main-window sizing/scrolling, stable selected-tab restoration after the approved tab reorder, and inclusion/restoration of `data/ui_state.ini` in new full backups while preserving legacy archives and ordinary `.db` backups.
- User authorized continuation with `«Работает. Записывай и идём дальше»`; candidate implementation proceeds within the already accepted P06 scope. Manual QA and clean promotion remain pending.


## P06 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-09

- Пользователь подтвердил полный manual PASS: обычный и минимальный размеры окна; все вкладки и прокрутка только таблиц; перестройка основного списка и отступы кнопок; цветные иконки/подсказки; страницы «Лоты» и «Проведение»; строка «Изображение» в настройках «Аукциона»; сохранение выбранной вкладки после обновления/перезапуска; резервное копирование `.db`, новая полная `.iolbackup` с состоянием UI и legacy `.iolbackup` без `data/ui_state.ini`. Отдельно приняты шрифты/пипетки OBS и первый показ компактных кнопок «Музыки».
- Tested candidate `0901fb2d864190cb2954909302217be0457699cb`; QA archive `InOneLine_P06_RESPONSIVE_TAB_STATE_BACKUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, Drive ID `1YfwqW1SF85QUaxZafI1bgwSozV6LLv-U`, 46,766,667 bytes, SHA-256 `166ffe31981a1f88510245bc64361c6dd5d50a41d129e8d6de55b9c68ad6a14c`.
- Clean promotion PR #66 reused the exact 15 candidate blobs from main `aae15c30ebd69b79d87bf3aeaf5a58a701e27884`; merged as `e9a8919357eeb4cb182e847ef115058e6c253f58`. Candidate PR #65 closed without merge.
- Pre-merge Regression Foundation `37936833848` and publication wording gate `37936833837`: **SUCCESS**. Exact post-merge Regression Foundation `37937370459` and wording gate `37937370714`: **SUCCESS**.
- **P06 = CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS.** App 1.0.8, schema 19, migrations 15, published release and rollback remain unchanged. Next roadmap package: **P07 — position policy + XLSX derived position**.


## P09 / UI-041 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- Пользователь принял весь UI-041 checklist: «Всё работает. Принимаю, записываем и идём дальше.» (2026-10-10 16:16:13 +07 / 09:16:13 UTC). Проверены порядок Веб-камера → Список → Информационный блок, положение и рамка списка, четыре группы шрифтов, независимые copy/preview действия при выключенном встроенном списке, сохранение/перезапуск и доступность при изменении размера окна.
- Exact accepted Windows QA ZIP: `InOneLine_P09_UI041_LIST_GROUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1XrswFhp9s0bVE_NOhiwWcse2QUPD_dTR/view); artifact `11665466642`, 46,790,609 bytes, SHA-256 `7e1938624027ffbff97d7769b62759c1887cc780ee6f56879da84fddae3402c4`. Tested code/test head `eedb5c60b467515a7e542df6ad6b59fdc3f25b88`, Windows `38040034301` SUCCESS; candidate acceptance recorded as `2cedf8fabd752495cb7035aa33537f37de214a48`.
- Clean promotion [PR #86](https://github.com/ALL-EX-E/InOneLine/pull/86), head `646fe570db95087b12c703b8a99e173958a87edd`, copied only the exact two accepted blobs: `streaming_manager/views/stream.py` = `e3ef5d3b81d573fd48021af4702edaf9813e54aa`; `tools/gui_regression_smoke.py` = `a2b17c0fe8dca378250b97448b54108623b8d3c6`. Premerge Windows `38040932080` and wording `38040932034` / `38040930233`: SUCCESS.
- Main merge `6703b123a45be432f30cdb52c7c05c632cfdc47d`: independent recursive Git-tree readback confirms **2/2 identical accepted blobs**. Exact postmerge Windows [38041134372](https://github.com/ALL-EX-E/InOneLine/actions/runs/38041134372) and wording `38041134425`: **SUCCESS**. Original draft PR #85 closed without merge; user-tested installer remains the acceptance reference.
- **UI-041 CLOSED; P09 IN PROGRESS.** Next approved isolated step **UI-042**: move server status to the top and actual OBS URLs plus existing copy/preview actions before the settings of their corresponding sections; preserve existing saves. Wheel access reuses Auction callbacks; its future UI-078 show-mode/settings scope remains queued. Rules editor relocation remains UI-048/UI-060. App 1.0.8 / schema 19 / 15 migrations unchanged.


## P09 / UI-042 — WINDOWS CANDIDATE PASS / AWAITING MANUAL QA / NOT MERGED — 2026-10-10

- After exact accepted UI-041 closure, implemented the already approved UI-042 in isolated `candidate/p09-ui042-obs-access-layout` from canonical main `20539e7afbbf5a2638e2ac7345bd4d7414282d2f`. Draft [PR #87](https://github.com/ALL-EX-E/InOneLine/pull/87), exact source/test head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`.
- One server status at the top; seven actual local URL labels plus copy/preview actions before their corresponding settings. Specialized Saves remain after the original settings forms; all six shared main-overlay Saves unchanged. List URL/actions remain visible with the embedded list disabled. Wheel access uses existing Auction callbacks through MainWindow wiring; both entry points share one URL/preview implementation.
- Only three source/test files: `streaming_manager/views/stream.py` = `035347ddce9fffb332a4150057a7c79924f64170`; `streaming_manager/views/main_window.py` = `1e045d66be0b30c4b74d9a091cb043f5e605e684`; `tools/gui_regression_smoke.py` = `14ee930ee783d607f2aff825c57295453d5dcd3e`. Independent Git tree readback confirms 3/3 local and GitHub blobs identical. AST audit: StreamTab constructor/status-label refresh and MainWindow constructor only; all other 55 StreamTab / 30 MainWindow methods unchanged.
- Real Qt/SQLite TDD: new helper fails on accepted UI-041 base (status below main settings), then passes seven actual copy/preview routes, changed server URL/error state, four specialized Save/refresh checks and previous UI-041 persistence/disabled-list behavior. All P09 helpers PASS; visual/geometry checks at 520/1100/2560 and repeated narrow resize show selectable readable URLs, full action captions and no horizontal overflow. Compile/diff checks and pinned dependency consistency PASS.
- Full local Linux/offscreen suite reaches the previously characterized P06 compact-tab font-metrics failure on accepted baseline; native Windows is the canonical full gate.
- Scope sequencing: UI-042 adds wheel heading/URL/access only; future UI-078 full wheel presentation/show-mode/settings/save remains queued. Existing Rules controls/save are preserved in their current location until UI-048/UI-060 editor relocation; no duplicate editor/settings were added. Remaining Local API health/JSON controls stay until next UI-043. Routes, settings keys, backend, audio and browser rendering unchanged. App 1.0.8 / schema 19 / 15 migrations; official release and rollback unchanged.
- Review follow-up: explicit keyboard order makes the moved copy/preview pairs precede their section settings; real Tab traversal is tested, including OBS Help → main Copy → preview → Current Game. QA helper restores the complete pre-test settings snapshot and deletes initially absent fixture rows, preventing repeated runs from inheriting test values. Keyboard test reproduced the old order before the correction, then PASS.

- Independent read-only Superpowers review on exact final head: no remaining Critical/Important/Minor findings. Reviewer independently passed repeated fresh-DB settings/page/focus restoration, working endpoints, keyboard traversal, existing UI-041 behavior and width geometry; all initial minor findings corrected.
- Full native Windows [Regression Foundation 38045525292](https://github.com/ALL-EX-E/InOneLine/actions/runs/38045525292) **SUCCESS**, exact head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`: compile, DB/backup/legacy/media/source/integrity, native full GUI with `P09_UI042_SECTION_URL_ACTIONS_STATUS_AND_EXISTING_SAVES=PASS` plus prior P09 checks, frozen startup/browser-source, installer build, silent installed startup and clean filesystem all PASS. Wording PR `38045525324` and push `38045522126`: SUCCESS. This final run supersedes earlier candidate validation.
- Manual QA archive: `InOneLine_P09_UI042_OBS_ACCESS_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1jVnnC99nP9Z7s9SUK1ZSQlrjU4EsuNZc/view), folder `Обзор_UI_1.0.8`. GitHub artifact `11666982770`; **46,790,489 bytes**, SHA-256 **`2995e3b138a58d0b93a5401c829af1cc409b081f0e1cbb60cd41ba931e0eef89`**. Downloaded bytes independently match GitHub size/digest; ZIP CRC PASS; exactly one `InOneLine_Setup_1.0.8.exe`. Drive readback confirms name, identical byte size and expected QA folder. This exact archive is the manual-test package.
- **UI-042 AWAITING USER MANUAL QA / NOT MERGED.** Main runtime remains accepted UI-041; P09 IN PROGRESS. Next after UI-042 manual acceptance, clean exact-blob promotion and postmerge PASS: **UI-043**, remove the remaining Local API health/JSON controls from the ordinary Stream/OBS UI while retaining endpoints.

Полный ручной checklist UI-042 (весь список проверяется одной сборкой):
1. Закрыть программу, установить QA installer и открыть Стрим / OBS; данные и сохранённые настройки сохраняются.
2. Состояние: РАБОТАЕТ находится сверху перед Главный оверлей. Под заголовком — фактический /overlay и обе кнопки перед текущей игрой/шрифтами.
3. Во всех семи разделах проверить Копировать URL и Открыть предпросмотр: главный /overlay, Список /list-overlay, таймер /timer-overlay, музыкальный плеер /music-player-overlay, колесо /wheel-overlay, список лотов /auction-lots-overlay, правила /rules-overlay. Копируется полный адрес с фактическим портом; предпросмотр открывает соответствующий виджет. Для списка сохраняется существующий URL без ?preview=1; остальные существующие preview URL имеют ?preview=1.
4. В блоке колеса пока только заголовок, URL и две кнопки; его настройки — отдельный UI-078. Порядок в разделах с существующими настройками: заголовок → URL → copy/preview → настройки → существующая Сохранить. В Список адрес/кнопки перед переключателем; общий порядок Веб-камера → Список → Информационный блок сохранён.
5. Выключить Показывать на оверлее в Список и сохранить: настройки скрываются, а URL и обе кнопки отдельного списка остаются доступны; отдельный список открывается. Снова включить — прежние настройки возвращаются.
6. Изменить размер/цвет таймера, плеера и списка лотов, фон/прозрачность правил; нажать соответствующую Сохранить после настроек. Проверить соответствующие OBS-предпросмотры и сохранение после перезапуска. Локальные Сохранить главного оверлея работают как прежде.
7. Проверить кнопки колеса и в Стрим / OBS, и в Аукцион: копируется один /wheel-overlay с тем же портом, предпросмотр открывается по одному прежнему адресу. Запуск/проведение аукциона и колесо работают как прежде.
8. Проверить Tab: Копировать URL → Открыть предпросмотр → настройки соответствующего раздела. Сузить окно до минимального размера, расширить и снова сузить: все адреса, кнопки и Сохранить доступны через прокрутку, длинные строки/кнопки не обрезаются и не перекрываются.
9. В нижнем Локальный API больше нет общего каталога overlay URL. Оставшиеся Проверить API, Открыть JSON OBS и две JSON-строки удаляются следующим UI-043. Настройки правил пока в прежнем месте; их перенос в редактор выполняется отдельно UI-048/UI-060.


## P09 / UI-042 — CLOSED / MANUALLY ACCEPTED / MERGED / POST-MERGE PASS — 2026-10-10

- Пользователь принял весь девятипунктный checklist UI-042: «Всё работает. Принимаю, записываем и идём дальше.» (2026-10-10 18:41:30 +07 / 11:41:30 UTC). Проверены сохранение данных при установке, верхний статус, семь OBS URL/actions, порядок разделов и Save, отдельный список при выключенном встроенном списке, специализированные сохранения/перезапуск, общие действия колеса, Tab и узкое/широкое окно.
- Exact accepted Windows QA ZIP: `InOneLine_P09_UI042_OBS_ACCESS_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1jVnnC99nP9Z7s9SUK1ZSQlrjU4EsuNZc/view); artifact `11666982770`, 46,790,489 bytes, SHA-256 `2995e3b138a58d0b93a5401c829af1cc409b081f0e1cbb60cd41ba931e0eef89`. Tested source/test head `537e1bf627340393bdd5aec1325ec10fe1ad9e31`, Windows `38045525292` SUCCESS. Candidate acceptance recorded as `949593fd61044c653dc82d4beefc26c136362304`.
- Clean promotion [PR #88](https://github.com/ALL-EX-E/InOneLine/pull/88), head `0e5121a2a3e479955868967d598675202a938dbb`, copied only three exact accepted blobs: `streaming_manager/views/stream.py` = `035347ddce9fffb332a4150057a7c79924f64170`; `streaming_manager/views/main_window.py` = `1e045d66be0b30c4b74d9a091cb043f5e605e684`; `tools/gui_regression_smoke.py` = `14ee930ee783d607f2aff825c57295453d5dcd3e`. Fresh premerge Windows `38049491911` and wording `38049491923` / `38049489084`: SUCCESS.
- Main merge `d50a337c699aec84a175b8b82abad2bae2f4cee3`: independent recursive Git-tree readback confirms **3/3 identical accepted blobs**. Exact postmerge Windows [38049666677](https://github.com/ALL-EX-E/InOneLine/actions/runs/38049666677) and wording `38049666701`: **SUCCESS**. Original draft PR #87 superseded by #88 and closed without merge; the user-tested installer remains the acceptance reference.
- Seven actual OBS URL/copy/preview sections and top server status accepted; existing saves and routes retained. Wheel access shares Auction callbacks; full wheel settings/show-mode remain UI-078. Rules settings remain in the current location until UI-048/UI-060.
- **UI-042 CLOSED; P09 IN PROGRESS.** Next approved isolated step **UI-043**: remove the old lower Local API block, health/JSON buttons and JSON URL rows from ordinary Stream/OBS UI, retaining all diagnostic/data/public endpoints and normal shared background-availability refresh. After UI-043 acceptance/closure, next package P10 begins with GLOBAL-OBS-VISIBILITY-001. App 1.0.8 / schema 19 / 15 migrations unchanged.


## P09 / UI-043 — WINDOWS CANDIDATE PASS / AWAITING MANUAL QA / NOT MERGED — 2026-10-10

- After user acceptance and exact postmerge UI-042 closure, implemented the already approved UI-043 scope in isolated `candidate/p09-ui043-api-diagnostics-cleanup` from canonical main `66461bfae7f3db36127141c62ffbc732360deb53`. Draft [PR #89](https://github.com/ALL-EX-E/InOneLine/pull/89), exact code/test head `36a31040d3c8e0656265a5e4a4c865a11a74c87a`.
- Removed the obsolete lower `Локальный API` block, `Проверить API` / `Открыть JSON OBS` buttons and `OBS JSON` / `Публичный JSON` URL rows. Top server status, seven OBS URL/copy/preview sections, existing specialized/shared Saves and real Tab order preserved. Existing main-overlay callbacks now constructed directly in their accepted top section; dead `_open_obs_json` handler and diagnostic counter removed after caller audit.
- Exactly two source/test blobs, independently identical locally and on GitHub: `streaming_manager/views/stream.py` = `66ef1428bab8a547b05655d5b8b800d6bf7cd5dd`; `tools/gui_regression_smoke.py` = `0aa8b98217f21d079b56053000ebe45b9a93dcd7`. AST: constructor/refresh changed, obsolete JSON method deleted; 54 other StreamTab methods identical. API server, browser templates, MainWindow, database, settings keys, schema and media logic unchanged.
- Real Qt/SQLite TDD: new contract fails on exact accepted base (old Local API heading), then PASS. Real HTTP /health, /api/health, /api/data, /api/public retain contracts; both main/list Browser Sources still consume /api/data. UI-042 seven copy/preview pairs, native Tab, four specialized Saves and UI-041 List behavior PASS. P08 dedup/missing/restored media PASS with ordinary tab-return availability; full refresh retains existing missing saved-selection cleanup. Visual/geometry at 520/1100/2560/repeated520: 14 actions accessible, no horizontal overflow or leftover service-block gap. Compileall/diff checks and exact pinned dependencies PASS.
- Independent read-only Superpowers reviewer on exact head: no Critical/Important/Minor findings. Independently checked real endpoints, UI-043/UI-042/UI-041/P08, full fixture settings/page/focus/clipboard restoration, missing/restored media, unchanged unsaved text and persisted settings on ordinary tab return, HTTP no-store, width geometry, AST54 and compile/diff checks. Local Linux full GUI reaches the known accepted P06 compact-tab font-metrics baseline after all P09 checks PASS; the native Windows full gate is canonical.
- Full native Windows [Regression Foundation 38050184969](https://github.com/ALL-EX-E/InOneLine/actions/runs/38050184969) **SUCCESS**, exact head `36a31040d3c8e0656265a5e4a4c865a11a74c87a`: compile, DB/backup/legacy/media/source/integrity, full GUI including `P09_UI043_DIAGNOSTIC_UI_REMOVED_AND_LIVE_API_RETAINED=PASS`, `P09_UI043_BACKGROUND_AVAILABILITY_ON_TAB_RETURN=PASS`, prior P09/P08, frozen startup/browser source, installer build, silent installed startup and clean filesystem all PASS. Wording PR `38050184948` and push `38050183666`: SUCCESS.
- Manual QA archive: `InOneLine_P09_UI043_API_UI_CLEANUP_CANDIDATE_1.0.8_WINDOWS_QA.zip`, [Google Drive](https://drive.google.com/file/d/1O8Y1d6Lc55vbdNlnhbdJBy7DC4me6QFa/view?usp=drivesdk), folder `Обзор_UI_1.0.8`. GitHub artifact `11668633936`; **46,798,871 bytes**, SHA-256 **`9e1fbada3371fe712775eac25f45e1eee32770d5da1aa159b1d7100f5a92dad6`**. Downloaded bytes independently match GitHub size/digest; ZIP CRC PASS; exactly one `InOneLine_Setup_1.0.8.exe`. Drive readback confirms name, identical size and expected QA folder. This exact ZIP is the user manual-test package.
- **UI-043 AWAITING USER MANUAL QA / NOT MERGED; P09 IN PROGRESS.** Main runtime remains accepted UI-042. After UI-043 acceptance, exact clean promotion and postmerge PASS close P09; next package **P10** starts with **GLOBAL-OBS-VISIBILITY-001**, then approved timer/music presentation. UI-044 is superseded by UI-090 and must not be implemented as written. App 1.0.8 / schema19 / 15 migrations; official release and rollback unchanged.

Полный ручной checklist UI-043 (весь список проверяется одной сборкой):
1. Закрыть In one line, распаковать QA ZIP и установить InOneLine_Setup_1.0.8.exe; открыть программу и проверить сохранение данных/настроек.
2. В Стрим / OBS сверху остаётся Состояние: РАБОТАЕТ. Нижнего Локальный API, кнопок Проверить API/Открыть JSON OBS и строк OBS JSON/Публичный JSON больше нет; после Информационного блока идут настройки таймера без пустого служебного блока.
3. Проверить Копировать URL и Открыть предпросмотр всех семи разделов: главный оверлей, отдельный список, таймер, плеер, колесо, список лотов, правила. Адреса имеют фактический порт; встроенный список можно выключить — доступ отдельного списка остаётся.
4. Проверить обычное сохранение главного оверлея и специализированные Сохранить таймера/плеера/списка лотов/правил; изменения видны в предпросмотрах и сохраняются после перезапуска.
5. Для медиа-фона главного оверлея или списка лотов проверить режим Использовать исходный файл: временно переместить выбранный файл, уйти на другую вкладку и вернуться в Стрим / OBS — недоступный файл не предлагается как доступный фон, предпросмотр продолжает работать. Вернуть файл на прежнее место, обновить F5 — фон снова доступен для выбора.
6. Сузить окно до минимального размера, расширить и снова сузить. URL, copy/preview и Сохранить доступны через прокрутку; Tab по-прежнему проходит Копировать URL → предпросмотр → настройки раздела. После перезапуска статус сервера и все OBS-входы работают.
