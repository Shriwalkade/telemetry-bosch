"""Application settings: alert thresholds, refresh preset, optional environment overrides."""

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self

from telemetry.alerts import AlertThresholds

SPEED_PRESETS_SEC: dict[str, float] = {"slow": 2.0, "normal": 1.0, "fast": 0.5}
DEFAULT_PRESET = "normal"

ENV_SPEED_PRESET = "TELEMETRY_SPEED_PRESET"
ENV_INTERVAL_SEC = "TELEMETRY_INTERVAL_SEC"
ENV_HIGH_TEMP_C = "TELEMETRY_HIGH_TEMP_C"
ENV_LOW_FUEL_PCT = "TELEMETRY_LOW_FUEL_PCT"


@dataclass(frozen=True)
class AppConfig:
    """Dashboard settings; `interval_sec` defaults to the preset's value when not given."""

    thresholds: AlertThresholds = field(default_factory=AlertThresholds)
    speed_preset: str = DEFAULT_PRESET
    interval_sec: float | None = None

    def __post_init__(self) -> None:
        if self.speed_preset not in SPEED_PRESETS_SEC:
            presets = sorted(SPEED_PRESETS_SEC)
            raise ValueError(f"speed_preset must be one of {presets}, got {self.speed_preset!r}")
        if self.interval_sec is None:
            object.__setattr__(self, "interval_sec", SPEED_PRESETS_SEC[self.speed_preset])
        _check_interval(self.interval_sec)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Build a config from optional `TELEMETRY_*` variables; blank values are ignored."""
        env = os.environ if environ is None else environ
        threshold_args: dict[str, float] = {}
        if (high_temp := _env_float(env, ENV_HIGH_TEMP_C)) is not None:
            threshold_args["high_temp_c"] = high_temp
        if (low_fuel := _env_float(env, ENV_LOW_FUEL_PCT)) is not None:
            threshold_args["low_fuel_pct"] = low_fuel
        return cls(
            thresholds=AlertThresholds(**threshold_args),
            speed_preset=(env.get(ENV_SPEED_PRESET) or "").strip() or DEFAULT_PRESET,
            interval_sec=_env_float(env, ENV_INTERVAL_SEC),
        )


def _check_interval(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"interval_sec must be a number, got {value!r}")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"interval_sec must be greater than 0, got {value}")


def _env_float(env: Mapping[str, str], name: str) -> float | None:
    raw = (env.get(name) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None
