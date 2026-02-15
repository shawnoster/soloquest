"""Momentum tracking and burn logic."""

from __future__ import annotations

MOMENTUM_MIN = -6
MOMENTUM_MAX = 10
MOMENTUM_RESET_DEFAULT = 2


def clamp_momentum(value: int) -> int:
    return max(MOMENTUM_MIN, min(MOMENTUM_MAX, value))


def momentum_after_burn(current: int) -> int:
    """Return momentum value after a burn (resets to reset value)."""
    return MOMENTUM_RESET_DEFAULT


def adjust_momentum(current: int, delta: int, max_momentum: int = MOMENTUM_MAX) -> int:
    """Apply a delta to momentum, clamped to valid range."""
    return max(MOMENTUM_MIN, min(max_momentum, current + delta))
