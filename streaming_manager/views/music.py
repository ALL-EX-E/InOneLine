from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..constants import (
    MUSIC_PLAYER_ORDER_ALPHABETICAL,
    MUSIC_PLAYER_ORDER_SHUFFLE,
    MUSIC_PLAYER_OUTPUT_MODE_APPLICATION,
    MUSIC_PLAYER_OUTPUT_MODE_OBS,
)
from ..media import (
    MEDIA_CATEGORY_MUSIC,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
    managed_media_directory,
    supported_media_extensions,
)
from ..music_player import PLAYER_PAUSE, PLAYER_PLAY, PLAYER_STOP, MusicPlayerController
from .common import ScrollSafeComboBox, ScrollSafeSpinBox, make_wide_step_control


class MusicTab(QWidget):
    """Operator controls for the D26 music player."""

    def __init__(self, db, controller: MusicPlayerController):
        super().__init__()
        self.db = db
        self.controller = controller
        self.music_dir = managed_media_directory(self.db.path.parent, MEDIA_CATEGORY_MUSIC)
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self._seeking = False

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        heading = QLabel("Музыкальный плеер")
        heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        root.addWidget(heading)

        self.now_playing = QLabel("Сейчас играет: —")
        self.now_playing.setStyleSheet("font-size: 12pt; font-weight: 600;")
        self.now_playing.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.now_playing)

        seek_row = QHBoxLayout()
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderPressed.connect(self._seek_pressed)
        self.seek_slider.sliderReleased.connect(self._seek_released)
        self.seek_time = QLabel("00:00 / 00:00")
        self.seek_time.setMinimumWidth(115)
        seek_row.addWidget(self.seek_slider, 1)
        seek_row.addWidget(self.seek_time)
        root.addLayout(seek_row)

        transport = QHBoxLayout()
        self.previous_btn = QPushButton("Предыдущий")
        self.stop_btn = QPushButton("Стоп")
        self.play_pause_btn = QPushButton("Play")
        self.next_btn = QPushButton("Следующий")
        self.previous_btn.clicked.connect(self.controller.previous_track)
        self.stop_btn.clicked.connect(self.controller.stop)
        self.play_pause_btn.clicked.connect(self.controller.play_pause)
        self.next_btn.clicked.connect(self.controller.next_track)
        for button in (self.previous_btn, self.stop_btn, self.play_pause_btn, self.next_btn):
            transport.addWidget(button)
        transport.addStretch()
        root.addLayout(transport)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Режим:"))
        self.mode_combo = ScrollSafeComboBox()
        self.mode_combo.addItem("По алфавиту", MUSIC_PLAYER_ORDER_ALPHABETICAL)
        self.mode_combo.addItem("Перемешать", MUSIC_PLAYER_ORDER_SHUFFLE)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        mode_row.addWidget(self.mode_combo)
        self.repeat_check = QCheckBox("Повторять текущий трек")
        self.repeat_check.toggled.connect(self.controller.set_repeat_current)
        mode_row.addWidget(self.repeat_check)
        mode_row.addStretch()
        root.addLayout(mode_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Вывод звука:"))
        self.output_combo = ScrollSafeComboBox()
        self.output_combo.addItem("В приложении", MUSIC_PLAYER_OUTPUT_MODE_APPLICATION)
        self.output_combo.addItem("Через OBS Browser Source", MUSIC_PLAYER_OUTPUT_MODE_OBS)
        self.output_combo.currentIndexChanged.connect(self._output_changed)
        output_row.addWidget(self.output_combo)
        output_row.addStretch()
        root.addLayout(output_row)

        gain_row = QHBoxLayout()
        gain_row.addWidget(QLabel("Громкость:"))
        self.volume = ScrollSafeSpinBox()
        self.volume.setRange(0, 100)
        self.volume.setSuffix(" %")
        self.volume.setMinimumWidth(88)
        self.volume.valueChanged.connect(self.controller.set_volume_percent)
        self.volume_control = make_wide_step_control(
            self.volume,
            up_tooltip="Увеличить громкость на 1 %",
            down_tooltip="Уменьшить громкость на 1 %",
        )
        gain_row.addWidget(self.volume_control)
        self.mute_check = QCheckBox("Без звука")
        self.mute_check.toggled.connect(self.controller.set_muted)
        gain_row.addWidget(self.mute_check)
        gain_row.addStretch()
        root.addLayout(gain_row)

        obs_row = QHBoxLayout()
        self.copy_player_overlay_url_btn = QPushButton("Копировать URL плеера")
        self.open_player_overlay_preview_btn = QPushButton("Открыть предпросмотр")
        obs_row.addWidget(self.copy_player_overlay_url_btn)
        obs_row.addWidget(self.open_player_overlay_preview_btn)
        obs_row.addStretch()
        root.addLayout(obs_row)

        library_actions = QHBoxLayout()
        self.add_music_btn = QPushButton("Добавить музыку…")
        self.add_music_btn.clicked.connect(self._import_music)
        library_actions.addWidget(self.add_music_btn)
        library_actions.addStretch()
        root.addLayout(library_actions)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по библиотеке…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        root.addWidget(self.search)

        label = QLabel("Библиотека / Очередность")
        label.setStyleSheet("font-weight: 600;")
        root.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._activate_item)
        root.addWidget(self.list_widget, 1)

        self.controller.libraryChanged.connect(self.refresh_library)
        self.controller.trackChanged.connect(self._refresh_transport)
        self.controller.stateChanged.connect(self._refresh_transport)
        self.controller.positionChanged.connect(self._position_changed)
        self.controller.playbackError.connect(self._show_playback_error)

        self.refresh_library()
        self._refresh_controls()
        self._refresh_transport()

    @staticmethod
    def _format_ms(value: int) -> str:
        total = max(0, int(value)) // 1000
        hours, rem = divmod(total, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

    def _refresh_controls(self) -> None:
        index = self.mode_combo.findData(self.controller.order_mode)
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self.mode_combo.blockSignals(False)

        self.repeat_check.blockSignals(True)
        self.repeat_check.setChecked(self.controller.repeat_current)
        self.repeat_check.blockSignals(False)

        index = self.output_combo.findData(self.controller.output_mode)
        self.output_combo.blockSignals(True)
        self.output_combo.setCurrentIndex(index if index >= 0 else 0)
        self.output_combo.blockSignals(False)

        self.volume.blockSignals(True)
        self.volume.setValue(self.controller.volume_percent)
        self.volume.blockSignals(False)

        self.mute_check.blockSignals(True)
        self.mute_check.setChecked(self.controller.muted)
        self.mute_check.blockSignals(False)

    def refresh_library(self) -> None:
        selected_id = None
        item = self.list_widget.currentItem()
        if item is not None:
            selected_id = item.data(Qt.UserRole)

        self.list_widget.clear()
        for asset in self.controller.assets_in_queue():
            metadata = self.controller.metadata_for_asset(asset.id)
            text = str(metadata.get("display_title") or asset.display_name)
            row = QListWidgetItem(text)
            row.setData(Qt.UserRole, int(asset.id))
            row.setToolTip(asset.display_name)
            self.list_widget.addItem(row)
            if selected_id == asset.id:
                self.list_widget.setCurrentItem(row)

        self._apply_filter(self.search.text())
        self._refresh_transport()

    def refresh(self) -> None:
        self.controller.refresh_library()
        self._refresh_controls()
        self._refresh_transport()

    def _refresh_transport(self) -> None:
        asset = self.controller.current_asset()
        if asset is None:
            self.now_playing.setText("Сейчас играет: —")
        else:
            metadata = self.controller.metadata_for_asset(asset.id)
            display = str(metadata.get("display_title") or asset.display_name)
            self.now_playing.setText(f"Сейчас играет: {display}")

        self.play_pause_btn.setText(
            "Пауза" if self.controller.desired_state == PLAYER_PLAY else "Play"
        )
        current = self.controller.current_media_id
        for index in range(self.list_widget.count()):
            row = self.list_widget.item(index)
            font = row.font()
            font.setBold(int(row.data(Qt.UserRole)) == int(current) if current is not None else False)
            row.setFont(font)
        self._refresh_controls()
        self._position_changed(self.controller.position_ms, self.controller.duration_ms)

    def _position_changed(self, position: int, duration: int) -> None:
        duration = max(0, int(duration))
        position = max(0, min(int(position), duration if duration else int(position)))
        if not self._seeking:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setRange(0, max(0, duration))
            self.seek_slider.setValue(position)
            self.seek_slider.blockSignals(False)
        self.seek_time.setText(f"{self._format_ms(position)} / {self._format_ms(duration)}")

    def _seek_pressed(self) -> None:
        self._seeking = True

    def _seek_released(self) -> None:
        self._seeking = False
        self.controller.seek(self.seek_slider.value())

    def _mode_changed(self, _index: int) -> None:
        self.controller.set_order_mode(str(self.mode_combo.currentData() or MUSIC_PLAYER_ORDER_ALPHABETICAL))

    def _output_changed(self, _index: int) -> None:
        self.controller.set_output_mode(str(self.output_combo.currentData() or MUSIC_PLAYER_OUTPUT_MODE_APPLICATION))

    def _apply_filter(self, text: str) -> None:
        query = str(text or "").strip().casefold()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item.setHidden(bool(query and query not in item.text().casefold()))

    def _activate_item(self, item: QListWidgetItem) -> None:
        media_id = item.data(Qt.UserRole)
        if media_id is not None:
            self.controller.select_media(int(media_id), play=True)

    @staticmethod
    def _asset_filename(asset) -> str:
        if asset.storage_mode == MEDIA_STORAGE_MANAGED:
            return Path(asset.managed_name).name
        if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
            return Path(asset.external_path).name
        return str(asset.display_name or "")

    def _existing_asset_by_filename(self, filename: str):
        wanted = Path(str(filename)).name.casefold()
        for asset in self.db.list_media_assets(MEDIA_CATEGORY_MUSIC):
            if self._asset_filename(asset).casefold() == wanted:
                return asset
        return None

    def _select_library_asset(self, media_id: int) -> None:
        if self.search.text():
            self.search.clear()
        for index in range(self.list_widget.count()):
            row = self.list_widget.item(index)
            if int(row.data(Qt.UserRole)) == int(media_id):
                self.list_widget.setCurrentItem(row)
                self.list_widget.scrollToItem(row)
                return

    def _choose_storage_mode(self, sources: list[Path]) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Как использовать музыку?")
        dialog.setIcon(QMessageBox.Icon.Question)
        if len(sources) == 1:
            selection_text = f"Выбран файл:\n{sources[0]}"
        else:
            preview = "\n".join(f"• {path.name}" for path in sources[:8])
            if len(sources) > 8:
                preview += f"\n• … и ещё {len(sources) - 8}"
            selection_text = (
                f"Выбрано файлов: {len(sources)}\n\n{preview}"
            )
        dialog.setText(
            selection_text
            + "\n\nКак In one line должен использовать выбранные файлы?"
        )
        dialog.setInformativeText(
            "«Копировать в программу» создаст управляемую копию в data\\music. "
            "«Использовать исходный файл» сохранит ссылку на оригинал."
        )
        copy_button = dialog.addButton("Копировать в программу", QMessageBox.ButtonRole.AcceptRole)
        external_button = dialog.addButton("Использовать исходный файл", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() is copy_button:
            return MEDIA_STORAGE_MANAGED
        if dialog.clickedButton() is external_button:
            return MEDIA_STORAGE_EXTERNAL
        return None

    def _duplicate_action(self, source: Path, target: Path) -> tuple[str, Path | None]:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Файл уже существует")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(f"В библиотеке уже есть файл «{target.name}».")
        use_button = dialog.addButton("Использовать существующий", QMessageBox.ButtonRole.AcceptRole)
        replace_button = dialog.addButton("Заменить", QMessageBox.ButtonRole.DestructiveRole)
        separate_button = dialog.addButton("Сохранить отдельную копию", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is use_button:
            return "use", target
        if clicked is replace_button:
            return "replace", target
        if clicked is separate_button:
            stem = source.stem
            suffix = source.suffix
            counter = 2
            candidate = self.music_dir / f"{stem} ({counter}){suffix}"
            while candidate.exists():
                counter += 1
                candidate = self.music_dir / f"{stem} ({counter}){suffix}"
            return "separate", candidate
        return "cancel", None

    def _import_music(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Добавить музыку",
            "",
            "Аудио (*.mp3 *.wav *.ogg);;Все файлы (*.*)",
        )
        if not paths:
            return

        allowed = supported_media_extensions(MEDIA_CATEGORY_MUSIC)
        sources: list[Path] = []
        invalid: list[str] = []
        for raw_path in paths:
            source = Path(raw_path)
            if not source.is_file():
                invalid.append(f"{source.name}: файл не найден")
                continue
            if source.suffix.lower() not in allowed:
                invalid.append(f"{source.name}: неподдерживаемый формат")
                continue
            sources.append(source)

        if not sources:
            QMessageBox.warning(
                self,
                "Добавление музыки",
                "Не найдено ни одного поддерживаемого аудиофайла. "
                "Поддерживаются MP3, WAV и OGG.",
            )
            return

        duplicates: list[tuple[str, int]] = []
        import_sources: list[Path] = []
        for source in sources:
            existing = self._existing_asset_by_filename(source.name)
            if existing is None:
                import_sources.append(source)
            else:
                duplicates.append((source.name, int(existing.id)))

        if duplicates:
            # Filename is the canonical duplicate rule for the Music Player.
            # Managed copies and external references intentionally share this
            # namespace: same basename means "already in the library".
            self._select_library_asset(duplicates[-1][1])
            if len(duplicates) == 1:
                duplicate_message = (
                    f"Трек «{duplicates[0][0]}» уже есть в музыкальной библиотеке.\n\n"
                    "Существующая запись выбрана в списке."
                )
            else:
                preview = "\n".join(f"• {name}" for name, _ in duplicates[:10])
                if len(duplicates) > 10:
                    preview += f"\n• … и ещё {len(duplicates) - 10}"
                duplicate_message = (
                    "Эти треки уже есть в музыкальной библиотеке:\n\n"
                    + preview
                    + "\n\nСуществующая запись одного из совпадений выбрана в списке."
                )
            QMessageBox.information(
                self,
                "Трек уже есть",
                duplicate_message,
            )

        if not import_sources:
            return

        mode = self._choose_storage_mode(import_sources)
        if mode is None:
            return

        sources = import_sources
        added_ids: list[int] = []
        skipped: list[str] = []
        errors: list[str] = list(invalid)

        for source in sources:
            try:
                if mode == MEDIA_STORAGE_EXTERNAL:
                    asset = self.db.register_external_media_asset(
                        MEDIA_CATEGORY_MUSIC,
                        source,
                    )
                else:
                    self.music_dir.mkdir(parents=True, exist_ok=True)
                    target = self.music_dir / source.name
                    if source.resolve() != target.resolve() and target.exists():
                        action, chosen = self._duplicate_action(source, target)
                        if action == "cancel" or chosen is None:
                            skipped.append(source.name)
                            continue
                        target = chosen
                        if action in {"replace", "separate"}:
                            shutil.copy2(source, target)
                    elif source.resolve() != target.resolve():
                        shutil.copy2(source, target)

                    asset = self.db.ensure_managed_media_asset(
                        MEDIA_CATEGORY_MUSIC,
                        target.name,
                        target.name,
                    )
                added_ids.append(int(asset.id))
            except Exception as exc:
                errors.append(f"{source.name}: {exc}")

        if added_ids:
            # One catalog refresh after the whole batch. Importing music must
            # not interrupt the currently playing/prepared track.
            self.controller.refresh_library()
            wanted = added_ids[-1]
            for index in range(self.list_widget.count()):
                row = self.list_widget.item(index)
                if int(row.data(Qt.UserRole)) == wanted:
                    self.list_widget.setCurrentItem(row)
                    break

        if errors or skipped:
            lines = []
            if skipped:
                lines.append(
                    "Пропущено по выбору пользователя: "
                    + ", ".join(skipped[:10])
                    + ("…" if len(skipped) > 10 else "")
                )
            if errors:
                lines.append(
                    "Не удалось добавить:\n"
                    + "\n".join(errors[:10])
                    + ("\n…" if len(errors) > 10 else "")
                )
            QMessageBox.warning(
                self,
                "Добавление музыки",
                "\n\n".join(lines),
            )

    def _show_playback_error(self, message: str) -> None:
        QMessageBox.warning(
            self,
            "Музыкальный плеер",
            f"Не удалось воспроизвести аудиофайл:\n{message}",
        )
