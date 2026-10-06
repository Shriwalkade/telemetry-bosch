# Test Spec - Telemetry Reading Buffer

**Feature:** telemetry-reading-buffer (`FEATURE_SLUG = telemetry_reading_buffer`, `STORY_ID = TRB`)
**Scope:** `telemetry/buffer.py` (`ReadingBuffer`)
**Test file:** `tests/test_telemetry_reading_buffer.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 4, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 3.4, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Existing tests are in `tests/test_buffer.py`; the "Legacy test" column names the matching function (`-` = not covered yet).

---

## Conventions

- Helper `make_reading(index)`: `FIXED_TIME + index seconds`, `VEH-001`, speed 80.0, RPM 3000, temp 90.0, fuel 50.0, so readings are distinguishable by timestamp.
- No clock, network, or filesystem dependencies.
- Test names describe behavior; each docstring starts with the case ID (`TRB-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- Synthetic vehicle IDs only.

## Test Cases

### A. Capacity and overflow

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TRB-01 | Capacity constant | `ReadingBuffer.MAX_READINGS` | `1000` | `test_buffer_capacity_is_1000` | Done |
| TRB-02 | Oldest dropped after 1001 appends | Append 1001 readings | `len == 1000`; oldest remaining is reading 1 | `test_buffer_drops_oldest_after_max_appends` | Done |
| TRB-03 | Length matches appends up to capacity | Parametrized: 0, 1, 999, 1000 appends | `len == count` | `test_length_matches_number_of_appends_up_to_capacity` | Done |
| TRB-04 | Repeated overflow keeps the newest 1000 | Append 1500 readings | First is reading 500, last is reading 1499 | - | Done |

### B. Access (`latest`, `recent`)

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TRB-05 | `latest()` returns the newest | Append 3 | Reading 2 | `test_latest_returns_newest_reading` | Done |
| TRB-06 | `latest()` on empty buffer | New buffer | `None` | `test_latest_on_empty_buffer_is_none` | Done |
| TRB-07 | `recent(n)` returns last n, oldest first | Append 10, `recent(3)` | Readings 7, 8, 9 | `test_recent_returns_last_n_oldest_first` | Done |
| TRB-08 | `recent(n)` with fewer than n items | Append 5, `recent(30)` | The 5 existing readings | `test_recent_returns_all_when_fewer_than_requested` | Done |
| TRB-09 | `recent(n)` on empty buffer | New buffer, `recent(30)` | `[]` | `test_recent_on_empty_buffer_is_empty` | Done |
| TRB-10 | `recent(0)` | Append 5, `recent(0)` | `[]` | `test_recent_zero_returns_empty_list` | Done |

### C. Clear

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TRB-11 | `clear()` empties the buffer | Append 5, `clear()` | `len == 0`, `latest()` is `None` | `test_clear_empties_buffer` | Done |
| TRB-12 | Buffer is reusable after `clear()` | `clear()`, then append 1 | `len == 1`, `latest()` equals it | - | Done |

### D. DataFrame conversion

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TRB-13 | Empty buffer gives empty frame with columns | `to_dataframe()` on new buffer | `frame.empty`; columns `timestamp, vehicle_id, speed_kmh, rpm, engine_temp_c, fuel_pct` | `test_empty_buffer_dataframe_has_columns_and_no_rows` | Done |
| TRB-14 | One row per reading | Append 7 | 7 rows, same columns | `test_dataframe_has_one_row_per_reading` | Done |
| TRB-15 | Rows are oldest first and values match | Append 3 with distinct timestamps | Row order and values equal the readings | - | Done |
| TRB-16 | `to_dataframe()` does not change the buffer | Call twice | `len` unchanged; frames equal | - | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Capacity and overflow | 4 | 4 | 0 |
| B. Access | 6 | 6 | 0 |
| C. Clear | 2 | 2 | 0 |
| D. DataFrame conversion | 4 | 4 | 0 |
| **Total** | **16** | **16** | **0** |

## Exit Criteria

- All `TRB-NN` tests pass under `pytest tests/test_telemetry_reading_buffer.py`.
- Phase 4 plan tests present: drops oldest after 1000 (TRB-02), `recent(n)` with fewer items (TRB-08).
- Every `TRB-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.

## Out of Scope

- Behavior of `recent(n)` for negative `n` (not defined in the LLD).
- Validation of appended readings (callers validate at the module boundary).
- Thread safety and persistence.
