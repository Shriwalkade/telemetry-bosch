from dataclasses import replace
from datetime import UTC, datetime

import pytest

from telemetry.alerts import AlertResult, AlertThresholds, check_alerts
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def reading() -> Reading:
    return Reading(
        timestamp=FIXED_TIME,
        vehicle_id="VEH-001",
        speed_kmh=80.0,
        rpm=3000,
        engine_temp_c=90.0,
        fuel_pct=50.0,
    )


@pytest.mark.parametrize(
    ("temp_c", "expected"),
    [(99.9, False), (100.0, True), (100.1, True)],
)
def test_high_temp_alert_boundary(reading: Reading, temp_c: float, expected: bool) -> None:
    result = check_alerts(replace(reading, engine_temp_c=temp_c), AlertThresholds())
    assert result.high_temp is expected


@pytest.mark.parametrize(
    ("fuel_pct", "expected"),
    [(10.1, False), (10.0, True), (9.9, True)],
)
def test_low_fuel_alert_boundary(reading: Reading, fuel_pct: float, expected: bool) -> None:
    result = check_alerts(replace(reading, fuel_pct=fuel_pct), AlertThresholds())
    assert result.low_fuel is expected


def test_custom_temperature_threshold_applies(reading: Reading) -> None:
    result = check_alerts(replace(reading, engine_temp_c=102.0), AlertThresholds(high_temp_c=105.0))
    assert result.high_temp is False


def test_custom_fuel_threshold_applies(reading: Reading) -> None:
    result = check_alerts(replace(reading, fuel_pct=15.0), AlertThresholds(low_fuel_pct=20.0))
    assert result.low_fuel is True


def test_default_thresholds() -> None:
    thresholds = AlertThresholds()
    assert thresholds.high_temp_c == 100.0
    assert thresholds.low_fuel_pct == 10.0


def test_both_alerts_active_together(reading: Reading) -> None:
    result = check_alerts(replace(reading, engine_temp_c=110.0, fuel_pct=5.0), AlertThresholds())
    assert (result.high_temp, result.low_fuel, result.any_active) == (True, True, True)


def test_no_alert_active_for_normal_reading(reading: Reading) -> None:
    result = check_alerts(reading, AlertThresholds())
    assert (result.high_temp, result.low_fuel, result.any_active) == (False, False, False)


@pytest.mark.parametrize(
    ("high_temp", "low_fuel", "expected"),
    [(True, False, True), (False, True, True), (False, False, False)],
)
def test_any_active_is_true_when_either_alert_is_set(
    high_temp: bool, low_fuel: bool, expected: bool
) -> None:
    assert AlertResult(high_temp=high_temp, low_fuel=low_fuel).any_active is expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"high_temp_c": 19.9},
        {"high_temp_c": 120.1},
        {"low_fuel_pct": -0.1},
        {"low_fuel_pct": 100.1},
    ],
)
def test_invalid_thresholds_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValueError, match=next(iter(overrides))):
        AlertThresholds(**overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"high_temp_c": 20.0},
        {"high_temp_c": 120.0},
        {"low_fuel_pct": 0.0},
        {"low_fuel_pct": 100.0},
    ],
)
def test_thresholds_at_range_limits_are_accepted(overrides: dict) -> None:
    AlertThresholds(**overrides)
