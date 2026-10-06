# Test Spec - Telemetry Data Model

**Feature:** telemetry-data-model (`FEATURE_SLUG = telemetry_data_model`, `STORY_ID = TDM`)
**Scope:** `telemetry/models.py` (`Reading`, `validate_reading`, `reading_to_dict`, range constants)
**Test file:** `tests/test_telemetry_data_model.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 1, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 3.1, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Existing coverage lives in `tests/test_models.py`; the "Legacy test" column names the matching function (`-` = not covered yet).

---

## Conventions

- Fixed timestamp `FIXED_TIME = 2026-10-05T12:00:00Z`; base reading `VEH-001`, speed 80.0, RPM 3000, temp 90.0, fuel 50.0.
- No clock, network, or filesystem dependencies.
- Boundary and invalid-input cases use `pytest.mark.parametrize`; error messages are matched on the field name.
- Test names describe behavior; each docstring starts with the case ID (`TDM-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- Synthetic vehicle IDs only.

## Test Cases

### A. Valid reading and immutability

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-01 | Valid reading passes | `validate_reading` on the base reading | Returns `None`, no exception | `test_valid_reading_passes_validation` | Done |
| TDM-02 | `Reading` is frozen | Assign to a field | `FrozenInstanceError` (an `AttributeError`) | `test_reading_is_immutable` | Done |

### B. Ranges (inclusive)

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-03 | Limits accepted at both ends | Parametrized per field: speed 0/200, RPM 0/7000, temp 20/120, fuel 0/100 | No exception | `test_range_limits_are_accepted_at_both_ends` | Done |
| TDM-04 | Values just outside rejected | Each field at min - step and max + step (0.1 for floats, 1 for RPM) | `ValueError` naming the field | `test_value_just_outside_range_is_rejected` | Done |
| TDM-05 | Range constants have documented values | Compare the eight `*_MIN` / `*_MAX` constants | 0/200, 0/7000, 20/120, 0/100 | - | Done |
| TDM-06 | `int` accepted for float fields | `speed_kmh=80`, `engine_temp_c=90`, `fuel_pct=50` | No exception | - | Done |

### C. Timestamp and vehicle ID

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-07 | Naive timestamp rejected | `datetime` without tzinfo | `ValueError` matching `timestamp` | `test_naive_timestamp_is_rejected` | Done |
| TDM-08 | Non-UTC aware timestamp accepted | Timestamp with `+02:00` offset | No exception | `test_non_utc_aware_timestamp_is_accepted` | Done |
| TDM-09 | Non-datetime timestamp rejected | Parametrized: `"2026-10-05"`, `None`, `0` | `ValueError` matching `timestamp` | - | Done |
| TDM-10 | Blank `vehicle_id` rejected | Parametrized: `""`, `"   "` | `ValueError` matching `vehicle_id` | `test_empty_vehicle_id_is_rejected` | Done |
| TDM-11 | Non-string `vehicle_id` rejected | Parametrized: `None`, `123` | `ValueError` matching `vehicle_id` | - | Done |

### D. Numeric type and finiteness

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-12 | NaN and infinity rejected in every numeric field | Parametrized: field x (`nan`, `inf`, `-inf`) | `ValueError` naming the field | `test_non_finite_value_is_rejected` (speed only) | Done |
| TDM-13 | Non-numeric values rejected in every numeric field | Parametrized: field x (`"fast"`, `None`, `True`) | `ValueError` naming the field (`bool` is not a number) | `test_non_numeric_value_is_rejected` (temp only) | Done |

### E. Validation order

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-14 | Timestamp is checked before `vehicle_id` | Naive timestamp and blank `vehicle_id` together | Message names `timestamp` | - | Done |
| TDM-15 | `vehicle_id` is checked before numeric fields | Blank `vehicle_id` and out-of-range speed together | Message names `vehicle_id` | - | Done |
| TDM-16 | Numeric fields are checked in field order | Invalid speed and invalid fuel together | Message names `speed_kmh` | - | Done |

### F. Conversion

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TDM-17 | `reading_to_dict` keys are the CSV columns in order | `list(reading_to_dict(reading))` | `timestamp, vehicle_id, speed_kmh, rpm, engine_temp_c, fuel_pct` | `test_reading_to_dict_uses_csv_column_names` | Done |
| TDM-18 | `reading_to_dict` values equal the fields | Compare each value with the reading attribute | All equal, including `timestamp` | - | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Valid reading and immutability | 2 | 2 | 0 |
| B. Ranges | 4 | 4 | 0 |
| C. Timestamp and vehicle ID | 5 | 5 | 0 |
| D. Numeric type and finiteness | 2 | 2 | 0 |
| E. Validation order | 3 | 3 | 0 |
| F. Conversion | 2 | 2 | 0 |
| **Total** | **18** | **18** | **0** |

## Exit Criteria

- All `TDM-NN` tests pass under `pytest tests/test_telemetry_data_model.py`.
- Every `TDM-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.
- Phase 1 plan tests present: valid passes (TDM-01), each field rejected just outside and accepted at limits (TDM-03, TDM-04), naive timestamp rejected (TDM-07), NaN rejected (TDM-12).

## Out of Scope

- Simulator, alerts, buffer, export, and UI behavior.
- Locale or string formatting of timestamps.
