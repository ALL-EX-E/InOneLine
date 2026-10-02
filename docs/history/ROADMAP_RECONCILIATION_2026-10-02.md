# Roadmap Reconciliation — 2026-10-02

## Scope

Повторно сверены:
- доступная история рабочих чатов «Программа для стрима» 1–31 и зафиксированные прямые пользовательские решения;
- Google Drive: cumulative current/history/order files, PASS 1–13 reconciliation archives, historical reference-review records и roadmap addenda 2026-09-28–2026-09-30;
- GitHub: current docs, Issues, release notes 1.0.0–1.0.8, current runtime/source and maintenance audit records.

Цель: найти потерянные идеи, неверные статусы, сломанный dependency-order и stale-задачи, которые уже реализованы/отклонены.

## Authority rule

При конфликте используется порядок:
1. более позднее прямое решение пользователя;
2. принятая/released реализация и exact current runtime;
3. поздний canonical reconciliation/status record;
4. более ранние assistant-authored planning/order documents;
5. промежуточные candidate/reference notes.

Само наличие пункта в старом cumulative-файле не делает его текущей задачей.

## Main finding — GitHub roadmap drift

После миграции source-of-truth в GitHub короткий `docs/ROADMAP.md` сохранил только:
- Global Multi-File Import / #4;
- D22 Battle Royale / #5.

Это потеряло часть ранее сохранённого backlog и создало ложное впечатление, что D22 автоматически следует сразу после post-D26 patch.

Отдельно зафиксировано: GitHub Issues не являются исчерпывающим backlog; отсутствие Issue не означает удаление идеи из canonical `docs/ROADMAP.md`.

Drift исправлен 2026-10-02.

## Restored retained dependency/complexity chain

После уже released D26 сохранённая поздняя dependency/complexity chain включает:
- D40 — manual soundtrack/music library order;
- D34 — Tourniquet adapter;
- D41 — cross-platform chat aggregation + standalone OBS chat overlay;
- older YouTube platform/integration candidate;
- D38 — optional LAN access to standalone OBS widgets;
- Public Web / ordinary site presentation;
- D27 — physics/final-stop «Честное колесо»;
- D7 — whole-snapshot cryptographic verification hardening.

Это planning order, а не pre-authorization. Перед каждым пунктом нужен fresh exact-CURRENT review и отдельный user approval.

## Restored parked/approved items

Сохранены и не потеряны:
- D23 — import custom participants;
- D24 — standalone OBS wheel-participant list;
- D25 — cumulative probability <= winner amount; approved post-completion, explicitly «не нужно сейчас»;
- D42 — current lot/sector under arrow during spin.

Также сохранены deferred:
- W1 Space -> existing Spin;
- Saved Auctions + dependent full New Auction workflow;
- A8 compensating Undo;
- B6 Pointauc API adapter contract;
- provider adapters iHAQ Donate v2.0, ODA/OpenDonationAssistant, DonateX, VK Video Live, Kick, Donate Helper, DonatePay;
- Twitch Channel Points/Custom Rewards live verification when eligibility allows.

## Later user decisions that supersede older PASS13 wording

Do NOT restore these old statuses blindly:
- D16 — explicitly deferred;
- D17 — explicitly skipped for now;
- D18 — explicitly skipped for now;
- D20 — explicitly deferred;
- D22 — explicitly deferred on 2026-09-29; Issue #5 remains deferred and is NOT the automatic next item.
- Games/List shared persisted Autoscroll — no longer a live task: on 2026-09-28 the user decided not to add it because required autoscroll behavior already exists.
- Games/List Compact presentation — postponed until a real future need appears.

## Provenance corrections retained

- D15 Twitch AI-bot/neural network is NOT a confirmed InOneLine roadmap item.
- D39 per-scene widget style profiles is assistant-originated historical possibility / NOT ACTIONABLE unless explicitly reopened.
- Historical W3 YouTube URL/video-ID soundtrack source is reference-only, not a direct-user-approved roadmap scope.
- Historical «Трейлер (YouTube)» is resolved/closed.
- D4 separate Wheel page, D6 generic Widgets umbrella, D8 video requests and D14 historical umbrella are rejected/superseded.
- F-series rejected/superseded entries are not backlog.
- H-series are existing behavior to preserve, not new work.

## Items confirmed closed rather than forgotten

- QA-1.0.2-01 unified OBS onboarding/help — closed in 1.0.2.
- QA-1.0.2-02 external donation auto-extension completion — closed in 1.0.3.
- D19 — released 1.0.4.
- D43 — released 1.0.5.
- D21 — released 1.0.6.
- D26 — released 1.0.7.
- Global Conditional UI Visibility / #3 — released 1.0.8.
- Old deferred stale OBS page reload/version handshake — current runtime already has the version/cache-busting overlay handshake.
- Old wheel-overlay infinite RAF concern — current wheel overlay stops RAF when wheel animation is not active.
- Old source/release filesystem hygiene items — handled by the 2026-10-01/02 maintenance audit.

## Review-later inventory retained

Not approved for automatic implementation:
- D1 double timer/count-up;
- D2 pin/unpin lot;
- D3 universal inline editing;
- D5 advanced auction analytics;
- D9 localization;
- D10 GitHub link (public-repo prerequisite now exists);
- D11 Telegram link;
- D12 support/Boosty link;
- D13 Pending/manual-processing queue;
- D28 artificial/fixed probability;
- D29 viewer names in viewer-facing table;
- D30 blind/hidden viewer amounts;
- D31 auto-processing selector dependent on D13;
- D32 viewer-name order text in separate participant mode;
- D33 alternative display sorts;
- D35 per-bet fortune multiplier;
- D36 viewer chooses lot dependent on D35;
- D37 presets export/import;
- Auction Lots Normal/Compact remains only specification-reconciliation territory.

## Current selection state

No product scope is selected automatically by this audit.

- Global Multi-File Import / #4 remains the current post-D26 eligible candidate for fresh review.
- D22 / #5 remains deferred.
- All other retained ideas keep the statuses in `docs/ROADMAP.md`.

## Exhaustive-orphan result

After comparing old cumulative inventories, PASS13, later chat decisions, release notes, current code and Issues:
- no D44 was found;
- no additional durable unnumbered user idea was found that is both unimplemented and absent from the reconciled roadmap;
- no currently closed/rejected item needs to be reopened.

If a future chat surfaces an older idea not listed in the reconciled roadmap, it must be provenance-checked against later direct user decisions before promotion.

## Files updated

- `docs/ROADMAP.md` — full survivable inventory + current statuses.
- `docs/PROJECT_STATE.md` — current queue summary points to reconciled roadmap.
- `docs/DECISIONS.md` — durable reconciliation/status rules.
- `docs/README.md` — this reconciliation added to the canonical reading path.


## Second exhaustive idea-inventory pass — 2026-10-02

После первого roadmap reconciliation выполнен отдельный полный проход уже не по «следующей очереди», а по всем пользовательским идеям.

Дополнительно сверены direct-chat decisions, full-history dedup audit и dedicated Wheel / History / Settings & Integrations / Widgets / Winner Verification reviews.

Recovered/corrected:
- создан canonical full inventory `docs/IDEA_INVENTORY.md`;
- на этом проходе были разведены Product A1–A8/A6.1 и Maintenance A1–A10; более глубокий хронологический pass позже восстановил **третий** namespace — August Stabilization A1–A12/A7.1/A11.1;
- advanced completed-auction History analytics восстановлена как **USER-ACCEPTED POST-COMPLETION / POST-INTEGRATION**, а не assistant-only review-later: heatmap, weekdays, participant rankings, points/donations analytics, record cards, «Самый дорогой победивший лот»;
- D9–D12 получили обратно direct-user provenance/conditionality;
- full external `.iolbackup` и расширенные Saved Auctions details восстановлены в полном inventory;
- historical aliases уточнены позже: **R1 = Rules editor/templates/session snapshot**, **R2 = standalone OBS Rules**, **I1 = DonationAlerts**;
- Wheel Point 13 перепроверен: отдельного нового result-panel backlog нет; existing confirmation + W4 + D25 + explicit reroll/delete rejections полностью покрывают решение;
- backup-retention last-N/N-days не восстановлен как user idea: evidence показывает assistant-originated maintenance suggestion, а не отдельное user-approved roadmap item.

Mechanical completeness:
- D1–D43: **43/43 present**;
- Product A1–A8 + A6.1: complete;
- S1–S3, W1–W4, B1–B6, E1–E4: complete;
- P1, C2, R1, R2, I1 and post-1.0 scopes are mapped.

Final orphan-only result:
- no D44;
- no additional durable user-proposed product idea found outside `docs/IDEA_INVENTORY.md`;
- no rejected/superseded/historical assistant idea needs revival.

Google Drive backup mirror: `USER_IDEA_INVENTORY_2026-10-02` in «Текстовый лог».


## Third independent comparison pass — 2026-10-02

This pass compared the new full inventory itself against:
- earlier chat decisions recovered from account history;
- the cumulative Drive project history;
- the dedicated Wheel, History, Settings/Integrations, Widgets and Winner Verification reviews;
- current GitHub source where a historical status could be checked against runtime behavior.

Newly recovered/corrected relative to the second-pass inventory:
- DonationAlerts/I1 entry was stale: the old auction-only enable/target model was superseded. Current accepted behavior is permanent contribution intake while connected, with source-time routing to a running auction or persistent game list outside auctions.
- Integration UX retains the user preference for provider-native one-click/browser/device authorization without manual client-secret management where technically possible.
- Cross-surface auction/game synchronization was promoted into the full inventory as a durable accepted invariant: DB -> Games/Public/Auction/Journal + applicable OBS/API without manual F5.
- Default wheel RNG-first/animation-hidden-until-finish/restart-persistence behavior was added explicitly to distinguish existing H4 behavior from future D27.
- The explicit rejection of a second fully-transparent whole-overlay mode was added; only game/webcam interior cutouts are transparent in the accepted main OBS layout.
- Direct W2/W3 UI decisions were added: «Добавить фон…», missing-external repair visibility, separated wheel-music controls and audio-failure isolation from RNG/winner lifecycle.
- The early public-GitHub-without-source publication plan was marked superseded by later SOURCE+INSTALLER publication.

Cross-check result of all five dedicated reference reviews:
- every accepted/deferred/rejected item maps to an existing entry in docs/IDEA_INVENTORY.md;
- no additional future feature identifier or durable orphan scope was found;
- no D44 was found;
- ROADMAP current future ordering does not change as a result of this pass.

The third pass therefore changed historical precision/current invariants, but did not add a new implementation candidate.


## Final orphan search after third-pass corrections — 2026-10-02

Additional recovered direct-user items after comparing chat history against the already-expanded IDEA_INVENTORY:
- `Игры -> Очистить все игры` — implemented/accepted; blocked while an auction is open, destructive typed confirmation, automatic backup, completed History and Journal preserved.
- `Журнал` search — implemented/accepted; a real query searches the complete journal and can match visible and raw event fields, not only the normal recent-row window.
- `Настройки -> Восстановить из резервной копии...` — implemented/accepted; selected DB is validated and current state is safety-backed up before restore.
- S1 integer conversion rule — implemented/accepted; positive fractional conversion results round upward for currencies and service units; no reverse SM-points-to-money product output.

A final account-history orphan search performed after these additions returned no further direct user-proposed product item. It surfaced only:
- the previously known outside-auction contribution rule, now covered by the corrected permanent-source integration entries;
- an old assistant-proposed backup-retention idea (`last N` / `N days`) with no recovered direct user proposal/acceptance, so it remains intentionally outside the user-idea inventory.

Final result of this pass:
- no new future implementation candidate;
- no D44;
- ROADMAP ordering unchanged;
- IDEA_INVENTORY historical/implemented coverage expanded and corrected.


## Deep chronological comparison pass — 2026-10-02

После уже расширенного IDEA_INVENTORY выполнена ещё одна независимая проверка снизу вверх по временной шкале: legacy changelog 0.2.x, ранние Project State 0.3.05–0.3.16, cumulative history, pre-1.0 R1.0.x release stages и direct conversation search.

Новая дельта относительно предыдущего полного inventory:

### Recovered historical namespaces / accepted engineering work
- найден отдельный **August Stabilization A1–A12** namespace (включая A7.1 и A11.1), не совпадающий ни с Product A, ни с October Maintenance A;
- восстановлен granular 0.2.0–0.3.02 implementation ledger: Games/Public UX, OBS layout/list refinements, Auction operator UX, timer point 9, performance/safety hardening и destructive safety flows;
- восстановлены user-approved **FINAL MAIN STABILIZATION 0.3.83**, **Optimization & Deep Audit 0.3.84**, **Optimization & Reliability Audit II 0.3.89** и release-clean QA separation;
- восстановлен E1 follow-up 0.3.91: убрать native up/down arrows из Games `Баллы` при сохранении numeric entry/wheel protection;
- восстановлен R1.0.x release-stage ledger: install-root architecture, full backup, installer/icon, final uninstall, update/reinstall, no-dev-stack gate, global geometry, minimum-window scrolling, Export reorganization и cold-start field-height correction.

### Corrected aliases / provenance
- старое свёртывание `R2 / Rules package` оказалось неверным: R1 и R2 — разные принятые этапы;
- отдельный live-only `Изменить текущие правила` workflow был отвергнут; финал — один обычный editor до/во время/после аукциона;
- old assistant proposal for a local InOneLine write API (`POST /api/v1/bids` / generic `PUT /lot`) не имел direct user approval. Direct approval относится к dedicated B6 provider adapter через официальный API провайдера.

### Recovered direct UX detail
- Auction subtabs retain per-tab `Правила вкладки / Скрыть правила`;
- manual bidding belongs on Conducting; Conduct list/search/autoscroll interaction and cross-surface DB synchronization restored in historical ledger;
- no automatic focus transfer into Auction search;
- tie UX uses `Несколько победителей` with additional-time or wheel path;
- Saved Auction ordinary Save updates linked configuration; explicit Save-As-like path creates a copy;
- New Auction resets only working-session runtime, not Games/Journal/History/Rules/Integrations/OBS settings;
- A6.1 live chance is authoritative weighted-wheel current-state information and separate from W4 frozen result chance;
- B1/B2 adapter/card/disconnect/history/status details and provider-neutral outside-auction contribution rule recovered;
- D19 quick picker direct-user contract restored: unified grid, no search/source filters, animated media animates before selection;
- W2 contextual add vs missing-reference repair action restored.

### Final result of this pass
- these findings expand **historical/implemented precision** only;
- no new future implementation candidate was discovered;
- D44 still does not exist;
- current ROADMAP selection/order remains unchanged;
- `docs/IDEA_INVENTORY.md` is now the exhaustive historical ledger, while `docs/ROADMAP.md` remains the short future-selection view.

## Fourth independent cross-source pass — 2026-10-02

После финального deep chronological pass выполнена ещё одна проверка уже против обновлённых `IDEA_INVENTORY.md` / `ROADMAP.md` / `DECISIONS.md`, direct conversation history, старых Drive master/order/audit records и exact current 1.0.8 source.

### Newly recovered accepted detail
- Старый user-accepted B1 contract для compact `Аукцион → Проведение` integration status включал **время последнего принятого integration event** наряду с configured/used-only services, persistent error visibility и переходом в Settings.
- Current 1.0.8 всё ещё сохраняет `integration_connections.last_event_at`; Settings показывает `Последняя принятая активность`; Conduct integration status/dialog не показывает это время.
- Более позднего direct-user решения убрать этот элемент из Conduct не найдено.
- Классификация: **QA-1.0.8-01 / ACCEPTED-REQUIREMENT OMISSION / DOCUMENTED / NOT FIXED / NOT AUTO-AUTHORIZED**.
- Это не новый D-item и не новая feature idea; retained future dependency order не меняется.

### B1/B2 detail-preservation correction
Предыдущий reconciliation утверждал, что B1/B2 detail contracts восстановлены, но exhaustive inventory снова слишком сильно сжал их. В `IDEA_INVENTORY.md` теперь явно закреплены:
- compact Conduct configured/used-only service status, persistent error visibility, Settings navigation и accepted last-event time;
- Disconnect != Remove, confirmation + history preservation;
- provider capabilities / non-blocking network rule;
- B2 Twitch Public Device Code/no-Client-Secret lifecycle, protected credentials, validation/refresh/error states и Connect/Reconnect/Disconnect/Remove semantics.

### Rejected false positives in this pass
- **SUPERSEDED BY SEVENTH PASS:** the earlier fourth-pass conclusion was wrong. Direct chat evidence confirms user approval on 2026-09-02 for outside-auction unknown-title handling: create a normal persistent game and credit it, without creating/starting/resuming auction/`auction_only`/timer/wheel state. Current 1.0.8 already implements this.
- **SUPERSEDED BY SEVENTH PASS:** direct chat evidence confirms user acceptance on 2026-08-28 through the DonateX review. Provider-marked `test/sandbox/demo` events must never mutate real points/auction/timer/wheel/winner state; diagnostics/history-only storage is allowed.
- W2 separate managed-media folders are not missing: the final inventory already records the per-purpose managed-folder rule and current runtime preserves the active categories.

### Result before the next requested full recheck
- one accepted-requirement QA omission recovered: **QA-1.0.8-01**;
- no D44;
- no newly approved future feature identifier;
- ROADMAP future dependency order unchanged;
- runtime/source/version/schema/migrations unchanged by this documentation pass.

## Fifth full recheck — chats + Drive + GitHub — 2026-10-02

Выполнен ещё один независимый проход по доступной истории чатов, старым Drive Project State/Master/Implementation Order и dedicated History/Widgets/Settings/Winner Verification reviews, текущему GitHub main/source, Issues, branches и PR history. Результаты сверены против уже обновлённых canonical docs.

### Additional documentation deltas recovered
- Future wheel entries **D16–D24 и D27** присутствовали в inventory по идентификаторам, но часть принятых design constraints была слишком сильно сжата. Exact retained constraints восстановлены в `IDEA_INVENTORY.md`: local-only/no-RNG hover; random-duration animation-only semantics; presentation-only wheel themes; logical-vs-visual D20 fragments; D22 temporary tournament weights; D23 import formats/destinations/preview/merge rules; D24 independent viewer list semantics; D27 physics-mode review boundary.
- Старый accepted Timer/Auction Music playlist contract был найден в Widgets review, но current release evidence показал более позднюю supersession: **D26 / 1.0.7** заменил current Auction soundtrack behavior на один выбранный зацикленный файл из shared `data\soundtrack`; старый playlist/checkbox больше не используется. Inventory/Decisions/Roadmap исправлены так, чтобы D40 не мог ошибочно восстановить superseded pre-D26 playlist автоматически.
- Provider target precision восстановлена из Settings review: retained future targets — **Kick Channel Points / Custom Rewards** и **VK Video Live rewards/points**, оба feasibility-conditional; generic provider-name compression была недостаточно точной.
- GitHub repository hygiene: открыт stale PR **#9 `Make 1.0.8 regression foundation persistent`**. Его purpose уже superseded принятым merged PR #11 `Make 1.0.8 regression foundation permanent`. PR #9 не является скрытым feature scope и не меняет CURRENT; в ходе audit он не закрывался автоматически.

### Mechanical cross-check
- Старый `APPROVED_FUTURE_IMPLEMENTATION_ORDER_CURRENT`: все обнаруженные буквенно-цифровые identifiers имеют mapping в current `IDEA_INVENTORY.md`; unmapped future identifier line = 0.
- D1–D43 остаются учтены; D44 не найден.
- Open Issues: только #4 Global Multi-File Import и #5 D22 Battle Royale; Issues по-прежнему не являются полным backlog.
- PR history: #1/#2/#6/#7/#8/#11–#18 merged/closed, #10 closed/unmerged, #9 stale/open as noted above.
- Historical candidate/maintenance branches не дали нового hidden product scope; их apparent divergence в основном объясняется squash merges и дальнейшим развитием main.
- Source TODO/FIXME/future scan не обнаружил отдельной незаписанной product feature.
- Public development-reference wording was rechecked; provider names are retained only where genuinely necessary to identify an actual provider/integration/API, not as disclosed development-reference provenance.

### Result
- Новая runtime accepted-requirement omission этого full pass остаётся одна: **QA-1.0.8-01**.
- Остальные новые находки этого прохода — documentation precision/supersession/repository-hygiene corrections.
- Нового durable user-approved future implementation identifier не найдено.
- Retained future dependency order не изменён.
- Runtime/source/version/schema/migrations не менялись: **1.0.8 / 19 / 15**.

## Sixth orphan-only control after all corrections — 2026-10-02

После fifth full recheck выполнены дополнительные direct-conversation orphan searches уже с исключением всего занесённого в обновлённый inventory.

Recovered documentation precision before the final zero-delta result:
- direct OBS layout detail: current-game title centered above game frame; disabling the lower-right info block reuses/frees that area for list layout;
- 19 August Auction UX details expanded: search label `Поиск`, no automatic search focus on subtab switch, no preset dropdowns for OBS information-block text, tie label `Несколько победителей` with additional-time or wheel paths, equal-chance tie wheel including all-zero fallback;
- Product A2 numeric new-lot field and shared manual points/bid field preserve the no-native-spin-arrows decision;
- Product A2 explanatory temporary-lot rule preserved with later corrected semantics: current-auction-only while open; completion/cancel promotes to Games; confirmed winner -> `ПРОХОДИТСЯ`, otherwise `НЕ ИГРАЛ`;
- D9 future localization boundary restored: centralized UI/program-string localization only; user data, game titles and historical content are not automatically translated.

Final orphan-only search after these additions returned no additional direct user-approved product/UX/future requirement. Returned items were already mapped decisions, historical test facts or previously rejected/superseded/assistant-only material.

**Final result of this control pass: ZERO NEW PRODUCT/FUTURE DELTA after documentation corrections.**

## Seventh full recheck — same scenario repeated — 2026-10-02

Повторный проход выполнен тем же сценарием: direct chat history -> Drive canonical/history/dedicated review files -> GitHub main/source/issues/PRs -> comparison against already corrected `IDEA_INVENTORY.md`, `ROADMAP.md`, `DECISIONS.md`, `PROJECT_STATE.md` and this reconciliation log.

### Newly recovered / corrected relative to the sixth pass

1. **B3 provenance correction — previous false-positive rejection was wrong.**
   - Direct chat evidence confirms user approval on 2026-09-02.
   - Outside an auction, a valid event with a usable unknown game title creates a **normal persistent game** and credits it.
   - It must not create/start/resume an auction, `auction_only`, auction entry, timer or wheel state.
   - Unknown conversion rate remains Pending and must not pre-create the game before credit can actually be applied.
   - Current 1.0.8 source already implements this behavior, so this is a documentation/provenance correction rather than a runtime defect.

2. **Generic B2 test-event safety — previous assistant-only classification was wrong.**
   - Direct chat evidence confirms the user accepted DonateX on 2026-08-28 with the proposed `isTest=true` rule; the rule was then generalized to B2.
   - Provider-marked test/sandbox/demo events must never credit real points, create/increment game/lot, change leader, trigger timer auto-extension or affect wheel/winner logic.
   - They may only be preserved in technical integration diagnostics/history marked as test.
   - Current 1.0.8 normalized-event core has no explicit test-event field/gate.
   - Classification added: **QA-1.0.8-02 / ACCEPTED SAFETY CONTRACT GAP / NOT FIXED / PROVIDER-CAPABILITY-DEPENDENT / NOT AUTO-AUTHORIZED**.
   - No current supported-provider reproduction was established during this audit.

3. **Deferred provider contracts were too compressed.**
   - Restored common B2/B3 contract: source+external-event-ID dedup; common source-unit conversion; message/order text as ordinary lot/game text; sender identity separate; immutable original source data + applied conversion rate + credited points; common timer path; official/reliable programmatic APIs only; no page/OBS/browser scraping.
   - iHAQ and Donate Helper remain feasibility-gated.
   - DonatePay realtime path requires exact endpoint/auth/channel/payload/currency/event-ID revalidation.
   - DonateX official API path was previously confirmed, but live-delivery contract must be revalidated and provider test flags must obey the common safety rule.

4. **Historical E1 exact build-gate detail was missing from the exhaustive inventory.**
   - User required the exact native build run to visibly reach `[9/9] BUILD EXE: OK`.
   - An auto-closing console was not accepted; rerun from CMD/PowerShell with the console left open/full output visible was required.
   - Exact binary/manual EXE QA and explicit user acceptance remained separate gates.

5. **Public GitHub reference-wording cleanup found a real documentation-policy drift.**
   - Direct user rule from 2026-09-28: do not disclose development-reference provenance in published GitHub files; provider/reference names may remain only where genuinely necessary as the name of the actual provider/integration/API.
   - Current public docs still contained historical reference/tab/export wording that was not necessary.
   - Those historical disclosures were neutralized in canonical docs.
   - Necessary B6 provider naming remains only where the actual B6 integration itself must be identified.

### GitHub/source check

- Current source confirms B3 unknown-title outside-auction auto-create behavior through the common normalized event transaction.
- Current source does **not** expose a generic normalized `is_test`/test-event gate.
- No additional new product identifier was found.
- Runtime/source/version/schema/migrations were not changed by this pass: **1.0.8 / 19 / 15**.

### Result after seventh pass

This pass was **NOT ZERO-DELTA**. It found:
- one new accepted safety-contract gap: **QA-1.0.8-02**;
- one previously misclassified but already implemented B3 requirement;
- several lost provider-contract details;
- one missing historical E1 acceptance detail;
- one public-documentation wording-policy drift.

A new control pass is required after these corrections before a clean stop result can be claimed.

## Eighth control pass — B3 binding + Rules UX — 2026-10-02

After seventh-pass corrections, another direct-chat control search recovered two additional durable details:

1. **B3 `Требует привязки` is a real accepted workflow, not just wording.**
   - User acceptance on 2026-09-02 explicitly covered: usable unknown title during running auction -> temporary `auction_only`; usable unknown title outside auction -> normal persistent game; missing/unusable title -> separate `Требует привязки` state.
   - `Требует привязки` means: no automatic create/credit; event waits for manual operator binding to a game/lot.
   - It is distinct from `pending_conversions`, which handles unknown conversion rate/unit.
   - Current 1.0.8 implements both usable-title paths, but `missing_target` is marked `inapplicable` and there is no manual bind path.
   - Added **QA-1.0.8-03 / ACCEPTED B3 WORKFLOW OMISSION / NOT FIXED / NOT AUTO-AUTHORIZED**.

2. **Rules standalone viewer exact numeric-control UX was missing from the exhaustive inventory.**
   - `Непрозрачность` and `Внутренний отступ` use wide external ▲/▼ buttons, manual numeric entry and hold/repeat.
   - Mouse-wheel scrolling must not silently change those values.
   - Current source already uses the shared wide-step/scroll-safe controls, so this is documentation precision, not a runtime defect.

Also restored the exact accepted DonationAlerts built-in public OAuth Client ID **20915**.

Runtime/source/version/schema/migrations remain unchanged: **1.0.8 / 19 / 15**.

## Ninth precision pass — dedicated Drive reviews + retained future contracts — 2026-10-02

After the eighth B3-binding correction, the dedicated Drive review archive (Wheel, Widgets, Settings, Winner Verification, History and the full dedup audit) was compared line-by-line against the updated exhaustive inventory.

No new identifier was recovered, but several **directly accepted constraints had been compressed too aggressively** and are now restored:

- **R1 Rules editor**: simple `Обычный текст / Заголовок / Подзаголовок` presets; selected-fragment formatting; quick + arbitrary colors; create-template confirm/cancel; normalized name validation/duplicate guard; active-template marking; direct edit mode; Save persists+closes; unsaved protection on switch/close/delete; content/style separated from viewer geometry.
- **B1 Integration Center**: purpose-grouped catalog, one specialized adapter/card per service, moderate branding, capability-driven controls, multiple active integrations, manual connection/auth test off GUI thread, adapter-specific automatic health tracking.
- **Winner Verification / D7 security boundary**: immutable per-run participant/weight/range/RNG/random/winner/timestamp/algorithm snapshot; read-only deterministic replay; optional pre-spin data view; Random.org+ ticket/signature reuse; same-database SHA-256 alone is not meaningful intentional-tamper protection; signing/key management/notarization/off-app verification remains post-completion.
- **D28–D36**: artificial-chance, viewer-name, blind-amount, D13 auto-processing selector, participant-mode naming, display-only sorting, per-bet fortune and dependent viewer-choice constraints restored exactly.
- **B4 Twitch rewards**: manage only app-created/registered auction rewards; preserve reward IDs; common title + cost/color; viewer text; common B2/B3/S1 path; bid-intake availability coupling; unlink != destructive reward delete; explicit delete confirmation; eligibility-safe failure.
- **S3 eyedropper**: multi-monitor/mixed-DPI center-pixel reticle, cancel/no-change and shared color-storage rule restored.
- **D34 / D37 / D38 / D42**: reliability/security/API gate, preset schema/security boundary, localhost/LAN security boundary, and actual-visual-sector-under-pointer/no-RNG-change contract restored.
- **D25**: future cumulative-probability metric must be computed from the immutable completed ordinary-weighted-wheel snapshot and must not be automatically inserted into core viewer/result UI.
- **D41**: reuse B1/B2 auth/adapters; ordinary chat never mutates auction business state; exact cross-chat ordering/author/badges/emotes/moderation/history/style/OBS contract remains intentionally unapproved until fresh D41 review.
- **Widgets live apply**: authoritative viewer settings change only on Save/Apply; unsaved edits are not pushed; stable URL/no manual refresh; keep separate from E2.
- Exact accepted full-backup button wording and the canonical green icon decision were restored as historical implemented detail.

### Mechanical result
- All old implementation-order identifiers still map to current inventory.
- D1–D43 remain accounted for; the literal sentence `D44 не найден` is documentation only and **not** a D44 item.
- No future dependency order changed.
- Runtime/source/version/schema/migrations unchanged: **1.0.8 / 19 / 15**.

A final orphan-only direct-chat control is required after these precision restorations before declaring this repeated audit clean.

## Tenth orphan-only control after seventh–ninth corrections — CLEAN — 2026-10-02

A final direct-chat orphan-only search was run after all new findings from the repeated audit had already been written into canonical documentation.

The search explicitly excluded the now-recorded:
- QA-1.0.8-01 / QA-1.0.8-02 / QA-1.0.8-03;
- B1/B2/B3 exact contracts and provider details;
- Rules/Widgets/Winner Verification exact UX/security boundaries;
- D1–D43 including restored post-completion constraints;
- E1–E4 deployment/release details;
- publication/privacy/reference-naming/license/SmartScreen rules;
- backup/uninstall/icon rules;
- process/cadence and exact-tested-bytes release workflow.

Returned direct-user decisions were already present in the updated inventory, including:
- one-change -> version -> automated checks -> documentation -> Windows/manual verification -> explicit acceptance;
- C1 every 25 accepted CURRENT/released versions;
- localhost-only MAIN / LAN post-completion;
- saved-widget settings live-apply;
- rejected Video Requests and rejected separate top-level Wheel page.

No additional durable user-approved product requirement, future idea, rejection, UX rule, provider contract, deployment rule or process rule remained orphaned.

### CLEAN result

- **New delta after the corrections: 0.**
- D1–D43 accounted for; no actual D44 item.
- All old implementation-order identifiers map to current inventory.
- Current QA gaps explicitly tracked: **QA-1.0.8-01, QA-1.0.8-02, QA-1.0.8-03**.
- Future dependency order unchanged.
- Runtime/source/version/schema/migrations unchanged: **1.0.8 / 19 / 15**.
- GitHub remains source of truth; Drive mirror is resynchronized after this pass.

This clean result applies to the **post-correction control pass**. The repeated audit itself was not zero-delta: it recovered/corrected the findings recorded in the seventh, eighth and ninth passes above.

## Post-clean read-back documentation correction — 2026-10-02

The final read-back found one stale **summary paragraph only**: Section XX of `IDEA_INVENTORY.md` still described the earlier third-pass conclusion as if no later findings had occurred.

That conclusion was rewritten to reflect the authoritative repeated-audit result:
- the repeated audit itself was not zero-delta;
- QA-1.0.8-01/02/03 are explicitly tracked;
- seventh–ninth pass recovered details are acknowledged;
- the tenth **post-correction** orphan-only control remains CLEAN / zero additional delta.

This was a documentation-consistency correction only. It did not recover another product requirement, did not change the roadmap order, and did not modify runtime/source/version/schema/migrations.

## Eleventh full recheck — archive/provenance + QA-ID control — 2026-10-02

The same scenario was repeated again against the already corrected state: prior direct chats -> Drive current/archive/dedicated reviews -> GitHub current docs/source/issues/PR -> orphan-only comparison.

### New delta recovered

1. **Historical reference archive gap had fallen out of the current GitHub reconciliation.**
   - Earlier PASS 12 recorded that the original 2026-08-21 external-reference screenshot set was no longer present in accessible Drive.
   - Fresh Drive image search again returns no image with that original reference naming; only unrelated 2026-08-21 InOneLine screenshots and later text/review material remain.
   - The product decisions themselves remain supported by direct chat plus cumulative/dedup/dedicated review text.
   - Do **not** claim the missing original reference images are still archived, and do **not** reconstruct replacements and present them as originals.
   - Classification: **REFERENCE ARCHIVE GAP / HISTORICAL EVIDENCE LIMITATION / NOT PRODUCT BACKLOG**.

2. **QA finding identifier convention was missing from current workflow docs.**
   - Historical accepted process rule: release/reconciliation defects and accepted-scope omissions use `QA-<version>-NN`.
   - Permanent roadmap/product IDs (D/A/W/B/E/R and similar) are never recycled for temporary defects.
   - Current QA-1.0.8-01/02/03 remain correctly named under this rule.

### Cross-checks

- Old QA-1.0.2-01 and QA-1.0.2-02 are historical and already resolved by accepted later releases: common OBS help in 1.0.2 and external monetary/service-unit timer-extension completion in 1.0.3.
- D39 remains assistant-only/not actionable.
- Games/List autoscroll remains superseded by the later direct user decision that no new autoscroll work is needed.
- D10 remains conditional/eligible for fresh review only; no auto-selection.
- C1 counting is already resolved by the later direct user rule: only final accepted CURRENT/released versions count; rejected Candidate/FIX iterations do not.
- No source TODO/FIXME/future comment exposed a hidden product backlog item.
- Open GitHub tracking remains Issues #4/#5 plus stale PR #9; no hidden implementation scope was found.

### Status before next control

This eleventh pass was **NOT ZERO-DELTA**, but its new findings are documentation/process/archive facts only. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. Another post-correction orphan-only pass is required before declaring the recheck clean.

## Twelfth control pass — History/Wheel/Timer detail recovery — 2026-10-02

After the eleventh archive/QA-ID correction, the dedicated History, Winner Verification, Widgets and Wheel reviews were compared again against the current exhaustive inventory and direct-chat summaries.

### Additional accepted detail recovered

- **Standalone Timer viewer**: viewer output is timer value only. No viewer controls/labels are added. With no active auction it shows the configured initial/default duration for the next auction/current pre-start mode; during an auction it mirrors authoritative timer state. Current 1.0.8 current_timer_payload() already implements the idle/default-duration behavior, so this is documentation precision, not a runtime defect.
- **W1 Space hotkey**: if reopened later, Space must call the existing Spin action, must be ignored while the user is typing/using a control where Space has normal meaning, and must not cause a duplicate/re-entrant spin while spinning or otherwise unavailable.
- **W2 external media**: source-file references never permit InOneLine to modify/delete the original external file; missing/moved/disconnected media must fail safely and remain repairable; Browser Sources must not receive arbitrary filesystem access or raw absolute-path exposure.
- **Advanced History participant identity**: source/provider + stable external user ID is the minimum durable identity; nickname is mutable presentation metadata. Same visible nickname across providers is not enough to merge accounts.
- **Advanced History comparability**: unrelated point systems and currencies are not naively combined. Record cards and analytics must use authoritative historical snapshots and an explicitly defined comparable basis/base-currency rule where needed.
- **A8 Undo safety invariants**: deferred Undo remains append-only compensation, never destructive history rewrite; dependent later changes can make reversal unavailable; operator-only controls never appear in viewer OBS outputs. Exact reversible-action whitelist remains deliberately unapproved until fresh review.

### No new runtime defect from these details

Current runtime already satisfies the recovered Timer-viewer default-duration behavior and W2 protected external-media architecture. W1/A8/advanced History remain deferred/future scope and are not auto-authorized.

Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**.

Because this control pass recovered additional durable detail, it is **NOT CLEAN**. A further post-correction orphan-only pass is required.

## Thirteenth control pass — S2/widget/B6 boundary recovery — 2026-10-02

The next post-correction comparison against the dedicated Settings/Widgets/Winner reviews recovered additional accepted boundaries that were still too compressed in the exhaustive inventory.

### Recovered details

- **S2 collision/threshold semantics**:
  - new-lot auto-extension applies only to actual creation of a new lot, not increment of an existing match or manual correction;
  - external-event extension applies only after successful common-pipeline acceptance/dedup;
  - one originating action/event may extend the timer only once; if multiple enabled reasons match, apply the largest configured extension instead of summing;
  - equality at the threshold is eligible;
  - disabling the threshold allows enabled reasons throughout a running auction;
  - paused/non-running sessions do not auto-extend and an expired timer is not resurrected.
- **Standalone widget architecture**:
  - Стрим / OBS remains the single top-level output center;
  - OBS owns composition/positioning and Browser Source viewport sizing;
  - stable standalone routes remain the model; generic named-instance/composite canvas is not MAIN;
  - operator-only controls/status do not get viewer widgets merely for parity.
- **B6 security/architecture**:
  - provider token is secret and uses B1 protected credential storage, not plaintext main SQLite;
  - B6 wraps the common integration/auction business path rather than creating a second auction backend;
  - source-of-truth direction, conflicts, IDs, dedup, temporary-lot behavior and provider write operations remain fresh-design items.
- **Winner Verification hosting boundary**:
  - MAIN verification does not imply a public Internet-hosted verification page;
  - localhost remains default; LAN/public sharing belongs to separate D38/Public-Web/security review.
- **Product A7 card semantics**:
  - history cards identify affected lot/object and relevant values/details;
  - event types use understandable icons, with color only as a secondary cue;
  - exact timestamp remains stored even when relative time is shown;
  - hover linkage is operator UI only.

### Result

These are accepted-contract/documentation restorations, not newly selected runtime work. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**.

Because this pass again recovered durable detail, it is **NOT CLEAN**. Another orphan-only control is required after synchronization.

## Fourteenth direct-chat/source control — B1/B2 secret/lifecycle precision — 2026-10-02

A further direct-chat orphan check focused on B1/B2/Twitch/DonationAlerts lifecycle and security details.

### Additional durable detail recovered

- Plaintext tokens/passwords/API secrets are prohibited not only from main SQLite but also ordinary settings/provider config, logs/diagnostics, exports and unprotected backup content. Full backup may carry credential files only as already-protected DPAPI ciphertext; diagnostic/error text must mask secret-bearing values.
- Disconnect/usage-disable preserves configuration, protected credentials, account/capability metadata and history. On restart it stays disabled and is excluded from background provider validation until re-enabled. The accepted visible state for a preserved connected grant is `Статус: Подключено · использование отключено`.
- Remove is distinct from Disconnect: after confirmation it removes local connection/credential metadata and returns to `Не настроено`, without deleting historical business records.

### Current-source result

- MainWindow validates only integrations that are both enabled and connected.
- Diagnostic integration errors are passed through the existing secret sanitizer.
- DonationAlerts production uses built-in public Client ID **20915**.
- A manual DonationAlerts Client-ID fallback branch still exists in Settings source after the `has_built_in_client_id()` early return. In the shipped construction path it is unreachable because MainWindow creates `DonationAlertsAdapter()` with the built-in ID. This is classified as **source-hygiene/compatibility residue**, not a runtime QA defect and not automatic cleanup authorization.

Runtime/source bytes were not changed by this audit; version/schema/migrations remain **1.0.8 / 19 / 15**.

Because this pass recovered additional durable documentation detail and one source-hygiene residue, it is **NOT CLEAN**. One more post-correction orphan-only control is required.

## Fifteenth post-correction orphan-only control — CLEAN — 2026-10-02

After the eleventh through fourteenth passes had been written into canonical documentation, a new direct-chat orphan-only search was run with all already recovered contracts explicitly excluded.

### Direct-chat result

No additional durable direct-user product requirement, rejection, deferred idea, UX rule, integration/provider contract, wheel/audio rule, deployment requirement, release/QA rule or documentation/process constraint was recovered.

Returned material was already mapped:
- August Stabilization A namespace;
- accepted Maintenance A4/A8 and A9 history;
- the user's current request to write findings and repeat the audit.

### Mechanical result

- D1–D43: **43/43 present**.
- Actual D44 item: **none**.
- August Stabilization A1–A12 including A7.1/A11.1: present.
- Product A1–A8/A6.1: present.
- Maintenance A1–A10: present.
- W1–W4, B1–B6, E1–E4, R1–R2: present.
- QA-1.0.8-01 / QA-1.0.8-02 / QA-1.0.8-03 are present in current inventory/roadmap/state.
- QA finding numbering rule `QA-<version>-NN` is restored in WORKFLOW.
- Runtime remains **1.0.8 / schema 19 / migrations 15**.
- GitHub tracking remains Issues **#4 / #5** plus stale PR **#9**; none represents a hidden new scope.

### CLEAN conclusion

**New delta after the eleventh–fourteenth corrections: 0.**

The repeated audit itself was **not zero-delta**: it recovered the archive/provenance rule, QA-ID convention, History/W1/W2/Timer/A8 details, S2/widget/B6/verification/A7 boundaries, B1/B2 secret/lifecycle rules and the DonationAlerts source-hygiene residue. The fifteenth pass establishes only that no further orphan remained after those corrections.

No runtime/source bytes were modified. No implementation scope was automatically selected.

### Post-clean public-wording read-back correction

Final read-back found one documentation-only regression introduced by this reconciliation itself: the archive-gap paragraph had repeated the historical filename pattern containing a third-party development-reference name. It was neutralized to **2026-08-21 external-reference screenshot set**. The only remaining third-party-name occurrence in current reconciliation is the actual **B6 provider API adapter**, where the name is factually necessary.

This wording correction does not change the fifteenth CLEAN orphan result, roadmap status or runtime.

## Sixteenth full recheck — B4 permanent-source supersession + direct UI precision — 2026-10-02

The same scenario was repeated again after the fifteenth CLEAN result: direct chats -> Drive current/archive/project-state records -> current GitHub docs/source -> comparison against the already corrected inventory.

### New delta

1. **B4 reward-availability wording in the exhaustive inventory was stale.**
   - Earlier B4 design allowed app-managed Twitch Custom Rewards to follow auction/bid-intake state.
   - Later direct user decision on 2026-09-03 explicitly removed that coupling as part of I1/permanent-source integration behavior.
   - Authoritative rule: remote rewards are controlled only by explicit manual `Включить награды` / `Отключить награды` in Settings and do not automatically follow auction start/resume/pause/finish.
   - Channel Points/EventSub intake is permanent while the integration is connected/configured and source-time routing decides auction vs outside-auction persistent-game handling.
   - Current source confirms this: `desired_rewards_enabled()` returns the manual setting, `set_link_to_auction(True)` is rejected as a retired behavior, and old auction-link/intake settings remain compatibility-only.
   - Classification: **DOCUMENTATION SUPERSESSION CORRECTION / CURRENT RUNTIME ALREADY CORRECT / NO QA DEFECT**.

2. **Direct RANDOM.ORG UI-location decision was compressed out.**
   - User directly requested moving the RANDOM.ORG API-key controls from `Настройки → Общие` to `Настройки → Интеграции`.
   - Current source already follows this.
   - Classification: **IMPLEMENTED / ACCEPTED DOCUMENTATION PRECISION**.

3. **Direct OBS information-block date removal was compressed out.**
   - User directly requested removing the date from the lower-right OBS information block.
   - Current accepted/runtime presentation keeps that date absent.
   - Classification: **IMPLEMENTED / ACCEPTED DOCUMENTATION PRECISION**.

4. **Restore safety UI precision was incomplete.**
   - Accepted Windows QA covered that selecting the current working `data\streaming.db` as the restore source is rejected.
   - A real backup is validated, current state is safety-backed up, restore is applied and the app restarts.
   - Current Settings source explicitly rejects `source == current`.
   - Classification: **IMPLEMENTED / ACCEPTED DOCUMENTATION PRECISION**.

### Rechecked false/insufficient candidate

- Games `Всего` currently includes ordinary archived records and excludes temporary `auction_only` rows until promotion. This is visible in current source and historical accepted implementation evidence, but this pass did not recover a sufficiently clean standalone direct-user wording to reclassify it as a newly recovered direct-user requirement. Existing archive/counter coverage remains unchanged.

### Status

This sixteenth pass is **NOT CLEAN** because the B4 supersession contradiction and direct UI/restore details required documentation changes.

Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**. No implementation scope is selected or authorized by this correction.

A new post-correction orphan-only control must be run before a clean stop can be claimed.

## Sixteenth same-scenario pass — engineering invariants + D43/D26 lifecycle — 2026-10-02

The user's requested scenario was repeated again after the fifteenth clean pass: direct prior chats -> Drive/release evidence -> current GitHub docs/source -> delta-only comparison.

### New documentation delta recovered

1. **Permanent engineering rule was only partially represented by the word `reuse-first`.**
   - Direct user decisions preserve the stronger rule: **reuse first -> minimal diff -> no parallel logic -> no new persistence unless unavoidable**.
   - Existing mechanisms/data/UI/settings/calculations/APIs/storage are reused unless objectively insufficient for correctness, reliability or required performance.
   - Speed/cleanup/package/RAM optimization must not trade away stability, correctness, data safety, RNG/business semantics or predictable resource use.
   - Risky cleanup/refactor follows a permanent regression + Windows QA foundation; QA/build-only compatibility problems are fixed in QA/build before touching runtime unless runtime change is separately approved.
   - No out-of-scope runtime/schema/RNG/persistence/data-semantics changes.
   - This durable rule is now explicit in `WORKFLOW.md`, `DECISIONS.md` and the exhaustive inventory.

2. **D43/D26 accepted audio lifecycle was still too compressed in the exhaustive inventory.**
   - Opening/configuring Auction alone does not pause Music Player; ownership changes only for a real active phase with an available unmuted soundtrack.
   - Suspension preserves exact track/position and Play/Pause intent; a paused player remains paused after release.
   - Max-amount timer phase end returns Music Player immediately; D21 allows it between elimination rounds.
   - Event Mute yields ownership immediately; unmute during the still-active phase reacquires without restarting event soundtrack transport.
   - Tie setup retains auction soundtrack position for overtime; choosing a different soundtrack during tie setup discards the old retained position so the new track starts from its own beginning.
   - Same-name managed soundtrack collision offers explicit use-existing / replace / save-separate / cancel choices.
   - Full backup/restore preserves managed music/soundtrack + selections/settings while external referenced bytes remain external; restored Music Player starts paused.
   - D43 Browser Source reload follows authoritative current media position and does not reset playback to zero.
   - Current 1.0.8 source/release evidence confirms these accepted behaviors; no new runtime defect was created.

### Status

This sixteenth pass is **NOT ZERO-DELTA** because it restored durable engineering/audio detail, but it did not recover a new feature identifier or change future roadmap order. Runtime/source/version/schema/migrations remain **1.0.8 / 19 / 15**.

Another post-correction full/orphan control is required before declaring this repeated check clean.

