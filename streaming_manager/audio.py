from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class ApplicationAudioEngine(QObject):
    """Application-owned local audio playback with scheduled loop + fade.

    The engine deliberately has no knowledge of auctions, RNG, OBS, or media
    metadata.  Callers resolve one safe local file path and schedule a playback
    window.  Playback failure is reported through a signal and never raises
    into the wheel/business lifecycle.
    """

    playbackError = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.errorOccurred.connect(self._handle_error)

        self._volume_percent = 100
        self._muted = False
        self._fade_factor = 1.0
        self._fade_started_monotonic: float | None = None
        self._fade_duration_ms = 0
        self._scheduled_source: Path | None = None
        self._last_scheduled_source: Path | None = None
        self._window_active = False

        self._start_timer = QTimer(self)
        self._start_timer.setSingleShot(True)
        self._start_timer.timeout.connect(self._start_now)

        self._finish_timer = QTimer(self)
        self._finish_timer.setSingleShot(True)
        self._finish_timer.timeout.connect(self._begin_fade)

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(30)
        self._fade_timer.timeout.connect(self._advance_fade)

        self._apply_gain()

    @property
    def scheduled_source(self) -> Path | None:
        return self._scheduled_source

    @property
    def last_scheduled_source(self) -> Path | None:
        return self._last_scheduled_source

    @property
    def window_active(self) -> bool:
        return bool(self._window_active)

    @property
    def volume_percent(self) -> int:
        return int(self._volume_percent)

    @property
    def muted(self) -> bool:
        return bool(self._muted)

    def set_volume_percent(self, value: int) -> int:
        self._volume_percent = max(0, min(100, int(value)))
        self._apply_gain()
        return self._volume_percent

    def set_muted(self, muted: bool) -> bool:
        self._muted = bool(muted)
        self.audio_output.setMuted(self._muted)
        return self._muted

    def schedule_loop(
        self,
        source: str | Path,
        *,
        started_at: str | datetime,
        duration_ms: int,
        fade_ms: int = 600,
    ) -> None:
        """Loop ``source`` for one authoritative runtime window.

        ``started_at`` is the same UTC timestamp used by the visual wheel.
        Fade starts only after the visual spin duration has elapsed.
        """
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(path)

        if isinstance(started_at, datetime):
            start_dt = started_at
        else:
            start_dt = datetime.fromisoformat(str(started_at))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        else:
            start_dt = start_dt.astimezone(timezone.utc)

        self.stop(immediate=True)
        self._scheduled_source = path.resolve(strict=False)
        self._last_scheduled_source = self._scheduled_source
        self._window_active = True
        self._fade_factor = 1.0
        self._fade_duration_ms = max(0, int(fade_ms))
        self._apply_gain()

        now_dt = datetime.now(timezone.utc)
        duration_ms = max(1, int(duration_ms))
        finish_dt = start_dt + timedelta(milliseconds=duration_ms)
        delay_ms = max(
            0,
            int(round((start_dt - now_dt).total_seconds() * 1000.0)),
        )
        finish_delay_ms = max(
            0,
            int(round((finish_dt - now_dt).total_seconds() * 1000.0)),
        )
        if finish_delay_ms <= 0:
            self.stop(immediate=True)
            return
        self._start_timer.start(delay_ms)
        self._finish_timer.start(finish_delay_ms)

    def stop(self, *, immediate: bool = False, fade_ms: int = 250) -> None:
        self._start_timer.stop()
        self._finish_timer.stop()
        if immediate or not self._window_active:
            self._fade_timer.stop()
            self.player.stop()
            # QMediaPlayer.stop() does not necessarily unload the current media.
            # In particular, the Windows FFmpeg backend may keep an external
            # soundtrack file handle open until the source itself is cleared.
            # Empty the source whenever playback is finished/stopped so managed
            # or external files can be moved/repaired immediately afterwards.
            self.player.setSource(QUrl())
            self._window_active = False
            self._scheduled_source = None
            self._fade_started_monotonic = None
            self._fade_factor = 1.0
            self._apply_gain()
            return

        self._fade_duration_ms = max(0, int(fade_ms))
        self._begin_fade()

    def _start_now(self) -> None:
        if not self._window_active or self._scheduled_source is None:
            return
        try:
            self.player.setSource(QUrl.fromLocalFile(str(self._scheduled_source)))
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
            self.player.play()
        except Exception as exc:  # backend/runtime failures must stay non-fatal
            self._handle_error(None, str(exc))

    def _begin_fade(self) -> None:
        if not self._window_active:
            return
        if self._fade_duration_ms <= 0:
            self.stop(immediate=True)
            return
        if self._fade_timer.isActive():
            return
        self._fade_started_monotonic = time.perf_counter()
        self._fade_timer.start()

    def _advance_fade(self) -> None:
        if self._fade_started_monotonic is None or self._fade_duration_ms <= 0:
            self.stop(immediate=True)
            return
        elapsed_ms = (time.perf_counter() - self._fade_started_monotonic) * 1000.0
        progress = min(1.0, max(0.0, elapsed_ms / self._fade_duration_ms))
        self._fade_factor = 1.0 - progress
        self._apply_gain()
        if progress >= 1.0:
            self.stop(immediate=True)

    def _apply_gain(self) -> None:
        base = max(0.0, min(1.0, self._volume_percent / 100.0))
        self.audio_output.setVolume(max(0.0, min(1.0, base * self._fade_factor)))
        self.audio_output.setMuted(self._muted)

    def _handle_error(self, _error, error_string: str = "") -> None:
        message = str(error_string or self.player.errorString() or "Ошибка воспроизведения аудио")
        # Reset only the audio window.  The caller's wheel/RNG state is untouched.
        self.stop(immediate=True)
        self.playbackError.emit(message)

class ApplicationPlaylistAudioEngine(QObject):
    """Application-owned playlist playback for the authoritative auction timer.

    Unlike :class:`ApplicationAudioEngine`, this engine is not scheduled to a
    fixed visual window.  The auction lifecycle explicitly starts, pauses,
    resumes and fades it.  Playlist state is deliberately local to the running
    application; a full application restart begins again at the configured
    starting track, matching the accepted Timer Music contract.
    """

    playbackError = Signal(str)
    trackChanged = Signal(str)
    stopped = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self._handle_error)
        self.player.mediaStatusChanged.connect(self._handle_media_status)

        self._volume_percent = 100
        self._muted = False
        self._fade_factor = 1.0
        self._fade_started_monotonic: float | None = None
        self._fade_duration_ms = 0
        self._playlist: list[Path] = []
        self._current_index = 0
        self._loop_one = False
        self._active = False
        self._paused = False
        self._stopping = False

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(30)
        self._fade_timer.timeout.connect(self._advance_fade)
        self._apply_gain()

    @property
    def active(self) -> bool:
        return bool(self._active)

    @property
    def paused(self) -> bool:
        return bool(self._paused)

    @property
    def volume_percent(self) -> int:
        return int(self._volume_percent)

    @property
    def muted(self) -> bool:
        return bool(self._muted)

    @property
    def loop_one(self) -> bool:
        return bool(self._loop_one)

    @property
    def current_source(self) -> Path | None:
        if not self._playlist or not (0 <= self._current_index < len(self._playlist)):
            return None
        return self._playlist[self._current_index]

    @property
    def position_ms(self) -> int:
        try:
            return max(0, int(self.player.position()))
        except Exception:
            return 0

    def set_volume_percent(self, value: int) -> int:
        self._volume_percent = max(0, min(100, int(value)))
        self._apply_gain()
        return self._volume_percent

    def set_muted(self, muted: bool) -> bool:
        self._muted = bool(muted)
        self.audio_output.setMuted(self._muted)
        return self._muted

    def start_playlist(
        self,
        sources: list[str | Path] | tuple[str | Path, ...],
        *,
        start_index: int = 0,
        loop_one: bool = False,
        start_paused: bool = False,
    ) -> None:
        resolved: list[Path] = []
        for source in sources:
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(path)
            resolved.append(path.resolve(strict=False))
        if not resolved:
            raise ValueError("Playlist is empty")

        self.stop(immediate=True)
        self._playlist = resolved
        self._current_index = max(0, min(len(resolved) - 1, int(start_index)))
        self._loop_one = bool(loop_one)
        self._active = True
        self._paused = bool(start_paused)
        self._stopping = False
        self._fade_factor = 1.0
        self._apply_gain()
        self._load_current(play=not self._paused)

    def pause(self) -> None:
        if not self._active or self._paused:
            return
        self.player.pause()
        self._paused = True

    def resume(self) -> None:
        if not self._active or not self._paused or self._stopping:
            return
        self.player.play()
        self._paused = False

    def stop(self, *, immediate: bool = False, fade_ms: int = 600) -> None:
        if immediate or not self._active or self._paused:
            self._reset_player()
            return
        self._fade_duration_ms = max(0, int(fade_ms))
        if self._fade_duration_ms <= 0:
            self._reset_player()
            return
        if self._fade_timer.isActive():
            return
        self._stopping = True
        self._fade_started_monotonic = time.perf_counter()
        self._fade_timer.start()

    def _load_current(self, *, play: bool) -> None:
        source = self.current_source
        if source is None:
            self._reset_player()
            return
        try:
            self.player.setSource(QUrl.fromLocalFile(str(source)))
            self.player.setLoops(
                QMediaPlayer.Loops.Infinite
                if self._loop_one
                else QMediaPlayer.Loops.Once
            )
            self.trackChanged.emit(str(source))
            if play:
                self.player.play()
        except Exception as exc:
            self._handle_error(None, str(exc))

    def _handle_media_status(self, status) -> None:
        if (
            status != QMediaPlayer.MediaStatus.EndOfMedia
            or not self._active
            or self._paused
            or self._stopping
            or self._loop_one
            or not self._playlist
        ):
            return
        self._current_index = (self._current_index + 1) % len(self._playlist)
        self._load_current(play=True)

    def _advance_fade(self) -> None:
        if self._fade_started_monotonic is None or self._fade_duration_ms <= 0:
            self._reset_player()
            return
        elapsed_ms = (time.perf_counter() - self._fade_started_monotonic) * 1000.0
        progress = min(1.0, max(0.0, elapsed_ms / self._fade_duration_ms))
        self._fade_factor = 1.0 - progress
        self._apply_gain()
        if progress >= 1.0:
            self._reset_player()

    def _reset_player(self) -> None:
        was_active = bool(self._active)
        self._fade_timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self._active = False
        self._paused = False
        self._stopping = False
        self._playlist = []
        self._current_index = 0
        self._fade_started_monotonic = None
        self._fade_duration_ms = 0
        self._fade_factor = 1.0
        self._apply_gain()
        if was_active:
            self.stopped.emit()

    def _apply_gain(self) -> None:
        base = max(0.0, min(1.0, self._volume_percent / 100.0))
        self.audio_output.setVolume(max(0.0, min(1.0, base * self._fade_factor)))
        self.audio_output.setMuted(self._muted)

    def _handle_error(self, _error, error_string: str = "") -> None:
        message = str(error_string or self.player.errorString() or "Ошибка воспроизведения аудио")
        self._reset_player()
        self.playbackError.emit(message)

