"""Telemetry reading definition and validation."""

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

SPEED_KMH_MIN = 0.0
SPEED_KMH_MAX = 200.0
RPM_MIN = 0
RPM_MAX = 7000
ENGINE_TEMP_C_MIN = 20.0
ENGINE_TEMP_C_MAX = 120.0
FUEL_PCT_MIN = 0.0
FUEL_PCT_MAX = 100.0

_NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "speed_kmh": (SPEED_KMH_MIN, SPEED_KMH_MAX),
    "rpm": (RPM_MIN, RPM_MAX),
    "engine_temp_c": (ENGINE_TEMP_C_MIN, ENGINE_TEMP_C_MAX),
    "fuel_pct": (FUEL_PCT_MIN, FUEL_PCT_MAX),
}


@dataclass(frozen=True)
class Reading:
    """One synthetic telemetry sample."""

    timestamp: datetime
    vehicle_id: str
    speed_kmh: float
    rpm: int
    engine_temp_c: float
    fuel_pct: float


def validate_reading(reading: Reading) -> None:
    """Raise ValueError if the reading is malformed or out of range."""
    timestamp = reading.timestamp
    if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be a timezone-aware datetime")

    if not isinstance(reading.vehicle_id, str) or not reading.vehicle_id.strip():
        raise ValueError("vehicle_id must be a non-empty string")

    for name, (low, high) in _NUMERIC_RANGES.items():
        _validate_number(name, getattr(reading, name), low, high)


def _validate_number(name: str, value: Any, low: float, high: float) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


def reading_to_dict(reading: Reading) -> dict[str, Any]:
    """Return a CSV-friendly mapping keyed by column name."""
    return asdict(reading)
