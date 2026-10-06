"""Threshold checks for demo telemetry alerts (indicators only, not safety advice)."""

import math
from dataclasses import dataclass
from typing import Any

from telemetry.models import (
    ENGINE_TEMP_C_MAX,
    ENGINE_TEMP_C_MIN,
    FUEL_PCT_MAX,
    FUEL_PCT_MIN,
    Reading,
)

DEFAULT_HIGH_TEMP_C = 100.0
DEFAULT_LOW_FUEL_PCT = 10.0


@dataclass(frozen=True)
class AlertThresholds:
    """Configurable alert limits; each value must lie inside its metric range."""

    high_temp_c: float = DEFAULT_HIGH_TEMP_C
    low_fuel_pct: float = DEFAULT_LOW_FUEL_PCT

    def __post_init__(self) -> None:
        _check_threshold("high_temp_c", self.high_temp_c, ENGINE_TEMP_C_MIN, ENGINE_TEMP_C_MAX)
        _check_threshold("low_fuel_pct", self.low_fuel_pct, FUEL_PCT_MIN, FUEL_PCT_MAX)


@dataclass(frozen=True)
class AlertResult:
    """Alert flags for one reading."""

    high_temp: bool
    low_fuel: bool

    @property
    def any_active(self) -> bool:
        """True when at least one alert is set."""
        return self.high_temp or self.low_fuel


def check_alerts(reading: Reading, thresholds: AlertThresholds) -> AlertResult:
    """Flag high temperature (>= threshold) and low fuel (<= threshold)."""
    return AlertResult(
        high_temp=reading.engine_temp_c >= thresholds.high_temp_c,
        low_fuel=reading.fuel_pct <= thresholds.low_fuel_pct,
    )


def _check_threshold(name: str, value: Any, low: float, high: float) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if math.isnan(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")
