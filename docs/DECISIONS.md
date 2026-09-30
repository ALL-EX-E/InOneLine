# Durable Decisions

Этот файл содержит решения, которые должны переживать отдельные чаты и релизы.

## 2026-09-30 — GitHub становится source of truth

- Текущие Project State, Roadmap, Decisions, Workflow и QA ведутся в GitHub.
- Google Drive остаётся резервным/историческим архивом и не определяет CURRENT.
- Существенное решение из чата должно быть перенесено в GitHub-документацию, а не существовать только в истории чата.
- Официальные бинарные релизы хранятся в GitHub Releases.
- Candidate/FIX artifacts могут существовать в Actions/Drive как временные или резервные копии, но не являются CURRENT.

## Release rule

- В release cadence считаются только принятые CURRENT/released версии.
- Candidate/FIX версии не считаются.
- После manual acceptance официальные installer/source bytes не пересобираются.
- Release metadata может быть добавлена отдельным commit, если runtime/source принятых bytes не меняются.

## Public naming rule

В публичных материалах функции называются по назначению, а не по стороннему продукту, использованному как внутренний референс. Сторонние названия допустимы только для объективно нужной интеграции/API/protocol/dependency/license/legacy compatibility.

## D43 / D26 audio architecture

- InOneLine остаётся авторитетом для playback state.
- Browser Source — renderer/transport, а не второй business-logic engine.
- Auction и wheel soundtrack используют Timer Browser Source.
- Music Player использует отдельный Music Player Browser Source.
- AudioCoordinator определяет слышимого владельца.
- Music Player уступает ownership только активному событию с реально доступным незаглушённым soundtrack.
- После события Music Player возвращается на сохранённую позицию.

## D26 Music Player

- Managed music: `data\music`; supported MP3/WAV/OGG.
- Managed soundtrack: общий `data\soundtrack`; выбор auction/wheel независим.
- После перезапуска текущий трек/позиция восстанавливаются в Pause; autoplay запрещён.
- Search меняет только видимость списка, не очередь.
- Show mode, animation, artwork, colors и Spectrum относятся к OBS Music Player Overlay.
- Preview не создаёт дополнительный слышимый звук.

## D21 Elimination

Released behavior имеет приоритет над ранними draft-описаниями: каждое elimination spin использует настоящий weighted RNG по текущим активным лотам; выбранный лот архивируется только после явного `В архив`; последний лот тоже проходит spin; нулевой список завершает режим без final winner.

## Post-D26 UX rules

Два отдельных patch item были записаны до закрытия D26 и теперь eligible for selection:

1. скрывать логически неприменимые controls вместо серого disabled UI после отдельного полного UI audit;
2. распространить стандартный Windows Ctrl/Shift multi-file import на все применимые `Добавить файл…` flows.
