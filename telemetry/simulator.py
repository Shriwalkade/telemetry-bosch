"""Deterministic synthetic telemetry generator based on bounded random walks."""

import random
from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry.models import (
    ENGINE_TEMP_C_MAX,
    ENGINE_TEMP_C_MIN,
    FUEL_PCT_MAX,
    FUEL_PCT_MIN,
    RPM_MAX,
    RPM_MIN,
    SPEED_KMH_MAX,
    SPEED_KMH_MIN,
    Reading,
)


@dataclass(frozen=True)
class SimulatorConfig:
    """Simulation ranges, step sizes, and initial state."""

    vehicle_id: str = "VEH-001"
    seed: int | None = None

    speed_min_kmh: float = SPEED_KMH_MIN
    speed_max_kmh: float = SPEED_KMH_MAX
    speed_initial_kmh: float = 60.0
    max_speed_step_kmh: float = 5.0

    rpm_min: int = RPM_MIN
    rpm_max: int = RPM_MAX
    rpm_idle: int = 800
    rpm_per_kmh: float = 30.0
    rpm_noise: int = 150

    temp_min_c: float = ENGINE_TEMP_C_MIN
    temp_max_c: float = ENGINE_TEMP_C_MAX
    temp_initial_c: float = 70.0
    temp_baseline_c: float = 85.0
    temp_heat_gain_c: float = 0.6
    temp_cooling_rate: float = 0.02
    max_temp_step_c: float = 1.0

    fuel_min_pct: float = FUEL_PCT_MIN
    fuel_max_pct: float = FUEL_PCT_MAX
    fuel_initial_pct: float = 80.0
    max_fuel_step_pct: float = 0.2

    def __post_init__(self) -> None:
        if not self.vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string")
        _check_range("speed", self.speed_min_kmh, self.speed_max_kmh, SPEED_KMH_MIN, SPEED_KMH_MAX)
        _check_range("rpm", self.rpm_min, self.rpm_max, RPM_MIN, RPM_MAX)
        _check_range("temp", self.temp_min_c, self.temp_max_c, ENGINE_TEMP_C_MIN, ENGINE_TEMP_C_MAX)
        _check_range("fuel", self.fuel_min_pct, self.fuel_max_pct, FUEL_PCT_MIN, FUEL_PCT_MAX)
        _check_inside(
            "speed_initial_kmh", self.speed_initial_kmh, self.speed_min_kmh, self.speed_max_kmh
        )
        _check_inside("temp_initial_c", self.temp_initial_c, self.temp_min_c, self.temp_max_c)
        _check_inside(
            "fuel_initial_pct", self.fuel_initial_pct, self.fuel_min_pct, self.fuel_max_pct
        )
        for name in (
            "max_speed_step_kmh",
            "rpm_noise",
            "rpm_per_kmh",
            "temp_heat_gain_c",
            "temp_cooling_rate",
            "max_temp_step_c",
            "max_fuel_step_pct",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")


def _check_range(name: str, low: float, high: float, limit_low: float, limit_high: float) -> None:
    if not limit_low <= low < high <= limit_high:
        raise ValueError(
            f"{name} range ({low}, {high}) must satisfy {limit_low} <= min < max <= {limit_high}"
        )


def _check_inside(name: str, value: float, low: float, high: float) -> None:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class Simulator:
    """Generates one reading per call; holds only generator state (no threads or timers)."""

    def __init__(self, config: SimulatorConfig | None = None) -> None:
        self._config = config or SimulatorConfig()
        self.reset()

    def reset(self) -> None:
        """Restore initial values and reseed the RNG."""
        cfg = self._config
        self._rng = random.Random(cfg.seed)
        self._speed_kmh = cfg.speed_initial_kmh
        self._temp_c = cfg.temp_initial_c
        self._fuel_pct = cfg.fuel_initial_pct

    def get_next_reading(self, now: datetime | None = None) -> Reading:
        """Advance the simulation one step; `now` must be timezone-aware when given."""
        cfg = self._config
        timestamp = now or datetime.now(UTC)

        self._speed_kmh = _clamp(
            self._speed_kmh + self._rng.uniform(-cfg.max_speed_step_kmh, cfg.max_speed_step_kmh),
            cfg.speed_min_kmh,
            cfg.speed_max_kmh,
        )
        rpm = self._next_rpm()
        self._temp_c = self._next_temp_c(rpm)
        self._fuel_pct = _clamp(
            self._fuel_pct - self._rng.uniform(0.0, cfg.max_fuel_step_pct),
            cfg.fuel_min_pct,
            cfg.fuel_max_pct,
        )

        return Reading(
            timestamp=timestamp,
            vehicle_id=cfg.vehicle_id,
            speed_kmh=self._speed_kmh,
            rpm=rpm,
            engine_temp_c=self._temp_c,
            fuel_pct=self._fuel_pct,
        )

    def _next_rpm(self) -> int:
        cfg = self._config
        noise = self._rng.uniform(-cfg.rpm_noise, cfg.rpm_noise)
        rpm = cfg.rpm_idle + self._speed_kmh * cfg.rpm_per_kmh + noise
        return int(_clamp(round(rpm), cfg.rpm_min, cfg.rpm_max))

    def _next_temp_c(self, rpm: int) -> float:
        cfg = self._config
        load = (rpm - cfg.rpm_min) / (cfg.rpm_max - cfg.rpm_min)
        heating = cfg.temp_heat_gain_c * load
        cooling = cfg.temp_cooling_rate * (self._temp_c - cfg.temp_baseline_c)
        delta = _clamp(heating - cooling, -cfg.max_temp_step_c, cfg.max_temp_step_c)
        return _clamp(self._temp_c + delta, cfg.temp_min_c, cfg.temp_max_c)
