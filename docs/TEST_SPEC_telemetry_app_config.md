# Test Spec - Telemetry App Config

**Feature:** telemetry-app-config (`FEATURE_SLUG = telemetry_app_config`, `STORY_ID = TAC`)
**Scope:** `telemetry/config.py` (`AppConfig`)
**Test file:** `tests/test_telemetry_app_config.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 4, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 3.6, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Existing tests are in `tests/test_config.py`; the "Legacy test" column names the matching function (`-` = not covered yet).

---

## Conventions

- No clock, network, or filesystem dependencies; environment variables are set only through `monkeypatch`.
- Boundary and invalid-input cases use `pytest.mark.parametrize`; error messages are matched on the field name.
- Test names describe behavior; each docstring starts with the case ID (`TAC-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- No secrets are involved in this module.

## Test Cases

### A. Defaults and presets

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAC-01 | Defaults | `AppConfig()` | `thresholds == AlertThresholds()` (100.0 C, 10.0 %), `speed_preset == "normal"`, `interval_sec == 1.0` | `test_defaults` | Done |
| TAC-02 | Preset sets the refresh interval | Parametrized: `slow` 2.0, `normal` 1.0, `fast` 0.5 | `interval_sec` equals the preset value | `test_preset_sets_refresh_interval` | Done |
| TAC-03 | Custom thresholds are kept | `AppConfig(thresholds=AlertThresholds(high_temp_c=95.0, low_fuel_pct=15.0))` | Values unchanged on `config.thresholds` | - | Done |

### B. Validation

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAC-04 | Non-positive interval rejected | Parametrized: `-1.0`, `0.0` | `ValueError` matching `interval` | `test_non_positive_interval_is_rejected` | Done |
| TAC-05 | Unknown preset rejected | Parametrized: `"turbo"`, `""`, `"NORMAL"` (case-sensitive) | `ValueError` matching `preset` | `test_unknown_preset_is_rejected` | Done |
| TAC-06 | Smallest positive interval accepted | `interval_sec=0.001` | No exception | - | Done |
| TAC-07 | `AppConfig` is frozen | Assign to a field | `FrozenInstanceError` | - | Done |

### C. Environment overrides (`AppConfig.from_env()`)

| ID | Behavior | Method | Expected | Legacy test | Status |
|----|----------|--------|----------|-------------|--------|
| TAC-08 | No overrides gives defaults | Empty mapping, or blank values, passed to `AppConfig.from_env(environ)` | Equals `AppConfig()` | - | Done |
| TAC-09 | Valid overrides are applied | `TELEMETRY_SPEED_PRESET=fast`, `TELEMETRY_HIGH_TEMP_C=95`, `TELEMETRY_LOW_FUEL_PCT=15.5`, `TELEMETRY_INTERVAL_SEC=0.25` | Config reflects every value | - | Done |
| TAC-10 | Invalid overrides are rejected | Unknown preset, negative interval, non-numeric text, out-of-range threshold | `ValueError` naming the setting, as with direct construction | - | Done |

## Design Decisions

- `from_env(environ=None)` reads `os.environ` by default; tests pass a mapping so no real environment is touched.
- Variables: `TELEMETRY_SPEED_PRESET`, `TELEMETRY_INTERVAL_SEC`, `TELEMETRY_HIGH_TEMP_C`, `TELEMETRY_LOW_FUEL_PCT`; blank values count as unset.
- An explicit `interval_sec` (argument or variable) overrides the preset-derived interval.

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Defaults and presets | 3 | 3 | 0 |
| B. Validation | 4 | 4 | 0 |
| C. Environment overrides | 3 | 3 | 0 |
| **Total** | **10** | **10** | **0** |

## Exit Criteria

- All `TAC-NN` tests pass under `pytest tests/test_telemetry_app_config.py`.
- Defaults match the spec (100 C, 10 %, normal 1.0 s) and presets are slow 2.0 s, normal 1.0 s, fast 0.5 s.
- Every implemented `TAC-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.

## Out of Scope

- Persistence across sessions (handled by `st.session_state` in Phase 5).
- Threshold range validation details (see `telemetry_alerts`).
- Reading `.env` files from disk.
