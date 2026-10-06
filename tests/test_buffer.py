from datetime import UTC, datetime, timedelta

import pytest

from telemetry.buffer import ReadingBuffer
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
COLUMNS = ["timestamp", "vehicle_id", "speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]


def make_reading(index: int) -> Reading:
    return Reading(
        timestamp=FIXED_TIME + timedelta(seconds=index),
        vehicle_id="VEH-001",
        speed_kmh=80.0,
        rpm=3000,
        engine_temp_c=90.0,
        fuel_pct=50.0,
    )


def filled_buffer(count: int) -> ReadingBuffer:
    buffer = ReadingBuffer()
    for index in range(count):
        buffer.append(make_reading(index))
    return buffer


def test_buffer_drops_oldest_after_max_appends() -> None:
    buffer = filled_buffer(1001)
    assert len(buffer) == 1000
    assert buffer.recent(1000)[0] == make_reading(1)


def test_buffer_capacity_is_1000() -> None:
    assert ReadingBuffer.MAX_READINGS == 1000


def test_recent_returns_all_when_fewer_than_requested() -> None:
    buffer = filled_buffer(5)
    assert buffer.recent(30) == [make_reading(i) for i in range(5)]


def test_recent_returns_last_n_oldest_first() -> None:
    buffer = filled_buffer(10)
    assert buffer.recent(3) == [make_reading(i) for i in (7, 8, 9)]


def test_recent_zero_returns_empty_list() -> None:
    assert filled_buffer(5).recent(0) == []


def test_latest_returns_newest_reading() -> None:
    assert filled_buffer(3).latest() == make_reading(2)


def test_latest_on_empty_buffer_is_none() -> None:
    assert ReadingBuffer().latest() is None


def test_recent_on_empty_buffer_is_empty() -> None:
    assert ReadingBuffer().recent(30) == []


def test_clear_empties_buffer() -> None:
    buffer = filled_buffer(5)
    buffer.clear()
    assert len(buffer) == 0
    assert buffer.latest() is None


def test_empty_buffer_dataframe_has_columns_and_no_rows() -> None:
    frame = ReadingBuffer().to_dataframe()
    assert frame.empty
    assert list(frame.columns) == COLUMNS


def test_dataframe_has_one_row_per_reading() -> None:
    frame = filled_buffer(7).to_dataframe()
    assert len(frame) == 7
    assert list(frame.columns) == COLUMNS


@pytest.mark.parametrize("count", [0, 1, 999, 1000])
def test_length_matches_number_of_appends_up_to_capacity(count: int) -> None:
    assert len(filled_buffer(count)) == count
