# InOneLine Roadmap

Обновлено: **2026-10-07**

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
- **P03 implementation and manual acceptance are complete; technical closure is pending.**
- P03-A / UI-021 complete on `candidate/p03-csv-date-caret`: canonical CSV headers `НАЗВАНИЕ` + `ДАТА` are accepted while legacy `НАЗВАНИЕ ИГРЫ` + `ДАТА ВЫХОДА` remain aliases. Implementation `d6b8b30a1336f5b7864b1ca3f19c41c4473815f2`; regression `2ac0f44deaa3f6234af194d88b755e36fc729c72`.
- P03-B / UI-020 complete: CSV help rewritten to the accepted neutral/canonical wording while explicitly preserving legacy aliases and `ИГРАЛ / НЕ ИГРАЛ` status labels. Implementation `a70f00688650638ff2173ba942b418db26ba8201`; GUI regression `ec74bed827edaa675f6360dd703326e442f38ee9`.
- P03-C / UI-019 complete: CSV error messages now state the problem, source row/value and correction guidance; TEST-001 error scenarios + atomicity + backup-path preservation are automated in the existing GUI smoke. Implementation `0f7f8b24b3b702607b9c1ef4b167745f714230c7`; regression `2230c10a06a986389bff3ab546afbe011368730c` + `e7a32323fbe3f951f966b8a2d538961ed34f6fa6`.
- P03-D / BUG-002 complete: existing date auto-format now preserves logical caret position instead of jumping to the end. Implementation `7872121a09c740e99073053d9b1ee9e776296202`; regression `2fd76ae1260738fdf289b36de084ac2b15234e19` covers Add/Edit, Backspace, Delete, selection replacement and sequential input.
- P03 clean review branch `candidate/p03-review`, head `9fb64bc0d0867f439b0866f82826b406c22ef012`, draft PR #25; exactly 3 changed files.
- Candidate-wide Windows regression `37633288322` — **SUCCESS**, including Native GUI P03 checks, frozen build/startup, Browser Source, installer and silent-install gates.
- Manual-QA ZIP uploaded to Drive: `InOneLine_P03_CANDIDATE_1.0.8_WINDOWS_QA.zip`, ID `1Fpk09-w7nq22ao8qdgDMLyJBSJIwD9tu`; installer SHA-256 `5f82f276e36ab316b2f2bc9f130036791e2b3f0c7de2d9c7d067690e9a57086d`.
- **P03 automated gate PASS; complete user manual QA PASS / ACCEPTED («Работает. Идём дальше.»).** Merge and post-merge regression remain the gate before P04.
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
7. **P06** — window sizing/state/tab-order migration + full backup ui_state.
8. **P07** — one position policy + XLSX derived position.
9. **P08** — shared media dedup/availability foundation.
10. **P09** — Stream/OBS structural cleanup and API-control removal.
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

- P03: user accepted the complete checklist. Finish merge and post-merge regression before starting P04.
- P04: first remove obsolete list hide/show state/hooks and fallback automatic selection, then implement the accepted search/Enter/deselect contract and total-points snapshot reuse. Keep individual implementation steps small.
- Manual checks for each current candidate package are delivered together as one complete checklist.
