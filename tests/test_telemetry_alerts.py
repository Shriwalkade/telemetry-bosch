import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

import telemetry.alerts as alerts_module
from telemetry.alerts import AlertResult, AlertThresholds, check_alerts
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def reading() -> Reading:
    """Return a valid reading that triggers no alert."""
    return Reading(
        timestamp=FIXED_TIME,
        vehicle_id="VEH-001",
        speed_kmh=80.0,
        rpm=3000,
        engine_temp_c=90.0,
        fuel_pct=50.0,
    )


def test_default_thresholds_match_the_spec() -> None:
    """TAL-01: default thresholds are 100.0 C and 10.0 %.
    A new AlertThresholds carries both defaults.
    """
    thresholds = AlertThresholds()
    assert thresholds.high_temp_c == 100.0
    assert thresholds.low_fuel_pct == 10.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"high_temp_c": 19.9},
        {"high_temp_c": 120.1},
        {"low_fuel_pct": -0.1},
        {"low_fuel_pct": 100.1},
    ],
)
def test_out_of_range_thresholds_are_rejected(overrides: dict) -> None:
    """TAL-02: thresholds outside the metric range are rejected.
    ValueError names the offending field.
    """
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
    """TAL-03: thresholds exactly at the model limits are accepted.
    No exception is raised.
    """
    AlertThresholds(**overrides)


def test_alert_thresholds_are_frozen() -> None:
    """TAL-04: AlertThresholds is a frozen dataclass.
    Assigning to a field raises FrozenInstanceError.
    """
    thresholds = AlertThresholds()
    with pytest.raises(FrozenInstanceError):
        thresholds.high_temp_c = 90.0  # type: ignore[misc]


@pytest.mark.parametrize(("temp_c", "expected"), [(99.9, False), (100.0, True), (100.1, True)])
def test_high_temp_alert_boundary_with_default_threshold(
    reading: Reading, temp_c: float, expected: bool
) -> None:
    """TAL-05: high temperature triggers at or above 100.0 C.
    Just below is False; at and above are True.
    """
    result = check_alerts(replace(reading, engine_temp_c=temp_c), AlertThresholds())
    assert result.high_temp is expected


def test_custom_temperature_threshold_applies(reading: Reading) -> None:
    """TAL-06: a custom temperature threshold replaces the default.
    Threshold 105.0 with 102.0 C is not an alert.
    """
    result = check_alerts(replace(reading, engine_temp_c=102.0), AlertThresholds(high_temp_c=105.0))
    assert result.high_temp is False


@pytest.mark.parametrize(("temp_c", "expected"), [(104.9, False), (105.0, True), (105.1, True)])
def test_high_temp_alert_boundary_with_custom_threshold(
    reading: Reading, temp_c: float, expected: bool
) -> None:
    """TAL-07: the temperature boundary follows the custom threshold.
    Threshold 105.0: below is False; at and above are True.
    """
    result = check_alerts(
        replace(reading, engine_temp_c=temp_c), AlertThresholds(high_temp_c=105.0)
    )
    assert result.high_temp is expected


def test_high_temp_alert_fires_at_model_maximum(reading: Reading) -> None:
    """TAL-08: high temperature triggers at the model maximum.
    120.0 C with default thresholds sets high_temp.
    """
    result = check_alerts(replace(reading, engine_temp_c=120.0), AlertThresholds())
    assert result.high_temp is True


@pytest.mark.parametrize(("fuel_pct", "expected"), [(10.1, False), (10.0, True), (9.9, True)])
def test_low_fuel_alert_boundary_with_default_threshold(
    reading: Reading, fuel_pct: float, expected: bool
) -> None:
    """TAL-09: low fuel triggers at or below 10.0 %.
    Just above is False; at and below are True.
    """
    result = check_alerts(replace(reading, fuel_pct=fuel_pct), AlertThresholds())
    assert result.low_fuel is expected


def test_custom_fuel_threshold_applies(reading: Reading) -> None:
    """TAL-10: a custom fuel threshold replaces the default.
    Threshold 20.0 with 15.0 % is an alert.
    """
    result = check_alerts(replace(reading, fuel_pct=15.0), AlertThresholds(low_fuel_pct=20.0))
    assert result.low_fuel is True


@pytest.mark.parametrize(("fuel_pct", "expected"), [(20.1, False), (20.0, True), (19.9, True)])
def test_low_fuel_alert_boundary_with_custom_threshold(
    reading: Reading, fuel_pct: float, expected: bool
) -> None:
    """TAL-11: the fuel boundary follows the custom threshold.
    Threshold 20.0: above is False; at and below are True.
    """
    result = check_alerts(replace(reading, fuel_pct=fuel_pct), AlertThresholds(low_fuel_pct=20.0))
    assert result.low_fuel is expected


def test_low_fuel_alert_fires_at_empty_tank(reading: Reading) -> None:
    """TAL-12: low fuel triggers at 0.0 %.
    Empty fuel with default thresholds sets low_fuel.
    """
    result = check_alerts(replace(reading, fuel_pct=0.0), AlertThresholds())
    assert result.low_fuel is True


def test_both_alerts_active_together(reading: Reading) -> None:
    """TAL-13: both alerts can be active at once.
    110.0 C with 5.0 % fuel sets high_temp, low_fuel, and any_active.
    """
    result = check_alerts(replace(reading, engine_temp_c=110.0, fuel_pct=5.0), AlertThresholds())
    assert (result.high_temp, result.low_fuel, result.any_active) == (True, True, True)


def test_alerts_are_independent(reading: Reading) -> None:
    """TAL-14: temperature and fuel alerts do not affect each other.
    Only the matching flag is set, and any_active is True.
    """
    hot = check_alerts(replace(reading, engine_temp_c=110.0), AlertThresholds())
    low = check_alerts(replace(reading, fuel_pct=5.0), AlertThresholds())
    assert (hot.high_temp, hot.low_fuel, hot.any_active) == (True, False, True)
    assert (low.high_temp, low.low_fuel, low.any_active) == (False, True, True)


def test_no_alert_active_for_normal_reading(reading: Reading) -> None:
    """TAL-15: a normal reading triggers nothing.
    All three flags are False.
    """
    result = check_alerts(reading, AlertThresholds())
    assert (result.high_temp, result.low_fuel, result.any_active) == (False, False, False)


@pytest.mark.parametrize(
    ("high_temp", "low_fuel", "expected"),
    [(True, False, True), (False, True, True), (False, False, False)],
)
def test_any_active_is_true_when_either_alert_is_set(
    high_temp: bool, low_fuel: bool, expected: bool
) -> None:
    """TAL-16: any_active is the logical OR of both flags.
    True when either flag is set, False when neither is.
    """
    assert AlertResult(high_temp=high_temp, low_fuel=low_fuel).any_active is expected


def test_alert_result_is_frozen() -> None:
    """TAL-17: AlertResult is a frozen dataclass.
    Assigning to a field raises FrozenInstanceError.
    """
    result = AlertResult(high_temp=False, low_fuel=False)
    with pytest.raises(FrozenInstanceError):
        result.high_temp = True  # type: ignore[misc]


def test_alerts_module_does_not_import_streamlit_or_simulator() -> None:
    """TAL-18: the alerts module stays independent of the UI and simulator.
    Its imports contain neither streamlit nor telemetry.simulator.
    """
    tree = ast.parse(inspect.getsource(alerts_module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not {name for name in imported if name.split(".")[0] == "streamlit"}
    assert "telemetry.simulator" not in imported
