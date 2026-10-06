import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

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
    reading_to_dict,
    validate_reading,
)

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


def test_valid_reading_passes_validation(reading: Reading) -> None:
    validate_reading(reading)


def test_reading_is_immutable(reading: Reading) -> None:
    with pytest.raises(AttributeError):
        reading.speed_kmh = 10.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "low", "high"),
    [
        ("speed_kmh", SPEED_KMH_MIN, SPEED_KMH_MAX),
        ("rpm", RPM_MIN, RPM_MAX),
        ("engine_temp_c", ENGINE_TEMP_C_MIN, ENGINE_TEMP_C_MAX),
        ("fuel_pct", FUEL_PCT_MIN, FUEL_PCT_MAX),
    ],
)
def test_range_limits_are_accepted_at_both_ends(
    reading: Reading, field: str, low: float, high: float
) -> None:
    validate_reading(replace(reading, **{field: low}))
    validate_reading(replace(reading, **{field: high}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("speed_kmh", SPEED_KMH_MIN - 0.1),
        ("speed_kmh", SPEED_KMH_MAX + 0.1),
        ("rpm", RPM_MIN - 1),
        ("rpm", RPM_MAX + 1),
        ("engine_temp_c", ENGINE_TEMP_C_MIN - 0.1),
        ("engine_temp_c", ENGINE_TEMP_C_MAX + 0.1),
        ("fuel_pct", FUEL_PCT_MIN - 0.1),
        ("fuel_pct", FUEL_PCT_MAX + 0.1),
    ],
)
def test_value_just_outside_range_is_rejected(reading: Reading, field: str, value: float) -> None:
    with pytest.raises(ValueError, match=field):
        validate_reading(replace(reading, **{field: value}))


def test_naive_timestamp_is_rejected(reading: Reading) -> None:
    naive = replace(reading, timestamp=datetime(2026, 10, 5, 12, 0, 0))
    with pytest.raises(ValueError, match="timestamp"):
        validate_reading(naive)


def test_non_utc_aware_timestamp_is_accepted(reading: Reading) -> None:
    local = replace(reading, timestamp=FIXED_TIME.astimezone(timezone(timedelta(hours=2))))
    validate_reading(local)


@pytest.mark.parametrize("vehicle_id", ["", "   "])
def test_empty_vehicle_id_is_rejected(reading: Reading, vehicle_id: str) -> None:
    with pytest.raises(ValueError, match="vehicle_id"):
        validate_reading(replace(reading, vehicle_id=vehicle_id))


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_non_finite_value_is_rejected(reading: Reading, bad_value: float) -> None:
    with pytest.raises(ValueError, match="speed_kmh"):
        validate_reading(replace(reading, speed_kmh=bad_value))


@pytest.mark.parametrize("bad_value", ["fast", None, True])
def test_non_numeric_value_is_rejected(reading: Reading, bad_value: object) -> None:
    with pytest.raises(ValueError, match="engine_temp_c"):
        validate_reading(replace(reading, engine_temp_c=bad_value))  # type: ignore[arg-type]


def test_reading_to_dict_uses_csv_column_names(reading: Reading) -> None:
    assert list(reading_to_dict(reading)) == [
        "timestamp",
        "vehicle_id",
        "speed_kmh",
        "rpm",
        "engine_temp_c",
        "fuel_pct",
    ]
    assert reading_to_dict(reading)["rpm"] == 3000
