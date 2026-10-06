"""CSV export of buffered readings, confined to one export directory."""

from datetime import UTC, datetime
from pathlib import Path

from telemetry.buffer import ReadingBuffer

DEFAULT_EXPORT_DIR = "exports"


def export_csv(
    buffer: ReadingBuffer,
    directory: str | Path = DEFAULT_EXPORT_DIR,
    now: datetime | None = None,
) -> Path:
    """Write the buffer to `readings_<YYYYMMDDTHHMMSSZ>.csv` and return the file path."""
    if len(buffer) == 0:
        raise ValueError("no readings to export: the buffer is empty")

    moment = now or datetime.now(UTC)
    if moment.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    filename = f"readings_{moment.astimezone(UTC):%Y%m%dT%H%M%SZ}.csv"

    export_dir = Path(directory).resolve()
    target = (export_dir / filename).resolve()
    if target.parent != export_dir:
        raise ValueError("export path must stay inside the export directory")

    export_dir.mkdir(parents=True, exist_ok=True)
    buffer.to_dataframe().to_csv(target, index=False)
    return target
