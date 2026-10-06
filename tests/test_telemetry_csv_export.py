import csv
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from telemetry.buffer import ReadingBuffer
from telemetry.export import export_csv
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
EXPECTED_NAME = "readings_20261005T120000Z.csv"
NAME_PATTERN = re.compile(r"readings_\d{8}T\d{6}Z\.csv")
COLUMNS = ["timestamp", "vehicle_id", "speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]


def make_buffer(count: int) -> ReadingBuffer:
    """Return a buffer with `count` readings of increasing speed."""
    buffer = ReadingBuffer()
    for index in range(count):
        buffer.append(
            Reading(
                timestamp=FIXED_TIME + timedelta(seconds=index),
                vehicle_id="VEH-001",
                speed_kmh=80.0 + (index % 100),
                rpm=3000,
                engine_temp_c=90.0,
                fuel_pct=50.0,
            )
        )
    return buffer


@pytest.fixture
def buffer() -> ReadingBuffer:
    """Return a buffer with three readings."""
    return make_buffer(3)


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV file and return its header and rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def test_export_file_name_uses_injected_utc_time(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-01: the file name is built from the injected UTC time.
    The returned path is readings_20261005T120000Z.csv inside the directory and exists.
    """
    path = export_csv(buffer, tmp_path, FIXED_TIME)
    assert path == tmp_path / EXPECTED_NAME
    assert path.is_file()


def test_export_default_time_still_matches_name_pattern(
    buffer: ReadingBuffer, tmp_path: Path
) -> None:
    """TCE-02: omitting now still produces a valid file name.
    The name matches the pattern; the value is not asserted.
    """
    assert NAME_PATTERN.fullmatch(export_csv(buffer, tmp_path).name)


def test_export_header_has_expected_columns_in_order(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-03: the CSV header lists the reading columns.
    Columns appear in the documented order.
    """
    columns, _ = read_rows(export_csv(buffer, tmp_path, FIXED_TIME))
    assert columns == COLUMNS


def test_export_row_count_equals_buffer_length(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-04: the CSV has one data row per buffered reading.
    Three readings give three rows.
    """
    _, rows = read_rows(export_csv(buffer, tmp_path, FIXED_TIME))
    assert len(rows) == 3


def test_export_cell_values_match_readings(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-05: CSV cells match the buffered readings.
    First and last rows carry the same vehicle ID, speed, RPM, temperature, and fuel.
    """
    _, rows = read_rows(export_csv(buffer, tmp_path, FIXED_TIME))
    for row, reading in ((rows[0], buffer.recent(3)[0]), (rows[-1], buffer.latest())):
        assert reading is not None
        assert row["vehicle_id"] == reading.vehicle_id
        assert float(row["speed_kmh"]) == reading.speed_kmh
        assert int(row["rpm"]) == reading.rpm
        assert float(row["engine_temp_c"]) == reading.engine_temp_c
        assert float(row["fuel_pct"]) == reading.fuel_pct


def test_export_has_no_index_column(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-06: no pandas index column is written.
    The header has exactly six columns.
    """
    columns, _ = read_rows(export_csv(buffer, tmp_path, FIXED_TIME))
    assert len(columns) == 6


def test_export_of_full_buffer_writes_1000_rows(tmp_path: Path) -> None:
    """TCE-07: a full buffer exports every reading.
    A buffer at capacity gives 1000 data rows.
    """
    _, rows = read_rows(export_csv(make_buffer(ReadingBuffer.MAX_READINGS), tmp_path, FIXED_TIME))
    assert len(rows) == 1000


def test_export_creates_missing_directory(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-08: a missing export directory is created.
    The directory exists afterwards and holds the file.
    """
    target = tmp_path / "new_exports"
    path = export_csv(buffer, target, FIXED_TIME)
    assert target.is_dir()
    assert path.parent == target


def test_export_accepts_existing_directory(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-09: an existing export directory is accepted.
    The file is written without error.
    """
    target = tmp_path / "exports"
    target.mkdir()
    assert export_csv(buffer, target, FIXED_TIME).is_file()


def test_export_returns_path_inside_directory(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-10: the returned path is inside the export directory.
    Its resolved parent equals the resolved directory.
    """
    path = export_csv(buffer, tmp_path, FIXED_TIME)
    assert isinstance(path, Path)
    assert path.resolve().parent == tmp_path.resolve()


def test_export_of_empty_buffer_raises_value_error(tmp_path: Path) -> None:
    """TCE-11: exporting an empty buffer fails clearly.
    ValueError mentions that the buffer is empty.
    """
    with pytest.raises(ValueError, match="empty|no readings|no data"):
        export_csv(ReadingBuffer(), tmp_path, FIXED_TIME)


def test_export_of_empty_buffer_writes_nothing(tmp_path: Path) -> None:
    """TCE-12: a failed export leaves no file.
    The directory stays empty after the error.
    """
    with pytest.raises(ValueError):
        export_csv(ReadingBuffer(), tmp_path, FIXED_TIME)
    assert list(tmp_path.iterdir()) == []


def test_export_of_empty_buffer_does_not_create_directory(tmp_path: Path) -> None:
    """TCE-13: a failed export does not create the directory.
    A missing target directory still does not exist afterwards.
    """
    target = tmp_path / "missing"
    with pytest.raises(ValueError):
        export_csv(ReadingBuffer(), target, FIXED_TIME)
    assert not target.exists()


def test_export_with_traversal_segments_never_writes_outside_directory(
    buffer: ReadingBuffer, tmp_path: Path
) -> None:
    """TCE-14: traversal segments cannot escape the export directory.
    The call either raises ValueError with no CSV, or writes only to the resolved directory.
    """
    exports = tmp_path / "exports"
    exports.mkdir()
    directory = exports / ".." / "outside"
    try:
        path = export_csv(buffer, directory, FIXED_TIME)
    except ValueError:
        assert list(tmp_path.glob("**/*.csv")) == []
    else:
        assert path.resolve().parent == directory.resolve()
        assert list(exports.iterdir()) == []


def test_export_does_not_modify_the_buffer(buffer: ReadingBuffer, tmp_path: Path) -> None:
    """TCE-15: exporting leaves the buffer unchanged.
    Length and newest reading are the same before and after.
    """
    before = (len(buffer), buffer.latest())
    export_csv(buffer, tmp_path, FIXED_TIME)
    assert (len(buffer), buffer.latest()) == before


def test_exports_with_different_times_create_distinct_files(
    buffer: ReadingBuffer, tmp_path: Path
) -> None:
    """TCE-16: different export times produce different files.
    Exports one second apart leave two files.
    """
    export_csv(buffer, tmp_path, FIXED_TIME)
    export_csv(buffer, tmp_path, FIXED_TIME + timedelta(seconds=1))
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "readings_20261005T120000Z.csv",
        "readings_20261005T120001Z.csv",
    ]
