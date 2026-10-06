# Test Spec - Telemetry Alerts

**Feature:** telemetry-alerts (`FEATURE_SLUG = telemetry_alerts`, `STORY_ID = TAL`)
**Scope:** `telemetry/alerts.py` (`AlertThresholds`, `AlertResult`, `check_alerts`)
**Test file:** `tests/test_telemetry_alerts.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 3, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 3.3, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Existing tests are in `tests/test_alerts.py`; the "Legacy test" column names the matching function (`-` = not covered yet).

---

## Conventions

- Fixed timestamp `FIXED_TIME = 2026-10-05T12:00:00Z`; base reading: speed 80.0, RPM 3000, temp 90.0, fuel 50.0 (no alert).
- No clock, network, or filesystem dependencies.
- Boundary cases are parametrized below, at, and above each threshold.
- Test names describe behavior; each docstring starts with the case ID (`TAL-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- Alerts are demo indicators, not safety or diagnostic advice.

## Test Cases

### A. Thresholds

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAL-01 | Defaults | `AlertThresholds()` | `high_temp_c == 100.0`, `low_fuel_pct == 10.0` | `test_default_thresholds` | Done |
| TAL-02 | Out-of-range thresholds rejected | Parametrized: `high_temp_c` 19.9 and 120.1; `low_fuel_pct` -0.1 and 100.1 | `ValueError` matching the field name | `test_invalid_thresholds_are_rejected` | Done |
| TAL-03 | Thresholds at model range limits accepted | Parametrized: `high_temp_c` 20.0 and 120.0; `low_fuel_pct` 0.0 and 100.0 | No exception | `test_thresholds_at_range_limits_are_accepted` | Done |
| TAL-04 | `AlertThresholds` is frozen | Assign to a field | `FrozenInstanceError` | - | Done |

### B. High temperature (`engine_temp_c >= high_temp_c`)

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAL-05 | Default boundary | Temp 99.9, 100.0, 100.1 with default thresholds | `high_temp` False, True, True | `test_high_temp_alert_boundary` | Done |
| TAL-06 | Custom threshold applies | `high_temp_c=105.0`, temp 102.0 | `high_temp` False | `test_custom_temperature_threshold_applies` | Done |
| TAL-07 | Custom threshold boundary | `high_temp_c=105.0`, temp 104.9, 105.0, 105.1 | False, True, True | - | Done |
| TAL-08 | Alert fires at the model maximum | Temp 120.0 with default thresholds | `high_temp` True | - | Done |

### C. Low fuel (`fuel_pct <= low_fuel_pct`)

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAL-09 | Default boundary | Fuel 10.1, 10.0, 9.9 with default thresholds | `low_fuel` False, True, True | `test_low_fuel_alert_boundary` | Done |
| TAL-10 | Custom threshold applies | `low_fuel_pct=20.0`, fuel 15.0 | `low_fuel` True | `test_custom_fuel_threshold_applies` | Done |
| TAL-11 | Custom threshold boundary | `low_fuel_pct=20.0`, fuel 20.1, 20.0, 19.9 | False, True, True | - | Done |
| TAL-12 | Alert fires at empty tank | Fuel 0.0 with default thresholds | `low_fuel` True | - | Done |

### D. Combined result

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAL-13 | Both alerts active together | Temp 110.0 and fuel 5.0 | `high_temp`, `low_fuel`, `any_active` all True | `test_both_alerts_active_together` | Done |
| TAL-14 | Alerts are independent | Hot with normal fuel; normal temp with low fuel | Only the matching flag is True; `any_active` True | - | Done |
| TAL-15 | Neither alert active | Base reading | All three flags False | `test_no_alert_active_for_normal_reading` | Done |
| TAL-16 | `any_active` truth table | `AlertResult` with (True, False), (False, True), (False, False) | True, True, False | `test_any_active_is_true_when_either_alert_is_set` | Done |
| TAL-17 | `AlertResult` is frozen | Assign to a field | `FrozenInstanceError` | - | Done |

### E. Module isolation

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAL-18 | No Streamlit or simulator dependency | Parse `alerts.py` imports with `ast` | No import of `streamlit` or `telemetry.simulator` | - | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Thresholds | 4 | 4 | 0 |
| B. High temperature | 4 | 4 | 0 |
| C. Low fuel | 4 | 4 | 0 |
| D. Combined result | 5 | 5 | 0 |
| E. Module isolation | 1 | 1 | 0 |
| **Total** | **18** | **18** | **0** |

## Exit Criteria

- All `TAL-NN` tests pass under `pytest tests/test_telemetry_alerts.py`.
- Boundary tests match the spec defaults (100 C, 10 %): TAL-05, TAL-09.
- Every `TAL-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.

## Out of Scope

- Banner text and "Demo indicator only" wording (UI, Phase 5).
- Reading validation (see `telemetry_data_model`); `check_alerts` is given valid readings.
- Hysteresis, alert history, or notifications.
