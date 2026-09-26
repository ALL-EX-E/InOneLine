from __future__ import annotations

APP_NAME = "In one line"
APP_VERSION = "1.0.0"
LEGACY_SETTINGS_APP_NAME = "Streaming Manager"
DEFAULT_API_HOST = "127.0.0.1"
SCHEMA_VERSION = 18

SHARED_XLSX_ENABLED_KEY = "shared_xlsx_enabled"
SHARED_XLSX_PATH_KEY = "shared_xlsx_path"
SHARED_XLSX_POLL_INTERVAL_MS = 1000
SHARED_XLSX_LOCAL_WRITE_DEBOUNCE_MS = 350

PUBLIC_XLSX_ENABLED_KEY = "public_xlsx_enabled"
PUBLIC_XLSX_PATH_KEY = "public_xlsx_path"
PUBLIC_XLSX_MISSING_POLL_INTERVAL_MS = 1000
PUBLIC_XLSX_LOCAL_WRITE_DEBOUNCE_MS = 350


RULES_OVERLAY_VISIBLE_KEY = "rules_overlay_visible"
RULES_OVERLAY_VISIBLE_DEFAULT = True
RULES_OVERLAY_AUTOSCROLL_KEY = "rules_overlay_autoscroll"
RULES_OVERLAY_AUTOSCROLL_DEFAULT = True
RULES_OVERLAY_BACKGROUND_KEY = "rules_overlay_background"
RULES_OVERLAY_BACKGROUND_DEFAULT = "transparent"
RULES_OVERLAY_BACKGROUND_COLOR_KEY = "rules_overlay_background_color"
RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT = "#000000"
RULES_OVERLAY_BACKGROUND_OPACITY_KEY = "rules_overlay_background_opacity"
RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT = 0
RULES_OVERLAY_PADDING_KEY = "rules_overlay_padding"
RULES_OVERLAY_PADDING_DEFAULT = 24

# Standalone visual-only OBS timer. These presentation settings are independent
# from the main/list/rules/wheel viewers and live in the existing generic
# settings table, so no schema migration is required.
TIMER_OVERLAY_FONT_FAMILY_KEY = "timer_overlay_font_family"
TIMER_OVERLAY_FONT_FAMILY_DEFAULT = "Segoe UI"
TIMER_OVERLAY_FONT_SIZE_KEY = "timer_overlay_font_size"
TIMER_OVERLAY_FONT_SIZE_DEFAULT = 96
TIMER_OVERLAY_FONT_COLOR_KEY = "timer_overlay_font_color"
TIMER_OVERLAY_FONT_COLOR_DEFAULT = "#FFFFFF"
TIMER_OVERLAY_BACKGROUND_KEY = "timer_overlay_background"
TIMER_OVERLAY_BACKGROUND_DEFAULT = "transparent"
TIMER_OVERLAY_BACKGROUND_COLOR_KEY = "timer_overlay_background_color"
TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT = "#000000"

AUCTION_MIN_DURATION_MS = 1_000
AUCTION_MAX_DURATION_MS = 24 * 60 * 60 * 1000

AUCTION_MANUAL_BID_POINTS_KEY = "auction_manual_bid_points"
AUCTION_MANUAL_BID_POINTS_DEFAULT = 10
AUCTION_MANUAL_BID_POINTS_MIN = 1
AUCTION_MANUAL_BID_POINTS_MAX = 10_000_000
AUCTION_WHEEL_CHANCE_VISIBLE_KEY = "auction_wheel_chance_visible"
AUCTION_WHEEL_CHANCE_VISIBLE_DEFAULT = True

# W3 — application-owned wheel soundtrack.  Values live in the existing
# generic settings table; B1 later raises the global schema to 17 for integration infrastructure.
WHEEL_SOUNDTRACK_MEDIA_ID_KEY = "wheel_soundtrack_media_id"
WHEEL_SOUNDTRACK_VOLUME_KEY = "wheel_soundtrack_volume"
WHEEL_SOUNDTRACK_VOLUME_DEFAULT = 100
WHEEL_SOUNDTRACK_MUTE_KEY = "wheel_soundtrack_mute"
WHEEL_SOUNDTRACK_MUTE_DEFAULT = False

# Timer/Auction Music — application-owned soundtrack for the max-amount
# auction countdown. It deliberately has separate persisted state from W3.
AUCTION_SOUNDTRACK_MEDIA_ID_KEY = "auction_soundtrack_media_id"
AUCTION_SOUNDTRACK_LOOP_ONE_KEY = "auction_soundtrack_loop_one"
AUCTION_SOUNDTRACK_LOOP_ONE_DEFAULT = False
AUCTION_SOUNDTRACK_VOLUME_KEY = "auction_soundtrack_volume"
AUCTION_SOUNDTRACK_VOLUME_DEFAULT = 100
AUCTION_SOUNDTRACK_MUTE_KEY = "auction_soundtrack_mute"
AUCTION_SOUNDTRACK_MUTE_DEFAULT = False

# S2 — timer auto-extension. Settings live in the existing generic settings
# table, so enabling the feature does not require a SQLite schema migration.
AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY = "auction_auto_extend_leader_enabled"
AUCTION_AUTO_EXTEND_LEADER_ENABLED_DEFAULT = False
AUCTION_AUTO_EXTEND_LEADER_MS_KEY = "auction_auto_extend_leader_ms"
AUCTION_AUTO_EXTEND_LEADER_MS_DEFAULT = 30_000
AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY = "auction_auto_extend_new_lot_enabled"
AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_DEFAULT = False
AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY = "auction_auto_extend_new_lot_ms"
AUCTION_AUTO_EXTEND_NEW_LOT_MS_DEFAULT = 60_000
AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY = "auction_auto_extend_external_enabled"
AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT = False
AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY = "auction_auto_extend_external_ms"
AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT = 60_000
AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY = "auction_auto_extend_threshold_enabled"
AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_DEFAULT = True
AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY = "auction_auto_extend_threshold_ms"
AUCTION_AUTO_EXTEND_THRESHOLD_MS_DEFAULT = 120_000
AUCTION_AUTO_EXTEND_MAX_MS = 24 * 60 * 60 * 1000


STATUS_PLAYING = "playing"
STATUS_PLAYED = "played"
STATUS_NOT_PLAYED = "not_played"
STATUS_COMPLETED = "completed"
STATUS_ABANDONED = "abandoned"

STATUS_LABELS = {
    STATUS_PLAYING: "ПРОХОДИТСЯ",
    STATUS_PLAYED: "ИГРАЛ",
    STATUS_NOT_PLAYED: "НЕ ИГРАЛ",
    STATUS_COMPLETED: "ПРОЙДЕНО",
    STATUS_ABANDONED: "ЗАБРОШЕНО",
}

STATUS_FROM_LABEL = {
    "ПРОХОДИТСЯ": STATUS_PLAYING,
    "ПРОХОДИТЬСЯ": STATUS_PLAYING,
    "ИГРАЛ": STATUS_PLAYED,
    "НЕ ИГРАЛ": STATUS_NOT_PLAYED,
    "ПРОЙДЕНО": STATUS_COMPLETED,
    "ПРОЙДЕННО": STATUS_COMPLETED,
    "ЗАБРОШЕНО": STATUS_ABANDONED,
    "ЗАБРОШЕНА": STATUS_ABANDONED,
    "ABANDONED": STATUS_ABANDONED,
    "PLAYING": STATUS_PLAYING,
    "PLAYED": STATUS_PLAYED,
    "NOT_PLAYED": STATUS_NOT_PLAYED,
    "COMPLETED": STATUS_COMPLETED,
}

COOP_LABELS = {0: "НЕ КООП", 1: "КООП"}
COOP_FROM_LABEL = {
    "НЕ КООП": 0,
    "НЕ КООПЕРАТИВ": 0,
    "НЕ КООПЕРАТИВНАЯ": 0,
    "NO": 0,
    "0": 0,
    "КООП": 1,
    "КООПЕРАТИВ": 1,
    "КООПЕРАТИВНАЯ": 1,
    "YES": 1,
    "1": 1,
}

STREAM_FORMATS = ("16:9", "4:3")
