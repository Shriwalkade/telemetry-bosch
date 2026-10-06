from datetime import UTC, datetime, timedelta

import pytest

from telemetry.buffer import ReadingBuffer
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
COLUMNS = ["timestamp", "vehicle_id", "speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]


def make_reading(index: int) -> Reading:
    """Return a reading made distinguishable by its timestamp and speed."""
    return Reading(
        timestamp=FIXED_TIME + timedelta(seconds=index),
        vehicle_id="VEH-001",
        speed_kmh=float(index % 200),
        rpm=3000,
        engine_temp_c=90.0,
        fuel_pct=50.0,
    )


def filled_buffer(count: int) -> ReadingBuffer:
    """Return a buffer with `count` sequential readings."""
    buffer = ReadingBuffer()
    for index in range(count):
        buffer.append(make_reading(index))
    return buffer


def test_buffer_capacity_is_1000() -> None:
    """TRB-01: the buffer capacity constant is 1000.
    MAX_READINGS equals 1000.
    """
    assert ReadingBuffer.MAX_READINGS == 1000


def test_buffer_drops_oldest_after_max_appends() -> None:
    """TRB-02: the oldest reading is dropped when full.
    After 1001 appends, length is 1000 and reading 1 is the oldest.
    """
    buffer = filled_buffer(1001)
    assert len(buffer) == 1000
    assert buffer.recent(1000)[0] == make_reading(1)


@pytest.mark.parametrize("count", [0, 1, 999, 1000])
def test_length_matches_number_of_appends_up_to_capacity(count: int) -> None:
    """TRB-03: length equals the number of appends up to capacity.
    0, 1, 999, and 1000 appends give the same lengths.
    """
    assert len(filled_buffer(count)) == count


def test_repeated_overflow_keeps_newest_1000() -> None:
    """TRB-04: repeated overflow keeps only the newest readings.
    After 1500 appends the oldest is reading 500 and the newest is 1499.
    """
    buffer = filled_buffer(1500)
    assert buffer.recent(1000)[0] == make_reading(500)
    assert buffer.latest() == make_reading(1499)


def test_latest_returns_newest_reading() -> None:
    """TRB-05: latest returns the newest reading.
    After 3 appends it is reading 2.
    """
    assert filled_buffer(3).latest() == make_reading(2)


def test_latest_on_empty_buffer_is_none() -> None:
    """TRB-06: latest on an empty buffer is None.
    A new buffer has no newest reading.
    """
    assert ReadingBuffer().latest() is None


def test_recent_returns_last_n_oldest_first() -> None:
    """TRB-07: recent returns the last n readings, oldest first.
    recent(3) of 10 readings is readings 7, 8, 9.
    """
    assert filled_buffer(10).recent(3) == [make_reading(i) for i in (7, 8, 9)]


def test_recent_returns_all_when_fewer_than_requested() -> None:
    """TRB-08: recent returns what exists when fewer than n are stored.
    recent(30) of 5 readings returns all 5.
    """
    assert filled_buffer(5).recent(30) == [make_reading(i) for i in range(5)]


def test_recent_on_empty_buffer_is_empty() -> None:
    """TRB-09: recent on an empty buffer is empty.
    recent(30) returns an empty list.
    """
    assert ReadingBuffer().recent(30) == []


def test_recent_zero_returns_empty_list() -> None:
    """TRB-10: recent(0) returns nothing.
    A buffer with 5 readings still returns an empty list.
    """
    assert filled_buffer(5).recent(0) == []


def test_clear_empties_buffer() -> None:
    """TRB-11: clear removes every reading.
    Length is 0 and latest is None afterwards.
    """
    buffer = filled_buffer(5)
    buffer.clear()
    assert len(buffer) == 0
    assert buffer.latest() is None


def test_buffer_is_reusable_after_clear() -> None:
    """TRB-12: a cleared buffer accepts new readings.
    One append after clear gives length 1 and that latest reading.
    """
    buffer = filled_buffer(5)
    buffer.clear()
    buffer.append(make_reading(99))
    assert len(buffer) == 1
    assert buffer.latest() == make_reading(99)


def test_empty_buffer_dataframe_has_columns_and_no_rows() -> None:
    """TRB-13: an empty buffer converts to an empty frame with columns.
    The frame is empty and keeps the six reading columns.
    """
    frame = ReadingBuffer().to_dataframe()
    assert frame.empty
    assert list(frame.columns) == COLUMNS


def test_dataframe_has_one_row_per_reading() -> None:
    """TRB-14: the frame has one row per reading.
    Seven readings give seven rows and the six columns.
    """
    frame = filled_buffer(7).to_dataframe()
    assert len(frame) == 7
    assert list(frame.columns) == COLUMNS


def test_dataframe_rows_are_oldest_first_and_match_values() -> None:
    """TRB-15: frame rows follow insertion order and carry the values.
    Timestamps and speeds equal those of the appended readings.
    """
    frame = filled_buffer(3).to_dataframe()
    expected = [make_reading(i) for i in range(3)]
    assert [stamp.to_pydatetime() for stamp in frame["timestamp"]] == [
        r.timestamp for r in expected
    ]
    assert list(frame["speed_kmh"]) == [r.speed_kmh for r in expected]


def test_to_dataframe_does_not_change_the_buffer() -> None:
    """TRB-16: converting to a frame has no side effects.
    Length is unchanged and two calls produce equal frames.
    """
    buffer = filled_buffer(4)
    first = buffer.to_dataframe()
    second = buffer.to_dataframe()
    assert len(buffer) == 4
    assert first.equals(second)
