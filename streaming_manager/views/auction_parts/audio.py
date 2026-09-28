from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...audio import ApplicationAudioEngine, ApplicationPlaylistAudioEngine
from ...constants import (
    AUCTION_AUDIO_OUTPUT_MODE_APPLICATION,
    AUCTION_AUDIO_OUTPUT_MODE_DEFAULT,
    AUCTION_AUDIO_OUTPUT_MODE_KEY,
    AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
    AUCTION_SOUNDTRACK_LOOP_ONE_DEFAULT,
    AUCTION_SOUNDTRACK_LOOP_ONE_KEY,
    AUCTION_SOUNDTRACK_MEDIA_ID_KEY,
    AUCTION_SOUNDTRACK_MUTE_DEFAULT,
    AUCTION_SOUNDTRACK_MUTE_KEY,
    AUCTION_SOUNDTRACK_VOLUME_DEFAULT,
    AUCTION_SOUNDTRACK_VOLUME_KEY,
    WHEEL_SOUNDTRACK_MEDIA_ID_KEY,
    WHEEL_SOUNDTRACK_MUTE_DEFAULT,
    WHEEL_SOUNDTRACK_MUTE_KEY,
    WHEEL_SOUNDTRACK_VOLUME_DEFAULT,
    WHEEL_SOUNDTRACK_VOLUME_KEY,
)
from ...media import (
    MEDIA_CATEGORY_MUSIC,
    MEDIA_CATEGORY_WHEEL_JINGLES,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
    media_asset_available,
    managed_media_directory,
    resolve_media_asset_path,
    supported_media_extensions,
)
from ...workers import FunctionWorker
from ..common import ScrollSafeComboBox, ScrollSafeSpinBox, make_wide_step_control


class AuctionAudioMixin:
    WHEEL_SOUNDTRACK_FADE_MS = 600
    AUCTION_SOUNDTRACK_FADE_MS = 600

    def _init_wheel_audio(self) -> None:
        # W3 remains unchanged and owns the wheel-spin jingle. Timer/Auction
        # Music uses a separate engine/profile so neither selection, gain nor
        # playback position can leak between the two contexts.
        self.wheel_audio = ApplicationAudioEngine(self)
        self.wheel_audio.playbackError.connect(self._wheel_audio_error)
        self._wheel_soundtrack_copy_worker: FunctionWorker | None = None
        self._wheel_audio_runtime_error = ""
        self.wheel_jingles_dir = managed_media_directory(
            self.db.path.parent,
            MEDIA_CATEGORY_WHEEL_JINGLES,
        )
        self.wheel_jingles_dir.mkdir(parents=True, exist_ok=True)
        self.wheel_audio.set_volume_percent(self._saved_wheel_soundtrack_volume())
        self.wheel_audio.set_muted(self._saved_wheel_soundtrack_mute())

        self.auction_audio = ApplicationPlaylistAudioEngine(self)
        self.auction_audio.playbackError.connect(self._auction_audio_error)
        self.auction_audio.trackChanged.connect(self._auction_audio_track_changed)
        self.auction_audio.stopped.connect(self._auction_audio_stopped)
        self._auction_soundtrack_copy_worker: FunctionWorker | None = None
        self._auction_audio_runtime_error = ""
        self._auction_audio_session_id: int | None = None
        self.auction_music_dir = managed_media_directory(
            self.db.path.parent,
            MEDIA_CATEGORY_MUSIC,
        )
        self.auction_music_dir.mkdir(parents=True, exist_ok=True)
        self.auction_audio.set_volume_percent(self._saved_auction_soundtrack_volume())
        self.auction_audio.set_muted(self._saved_auction_soundtrack_mute())

        # D43 keeps the existing Qt players as the authoritative transport even
        # when OBS renders the sound. In OBS mode they continue tracking exact
        # playlist/position/fade state but their local QAudioOutput is muted.
        self._auction_audio_asset_ids: list[int] = []
        self._wheel_audio_asset_id: int | None = None
        self._browser_audio_snapshot: dict[str, object] = {
            "enabled": False,
            "owner": "idle",
            "active": False,
            "kind": "none",
        }
        self._browser_audio_snapshot_timer = QTimer(self)
        self._browser_audio_snapshot_timer.setInterval(100)
        self._browser_audio_snapshot_timer.timeout.connect(
            self._refresh_browser_audio_snapshot
        )
        self._apply_audio_output_mode()
        self._refresh_browser_audio_snapshot()
        self._browser_audio_snapshot_timer.start()

    def _saved_audio_output_mode(self) -> str:
        mode = str(
            self.db.get_setting(
                AUCTION_AUDIO_OUTPUT_MODE_KEY,
                AUCTION_AUDIO_OUTPUT_MODE_DEFAULT,
            )
            or AUCTION_AUDIO_OUTPUT_MODE_DEFAULT
        ).strip().casefold()
        if mode not in {
            AUCTION_AUDIO_OUTPUT_MODE_APPLICATION,
            AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
        }:
            return AUCTION_AUDIO_OUTPUT_MODE_DEFAULT
        return mode

    def _audio_output_mode_changed(self, _index: int = -1) -> None:
        combo = getattr(self, "audio_output_mode_combo", None)
        if combo is None:
            return
        mode = str(combo.currentData() or AUCTION_AUDIO_OUTPUT_MODE_DEFAULT)
        if mode not in {
            AUCTION_AUDIO_OUTPUT_MODE_APPLICATION,
            AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
        }:
            mode = AUCTION_AUDIO_OUTPUT_MODE_DEFAULT
        self.db.set_setting(AUCTION_AUDIO_OUTPUT_MODE_KEY, mode)
        self._apply_audio_output_mode()
        self._refresh_browser_audio_snapshot()

    def _apply_audio_output_mode(self) -> None:
        through_obs = self._saved_audio_output_mode() == AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER
        self.auction_audio.set_transport_silent(through_obs)
        self.wheel_audio.set_transport_silent(through_obs)

    def _acquire_auction_audio_owner(self) -> None:
        coordinator = getattr(self, "audio_coordinator", None)
        if coordinator is not None:
            coordinator.acquire_auction()

    def _release_auction_audio_owner(self) -> None:
        coordinator = getattr(self, "audio_coordinator", None)
        if coordinator is not None:
            coordinator.release_auction()

    def _sync_audio_owner_with_session(
        self,
        session: dict | None,
        *,
        spin_running: bool | None = None,
    ) -> None:
        if session is None:
            self._release_auction_audio_owner()
            return
        status = str(session.get("status") or "")
        if status == "winner_selected":
            if spin_running is None:
                spin_running = bool(
                    session.get("wheel_spin_id")
                    and not self._wheel_spin_complete(session)
                )
            if not spin_running:
                self._release_auction_audio_owner()
                return
        if status in self.db.AUCTION_OPEN_STATUSES:
            self._acquire_auction_audio_owner()
        else:
            self._release_auction_audio_owner()

    def _refresh_browser_audio_snapshot(self) -> None:
        mode = self._saved_audio_output_mode()
        coordinator = getattr(self, "audio_coordinator", None)
        owner = str(coordinator.owner) if coordinator is not None else "idle"
        snapshot: dict[str, object] = {
            "enabled": mode == AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
            "owner": owner,
            "active": False,
            "kind": "none",
            "media_id": None,
            "url": "",
            "playing": False,
            "paused": False,
            "position_ms": 0,
            "gain": 0.0,
            "muted": False,
            "loop": False,
        }

        if not snapshot["enabled"] or owner != "auction":
            self._browser_audio_snapshot = snapshot
            return

        if self.wheel_audio.window_active and self._wheel_audio_asset_id is not None:
            snapshot.update(
                {
                    "active": True,
                    "kind": "wheel",
                    "media_id": int(self._wheel_audio_asset_id),
                    "url": f"/media/{int(self._wheel_audio_asset_id)}",
                    "playing": bool(self.wheel_audio.playing),
                    "paused": False,
                    "position_ms": int(self.wheel_audio.position_ms),
                    "gain": float(self.wheel_audio.effective_gain),
                    "muted": bool(self.wheel_audio.muted),
                    "loop": True,
                }
            )
            self._browser_audio_snapshot = snapshot
            return

        if self.auction_audio.active and self._auction_audio_asset_ids:
            index = max(
                0,
                min(
                    len(self._auction_audio_asset_ids) - 1,
                    int(self.auction_audio.current_index),
                ),
            )
            media_id = int(self._auction_audio_asset_ids[index])
            snapshot.update(
                {
                    "active": True,
                    "kind": "auction",
                    "media_id": media_id,
                    "url": f"/media/{media_id}",
                    "playing": bool(self.auction_audio.playing),
                    "paused": bool(self.auction_audio.paused),
                    "position_ms": int(self.auction_audio.position_ms),
                    "gain": float(self.auction_audio.effective_gain),
                    "muted": bool(self.auction_audio.muted),
                    "loop": bool(self.auction_audio.loop_one),
                }
            )

        self._browser_audio_snapshot = snapshot

    def auction_browser_audio_state(self) -> dict[str, object]:
        # HTTP runs on its own thread. Return only a copy of the primitive cache;
        # QMediaPlayer/QAudioOutput are read exclusively by the main-thread timer.
        return dict(self._browser_audio_snapshot)

    def _build_wheel_soundtrack_controls(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)

        # W3 narrow-panel layout: do not force the selector and import action
        # into one horizontal row. The wheel panel can legitimately be only
        # 300 px wide, so those controls must stack instead of overlapping.
        root.addWidget(QLabel("Музыка колеса:"))
        self.wheel_soundtrack_combo = ScrollSafeComboBox()
        self.wheel_soundtrack_combo.currentIndexChanged.connect(
            self._wheel_soundtrack_selection_changed
        )
        root.addWidget(self.wheel_soundtrack_combo)

        soundtrack_action_row = QHBoxLayout()
        soundtrack_action_row.setSpacing(5)
        self.add_wheel_soundtrack_btn = QPushButton("Добавить soundtrack…")
        self.add_wheel_soundtrack_btn.clicked.connect(self._import_wheel_soundtrack)
        soundtrack_action_row.addWidget(self.add_wheel_soundtrack_btn)
        soundtrack_action_row.addStretch()
        root.addLayout(soundtrack_action_row)

        self.wheel_soundtrack_status = QLabel("Soundtrack не выбран")
        self.wheel_soundtrack_status.setProperty("muted", True)
        self.wheel_soundtrack_status.setWordWrap(True)
        root.addWidget(self.wheel_soundtrack_status)

        repair_row = QHBoxLayout()
        repair_row.setSpacing(5)
        self.repair_wheel_soundtrack_btn = QPushButton("Восстановить ссылку…")
        self.repair_wheel_soundtrack_btn.clicked.connect(
            self._repair_wheel_soundtrack_reference
        )
        self.repair_wheel_soundtrack_btn.setVisible(False)
        self.repair_wheel_soundtrack_btn.setEnabled(False)
        repair_row.addWidget(self.repair_wheel_soundtrack_btn)
        repair_row.addStretch()
        root.addLayout(repair_row)

        gain_row = QHBoxLayout()
        gain_row.setSpacing(5)
        gain_row.addWidget(QLabel("Громкость:"))
        self.wheel_soundtrack_volume = ScrollSafeSpinBox()
        self.wheel_soundtrack_volume.setRange(0, 100)
        self.wheel_soundtrack_volume.setSuffix(" %")
        self.wheel_soundtrack_volume.setMinimumWidth(88)
        self.wheel_soundtrack_volume.setValue(self._saved_wheel_soundtrack_volume())
        self.wheel_soundtrack_volume.valueChanged.connect(
            self._wheel_soundtrack_volume_changed
        )
        self.wheel_soundtrack_volume_control = make_wide_step_control(
            self.wheel_soundtrack_volume,
            up_tooltip="Увеличить громкость на 1 %",
            down_tooltip="Уменьшить громкость на 1 %",
        )
        volume_step_buttons = self.wheel_soundtrack_volume_control.findChildren(QPushButton)
        self.wheel_soundtrack_volume_up_btn = next(
            button for button in volume_step_buttons if button.text() == "▲"
        )
        self.wheel_soundtrack_volume_down_btn = next(
            button for button in volume_step_buttons if button.text() == "▼"
        )
        gain_row.addWidget(self.wheel_soundtrack_volume_control)
        gain_row.addStretch()
        root.addLayout(gain_row)

        mute_row = QHBoxLayout()
        mute_row.setSpacing(5)
        self.wheel_soundtrack_mute = QCheckBox("Без звука")
        self.wheel_soundtrack_mute.setChecked(self._saved_wheel_soundtrack_mute())
        self.wheel_soundtrack_mute.toggled.connect(self._wheel_soundtrack_mute_changed)
        mute_row.addWidget(self.wheel_soundtrack_mute)
        mute_row.addStretch()
        root.addLayout(mute_row)

        self._refresh_wheel_soundtrack_library()
        return panel

    def _saved_wheel_soundtrack_volume(self) -> int:
        raw = self.db.get_setting(
            WHEEL_SOUNDTRACK_VOLUME_KEY,
            str(WHEEL_SOUNDTRACK_VOLUME_DEFAULT),
        )
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return WHEEL_SOUNDTRACK_VOLUME_DEFAULT
        return max(0, min(100, value))

    def _saved_wheel_soundtrack_mute(self) -> bool:
        return self.db.get_setting(
            WHEEL_SOUNDTRACK_MUTE_KEY,
            "1" if WHEEL_SOUNDTRACK_MUTE_DEFAULT else "0",
        ) == "1"

    @staticmethod
    def _wheel_soundtrack_asset_label(asset, available: bool) -> str:
        if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
            label = f"{asset.display_name} — исходный файл"
        else:
            label = asset.display_name
        return label if available else f"⚠ файл недоступен: {label}"

    def _wheel_soundtrack_assets(self):
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_WHEEL_JINGLES)

    def _selected_wheel_soundtrack_asset(self):
        raw = self.wheel_soundtrack_combo.currentData()
        if not str(raw or "").isdigit():
            return None
        asset = self.db.get_media_asset(int(raw))
        if asset is None or asset.category != MEDIA_CATEGORY_WHEEL_JINGLES:
            return None
        return asset

    def _refresh_wheel_soundtrack_library(self, selected_asset_id=None) -> None:
        if selected_asset_id is None:
            selected_asset_id = self.db.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "")
        try:
            selected_id = int(selected_asset_id) if str(selected_asset_id or "").isdigit() else None
        except (TypeError, ValueError):
            selected_id = None

        self.wheel_soundtrack_combo.blockSignals(True)
        self.wheel_soundtrack_combo.clear()
        self.wheel_soundtrack_combo.addItem("— без soundtrack —", "")
        for asset in self._wheel_soundtrack_assets():
            available = media_asset_available(self.db.path.parent, asset)
            self.wheel_soundtrack_combo.addItem(
                self._wheel_soundtrack_asset_label(asset, available),
                asset.id,
            )
        index = self.wheel_soundtrack_combo.findData(selected_id) if selected_id else 0
        self.wheel_soundtrack_combo.setCurrentIndex(index if index >= 0 else 0)
        self.wheel_soundtrack_combo.blockSignals(False)
        self._refresh_wheel_soundtrack_availability()

    def _refresh_wheel_soundtrack_availability(self) -> None:
        if not hasattr(self, "wheel_soundtrack_combo"):
            return
        asset = self._selected_wheel_soundtrack_asset()
        if asset is None:
            self.wheel_soundtrack_status.setText("Soundtrack не выбран")
            self.wheel_soundtrack_status.setToolTip("")
            self.repair_wheel_soundtrack_btn.setVisible(False)
            self.repair_wheel_soundtrack_btn.setEnabled(False)
            return

        available = media_asset_available(self.db.path.parent, asset)
        index = self.wheel_soundtrack_combo.currentIndex()
        if index >= 0:
            expected = self._wheel_soundtrack_asset_label(asset, available)
            if self.wheel_soundtrack_combo.itemText(index) != expected:
                self.wheel_soundtrack_combo.setItemText(index, expected)

        try:
            resolved = resolve_media_asset_path(self.db.path.parent, asset)
            path_text = str(resolved)
        except (OSError, ValueError):
            path_text = str(asset.external_path or asset.managed_name)
        self.wheel_soundtrack_status.setToolTip(path_text)

        needs_repair = asset.storage_mode == MEDIA_STORAGE_EXTERNAL and not available
        if available:
            self.wheel_soundtrack_status.setText(
                "Доступен" if not self._wheel_audio_runtime_error else self._wheel_audio_runtime_error
            )
        elif needs_repair:
            self.wheel_soundtrack_status.setText(
                "Файл недоступен — восстановите ссылку или выберите другой soundtrack"
            )
        else:
            self.wheel_soundtrack_status.setText(
                "Файл недоступен — добавьте soundtrack заново или выберите другой"
            )
        self.repair_wheel_soundtrack_btn.setVisible(needs_repair)
        self.repair_wheel_soundtrack_btn.setEnabled(needs_repair)

    def _wheel_soundtrack_selection_changed(self, _index: int = -1) -> None:
        asset = self._selected_wheel_soundtrack_asset()
        self._wheel_audio_runtime_error = ""
        self.db.set_setting(
            WHEEL_SOUNDTRACK_MEDIA_ID_KEY,
            str(asset.id) if asset is not None else "",
        )
        self._refresh_wheel_soundtrack_availability()

    def _wheel_soundtrack_volume_changed(self, value: int) -> None:
        normalized = self.wheel_audio.set_volume_percent(value)
        self.db.set_setting(WHEEL_SOUNDTRACK_VOLUME_KEY, str(normalized))

    def _wheel_soundtrack_mute_changed(self, muted: bool) -> None:
        normalized = self.wheel_audio.set_muted(muted)
        self.db.set_setting(WHEEL_SOUNDTRACK_MUTE_KEY, "1" if normalized else "0")

    def _choose_wheel_soundtrack_storage_mode(self, source: Path) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Как использовать soundtrack?")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(
            f"Выбран файл:\n{source}\n\nКак In one line должен его использовать?"
        )
        dialog.setInformativeText(
            "«Копировать в программу» создаст управляемую копию в отдельной папке "
            "data\\wheel_jingles. «Использовать исходный файл» сохранит ссылку "
            "на оригинал; сам оригинал программа не изменяет и не удаляет."
        )
        copy_button = dialog.addButton(
            "Копировать в программу", QMessageBox.ButtonRole.AcceptRole
        )
        external_button = dialog.addButton(
            "Использовать исходный файл", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is copy_button:
            return MEDIA_STORAGE_MANAGED
        if clicked is external_button:
            return MEDIA_STORAGE_EXTERNAL
        return None

    def _unique_wheel_soundtrack_target(self, source: Path) -> Path:
        existing = {
            item.name.casefold()
            for item in self.wheel_jingles_dir.iterdir()
            if item.is_file()
        }
        candidate = self.wheel_jingles_dir / source.name
        counter = 2
        while candidate.name.casefold() in existing:
            candidate = self.wheel_jingles_dir / f"{source.stem} ({counter}){source.suffix}"
            counter += 1
        return candidate

    @staticmethod
    def _copy_wheel_soundtrack(source: Path, target: Path) -> Path:
        try:
            shutil.copy2(source, target)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def _start_wheel_soundtrack_copy(self, source: Path, target: Path) -> None:
        if self._wheel_soundtrack_copy_worker is not None:
            return
        self.add_wheel_soundtrack_btn.setEnabled(False)
        self.add_wheel_soundtrack_btn.setText("Копирование…")
        worker = FunctionWorker(self._copy_wheel_soundtrack, source, target)
        self._wheel_soundtrack_copy_worker = worker
        worker.signals.result.connect(self._wheel_soundtrack_copy_ready)
        worker.signals.error.connect(self._wheel_soundtrack_copy_failed)
        worker.signals.finished.connect(self._wheel_soundtrack_copy_finished)
        self.thread_pool.start(worker)

    def _wheel_soundtrack_copy_ready(self, target: Path) -> None:
        asset = self.db.ensure_managed_media_asset(
            MEDIA_CATEGORY_WHEEL_JINGLES,
            target.name,
            target.name,
        )
        self.db.set_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
        self._refresh_wheel_soundtrack_library(asset.id)

    def _wheel_soundtrack_copy_failed(self, exc) -> None:
        QMessageBox.critical(
            self,
            "Ошибка копирования soundtrack",
            f"Не удалось скопировать аудиофайл во внутреннюю библиотеку:\n{exc}",
        )

    def _wheel_soundtrack_copy_finished(self) -> None:
        self._wheel_soundtrack_copy_worker = None
        self.add_wheel_soundtrack_btn.setEnabled(True)
        self.add_wheel_soundtrack_btn.setText("Добавить soundtrack…")

    def _import_wheel_soundtrack(self) -> None:
        if self._wheel_soundtrack_copy_worker is not None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите soundtrack колеса",
            "",
            "Аудио (*.mp3 *.wav *.ogg);;Все файлы (*.*)",
        )
        if not path:
            return
        source = Path(path)
        if source.suffix.lower() not in supported_media_extensions(MEDIA_CATEGORY_WHEEL_JINGLES):
            QMessageBox.warning(
                self,
                "Неподдерживаемый формат",
                "Для soundtrack колеса поддерживаются MP3, WAV и OGG.",
            )
            return
        if not source.is_file():
            QMessageBox.critical(self, "Ошибка", "Выбранный аудиофайл не найден.")
            return

        self.wheel_jingles_dir.mkdir(parents=True, exist_ok=True)
        storage_mode = self._choose_wheel_soundtrack_storage_mode(source)
        if storage_mode is None:
            return
        if storage_mode == MEDIA_STORAGE_EXTERNAL:
            asset = self.db.register_external_media_asset(
                MEDIA_CATEGORY_WHEEL_JINGLES,
                source,
            )
            self.db.set_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
            self._refresh_wheel_soundtrack_library(asset.id)
            return

        if source.resolve().parent == self.wheel_jingles_dir.resolve():
            asset = self.db.ensure_managed_media_asset(
                MEDIA_CATEGORY_WHEEL_JINGLES,
                source.name,
                source.name,
            )
            self.db.set_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
            self._refresh_wheel_soundtrack_library(asset.id)
            return

        target = self._unique_wheel_soundtrack_target(source)
        self._start_wheel_soundtrack_copy(source, target)

    def _repair_wheel_soundtrack_reference(self) -> None:
        asset = self._selected_wheel_soundtrack_asset()
        if asset is None or asset.storage_mode != MEDIA_STORAGE_EXTERNAL:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Восстановить ссылку на soundtrack",
            "",
            "Аудио (*.mp3 *.wav *.ogg);;Все файлы (*.*)",
        )
        if not path:
            return
        source = Path(path)
        if not source.is_file():
            QMessageBox.critical(self, "Ошибка", "Выбранный аудиофайл не найден.")
            return
        try:
            repaired = self.db.update_external_media_asset(asset.id, source)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Ошибка восстановления ссылки",
                f"Не удалось обновить ссылку на soundtrack:\n{exc}",
            )
            return
        self._wheel_audio_runtime_error = ""
        self._refresh_wheel_soundtrack_library(repaired.id)

    def _build_auction_soundtrack_controls(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)

        root.addWidget(QLabel("Музыка аукциона:"))
        self.auction_soundtrack_combo = ScrollSafeComboBox()
        self.auction_soundtrack_combo.currentIndexChanged.connect(
            self._auction_soundtrack_selection_changed
        )
        root.addWidget(self.auction_soundtrack_combo)

        action_row = QHBoxLayout()
        action_row.setSpacing(5)
        self.add_auction_soundtrack_btn = QPushButton("Добавить soundtrack…")
        self.add_auction_soundtrack_btn.clicked.connect(self._import_auction_soundtrack)
        action_row.addWidget(self.add_auction_soundtrack_btn)
        action_row.addStretch()
        root.addLayout(action_row)

        self.auction_soundtrack_status = QLabel("Soundtrack не выбран")
        self.auction_soundtrack_status.setProperty("muted", True)
        self.auction_soundtrack_status.setWordWrap(True)
        root.addWidget(self.auction_soundtrack_status)

        repair_row = QHBoxLayout()
        repair_row.setSpacing(5)
        self.repair_auction_soundtrack_btn = QPushButton("Восстановить ссылку…")
        self.repair_auction_soundtrack_btn.clicked.connect(
            self._repair_auction_soundtrack_reference
        )
        self.repair_auction_soundtrack_btn.setVisible(False)
        self.repair_auction_soundtrack_btn.setEnabled(False)
        repair_row.addWidget(self.repair_auction_soundtrack_btn)
        repair_row.addStretch()
        root.addLayout(repair_row)

        self.auction_soundtrack_loop_one = QCheckBox("Зациклить выбранный трек")
        self.auction_soundtrack_loop_one.setChecked(self._saved_auction_soundtrack_loop_one())
        self.auction_soundtrack_loop_one.toggled.connect(
            self._auction_soundtrack_loop_one_changed
        )
        root.addWidget(self.auction_soundtrack_loop_one)

        gain_row = QHBoxLayout()
        gain_row.setSpacing(5)
        gain_row.addWidget(QLabel("Громкость:"))
        self.auction_soundtrack_volume = ScrollSafeSpinBox()
        self.auction_soundtrack_volume.setRange(0, 100)
        self.auction_soundtrack_volume.setSuffix(" %")
        self.auction_soundtrack_volume.setMinimumWidth(88)
        self.auction_soundtrack_volume.setValue(self._saved_auction_soundtrack_volume())
        self.auction_soundtrack_volume.valueChanged.connect(
            self._auction_soundtrack_volume_changed
        )
        self.auction_soundtrack_volume_control = make_wide_step_control(
            self.auction_soundtrack_volume,
            up_tooltip="Увеличить громкость на 1 %",
            down_tooltip="Уменьшить громкость на 1 %",
        )
        volume_step_buttons = self.auction_soundtrack_volume_control.findChildren(QPushButton)
        self.auction_soundtrack_volume_up_btn = next(
            button for button in volume_step_buttons if button.text() == "▲"
        )
        self.auction_soundtrack_volume_down_btn = next(
            button for button in volume_step_buttons if button.text() == "▼"
        )
        gain_row.addWidget(self.auction_soundtrack_volume_control)
        gain_row.addStretch()
        root.addLayout(gain_row)

        self.auction_soundtrack_mute = QCheckBox("Без звука")
        self.auction_soundtrack_mute.setChecked(self._saved_auction_soundtrack_mute())
        self.auction_soundtrack_mute.toggled.connect(self._auction_soundtrack_mute_changed)
        root.addWidget(self.auction_soundtrack_mute)

        self._refresh_auction_soundtrack_library()
        return panel

    def _saved_auction_soundtrack_volume(self) -> int:
        raw = self.db.get_setting(
            AUCTION_SOUNDTRACK_VOLUME_KEY,
            str(AUCTION_SOUNDTRACK_VOLUME_DEFAULT),
        )
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return AUCTION_SOUNDTRACK_VOLUME_DEFAULT
        return max(0, min(100, value))

    def _saved_auction_soundtrack_mute(self) -> bool:
        return self.db.get_setting(
            AUCTION_SOUNDTRACK_MUTE_KEY,
            "1" if AUCTION_SOUNDTRACK_MUTE_DEFAULT else "0",
        ) == "1"

    def _saved_auction_soundtrack_loop_one(self) -> bool:
        return self.db.get_setting(
            AUCTION_SOUNDTRACK_LOOP_ONE_KEY,
            "1" if AUCTION_SOUNDTRACK_LOOP_ONE_DEFAULT else "0",
        ) == "1"

    @staticmethod
    def _auction_soundtrack_asset_label(asset, available: bool) -> str:
        if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
            label = f"{asset.display_name} — исходный файл"
        else:
            label = asset.display_name
        return label if available else f"⚠ файл недоступен: {label}"

    def _auction_soundtrack_assets(self):
        # media_assets ORDER BY id is the existing deterministic library order.
        # The selected item is the starting point; sequential playback then wraps.
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_MUSIC)

    def _selected_auction_soundtrack_asset(self):
        raw = self.auction_soundtrack_combo.currentData()
        if not str(raw or "").isdigit():
            return None
        asset = self.db.get_media_asset(int(raw))
        if asset is None or asset.category != MEDIA_CATEGORY_MUSIC:
            return None
        return asset

    def _refresh_auction_soundtrack_library(self, selected_asset_id=None) -> None:
        if selected_asset_id is None:
            selected_asset_id = self.db.get_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, "")
        selected_id = (
            int(selected_asset_id)
            if str(selected_asset_id or "").isdigit()
            else None
        )

        self.auction_soundtrack_combo.blockSignals(True)
        self.auction_soundtrack_combo.clear()
        self.auction_soundtrack_combo.addItem("— без soundtrack —", "")
        for asset in self._auction_soundtrack_assets():
            available = media_asset_available(self.db.path.parent, asset)
            self.auction_soundtrack_combo.addItem(
                self._auction_soundtrack_asset_label(asset, available),
                asset.id,
            )
        index = self.auction_soundtrack_combo.findData(selected_id) if selected_id else 0
        self.auction_soundtrack_combo.setCurrentIndex(index if index >= 0 else 0)
        self.auction_soundtrack_combo.blockSignals(False)
        self._refresh_auction_soundtrack_availability()

    def _refresh_auction_soundtrack_availability(self) -> None:
        if not hasattr(self, "auction_soundtrack_combo"):
            return
        asset = self._selected_auction_soundtrack_asset()
        if asset is None:
            self.auction_soundtrack_status.setText("Soundtrack не выбран")
            self.auction_soundtrack_status.setToolTip("")
            self.repair_auction_soundtrack_btn.setVisible(False)
            self.repair_auction_soundtrack_btn.setEnabled(False)
            return

        available = media_asset_available(self.db.path.parent, asset)
        index = self.auction_soundtrack_combo.currentIndex()
        if index >= 0:
            expected = self._auction_soundtrack_asset_label(asset, available)
            if self.auction_soundtrack_combo.itemText(index) != expected:
                self.auction_soundtrack_combo.setItemText(index, expected)

        try:
            resolved = resolve_media_asset_path(self.db.path.parent, asset)
            path_text = str(resolved)
        except (OSError, ValueError):
            path_text = str(asset.external_path or asset.managed_name)
        self.auction_soundtrack_status.setToolTip(path_text)

        needs_repair = asset.storage_mode == MEDIA_STORAGE_EXTERNAL and not available
        if self._auction_audio_runtime_error:
            self.auction_soundtrack_status.setText(self._auction_audio_runtime_error)
        elif self.auction_audio.active:
            current = self.auction_audio.current_source
            prefix = "Пауза" if self.auction_audio.paused else "Воспроизводится"
            self.auction_soundtrack_status.setText(
                f"{prefix}: {current.name if current is not None else asset.display_name}"
            )
        elif available:
            self.auction_soundtrack_status.setText("Доступен")
        elif needs_repair:
            self.auction_soundtrack_status.setText(
                "Файл недоступен — восстановите ссылку или выберите другой soundtrack"
            )
        else:
            self.auction_soundtrack_status.setText(
                "Файл недоступен — добавьте soundtrack заново или выберите другой"
            )
        self.repair_auction_soundtrack_btn.setVisible(needs_repair)
        self.repair_auction_soundtrack_btn.setEnabled(needs_repair)

    def _auction_soundtrack_selection_changed(self, _index: int = -1) -> None:
        asset = self._selected_auction_soundtrack_asset()
        self._auction_audio_runtime_error = ""
        self.db.set_setting(
            AUCTION_SOUNDTRACK_MEDIA_ID_KEY,
            str(asset.id) if asset is not None else "",
        )
        self._refresh_auction_soundtrack_availability()

    def _auction_soundtrack_loop_one_changed(self, enabled: bool) -> None:
        self.db.set_setting(AUCTION_SOUNDTRACK_LOOP_ONE_KEY, "1" if enabled else "0")

    def _auction_soundtrack_volume_changed(self, value: int) -> None:
        normalized = self.auction_audio.set_volume_percent(value)
        self.db.set_setting(AUCTION_SOUNDTRACK_VOLUME_KEY, str(normalized))

    def _auction_soundtrack_mute_changed(self, muted: bool) -> None:
        normalized = self.auction_audio.set_muted(muted)
        self.db.set_setting(AUCTION_SOUNDTRACK_MUTE_KEY, "1" if normalized else "0")

    def _choose_auction_soundtrack_storage_mode(self, source: Path) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Как использовать soundtrack?")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(
            f"Выбран файл:\n{source}\n\nКак In one line должен его использовать?"
        )
        dialog.setInformativeText(
            "«Копировать в программу» создаст управляемую копию в папке "
            "data\\music. «Использовать исходный файл» сохранит ссылку на "
            "оригинал; сам оригинал программа не изменяет и не удаляет."
        )
        copy_button = dialog.addButton(
            "Копировать в программу", QMessageBox.ButtonRole.AcceptRole
        )
        external_button = dialog.addButton(
            "Использовать исходный файл", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is copy_button:
            return MEDIA_STORAGE_MANAGED
        if clicked is external_button:
            return MEDIA_STORAGE_EXTERNAL
        return None

    def _unique_auction_soundtrack_target(self, source: Path) -> Path:
        existing = {
            item.name.casefold()
            for item in self.auction_music_dir.iterdir()
            if item.is_file()
        }
        candidate = self.auction_music_dir / source.name
        counter = 2
        while candidate.name.casefold() in existing:
            candidate = self.auction_music_dir / f"{source.stem} ({counter}){source.suffix}"
            counter += 1
        return candidate

    @staticmethod
    def _copy_auction_soundtrack(source: Path, target: Path) -> Path:
        try:
            shutil.copy2(source, target)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def _start_auction_soundtrack_copy(self, source: Path, target: Path) -> None:
        if self._auction_soundtrack_copy_worker is not None:
            return
        self.add_auction_soundtrack_btn.setEnabled(False)
        self.add_auction_soundtrack_btn.setText("Копирование…")
        worker = FunctionWorker(self._copy_auction_soundtrack, source, target)
        self._auction_soundtrack_copy_worker = worker
        worker.signals.result.connect(self._auction_soundtrack_copy_ready)
        worker.signals.error.connect(self._auction_soundtrack_copy_failed)
        worker.signals.finished.connect(self._auction_soundtrack_copy_finished)
        self.thread_pool.start(worker)

    def _auction_soundtrack_copy_ready(self, target: Path) -> None:
        asset = self.db.ensure_managed_media_asset(
            MEDIA_CATEGORY_MUSIC,
            target.name,
            target.name,
        )
        self.db.set_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
        self._refresh_auction_soundtrack_library(asset.id)

    def _auction_soundtrack_copy_failed(self, exc) -> None:
        QMessageBox.critical(
            self,
            "Ошибка копирования soundtrack",
            f"Не удалось скопировать аудиофайл во внутреннюю библиотеку:\n{exc}",
        )

    def _auction_soundtrack_copy_finished(self) -> None:
        self._auction_soundtrack_copy_worker = None
        self.add_auction_soundtrack_btn.setEnabled(True)
        self.add_auction_soundtrack_btn.setText("Добавить soundtrack…")

    def _import_auction_soundtrack(self) -> None:
        if self._auction_soundtrack_copy_worker is not None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите музыку аукциона",
            "",
            "Аудио (*.mp3 *.wav *.ogg);;Все файлы (*.*)",
        )
        if not path:
            return
        source = Path(path)
        if source.suffix.lower() not in supported_media_extensions(MEDIA_CATEGORY_MUSIC):
            QMessageBox.warning(
                self,
                "Неподдерживаемый формат",
                "Для музыки аукциона поддерживаются MP3, WAV и OGG.",
            )
            return
        if not source.is_file():
            QMessageBox.critical(self, "Ошибка", "Выбранный аудиофайл не найден.")
            return

        self.auction_music_dir.mkdir(parents=True, exist_ok=True)
        storage_mode = self._choose_auction_soundtrack_storage_mode(source)
        if storage_mode is None:
            return
        if storage_mode == MEDIA_STORAGE_EXTERNAL:
            asset = self.db.register_external_media_asset(MEDIA_CATEGORY_MUSIC, source)
            self.db.set_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
            self._refresh_auction_soundtrack_library(asset.id)
            return

        if source.resolve().parent == self.auction_music_dir.resolve():
            asset = self.db.ensure_managed_media_asset(
                MEDIA_CATEGORY_MUSIC,
                source.name,
                source.name,
            )
            self.db.set_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, str(asset.id))
            self._refresh_auction_soundtrack_library(asset.id)
            return

        target = self._unique_auction_soundtrack_target(source)
        self._start_auction_soundtrack_copy(source, target)

    def _repair_auction_soundtrack_reference(self) -> None:
        asset = self._selected_auction_soundtrack_asset()
        if asset is None or asset.storage_mode != MEDIA_STORAGE_EXTERNAL:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Восстановить ссылку на музыку аукциона",
            "",
            "Аудио (*.mp3 *.wav *.ogg);;Все файлы (*.*)",
        )
        if not path:
            return
        source = Path(path)
        if not source.is_file():
            QMessageBox.critical(self, "Ошибка", "Выбранный аудиофайл не найден.")
            return
        try:
            repaired = self.db.update_external_media_asset(asset.id, source)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Ошибка восстановления ссылки",
                f"Не удалось обновить ссылку на soundtrack:\n{exc}",
            )
            return
        self._auction_audio_runtime_error = ""
        self._refresh_auction_soundtrack_library(repaired.id)

    def _resolved_auction_soundtrack_playlist(self) -> tuple[list[Path], list[int], int]:
        selected = self._selected_auction_soundtrack_asset()
        if selected is None or not media_asset_available(self.db.path.parent, selected):
            return [], [], 0
        paths: list[Path] = []
        asset_ids: list[int] = []
        start_index = 0
        for asset in self._auction_soundtrack_assets():
            if not media_asset_available(self.db.path.parent, asset):
                continue
            try:
                path = resolve_media_asset_path(self.db.path.parent, asset)
            except (OSError, ValueError):
                continue
            if asset.id == selected.id:
                start_index = len(paths)
            paths.append(path)
            asset_ids.append(int(asset.id))
        return paths, asset_ids, start_index

    def _start_auction_soundtrack_for_session(self, session: dict | None, *, restart: bool = False) -> None:
        if session is None or str(session.get("mode") or "") != "max_amount":
            return
        status = str(session.get("status") or "")
        if status not in ("running", "paused"):
            return
        session_id = int(session["id"])
        if not restart and self._auction_audio_session_id == session_id:
            if self.auction_audio.active:
                if status == "paused":
                    self.auction_audio.pause()
                else:
                    self.auction_audio.resume()
                self._refresh_auction_soundtrack_availability()
            return

        paths, asset_ids, start_index = self._resolved_auction_soundtrack_playlist()
        self._auction_audio_session_id = session_id
        if not paths:
            self._auction_audio_asset_ids = []
            self.auction_audio.stop(immediate=True)
            self._refresh_browser_audio_snapshot()
            self._refresh_auction_soundtrack_availability()
            return
        try:
            self._auction_audio_runtime_error = ""
            self.auction_audio.start_playlist(
                paths,
                start_index=start_index,
                loop_one=self._saved_auction_soundtrack_loop_one(),
                start_paused=status == "paused",
            )
            # start_playlist() first resets the old transport and can emit
            # stopped(), so align IDs only after the new transport is live.
            self._auction_audio_asset_ids = list(asset_ids)
            self._refresh_browser_audio_snapshot()
        except Exception as exc:
            self._auction_audio_asset_ids = []
            self._auction_audio_error(str(exc))
        self._refresh_auction_soundtrack_availability()

    def _sync_auction_soundtrack_state(self, session: dict | None) -> None:
        if session is None:
            # If lifecycle code already cleared the session id, a normal fade is
            # in progress and must not be truncated by the following UI refresh.
            if self.auction_audio.active and self._auction_audio_session_id is not None:
                self._stop_auction_soundtrack(immediate=True)
            self._auction_audio_session_id = None
            return
        if str(session.get("mode") or "") != "max_amount":
            return
        status = str(session.get("status") or "")
        if status in ("running", "paused"):
            self._start_auction_soundtrack_for_session(session)

    def _stop_auction_soundtrack(self, *, immediate: bool = False) -> None:
        self.auction_audio.stop(immediate=immediate, fade_ms=self.AUCTION_SOUNDTRACK_FADE_MS)
        self._auction_audio_session_id = None
        self._refresh_auction_soundtrack_availability()

    def _auction_audio_track_changed(self, _source: str) -> None:
        self._auction_audio_runtime_error = ""
        self._refresh_browser_audio_snapshot()
        self._refresh_auction_soundtrack_availability()

    def _auction_audio_stopped(self) -> None:
        self._auction_audio_asset_ids = []
        self._refresh_browser_audio_snapshot()
        self._refresh_auction_soundtrack_availability()

    def _auction_audio_error(self, message) -> None:
        self._auction_audio_runtime_error = (
            f"Ошибка воспроизведения — аукцион продолжает работу: {message}"
        )
        if hasattr(self, "auction_soundtrack_status"):
            self.auction_soundtrack_status.setText(self._auction_audio_runtime_error)

    def _set_auction_soundtrack_edit_enabled(self, enabled: bool) -> None:
        if not hasattr(self, "auction_soundtrack_combo"):
            return
        enabled = bool(enabled)
        self.auction_soundtrack_combo.setEnabled(enabled)
        self.auction_soundtrack_loop_one.setEnabled(enabled)
        self.add_auction_soundtrack_btn.setEnabled(
            enabled and self._auction_soundtrack_copy_worker is None
        )
        # Volume and Mute intentionally remain live while the auction is active.
        asset = self._selected_auction_soundtrack_asset()
        repair = bool(
            enabled
            and asset is not None
            and asset.storage_mode == MEDIA_STORAGE_EXTERNAL
            and not media_asset_available(self.db.path.parent, asset)
        )
        self.repair_auction_soundtrack_btn.setVisible(repair)
        self.repair_auction_soundtrack_btn.setEnabled(repair)

    def _update_auction_soundtrack_panel(self, session: dict | None) -> None:
        if not hasattr(self, "auction_soundtrack_widget"):
            return
        if session is None:
            show = str(self.mode_combo.currentData() or "max_amount") == "max_amount"
            editable = True
        else:
            status = str(session.get("status") or "")
            mode = str(session.get("mode") or "")
            wheel_context = bool(
                status == "awaiting_wheel"
                or session.get("wheel_spin_id")
                or mode == "weighted_wheel"
            )
            show = mode == "max_amount" and not wheel_context
            editable = status not in ("running", "paused")

        self._set_visible_state(self.auction_soundtrack_widget, show)
        if show:
            self._refresh_auction_soundtrack_availability()
            self._set_auction_soundtrack_edit_enabled(editable)
        self._sync_auction_soundtrack_state(session)

    def _schedule_wheel_soundtrack(self, wheel_payload: dict) -> None:
        """Schedule audio from the exact authoritative visual animation clock."""
        asset = None
        raw = self.db.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "")
        if str(raw).isdigit():
            asset = self.db.get_media_asset(int(raw))
        if asset is None or asset.category != MEDIA_CATEGORY_WHEEL_JINGLES:
            return
        if not media_asset_available(self.db.path.parent, asset):
            self._refresh_wheel_soundtrack_availability()
            return

        animation = (wheel_payload or {}).get("animation") or {}
        started_at = animation.get("started_at")
        duration_ms = int(animation.get("duration_ms") or 0)
        if not started_at or duration_ms <= 0:
            return
        try:
            source = resolve_media_asset_path(self.db.path.parent, asset)
            self._wheel_audio_runtime_error = ""
            self._wheel_audio_asset_id = int(asset.id)
            self.wheel_audio.schedule_loop(
                source,
                started_at=str(started_at),
                duration_ms=duration_ms,
                fade_ms=self.WHEEL_SOUNDTRACK_FADE_MS,
            )
        except Exception as exc:
            self._wheel_audio_error(str(exc))

    def _stop_wheel_soundtrack(self, *, immediate: bool = False) -> None:
        self.wheel_audio.stop(immediate=immediate, fade_ms=self.WHEEL_SOUNDTRACK_FADE_MS)

    def shutdown_audio(self) -> None:
        """Release application audio promptly during MainWindow shutdown."""
        self._browser_audio_snapshot_timer.stop()
        self.auction_audio.stop(immediate=True)
        self.wheel_audio.stop(immediate=True)
        self._release_auction_audio_owner()

    def _wheel_audio_error(self, message) -> None:
        self._wheel_audio_runtime_error = f"Ошибка воспроизведения — колесо продолжает работу: {message}"
        if hasattr(self, "wheel_soundtrack_status"):
            self.wheel_soundtrack_status.setText(self._wheel_audio_runtime_error)

    def _set_wheel_soundtrack_edit_enabled(self, enabled: bool) -> None:
        if not hasattr(self, "wheel_soundtrack_combo"):
            return
        enabled = bool(enabled)
        self.wheel_soundtrack_combo.setEnabled(enabled)
        self.add_wheel_soundtrack_btn.setEnabled(
            enabled and self._wheel_soundtrack_copy_worker is None
        )
        # Volume and Mute intentionally remain live during playback.
        asset = self._selected_wheel_soundtrack_asset()
        repair = bool(
            enabled
            and asset is not None
            and asset.storage_mode == MEDIA_STORAGE_EXTERNAL
            and not media_asset_available(self.db.path.parent, asset)
        )
        self.repair_wheel_soundtrack_btn.setVisible(repair)
        self.repair_wheel_soundtrack_btn.setEnabled(repair)
