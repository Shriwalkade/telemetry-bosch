import csv
from datetime import UTC, datetime
from pathlib import Path

import pytest

from telemetry.buffer import ReadingBuffer
from telemetry.export import export_csv
from telemetry.models import Reading

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
EXPECTED_NAME = "readings_20261005T120000Z.csv"
COLUMNS = ["timestamp", "vehicle_id", "speed_kmh", "rpm", "engine_temp_c", "fuel_pct"]


@pytest.fixture
def buffer() -> ReadingBuffer:
    items = ReadingBuffer()
    for index in range(3):
        items.append(
            Reading(
                timestamp=FIXED_TIME,
                vehicle_id="VEH-001",
                speed_kmh=80.0 + index,
                rpm=3000,
                engine_temp_c=90.0,
                fuel_pct=50.0,
            )
        )
    return items


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def test_export_writes_csv_with_expected_name_columns_and_rows(
    buffer: ReadingBuffer, tmp_path: Path
) -> None:
    path = export_csv(buffer, tmp_path, FIXED_TIME)
    columns, rows = read_rows(path)
    assert path == tmp_path / EXPECTED_NAME
    assert columns == COLUMNS
    assert len(rows) == 3


def test_export_creates_missing_directory(buffer: ReadingBuffer, tmp_path: Path) -> None:
    target = tmp_path / "new_exports"
    path = export_csv(buffer, target, FIXED_TIME)
    assert path.parent == target
    assert path.is_file()


def test_export_of_empty_buffer_raises_and_writes_nothing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty|no readings|no data"):
        export_csv(ReadingBuffer(), tmp_path, FIXED_TIME)
    assert list(tmp_path.iterdir()) == []


def test_export_with_traversal_segments_never_writes_outside_directory(
    buffer: ReadingBuffer, tmp_path: Path
) -> None:
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
