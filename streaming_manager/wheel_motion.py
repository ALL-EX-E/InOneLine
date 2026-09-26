from __future__ import annotations

import math


ACCEL_FRACTION = 0.22
DECEL_FRACTION = 0.30
ACCEL_CAP_MS = 2_000.0
DECEL_CAP_MS = 3_000.0


def wheel_motion_progress(progress: float, duration_ms: int | float) -> float:
    """Return normalized wheel position for accel -> cruise -> decel motion.

    The wheel starts and finishes at zero angular velocity. Short spins devote a
    visible share of their duration to acceleration/deceleration, while long
    spins cap those phases so they still spend most of the requested time at
    full speed instead of stretching easing over minutes or hours.
    """
    t = max(0.0, min(1.0, float(progress)))
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    duration = max(1.0, float(duration_ms))

    accel_ms = min(ACCEL_CAP_MS, duration * ACCEL_FRACTION)
    decel_ms = min(DECEL_CAP_MS, duration * DECEL_FRACTION)
    accel = accel_ms / duration
    decel = decel_ms / duration
    cruise = max(0.0, 1.0 - accel - decel)

    # A raised-cosine velocity ramp has zero velocity and zero acceleration at
    # the exact endpoints. Normalize the integrated area so position still
    # reaches exactly 1.0 at the persisted target_rotation.
    area = cruise + 0.5 * (accel + decel)
    peak_velocity = 1.0 / max(1e-9, area)

    if t <= accel:
        if accel <= 0.0:
            return 0.0
        position = peak_velocity * (
            0.5 * t
            - (accel / (2.0 * math.pi)) * math.sin(math.pi * t / accel)
        )
    elif t < 1.0 - decel:
        position = peak_velocity * (0.5 * accel + (t - accel))
    else:
        if decel <= 0.0:
            return 1.0
        u = max(0.0, min(decel, t - (1.0 - decel)))
        position = peak_velocity * (
            0.5 * accel
            + cruise
            + 0.5 * u
            + (decel / (2.0 * math.pi)) * math.sin(math.pi * u / decel)
        )

    return max(0.0, min(1.0, position))
