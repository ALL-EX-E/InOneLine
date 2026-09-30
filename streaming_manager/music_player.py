from __future__ import annotations

import base64
import json
import random
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from mutagen import File as MutagenFile

from .constants import (
    MUSIC_PLAYER_CURRENT_MEDIA_ID_KEY,
    MUSIC_PLAYER_MUTE_DEFAULT,
    MUSIC_PLAYER_MUTE_KEY,
    MUSIC_PLAYER_ORDER_ALPHABETICAL,
    MUSIC_PLAYER_ORDER_MODE_DEFAULT,
    MUSIC_PLAYER_ORDER_MODE_KEY,
    MUSIC_PLAYER_ORDER_SHUFFLE,
    MUSIC_PLAYER_OUTPUT_MODE_APPLICATION,
    MUSIC_PLAYER_OUTPUT_MODE_DEFAULT,
    MUSIC_PLAYER_OUTPUT_MODE_KEY,
    MUSIC_PLAYER_OUTPUT_MODE_OBS,
    MUSIC_PLAYER_POSITION_MS_KEY,
    MUSIC_PLAYER_QUEUE_KEY,
    MUSIC_PLAYER_REPEAT_DEFAULT,
    MUSIC_PLAYER_REPEAT_KEY,
    MUSIC_PLAYER_VOLUME_DEFAULT,
    MUSIC_PLAYER_VOLUME_KEY,
)
from .media import (
    MEDIA_CATEGORY_MUSIC,
    MediaAsset,
    media_asset_available,
    resolve_media_asset_path,
)


PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"


class MusicPlayerController(QObject):
    """Authoritative D26 music transport shared by local UI and OBS renderer."""

    stateChanged = Signal()
    libraryChanged = Signal()
    trackChanged = Signal()
    positionChanged = Signal(int, int)
    playbackError = Signal(str)

    def __init__(self, db, audio_coordinator=None, parent: QObject | None = None):
        super().__init__(parent)
        self.db = db
        self.audio_coordinator = audio_coordinator
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Once)
        self.player.errorOccurred.connect(self._on_error)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        self._assets: dict[int, MediaAsset] = {}
        self._metadata_cache: dict[tuple[int, int, int], dict[str, object]] = {}
        self._cover_cache: dict[int, tuple[str, bytes] | None] = {}
        self._cache_lock = threading.RLock()
        self._browser_lock = threading.RLock()
        self._browser_snapshot: dict[str, object] = {}

        self._current_media_id: int | None = None
        self._queue: list[int] = []
        self._order_mode = self._saved_order_mode()
        self._repeat = self._saved_bool(MUSIC_PLAYER_REPEAT_KEY, MUSIC_PLAYER_REPEAT_DEFAULT)
        self._output_mode = self._saved_output_mode()
        self._volume_percent = self._saved_int(
            MUSIC_PLAYER_VOLUME_KEY, MUSIC_PLAYER_VOLUME_DEFAULT, 0, 100
        )
        self._muted = self._saved_bool(MUSIC_PLAYER_MUTE_KEY, MUSIC_PLAYER_MUTE_DEFAULT)
        self._desired_state = PLAYER_PAUSE
        self._suppressed = False
        self._revision = 0
        self._event_serial = 0
        self._pending_new_track_event = False
        self._pending_seek_ms: int | None = None
        self._loading_source = False
        self._shutdown = False

        self.audio_output.setVolume(self._volume_percent / 100.0)
        self._apply_local_audio_route()

        self._persist_timer = QTimer(self)
        self._persist_timer.setInterval(1500)
        self._persist_timer.timeout.connect(self._persist_position)
        self._persist_timer.start()

        self._snapshot_timer = QTimer(self)
        self._snapshot_timer.setInterval(100)
        self._snapshot_timer.timeout.connect(self._refresh_browser_snapshot)
        self._snapshot_timer.start()

        self.refresh_library(emit=False)
        self._restore_saved_current()
        self._refresh_browser_snapshot()

        if self.audio_coordinator is not None:
            self.audio_coordinator.register_music_player(
                self.snapshot_for_external,
                self.pause_for_external,
                self.restore_from_external,
            )

    @property
    def desired_state(self) -> str:
        return self._desired_state

    @property
    def current_media_id(self) -> int | None:
        return self._current_media_id

    @property
    def queue(self) -> list[int]:
        return list(self._queue)

    @property
    def order_mode(self) -> str:
        return self._order_mode

    @property
    def repeat_current(self) -> bool:
        return self._repeat

    @property
    def output_mode(self) -> str:
        return self._output_mode

    @property
    def volume_percent(self) -> int:
        return self._volume_percent

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    @property
    def position_ms(self) -> int:
        try:
            return max(0, int(self.player.position()))
        except Exception:
            return 0

    @property
    def duration_ms(self) -> int:
        try:
            return max(0, int(self.player.duration()))
        except Exception:
            return 0

    def _saved_bool(self, key: str, default: bool) -> bool:
        return str(self.db.get_setting(key, "1" if default else "0")).strip() == "1"

    def _saved_int(self, key: str, default: int, low: int, high: int) -> int:
        try:
            value = int(self.db.get_setting(key, str(default)))
        except (TypeError, ValueError):
            value = default
        return max(low, min(high, value))

    def _saved_order_mode(self) -> str:
        value = str(
            self.db.get_setting(MUSIC_PLAYER_ORDER_MODE_KEY, MUSIC_PLAYER_ORDER_MODE_DEFAULT)
            or MUSIC_PLAYER_ORDER_MODE_DEFAULT
        )
        return value if value in {MUSIC_PLAYER_ORDER_ALPHABETICAL, MUSIC_PLAYER_ORDER_SHUFFLE} else MUSIC_PLAYER_ORDER_MODE_DEFAULT

    def _saved_output_mode(self) -> str:
        value = str(
            self.db.get_setting(MUSIC_PLAYER_OUTPUT_MODE_KEY, MUSIC_PLAYER_OUTPUT_MODE_DEFAULT)
            or MUSIC_PLAYER_OUTPUT_MODE_DEFAULT
        )
        return value if value in {MUSIC_PLAYER_OUTPUT_MODE_APPLICATION, MUSIC_PLAYER_OUTPUT_MODE_OBS} else MUSIC_PLAYER_OUTPUT_MODE_DEFAULT

    def _available_assets(self) -> list[MediaAsset]:
        assets = self.db.sync_managed_media_category(MEDIA_CATEGORY_MUSIC)
        return [
            asset for asset in assets
            if media_asset_available(self.db.path.parent, asset)
        ]

    def refresh_library(self, *, emit: bool = True) -> None:
        old_ids = set(self._assets)
        assets = self._available_assets()
        self._assets = {int(asset.id): asset for asset in assets}
        ids = list(self._assets)
        saved_queue: list[int] = []
        try:
            raw = json.loads(self.db.get_setting(MUSIC_PLAYER_QUEUE_KEY, "[]") or "[]")
            if isinstance(raw, list):
                saved_queue = [int(value) for value in raw if str(value).isdigit()]
        except (TypeError, ValueError, json.JSONDecodeError):
            saved_queue = []

        if self._order_mode == MUSIC_PLAYER_ORDER_ALPHABETICAL:
            self._queue = sorted(
                ids,
                key=lambda media_id: (
                    self._assets[media_id].display_name.casefold(),
                    media_id,
                ),
            )
        else:
            kept = [media_id for media_id in saved_queue if media_id in self._assets]
            missing = [media_id for media_id in ids if media_id not in kept]
            random.shuffle(missing)
            self._queue = kept + missing
            if not self._queue and ids:
                self._queue = list(ids)
                random.shuffle(self._queue)

        if self._current_media_id is not None and self._current_media_id not in self._assets:
            replacement = self._queue[0] if self._queue else None
            self._current_media_id = replacement
            self._desired_state = PLAYER_PAUSE
            self._pending_new_track_event = bool(replacement)
            self._load_current(position_ms=0, play=False)
        self._persist_queue()
        if emit and (old_ids != set(self._assets) or True):
            self.libraryChanged.emit()
            self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def assets_in_queue(self) -> list[MediaAsset]:
        return [self._assets[mid] for mid in self._queue if mid in self._assets]

    def asset_for_id(self, media_id: int | None) -> MediaAsset | None:
        if media_id is None:
            return None
        return self._assets.get(int(media_id))

    def current_asset(self) -> MediaAsset | None:
        return self.asset_for_id(self._current_media_id)

    def _restore_saved_current(self) -> None:
        raw_id = str(self.db.get_setting(MUSIC_PLAYER_CURRENT_MEDIA_ID_KEY, "") or "")
        media_id = int(raw_id) if raw_id.isdigit() and int(raw_id) in self._assets else None
        if media_id is None and self._queue:
            media_id = self._queue[0]
        self._current_media_id = media_id
        position = self._saved_int(MUSIC_PLAYER_POSITION_MS_KEY, 0, 0, 2_147_483_647)
        # Never auto-play on application launch.
        self._desired_state = PLAYER_PAUSE
        self._pending_new_track_event = False
        if media_id is not None:
            self._load_current(position_ms=position, play=False)
        self._persist_state()

    def _path_for_asset(self, asset: MediaAsset) -> Path:
        return resolve_media_asset_path(self.db.path.parent, asset)

    def _load_current(self, *, position_ms: int = 0, play: bool | None = None) -> None:
        asset = self.current_asset()
        if asset is None:
            self.player.stop()
            self.player.setSource(QUrl())
            self._pending_seek_ms = None
            self.trackChanged.emit()
            self.stateChanged.emit()
            return
        try:
            path = self._path_for_asset(asset)
        except (OSError, ValueError) as exc:
            self.playbackError.emit(str(exc))
            return
        self._loading_source = True
        self._pending_seek_ms = max(0, int(position_ms))
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.setLoops(QMediaPlayer.Loops.Once)
        self._loading_source = False
        if play is None:
            play = self._desired_state == PLAYER_PLAY
        if play and not self._suppressed:
            self.player.play()
        else:
            self.player.pause()
        self._apply_local_audio_route()
        self.trackChanged.emit()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def _apply_pending_seek(self) -> None:
        if self._pending_seek_ms is None:
            return
        try:
            self.player.setPosition(max(0, int(self._pending_seek_ms)))
        finally:
            self._pending_seek_ms = None

    def _apply_transport_intent(self) -> None:
        if self._current_media_id is None:
            return
        if self._suppressed:
            self.player.pause()
            return
        if self._desired_state == PLAYER_PLAY:
            self.player.play()
        elif self._desired_state == PLAYER_PAUSE:
            self.player.pause()
        else:
            self.player.stop()
            self.player.setPosition(0)
        self._apply_local_audio_route()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def _mark_user_change(self) -> None:
        self._revision += 1

    def _trigger_new_track_event(self) -> None:
        self._event_serial += 1
        self._pending_new_track_event = False

    def select_media(self, media_id: int, *, play: bool = True) -> None:
        media_id = int(media_id)
        if media_id not in self._assets:
            return
        changed = media_id != self._current_media_id
        self._current_media_id = media_id
        self._desired_state = PLAYER_PLAY if play else PLAYER_PAUSE
        self._pending_new_track_event = not play
        self._mark_user_change()
        self._load_current(position_ms=0, play=play)
        if play:
            self._trigger_new_track_event()
        self._persist_state()
        if changed:
            self.trackChanged.emit()
        self.stateChanged.emit()

    def play_pause(self) -> None:
        if self._current_media_id is None:
            if not self._queue:
                return
            self._current_media_id = self._queue[0]
            self._pending_new_track_event = True
            self._load_current(position_ms=0, play=False)

        if self._desired_state == PLAYER_PLAY:
            self._desired_state = PLAYER_PAUSE
        else:
            from_stop = self._desired_state == PLAYER_STOP
            if from_stop:
                self.player.setPosition(0)
            self._desired_state = PLAYER_PLAY
            if from_stop or self._pending_new_track_event:
                self._trigger_new_track_event()
        self._mark_user_change()
        self._apply_transport_intent()
        self._persist_state()

    def stop(self) -> None:
        if self._current_media_id is None:
            return
        self._desired_state = PLAYER_STOP
        self._pending_new_track_event = True
        self._mark_user_change()
        self.player.stop()
        self.player.setPosition(0)
        self._apply_local_audio_route()
        self._persist_state()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def seek(self, position_ms: int) -> None:
        if self._current_media_id is None:
            return
        duration = self.duration_ms
        position = max(0, int(position_ms))
        if duration > 0:
            position = min(position, duration)
        self.player.setPosition(position)
        self._mark_user_change()
        self._persist_state()

    def _queue_index(self) -> int:
        try:
            return self._queue.index(int(self._current_media_id))
        except (ValueError, TypeError):
            return -1

    def next_track(self, *, automatic: bool = False) -> None:
        if not self._queue:
            return
        desired = self._desired_state
        index = self._queue_index()
        if self._order_mode == MUSIC_PLAYER_ORDER_SHUFFLE and index == len(self._queue) - 1:
            previous = self._current_media_id
            self._queue = list(self._assets)
            random.shuffle(self._queue)
            if len(self._queue) > 1 and self._queue[0] == previous:
                self._queue[0], self._queue[1] = self._queue[1], self._queue[0]
            index = -1
            self._persist_queue()
            self.libraryChanged.emit()
        next_index = 0 if index < 0 else (index + 1) % len(self._queue)
        self._change_track_preserving_state(self._queue[next_index], desired, automatic=automatic)

    def previous_track(self) -> None:
        if not self._queue:
            return
        desired = self._desired_state
        index = self._queue_index()
        previous_index = len(self._queue) - 1 if index < 0 else (index - 1) % len(self._queue)
        self._change_track_preserving_state(self._queue[previous_index], desired, automatic=False)

    def _change_track_preserving_state(self, media_id: int, desired: str, *, automatic: bool) -> None:
        self._current_media_id = int(media_id)
        self._desired_state = desired
        should_play = desired == PLAYER_PLAY
        self._pending_new_track_event = not should_play
        if not automatic:
            self._mark_user_change()
        self._load_current(position_ms=0, play=should_play)
        if should_play:
            self._trigger_new_track_event()
        self._persist_state()
        self.trackChanged.emit()
        self.stateChanged.emit()

    def set_order_mode(self, mode: str) -> None:
        mode = str(mode)
        if mode not in {MUSIC_PLAYER_ORDER_ALPHABETICAL, MUSIC_PLAYER_ORDER_SHUFFLE}:
            return
        if mode == self._order_mode:
            return
        current = self._current_media_id
        self._order_mode = mode
        if mode == MUSIC_PLAYER_ORDER_ALPHABETICAL:
            self._queue = sorted(
                self._assets,
                key=lambda media_id: (
                    self._assets[media_id].display_name.casefold(),
                    media_id,
                ),
            )
        else:
            self._queue = list(self._assets)
            random.shuffle(self._queue)
            if current in self._queue:
                self._queue.remove(current)
                self._queue.insert(0, current)
        self.db.set_setting(MUSIC_PLAYER_ORDER_MODE_KEY, mode)
        self._persist_queue()
        self.libraryChanged.emit()
        self.stateChanged.emit()

    def set_repeat_current(self, enabled: bool) -> None:
        self._repeat = bool(enabled)
        self.db.set_setting(MUSIC_PLAYER_REPEAT_KEY, "1" if self._repeat else "0")
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def set_output_mode(self, mode: str) -> None:
        mode = str(mode)
        if mode not in {MUSIC_PLAYER_OUTPUT_MODE_APPLICATION, MUSIC_PLAYER_OUTPUT_MODE_OBS}:
            return
        self._output_mode = mode
        self.db.set_setting(MUSIC_PLAYER_OUTPUT_MODE_KEY, mode)
        self._apply_local_audio_route()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def set_volume_percent(self, value: int) -> int:
        self._volume_percent = max(0, min(100, int(value)))
        self.audio_output.setVolume(self._volume_percent / 100.0)
        self.db.set_setting(MUSIC_PLAYER_VOLUME_KEY, str(self._volume_percent))
        self.stateChanged.emit()
        self._refresh_browser_snapshot()
        return self._volume_percent

    def set_muted(self, muted: bool) -> bool:
        self._muted = bool(muted)
        self.db.set_setting(MUSIC_PLAYER_MUTE_KEY, "1" if self._muted else "0")
        self._apply_local_audio_route()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()
        return self._muted

    def _apply_local_audio_route(self) -> None:
        self.audio_output.setVolume(self._volume_percent / 100.0)
        local_silent = (
            self._muted
            or self._suppressed
            or self._output_mode == MUSIC_PLAYER_OUTPUT_MODE_OBS
        )
        self.audio_output.setMuted(local_silent)

    def snapshot_for_external(self) -> dict[str, object]:
        return {
            "revision": self._revision,
            "media_id": self._current_media_id,
            "position_ms": self.position_ms,
            "desired_state": self._desired_state,
        }

    def pause_for_external(self) -> None:
        if self._suppressed:
            return
        self._suppressed = True
        self.player.pause()
        self._apply_local_audio_route()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def restore_from_external(self, snapshot: dict[str, object] | None) -> None:
        if not self._suppressed:
            return
        self._suppressed = False
        if isinstance(snapshot, dict) and int(snapshot.get("revision") or -1) == self._revision:
            media_id = snapshot.get("media_id")
            if media_id is not None and int(media_id) in self._assets and int(media_id) != self._current_media_id:
                self._current_media_id = int(media_id)
                self._desired_state = str(snapshot.get("desired_state") or PLAYER_PAUSE)
                self._load_current(
                    position_ms=int(snapshot.get("position_ms") or 0),
                    play=False,
                )
        self._apply_local_audio_route()
        self._apply_transport_intent()
        self.stateChanged.emit()
        self._refresh_browser_snapshot()

    def metadata_for_asset(self, media_id: int | None) -> dict[str, object]:
        asset = self.asset_for_id(media_id)
        if asset is None:
            return {"title": "", "artist": "", "display_title": "", "has_cover": False}
        try:
            path = self._path_for_asset(asset)
            stat = path.stat()
            key = (int(asset.id), int(stat.st_mtime_ns), int(stat.st_size))
        except OSError:
            return {"title": "", "artist": "", "display_title": asset.display_name, "has_cover": False}
        cached = self._metadata_cache.get(key)
        if cached is not None:
            return dict(cached)

        title = ""
        artist = ""
        try:
            easy = MutagenFile(path, easy=True)
            tags = getattr(easy, "tags", None) or {}
            title_value = tags.get("title") if hasattr(tags, "get") else None
            artist_value = tags.get("artist") if hasattr(tags, "get") else None
            if title_value:
                title = str(title_value[0] if isinstance(title_value, (list, tuple)) else title_value).strip()
            if artist_value:
                artist = str(artist_value[0] if isinstance(artist_value, (list, tuple)) else artist_value).strip()
        except Exception:
            pass

        cover = self._extract_cover(path)
        with self._cache_lock:
            self._cover_cache[int(asset.id)] = cover
        display_title = f"{artist} - {title}" if artist and title else asset.display_name
        result = {
            "title": title,
            "artist": artist,
            "display_title": display_title,
            "has_cover": cover is not None,
        }
        self._metadata_cache[key] = dict(result)
        return result

    def _extract_cover(self, path: Path) -> tuple[str, bytes] | None:
        try:
            raw = MutagenFile(path, easy=False)
            if raw is None:
                return None
            pictures = getattr(raw, "pictures", None)
            if pictures:
                pic = pictures[0]
                data = bytes(getattr(pic, "data", b""))
                if data:
                    return str(getattr(pic, "mime", "") or "image/jpeg"), data

            tags = getattr(raw, "tags", None)
            if tags is None:
                return None
            values = list(tags.values()) if hasattr(tags, "values") else []
            for value in values:
                data = getattr(value, "data", None)
                if data and value.__class__.__name__.upper().startswith("APIC"):
                    return str(getattr(value, "mime", "") or "image/jpeg"), bytes(data)

            if hasattr(tags, "get"):
                block = tags.get("metadata_block_picture")
                if block:
                    from mutagen.flac import Picture
                    encoded = block[0] if isinstance(block, (list, tuple)) else block
                    pic = Picture(base64.b64decode(encoded))
                    if pic.data:
                        return str(pic.mime or "image/jpeg"), bytes(pic.data)
                coverart = tags.get("coverart")
                if coverart:
                    encoded = coverart[0] if isinstance(coverart, (list, tuple)) else coverart
                    data = base64.b64decode(encoded)
                    mime_value = tags.get("coverartmime")
                    mime = (
                        mime_value[0]
                        if isinstance(mime_value, (list, tuple)) and mime_value
                        else mime_value
                    )
                    if data:
                        return str(mime or "image/jpeg"), data
        except Exception:
            return None
        return None

    def cover_bytes(self, media_id: int) -> tuple[str, bytes] | None:
        media_id = int(media_id)
        with self._cache_lock:
            if media_id in self._cover_cache:
                return self._cover_cache[media_id]
        self.metadata_for_asset(media_id)
        with self._cache_lock:
            return self._cover_cache.get(media_id)

    def _on_media_status(self, status) -> None:
        if status in {
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        }:
            self._apply_pending_seek()
            if not self._suppressed:
                if self._desired_state == PLAYER_PLAY:
                    self.player.play()
                elif self._desired_state == PLAYER_PAUSE:
                    self.player.pause()
            return
        if status != QMediaPlayer.MediaStatus.EndOfMedia or self._shutdown:
            return
        if self._desired_state != PLAYER_PLAY:
            return
        if self._repeat:
            self.player.setPosition(0)
            if not self._suppressed:
                self.player.play()
            return
        self.next_track(automatic=True)

    def _on_position_changed(self, position: int) -> None:
        self.positionChanged.emit(max(0, int(position)), self.duration_ms)

    def _on_duration_changed(self, duration: int) -> None:
        self.positionChanged.emit(self.position_ms, max(0, int(duration)))

    def _on_error(self, _error, error_string: str = "") -> None:
        message = str(error_string or self.player.errorString() or "Ошибка воспроизведения аудио")
        self.playbackError.emit(message)

    def _persist_queue(self) -> None:
        self.db.set_setting(MUSIC_PLAYER_QUEUE_KEY, json.dumps(self._queue, ensure_ascii=False))

    def _persist_position(self) -> None:
        if self._shutdown:
            return
        self.db.set_setting(MUSIC_PLAYER_POSITION_MS_KEY, str(self.position_ms))
        self._refresh_browser_snapshot()

    def _persist_state(self) -> None:
        self.db.set_settings_bulk(
            {
                MUSIC_PLAYER_CURRENT_MEDIA_ID_KEY: (
                    str(self._current_media_id) if self._current_media_id is not None else ""
                ),
                MUSIC_PLAYER_POSITION_MS_KEY: str(self.position_ms),
                MUSIC_PLAYER_ORDER_MODE_KEY: self._order_mode,
                MUSIC_PLAYER_QUEUE_KEY: json.dumps(self._queue, ensure_ascii=False),
                MUSIC_PLAYER_REPEAT_KEY: "1" if self._repeat else "0",
                MUSIC_PLAYER_OUTPUT_MODE_KEY: self._output_mode,
                MUSIC_PLAYER_VOLUME_KEY: str(self._volume_percent),
                MUSIC_PLAYER_MUTE_KEY: "1" if self._muted else "0",
            }
        )
        self._refresh_browser_snapshot()

    def _refresh_browser_snapshot(self) -> None:
        asset = self.current_asset()
        metadata = self.metadata_for_asset(asset.id) if asset is not None else {
            "title": "",
            "artist": "",
            "display_title": "",
            "has_cover": False,
        }
        browser_should_play = bool(
            asset is not None
            and self._desired_state == PLAYER_PLAY
            and not self._suppressed
        )
        snapshot = {
            "active": bool(asset is not None and self._desired_state != PLAYER_STOP),
            "suppressed": bool(self._suppressed),
            "owner": "auction" if self._suppressed else "music_player",
            "media_id": int(asset.id) if asset is not None else None,
            "url": f"/media/{int(asset.id)}" if asset is not None else "",
            "cover_url": (
                f"/music-cover/{int(asset.id)}"
                if asset is not None and bool(metadata.get("has_cover"))
                else "/music-placeholder"
            ),
            "has_cover": bool(metadata.get("has_cover")),
            "filename": asset.display_name if asset is not None else "",
            "title": str(metadata.get("title") or ""),
            "artist": str(metadata.get("artist") or ""),
            "display_title": str(metadata.get("display_title") or ""),
            "desired_state": self._desired_state,
            "playing": browser_should_play,
            "paused": bool(asset is not None and self._desired_state == PLAYER_PAUSE),
            "stopped": bool(self._desired_state == PLAYER_STOP),
            "position_ms": self.position_ms,
            "duration_ms": self.duration_ms,
            "gain": max(0.0, min(1.0, self._volume_percent / 100.0)),
            "muted": bool(self._muted),
            "output_mode": self._output_mode,
            "browser_audible": bool(
                browser_should_play
                and self._output_mode == MUSIC_PLAYER_OUTPUT_MODE_OBS
                and not self._muted
            ),
            "event_serial": int(self._event_serial),
        }
        with self._browser_lock:
            self._browser_snapshot = snapshot

    def browser_state(self) -> dict[str, object]:
        with self._browser_lock:
            return dict(self._browser_snapshot)

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self._persist_timer.stop()
        self._snapshot_timer.stop()
        self._persist_state()
        self.player.stop()
        self.player.setSource(QUrl())
        if self.audio_coordinator is not None:
            self.audio_coordinator.unregister_music_player()
