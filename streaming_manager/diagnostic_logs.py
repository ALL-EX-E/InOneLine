from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

STARTUP_ERROR_MAX_BYTES = 1 * 1024 * 1024
PERFORMANCE_LOG_MAX_BYTES = 512 * 1024
PERFORMANCE_LOG_ENV = "STREAMING_MANAGER_PERFORMANCE_LOG"
_TRUE_VALUES = {"1", "true", "yes", "on"}



_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(\b(?:access_token|refresh_token|api[_-]?key|password|passwd|secret|token)\b\s*[:=]\s*)([^\s,&;\"']+)"),
    re.compile(r'(?i)(["\'](?:access_token|refresh_token|api[_-]?key|password|passwd|secret|token)["\']\s*:\s*["\'])(.*?)(["\'])'),
)


def sanitize_diagnostic_text(text: str) -> str:
    """Best-effort fail-closed masking for common secret-bearing diagnostics."""
    sanitized = str(text)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups == 3:
            sanitized = pattern.sub(r"\1[СКРЫТО]\3", sanitized)
        else:
            sanitized = pattern.sub(r"\1[СКРЫТО]", sanitized)
    return sanitized

def _rotated_path(path: Path, index: int) -> Path:
    return Path(f"{path}.{index}")


def append_capped_log(
    path: str | Path,
    text: str,
    *,
    max_bytes: int,
    backup_count: int = 1,
) -> None:
    """Append text to a small diagnostic log with size-based rotation.

    Rotation happens before a write that would exceed ``max_bytes``.  Only a
    tiny fixed number of old files is kept, so diagnostic files cannot grow
    without bound.  The helper intentionally has no dependency on Qt or the
    application database and is therefore safe to use from startup handling.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = sanitize_diagnostic_text(text).encode("utf-8", errors="replace")

    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")
    if backup_count < 0:
        raise ValueError("backup_count must not be negative")

    if len(payload) > max_bytes:
        marker = b"\n... diagnostic entry truncated to log size limit ...\n"
        if len(marker) >= max_bytes:
            payload = payload[:max_bytes]
        else:
            remaining = max_bytes - len(marker)
            head = remaining // 2
            tail = remaining - head
            payload = payload[:head] + marker + payload[-tail:]

    current_size = target.stat().st_size if target.exists() else 0
    if current_size and current_size + len(payload) > max_bytes:
        if backup_count == 0:
            target.unlink(missing_ok=True)
        else:
            _rotated_path(target, backup_count).unlink(missing_ok=True)
            for index in range(backup_count - 1, 0, -1):
                older = _rotated_path(target, index)
                if older.exists():
                    older.replace(_rotated_path(target, index + 1))
            target.replace(_rotated_path(target, 1))

    with target.open("ab") as fh:
        fh.write(payload)


def performance_trace_enabled() -> bool:
    """Return whether temporary performance diagnostics were explicitly enabled."""
    return os.environ.get(PERFORMANCE_LOG_ENV, "").strip().lower() in _TRUE_VALUES


def append_performance_trace(log_dir: str | Path, message: str) -> bool:
    """Write an opt-in performance line and return whether anything was written."""
    if not performance_trace_enabled():
        return False

    timestamp = datetime.now().isoformat(timespec="seconds")
    append_capped_log(
        Path(log_dir) / "performance.log",
        f"{timestamp} {message.rstrip()}\n",
        max_bytes=PERFORMANCE_LOG_MAX_BYTES,
        backup_count=1,
    )
    return True
