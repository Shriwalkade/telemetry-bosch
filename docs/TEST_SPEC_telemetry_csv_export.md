# Test Spec - Telemetry CSV Export

**Feature:** telemetry-csv-export (`FEATURE_SLUG = telemetry_csv_export`, `STORY_ID = TCE`)
**Scope:** `telemetry/export.py` (`export_csv`)
**Test file:** `tests/test_telemetry_csv_export.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 4, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 3.5, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Existing tests are in `tests/test_export.py`; the "Legacy test" column names the matching function (`-` = not covered yet).

---

## Conventions

- Fixed `now = FIXED_TIME = 2026-10-05T12:00:00Z`, so the file name is `readings_20261005T120000Z.csv`.
- Fixture buffer: 3 readings, `VEH-001`, speed 80.0 + index, RPM 3000, temp 90.0, fuel 50.0.
- Always export to `tmp_path`; never write to the real `exports/` folder.
- CSV is read back with `csv.DictReader`.
- Test names describe behavior; each docstring starts with the case ID (`TCE-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- Synthetic vehicle IDs only.

## Test Cases

### A. File name and content

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TCE-01 | File name from injected UTC time | `export_csv(buffer, tmp_path, FIXED_TIME)` | Returned path is `tmp_path / "readings_20261005T120000Z.csv"` and the file exists | `test_export_writes_csv_with_expected_name_columns_and_rows` | Done |
| TCE-02 | Default `now` still matches the name pattern | `export_csv(buffer, tmp_path)` | Name matches `readings_\d{8}T\d{6}Z\.csv` (pattern only, not value) | - | Done |
| TCE-03 | Header columns | Read CSV header | `timestamp, vehicle_id, speed_kmh, rpm, engine_temp_c, fuel_pct`, in this order | `test_export_writes_csv_with_expected_name_columns_and_rows` | Done |
| TCE-04 | Row count equals buffer length | Export 3 readings | 3 data rows | `test_export_writes_csv_with_expected_name_columns_and_rows` | Done |
| TCE-05 | Cell values match the readings | Compare first and last row with the readings | `vehicle_id`, `speed_kmh`, `rpm`, `engine_temp_c`, `fuel_pct` equal as text | - | Done |
| TCE-06 | No index column | Read CSV header | Header has exactly 6 columns | - | Done |
| TCE-07 | Full buffer exports 1000 rows | Buffer filled to capacity | 1000 data rows | - | Done |

### B. Directory handling

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TCE-08 | Missing directory is created | Directory `tmp_path / "new_exports"` does not exist | Directory exists; file is inside it | `test_export_creates_missing_directory` | Done |
| TCE-09 | Existing directory is accepted | Directory already created | File written; no error | - | Done |
| TCE-10 | Returns a `Path` inside the directory | Resolve the returned path | `path.resolve().parent == directory.resolve()` | `test_export_creates_missing_directory` | Done |

### C. Empty buffer

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TCE-11 | Empty buffer raises | `export_csv(ReadingBuffer(), tmp_path, FIXED_TIME)` | `ValueError` with a message about empty or no data | `test_export_of_empty_buffer_raises_and_writes_nothing` | Done |
| TCE-12 | Empty buffer writes nothing | Same call | `tmp_path` has no files | `test_export_of_empty_buffer_raises_and_writes_nothing` | Done |
| TCE-13 | Empty buffer does not create the directory | Missing target directory | Directory still does not exist after the error | - | Done |

### D. Path confinement

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TCE-14 | Traversal segments never write outside the directory | Directory `exports/../outside` | Either `ValueError` and no CSV anywhere under `tmp_path`, or the file lands in the resolved directory and `exports/` stays empty | `test_export_with_traversal_segments_never_writes_outside_directory` | Done |

### E. Side effects

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TCE-15 | Export does not modify the buffer | Compare `len` and `latest()` before and after | Unchanged | - | Done |
| TCE-16 | Two exports with different `now` create two files | Exports at 12:00:00Z and 12:00:01Z | Two distinct file names, both present | - | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. File name and content | 7 | 7 | 0 |
| B. Directory handling | 3 | 3 | 0 |
| C. Empty buffer | 3 | 3 | 0 |
| D. Path confinement | 1 | 1 | 0 |
| E. Side effects | 2 | 2 | 0 |
| **Total** | **16** | **16** | **0** |

## Exit Criteria

- All `TCE-NN` tests pass under `pytest tests/test_telemetry_csv_export.py`.
- No file is written outside `tmp_path` during tests.
- Every `TCE-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.

## Out of Scope

- Streamlit download button and success or error messages (Phase 5).
- File permissions, disk-full errors, and symlink handling.
- Reading validation and buffer behavior (see `telemetry_data_model`, `telemetry_reading_buffer`).
