"""In-memory bounded store of recent readings."""

from collections import deque
from dataclasses import fields

import pandas as pd

from telemetry.models import Reading, reading_to_dict

READING_COLUMNS: tuple[str, ...] = tuple(field.name for field in fields(Reading))


class ReadingBuffer:
    """Keeps the newest `MAX_READINGS` readings; the oldest are dropped automatically."""

    MAX_READINGS = 1000

    def __init__(self) -> None:
        self._items: deque[Reading] = deque(maxlen=self.MAX_READINGS)

    def __len__(self) -> int:
        return len(self._items)

    def append(self, reading: Reading) -> None:
        """Add a reading, dropping the oldest when full."""
        self._items.append(reading)

    def clear(self) -> None:
        """Remove all readings."""
        self._items.clear()

    def latest(self) -> Reading | None:
        """Return the newest reading, or None when empty."""
        return self._items[-1] if self._items else None

    def recent(self, n: int) -> list[Reading]:
        """Return up to the last `n` readings, oldest first."""
        if n < 0:
            raise ValueError(f"n must not be negative, got {n}")
        if n == 0:
            return []
        return list(self._items)[-n:]

    def to_dataframe(self) -> pd.DataFrame:
        """Return all readings as a frame; an empty buffer keeps the column names."""
        rows = [reading_to_dict(reading) for reading in self._items]
        return pd.DataFrame(rows, columns=list(READING_COLUMNS))
