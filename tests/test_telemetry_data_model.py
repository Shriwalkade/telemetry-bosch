import math
from dataclasses import FrozenInstanceError, replace
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
NUMERIC_FIELDS = ["speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]
CSV_COLUMNS = ["timestamp", "vehicle_id", "speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]


@pytest.fixture
def reading() -> Reading:
    """Return a valid synthetic reading."""
    return Reading(
        timestamp=FIXED_TIME,
        vehicle_id="VEH-001",
        speed_kmh=80.0,
        rpm=3000,
        engine_temp_c=90.0,
        fuel_pct=50.0,
    )


def test_valid_reading_passes_validation(reading: Reading) -> None:
    """TDM-01: a valid reading passes validation.
    The base reading raises no exception and returns None.
    """
    assert validate_reading(reading) is None


def test_reading_is_immutable(reading: Reading) -> None:
    """TDM-02: Reading is a frozen dataclass.
    Assigning to a field raises FrozenInstanceError.
    """
    with pytest.raises(FrozenInstanceError):
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
    """TDM-03: range limits are inclusive.
    Each field is accepted exactly at its minimum and maximum.
    """
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
    """TDM-04: values just outside a range are rejected.
    ValueError names the offending field.
    """
    with pytest.raises(ValueError, match=field):
        validate_reading(replace(reading, **{field: value}))


def test_range_constants_have_documented_values() -> None:
    """TDM-05: range constants match the design.
    Speed 0-200, RPM 0-7000, temperature 20-120, fuel 0-100.
    """
    assert (SPEED_KMH_MIN, SPEED_KMH_MAX) == (0.0, 200.0)
    assert (RPM_MIN, RPM_MAX) == (0, 7000)
    assert (ENGINE_TEMP_C_MIN, ENGINE_TEMP_C_MAX) == (20.0, 120.0)
    assert (FUEL_PCT_MIN, FUEL_PCT_MAX) == (0.0, 100.0)


def test_int_values_are_accepted_for_float_fields(reading: Reading) -> None:
    """TDM-06: int values are valid numbers for float fields.
    Integer speed, temperature, and fuel pass validation.
    """
    validate_reading(replace(reading, speed_kmh=80, engine_temp_c=90, fuel_pct=50))


def test_naive_timestamp_is_rejected(reading: Reading) -> None:
    """TDM-07: a timestamp without timezone is rejected.
    ValueError matches timestamp.
    """
    naive = replace(reading, timestamp=datetime(2026, 10, 5, 12, 0, 0))
    with pytest.raises(ValueError, match="timestamp"):
        validate_reading(naive)


def test_non_utc_aware_timestamp_is_accepted(reading: Reading) -> None:
    """TDM-08: any timezone-aware timestamp is accepted.
    A +02:00 offset passes validation.
    """
    local = replace(reading, timestamp=FIXED_TIME.astimezone(timezone(timedelta(hours=2))))
    validate_reading(local)


@pytest.mark.parametrize("bad_timestamp", ["2026-10-05", None, 0])
def test_non_datetime_timestamp_is_rejected(reading: Reading, bad_timestamp: object) -> None:
    """TDM-09: a timestamp that is not a datetime is rejected.
    ValueError matches timestamp.
    """
    with pytest.raises(ValueError, match="timestamp"):
        validate_reading(replace(reading, timestamp=bad_timestamp))  # type: ignore[arg-type]


@pytest.mark.parametrize("vehicle_id", ["", "   "])
def test_blank_vehicle_id_is_rejected(reading: Reading, vehicle_id: str) -> None:
    """TDM-10: a blank vehicle ID is rejected.
    Empty and whitespace-only values raise ValueError matching vehicle_id.
    """
    with pytest.raises(ValueError, match="vehicle_id"):
        validate_reading(replace(reading, vehicle_id=vehicle_id))


@pytest.mark.parametrize("vehicle_id", [None, 123])
def test_non_string_vehicle_id_is_rejected(reading: Reading, vehicle_id: object) -> None:
    """TDM-11: a vehicle ID that is not a string is rejected.
    ValueError matches vehicle_id.
    """
    with pytest.raises(ValueError, match="vehicle_id"):
        validate_reading(replace(reading, vehicle_id=vehicle_id))  # type: ignore[arg-type]


@pytest.mark.parametrize("field", NUMERIC_FIELDS)
@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_non_finite_value_is_rejected(reading: Reading, field: str, bad_value: float) -> None:
    """TDM-12: NaN and infinity are rejected in every numeric field.
    ValueError names the field.
    """
    with pytest.raises(ValueError, match=field):
        validate_reading(replace(reading, **{field: bad_value}))


@pytest.mark.parametrize("field", NUMERIC_FIELDS)
@pytest.mark.parametrize("bad_value", ["fast", None, True])
def test_non_numeric_value_is_rejected(reading: Reading, field: str, bad_value: object) -> None:
    """TDM-13: strings, None, and bool are rejected in every numeric field.
    ValueError names the field.
    """
    with pytest.raises(ValueError, match=field):
        validate_reading(replace(reading, **{field: bad_value}))  # type: ignore[arg-type]


def test_timestamp_is_checked_before_vehicle_id(reading: Reading) -> None:
    """TDM-14: validation order puts the timestamp first.
    A naive timestamp with a blank vehicle ID reports timestamp.
    """
    broken = replace(reading, timestamp=datetime(2026, 10, 5, 12, 0, 0), vehicle_id=" ")
    with pytest.raises(ValueError, match="timestamp"):
        validate_reading(broken)


def test_vehicle_id_is_checked_before_numeric_fields(reading: Reading) -> None:
    """TDM-15: validation order puts the vehicle ID before numeric fields.
    A blank vehicle ID with an out-of-range speed reports vehicle_id.
    """
    with pytest.raises(ValueError, match="vehicle_id"):
        validate_reading(replace(reading, vehicle_id=" ", speed_kmh=999.0))


def test_numeric_fields_are_checked_in_field_order(reading: Reading) -> None:
    """TDM-16: numeric fields are validated in declaration order.
    An invalid speed and invalid fuel report speed_kmh.
    """
    with pytest.raises(ValueError, match="speed_kmh"):
        validate_reading(replace(reading, speed_kmh=-1.0, fuel_pct=200.0))


def test_reading_to_dict_keys_are_csv_columns_in_order(reading: Reading) -> None:
    """TDM-17: reading_to_dict keys are the CSV columns.
    Keys appear in the documented order.
    """
    assert list(reading_to_dict(reading)) == CSV_COLUMNS


def test_reading_to_dict_values_equal_reading_fields(reading: Reading) -> None:
    """TDM-18: reading_to_dict values mirror the reading.
    Every value equals the matching attribute, including timestamp.
    """
    values = reading_to_dict(reading)
    assert all(values[column] == getattr(reading, column) for column in CSV_COLUMNS)
