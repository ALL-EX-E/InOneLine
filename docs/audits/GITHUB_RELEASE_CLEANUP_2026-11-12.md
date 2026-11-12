# Оформление GitHub перед выпуском 1.0.11

Дата: 12.11.2026. Пользователь приостановил разработку новых функций и поручил закончить описание и выпуск на GitHub.

## Полное описание

README и docs/FEATURES.md сверены с действующим кодом; последние изменения выделены в RELEASE_NOTES_1.0.11.md. Публичная версия — [1.0.11](https://github.com/ALL-EX-E/InOneLine/releases/tag/v1.0.11). Кандидат 1.0.11 — [PR #429](https://github.com/ALL-EX-E/InOneLine/pull/429), HEAD `5644a6be84687f50e0e7c6898956a642c987ed7d`. Windows-проверка [43184622248](https://github.com/ALL-EX-E/InOneLine/actions/runs/43184622248) прошла: 92 success / 16 skipped. Пользователь принял установщик, Drive readback подтверждён; PR №429 слит как `9ddce421ef6a6e8ba2a72ed39513f969d85132dd`. Независимая Windows-проверка main `43189823708` — SUCCESS. Publisher `43193079477` — SUCCESS; выпуск 1.0.11 опубликован, исходные принятые assets подтверждены повторным скачиванием и SHA-256. После слияния #429 открыты только сохранённые #34, #387 и #408.

## Закрытые устаревшие запросы

Закрыты **48** старых проверочных/служебных PR. Перед закрытием проверены текущая открытость, канонические записи о замене/приёмке и фактическое слияние заменяющего PR через GitHub. После закрытия повторно получен список открытых PR: остались только #34, #387, #408 и новый кандидат #429. Ветки не удалялись. В описание каждого закрытого PR добавлена ссылка на замену, исходный текст сохранён.

Это **закрытие как заменённого**, а не слияние старой ветки или новая приёмка её байтов. В частности #391 заменён новой реализацией #392, а #287/#289/#290 — принятым исправлением #291; исходный дефектный/промежуточный вариант не объявляется принятым.

| Закрыт PR | Заменяющий слитый PR | Merge commit замены |
| --- | --- | --- |
| [#9](https://github.com/ALL-EX-E/InOneLine/pull/9) | [#11](https://github.com/ALL-EX-E/InOneLine/pull/11) | `90ab778f2952dadb203f467b6d69e1930f34751c` |
| [#219](https://github.com/ALL-EX-E/InOneLine/pull/219) | [#221](https://github.com/ALL-EX-E/InOneLine/pull/221) | `89abf8761fcb6054273edb1eb2b5e58868a48177` |
| [#241](https://github.com/ALL-EX-E/InOneLine/pull/241) | [#242](https://github.com/ALL-EX-E/InOneLine/pull/242) | `fff2907c85b8c3a235f7b77a50f11b4003da4fa1` |
| [#243](https://github.com/ALL-EX-E/InOneLine/pull/243) | [#244](https://github.com/ALL-EX-E/InOneLine/pull/244) | `c9fee6401537fb37f629f42d3b1a5e0b5f8c578c` |
| [#245](https://github.com/ALL-EX-E/InOneLine/pull/245) | [#246](https://github.com/ALL-EX-E/InOneLine/pull/246) | `34498e854d93eb68675d212cf7ea40a8efd52a46` |
| [#247](https://github.com/ALL-EX-E/InOneLine/pull/247) | [#248](https://github.com/ALL-EX-E/InOneLine/pull/248) | `d5a15c4f94deb6a4adbf3722ab27d7130a105eac` |
| [#249](https://github.com/ALL-EX-E/InOneLine/pull/249) | [#250](https://github.com/ALL-EX-E/InOneLine/pull/250) | `3ee23a6f74025551290af232fedcfd9c47807e6a` |
| [#251](https://github.com/ALL-EX-E/InOneLine/pull/251) | [#252](https://github.com/ALL-EX-E/InOneLine/pull/252) | `5b4c8400aebdc3d731a453f32b2dde3944bd9993` |
| [#253](https://github.com/ALL-EX-E/InOneLine/pull/253) | [#254](https://github.com/ALL-EX-E/InOneLine/pull/254) | `88aa5b3a4af38a312d473d247acd9e814c7a3b7b` |
| [#255](https://github.com/ALL-EX-E/InOneLine/pull/255) | [#256](https://github.com/ALL-EX-E/InOneLine/pull/256) | `1656d40ec6f48d3bbfdf838de31b341d2b3a5813` |
| [#257](https://github.com/ALL-EX-E/InOneLine/pull/257) | [#259](https://github.com/ALL-EX-E/InOneLine/pull/259) | `5580f4b0461b218c2d6826e506477840d11853e0` |
| [#260](https://github.com/ALL-EX-E/InOneLine/pull/260) | [#262](https://github.com/ALL-EX-E/InOneLine/pull/262) | `54ab80dfeebd33fc627f28743fb46f90617f9283` |
| [#263](https://github.com/ALL-EX-E/InOneLine/pull/263) | [#265](https://github.com/ALL-EX-E/InOneLine/pull/265) | `333adeca80bcc37b0e5d7c0b2704e30bae4c2a9a` |
| [#266](https://github.com/ALL-EX-E/InOneLine/pull/266) | [#268](https://github.com/ALL-EX-E/InOneLine/pull/268) | `76e36770b5a20cd09f1822be145dbe2e8a5a181f` |
| [#269](https://github.com/ALL-EX-E/InOneLine/pull/269) | [#271](https://github.com/ALL-EX-E/InOneLine/pull/271) | `09de164370193a77f538de1b7038d4abaa2b56b3` |
| [#272](https://github.com/ALL-EX-E/InOneLine/pull/272) | [#274](https://github.com/ALL-EX-E/InOneLine/pull/274) | `19a0d5bc2c6d44d30cd98c750f426bc92dc9a276` |
| [#275](https://github.com/ALL-EX-E/InOneLine/pull/275) | [#277](https://github.com/ALL-EX-E/InOneLine/pull/277) | `811789f47a6593d518ba413244a8505c0376777e` |
| [#278](https://github.com/ALL-EX-E/InOneLine/pull/278) | [#280](https://github.com/ALL-EX-E/InOneLine/pull/280) | `73e8da4dbea67b0dd4e13028465d71c3f744892a` |
| [#281](https://github.com/ALL-EX-E/InOneLine/pull/281) | [#283](https://github.com/ALL-EX-E/InOneLine/pull/283) | `96914c129f6abe7318598466476884c9f420f1a0` |
| [#284](https://github.com/ALL-EX-E/InOneLine/pull/284) | [#286](https://github.com/ALL-EX-E/InOneLine/pull/286) | `cd38520c7d4f63154f918a87f446195c08b036d9` |
| [#287](https://github.com/ALL-EX-E/InOneLine/pull/287) | [#291](https://github.com/ALL-EX-E/InOneLine/pull/291) | `785051caabea80cc9b43c298a74e701f9b43c95e` |
| [#289](https://github.com/ALL-EX-E/InOneLine/pull/289) | [#291](https://github.com/ALL-EX-E/InOneLine/pull/291) | `785051caabea80cc9b43c298a74e701f9b43c95e` |
| [#290](https://github.com/ALL-EX-E/InOneLine/pull/290) | [#291](https://github.com/ALL-EX-E/InOneLine/pull/291) | `785051caabea80cc9b43c298a74e701f9b43c95e` |
| [#292](https://github.com/ALL-EX-E/InOneLine/pull/292) | [#294](https://github.com/ALL-EX-E/InOneLine/pull/294) | `ba8ea0c941e6cefc75301df69ad38ab420abe899` |
| [#295](https://github.com/ALL-EX-E/InOneLine/pull/295) | [#296](https://github.com/ALL-EX-E/InOneLine/pull/296) | `c0eb56af7a108c70593e82fc8de501c0f3e862dc` |
| [#297](https://github.com/ALL-EX-E/InOneLine/pull/297) | [#298](https://github.com/ALL-EX-E/InOneLine/pull/298) | `341b3f40441eed53a5c70f8d5df9dd3f574a117a` |
| [#299](https://github.com/ALL-EX-E/InOneLine/pull/299) | [#300](https://github.com/ALL-EX-E/InOneLine/pull/300) | `a3a097edd310122009eeb60689b02164739c3aee` |
| [#301](https://github.com/ALL-EX-E/InOneLine/pull/301) | [#302](https://github.com/ALL-EX-E/InOneLine/pull/302) | `b893dce5bfc4685dbc074a211becf4ac087bf346` |
| [#303](https://github.com/ALL-EX-E/InOneLine/pull/303) | [#304](https://github.com/ALL-EX-E/InOneLine/pull/304) | `9652ab600ac88346f366b7ea9a87c299c9ef596e` |
| [#305](https://github.com/ALL-EX-E/InOneLine/pull/305) | [#306](https://github.com/ALL-EX-E/InOneLine/pull/306) | `1e223b255f51ce248755480d951e0e6e963a32ad` |
| [#307](https://github.com/ALL-EX-E/InOneLine/pull/307) | [#308](https://github.com/ALL-EX-E/InOneLine/pull/308) | `34783ca051280adf2bc2b36fe673014f1a36e0dd` |
| [#309](https://github.com/ALL-EX-E/InOneLine/pull/309) | [#310](https://github.com/ALL-EX-E/InOneLine/pull/310) | `a966bd5ed82bafaf2e52df063473617dae0faff3` |
| [#311](https://github.com/ALL-EX-E/InOneLine/pull/311) | [#312](https://github.com/ALL-EX-E/InOneLine/pull/312) | `75a37dd6c90f8645e860fe5d4debdaaee3454af6` |
| [#313](https://github.com/ALL-EX-E/InOneLine/pull/313) | [#314](https://github.com/ALL-EX-E/InOneLine/pull/314) | `5aa9fb45c9e0545c8e21d10162dea8d1de7bfc7e` |
| [#315](https://github.com/ALL-EX-E/InOneLine/pull/315) | [#316](https://github.com/ALL-EX-E/InOneLine/pull/316) | `5462dae8443588e939d5974d2aacf8572ea66ebb` |
| [#317](https://github.com/ALL-EX-E/InOneLine/pull/317) | [#318](https://github.com/ALL-EX-E/InOneLine/pull/318) | `c653f9352f5502b525a3d5878af8e0089def38f5` |
| [#320](https://github.com/ALL-EX-E/InOneLine/pull/320) | [#322](https://github.com/ALL-EX-E/InOneLine/pull/322) | `484f96b683817830866078c2c360103995313c91` |
| [#323](https://github.com/ALL-EX-E/InOneLine/pull/323) | [#326](https://github.com/ALL-EX-E/InOneLine/pull/326) | `89eeb3257648da91ec8e22e7e0699b73ed9544a8` |
| [#328](https://github.com/ALL-EX-E/InOneLine/pull/328) | [#329](https://github.com/ALL-EX-E/InOneLine/pull/329) | `a197678b280b5ab43178ee27e6c0594aad89b4db` |
| [#331](https://github.com/ALL-EX-E/InOneLine/pull/331) | [#333](https://github.com/ALL-EX-E/InOneLine/pull/333) | `ae1480dc5cba33c0f161c5151369d40f8fc810b1` |
| [#336](https://github.com/ALL-EX-E/InOneLine/pull/336) | [#338](https://github.com/ALL-EX-E/InOneLine/pull/338) | `2db21f39b6d3d1b0855faf0308725e2012aa16fe` |
| [#341](https://github.com/ALL-EX-E/InOneLine/pull/341) | [#344](https://github.com/ALL-EX-E/InOneLine/pull/344) | `3c431aae0c97faec4ff49bf6e13546e11cb9ea2a` |
| [#343](https://github.com/ALL-EX-E/InOneLine/pull/343) | [#342](https://github.com/ALL-EX-E/InOneLine/pull/342) | `eda021640dd657d142b87990a8533fe78489ace3` |
| [#347](https://github.com/ALL-EX-E/InOneLine/pull/347) | [#349](https://github.com/ALL-EX-E/InOneLine/pull/349) | `44ece91138ebe6bf2d5e2d9b66bd5bb17031c16d` |
| [#350](https://github.com/ALL-EX-E/InOneLine/pull/350) | [#353](https://github.com/ALL-EX-E/InOneLine/pull/353) | `1c7c9abf262801b7e72e26034be448ebe32dd7c1` |
| [#391](https://github.com/ALL-EX-E/InOneLine/pull/391) | [#392](https://github.com/ALL-EX-E/InOneLine/pull/392) | `cf5609d1e12b734a8ba451eef2c8ebe6e79c931e` |
| [#398](https://github.com/ALL-EX-E/InOneLine/pull/398) | [#400](https://github.com/ALL-EX-E/InOneLine/pull/400) | `9c24b5a16cc108f9533dd16699994b023ee83234` |
| [#399](https://github.com/ALL-EX-E/InOneLine/pull/399) | [#400](https://github.com/ALL-EX-E/InOneLine/pull/400) | `9c24b5a16cc108f9533dd16699994b023ee83234` |

Для документационного #343 замена #342 подтверждена последующей приёмкой продукта #344.

## Сохранённые черновики

- **#34:** отдельный непринятый аудит; полного продвижения или решения о закрытии не доказано.
- **#387:** рабочий документ содержит прямое указание сохранить PR открытым.
- **#408:** рабочий документ содержит прямое указание сохранить draft как reference; частичная проверка не равна полной приёмке.

Их сохранение не означает активную разработку, разрешение слияния или включение в 1.0.11. Все отложенные идеи и артефакты сохраняются.
