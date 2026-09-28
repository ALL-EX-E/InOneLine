from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.audio import AudioCoordinator
from streaming_manager.constants import (
    APP_VERSION,
    AUCTION_AUDIO_OUTPUT_MODE_APPLICATION,
    AUCTION_AUDIO_OUTPUT_MODE_KEY,
    AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
    SCHEMA_VERSION,
)
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_MUSIC,
    MEDIA_CATEGORY_WHEEL_JINGLES,
    managed_media_directory,
)
from streaming_manager.views.main_window import MainWindow


assert APP_VERSION == "1.0.5", APP_VERSION
assert SCHEMA_VERSION == 18, SCHEMA_VERSION


def write_test_wav(path: Path, seconds: float = 2.0) -> None:
    sample_rate = 8000
    frames = int(sample_rate * seconds)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(b"\x00\x00" * frames)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


# D43 future-player handoff contract: capture -> pause -> auction -> restore.
events: list[object] = []
coordinator = AudioCoordinator()
coordinator.register_music_player(
    lambda: {"track": "demo", "position_ms": 1234, "was_playing": True},
    lambda: events.append("pause"),
    lambda state: events.append(("restore", dict(state))),
)
assert coordinator.owner == "music_player"
coordinator.acquire_auction()
assert coordinator.owner == "auction"
assert events == ["pause"], events
coordinator.release_auction()
assert coordinator.owner == "music_player"
assert events[-1] == (
    "restore",
    {"track": "demo", "position_ms": 1234, "was_playing": True},
), events


app = QApplication.instance() or QApplication([])
old_info = QMessageBox.information
old_warn = QMessageBox.warning
old_critical = QMessageBox.critical
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)

try:
    with TemporaryDirectory() as root:
        paths = AppPaths.from_root(root)
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        db.set_setting("api_port", "18770")

        with db.connect() as conn:
            migration_count = int(
                conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            )
        assert migration_count == 14, migration_count

        # Backward compatibility: upgrading from 1.0.4 keeps local playback.
        assert (
            db.get_setting(
                AUCTION_AUDIO_OUTPUT_MODE_KEY,
                AUCTION_AUDIO_OUTPUT_MODE_APPLICATION,
            )
            == AUCTION_AUDIO_OUTPUT_MODE_APPLICATION
        )
        db.set_setting(
            AUCTION_AUDIO_OUTPUT_MODE_KEY,
            AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER,
        )

        music_dir = managed_media_directory(db.path.parent, MEDIA_CATEGORY_MUSIC)
        wheel_dir = managed_media_directory(
            db.path.parent, MEDIA_CATEGORY_WHEEL_JINGLES
        )
        music_dir.mkdir(parents=True, exist_ok=True)
        wheel_dir.mkdir(parents=True, exist_ok=True)

        music_path = music_dir / "d43-auction.wav"
        wheel_path = wheel_dir / "d43-wheel.wav"
        write_test_wav(music_path, 3.0)
        write_test_wav(wheel_path, 1.0)
        music_asset = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_MUSIC,
            music_path.name,
            "D43 Auction",
        )
        wheel_asset = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_WHEEL_JINGLES,
            wheel_path.name,
            "D43 Wheel",
        )

        window = MainWindow(db, paths)
        try:
            auction = window.auction_tab
            assert auction._saved_audio_output_mode() == AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER
            assert auction.auction_audio.transport_silent is True
            assert auction.wheel_audio.transport_silent is True
            assert (
                auction.audio_output_mode_combo.currentData()
                == AUCTION_AUDIO_OUTPUT_MODE_OBS_TIMER
            )

            # No active transport yet: Timer API advertises the mode but no sound.
            timer = get_json(window.api.base_url + "/api/timer")
            assert timer["audio"]["enabled"] is True, timer["audio"]
            assert timer["audio"]["active"] is False, timer["audio"]

            # Simulate authoritative auction playlist transport.
            window.audio_coordinator.acquire_auction()
            auction._auction_audio_asset_ids = [int(music_asset.id)]
            auction.auction_audio.start_playlist(
                [music_path],
                start_index=0,
                loop_one=False,
                start_paused=False,
            )
            # start_playlist resets the old transport, so align the public ID after it.
            auction._auction_audio_asset_ids = [int(music_asset.id)]
            for _ in range(8):
                app.processEvents()
                time.sleep(0.05)
            auction._refresh_browser_audio_snapshot()

            timer = get_json(window.api.base_url + "/api/timer")
            audio = timer["audio"]
            assert audio["enabled"] is True, audio
            assert audio["active"] is True, audio
            assert audio["kind"] == "auction", audio
            assert audio["media_id"] == music_asset.id, audio
            assert audio["url"] == f"/media/{music_asset.id}", audio

            # Pause keeps auction ownership and exposes the same transport/position.
            auction.auction_audio.pause()
            app.processEvents()
            auction._refresh_browser_audio_snapshot()
            timer = get_json(window.api.base_url + "/api/timer")
            assert timer["audio"]["owner"] == "auction", timer["audio"]
            assert timer["audio"]["paused"] is True, timer["audio"]

            # Range serving is what Chromium/OBS uses for local media seeking.
            request = urllib.request.Request(
                window.api.base_url + f"/media/{music_asset.id}",
                headers={"Range": "bytes=0-31"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                assert response.status == 206, response.status
                assert len(response.read()) == 32

            # Wheel takes the same Timer Browser Source, not a second audio source.
            auction.auction_audio.stop(immediate=True)
            auction._wheel_audio_asset_id = int(wheel_asset.id)
            auction.wheel_audio.schedule_loop(
                wheel_path,
                started_at=datetime.now(timezone.utc),
                duration_ms=1500,
                fade_ms=600,
            )
            for _ in range(6):
                app.processEvents()
                time.sleep(0.05)
            auction._refresh_browser_audio_snapshot()
            timer = get_json(window.api.base_url + "/api/timer")
            audio = timer["audio"]
            assert audio["active"] is True, audio
            assert audio["kind"] == "wheel", audio
            assert audio["media_id"] == wheel_asset.id, audio
            assert audio["loop"] is True, audio

            # Output-mode switch unmutes the authoritative local transports and
            # disables browser playback without creating a second state machine.
            index = auction.audio_output_mode_combo.findData(
                AUCTION_AUDIO_OUTPUT_MODE_APPLICATION
            )
            assert index >= 0
            auction.audio_output_mode_combo.setCurrentIndex(index)
            app.processEvents()
            auction._refresh_browser_audio_snapshot()
            assert auction.auction_audio.transport_silent is False
            assert auction.wheel_audio.transport_silent is False
            timer = get_json(window.api.base_url + "/api/timer")
            assert timer["audio"]["enabled"] is False, timer["audio"]

            overlay = (
                Path("streaming_manager/web/timer_overlay.html")
                .read_text(encoding="utf-8")
            )
            assert 'id="auction-audio"' in overlay
            assert "syncAuctionAudio" in overlay
            assert 'const API = "/api/timer"' in overlay
        finally:
            window.api.stop()
            window.close()
            app.processEvents()
finally:
    QMessageBox.information = old_info
    QMessageBox.warning = old_warn
    QMessageBox.critical = old_critical

print("D43 TIMER/OBS AUDIO TRANSPORT SMOKE: PASS")
