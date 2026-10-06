# Test Spec - Telemetry Simulator Core

**Feature:** telemetry-simulator-core (`FEATURE_SLUG = telemetry_simulator_core`, `STORY_ID = TSC`)
**Scope:** `telemetry/simulator.py` (`SimulatorConfig`, `Simulator`)
**Test file:** `tests/test_telemetry_simulator_core.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 2, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md), [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** [TEST_SPEC_PHASE2.md](TEST_SPEC_PHASE2.md) covers the same module by phase; this spec is keyed by feature. Phase 2 reference IDs (`SIM-NN`) are listed per case for traceability.

---

## Conventions

- Fixed seed `SEED = 42`; fixed timestamp `FIXED_TIME = 2026-10-05T12:00:00Z` injected via `now`.
- No clock, network, or filesystem dependencies. The only clock-dependent test (default timestamp) asserts timezone awareness, not value.
- Boundary and invalid-input cases use `pytest.mark.parametrize`.
- Float step comparisons use `FLOAT_TOLERANCE = 1e-9`.
- Test names describe behavior (`test_<subject>_<expected behavior>`); each docstring starts with the case ID (`TSC-NN`).
- Status: **Planned** = to be written in `tests/test_telemetry_simulator_core.py`; **Done** = exists in that file.
- Synthetic vehicle IDs only (`VEH-001`, `VEH-002`).

## Test Cases

### A. Determinism and reset

| ID | Behavior | Method | Expected | Phase 2 ref | Status |
|----|----------|--------|----------|-------------|--------|
| TSC-01 | Same seed gives same sequence | Two simulators, seed 42, 100 readings each | Sequences equal | SIM-01 | Done |
| TSC-02 | Different seeds differ | Seeds 1 and 2, 20 readings | Sequences not equal | SIM-02 | Done |
| TSC-03 | `reset()` reproduces sequence | Generate 100, `reset()`, generate 100 | Both sequences equal | SIM-03 | Done |
| TSC-04 | `reset()` mid-run restores initial state | Generate 10, `reset()`, take first reading | Equals first reading of a fresh simulator | SIM-04 | Done |
| TSC-05 | Simulator does not use the global RNG | Seed `random` globally to different values between two same-seed simulators | Sequences still equal | SIM-05 | Done |
| TSC-06 | `seed=None` is accepted | Generate 10 readings | All pass `validate_reading`; no exception | SIM-06 | Done |

### B. Range and validity

| ID | Behavior | Method | Expected | Phase 2 ref | Status |
|----|----------|--------|----------|-------------|--------|
| TSC-07 | 1000 readings are valid | `validate_reading` on each | No exception | SIM-07 | Done |
| TSC-08 | Stays in range with extreme steps | `max_speed_step_kmh=100`, `max_temp_step_c=50` | All valid (clamping works) | SIM-08 | Done |
| TSC-09 | Speed clamps at limits | Initial speed at max (and min), large step, 200 readings | `min_kmh <= speed <= max_kmh` on all | SIM-09 | Done |
| TSC-10 | RPM stays within `[rpm_min, rpm_max]` | High `rpm_noise` and `rpm_per_kmh`, 1000 readings | All in range; values are `int` | SIM-10 | Done |
| TSC-11 | Narrowed custom ranges are respected | Config with tighter min/max for every metric | All readings inside the custom ranges | SIM-11 | Done |

### C. Fuel behavior

| ID | Behavior | Method | Expected | Phase 2 ref | Status |
|----|----------|--------|----------|-------------|--------|
| TSC-12 | Fuel never increases | 1000 readings | `fuel[n+1] <= fuel[n]` | SIM-12 | Done |
| TSC-13 | Fuel never below minimum | `fuel_initial_pct=0.5`, step 0.4, 100 readings | Minimum is exactly `0.0` | SIM-13 | Done |
| TSC-14 | Fuel starts at or below initial value | First reading | `fuel <= fuel_initial_pct` | SIM-14 | Done |
| TSC-15 | Zero fuel step keeps fuel constant | `max_fuel_step_pct=0` | All fuel values equal initial | SIM-15 | Done |

### D. Step limits and signal behavior

| ID | Behavior | Method | Expected | Phase 2 ref | Status |
|----|----------|--------|----------|-------------|--------|
| TSC-16 | Speed step bounded | `max_speed_step_kmh=3.0`, 1000 readings | `abs(delta) <= 3.0 + tol` | SIM-16 | Done |
| TSC-17 | Temperature step bounded | `max_temp_step_c=0.5`, 1000 readings | `abs(delta) <= 0.5 + tol` | SIM-17 | Done |
| TSC-18 | Zero speed step keeps speed constant | `max_speed_step_kmh=0` | All speeds equal initial | SIM-18 | Done |
| TSC-19 | RPM follows speed | Zero RPM noise, `rpm_idle=800`, `rpm_per_kmh=30` | `rpm == round(800 + speed * 30)` (clamped) | SIM-19 | Done |
| TSC-20 | Temperature decays toward baseline | `temp_initial_c` well above baseline, heat gain 0 | Temperature decreases monotonically toward baseline | SIM-20 | Done |
| TSC-21 | Temperature rises under load | `temp_initial_c` below baseline, high speed, cooling rate 0 | Temperature trends upward | SIM-21 | Done |

### E. Output metadata

| ID | Behavior | Method | Expected | Phase 2 ref | Status |
|----|----------|--------|----------|-------------|--------|
| TSC-22 | Injected timestamp and vehicle ID used | `now=FIXED_TIME`, `vehicle_id="VEH-002"` | Reading carries both | SIM-22 | Done |
| TSC-23 | Default timestamp is UTC-aware | No `now` | `timestamp.utcoffset() is not None` | SIM-23 | Done |
| TSC-24 | Default `vehicle_id` | `SimulatorConfig()` | `"VEH-001"` | SIM-24 | Done |
| TSC-25 | Naive `now` is flagged by validation | Pass naive datetime | `validate_reading` raises `ValueError` | SIM-25 | Done |
| TSC-26 | `Simulator()` with no config works | `Simulator()` | Returns a valid reading | SIM-26 | Done |

### F. Configuration validation

`SimulatorConfig(**overrides)` must raise `ValueError` for each case (parametrized); match on the field name in the message.

| ID | Override | Phase 2 ref | Status |
|----|----------|-------------|--------|
| TSC-27 | `vehicle_id=" "` | SIM-27 | Done |
| TSC-28 | `speed_min_kmh=100, speed_max_kmh=50` (min > max) | SIM-28 | Done |
| TSC-29 | `speed_max_kmh=250` (above model limit) | SIM-29 | Done |
| TSC-30 | `rpm_max=9000` | SIM-30 | Done |
| TSC-31 | `temp_min_c=10.0` | SIM-31 | Done |
| TSC-32 | `fuel_min_pct=-1.0` | SIM-32 | Done |
| TSC-33 | `speed_initial_kmh=300.0` | SIM-33 | Done |
| TSC-34 | `fuel_initial_pct=101.0` | SIM-34 | Done |
| TSC-35 | `max_speed_step_kmh=-1.0` | SIM-35 | Done |
| TSC-36 | `speed_min_kmh == speed_max_kmh` (min must be < max) | SIM-36 | Done |
| TSC-37 | `temp_initial_c` outside the configured temp range | SIM-37 | Done |
| TSC-38 | Each remaining negative parameter: `rpm_noise`, `rpm_per_kmh`, `temp_heat_gain_c`, `temp_cooling_rate`, `max_temp_step_c`, `max_fuel_step_pct` | SIM-38 | Done |
| TSC-39 | Boundary acceptance: initial values exactly at min and max are accepted | SIM-39 | Done |
| TSC-40 | `SimulatorConfig` is frozen (assignment raises `FrozenInstanceError`) | SIM-40 | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Determinism and reset | 6 | 6 | 0 |
| B. Range and validity | 5 | 5 | 0 |
| C. Fuel | 4 | 4 | 0 |
| D. Steps and signals | 6 | 6 | 0 |
| E. Metadata | 5 | 5 | 0 |
| F. Config validation | 14 | 14 | 0 |
| **Total** | **40** | **40** | **0** |

## Exit Criteria

- All `TSC-NN` tests pass under `pytest tests/test_telemetry_simulator_core.py`.
- Plan-required checks present: same-seed determinism (TSC-01), 1000 valid readings (TSC-07), fuel never increases (TSC-12), speed step bound (TSC-16), reset reproduces sequence (TSC-03).
- `ruff check` and `ruff format --check` pass for the test file.
- Every `TSC-NN` ID appears in exactly one test docstring.

## Out of Scope

- Threads, timers, or real-time pacing (the simulator is pure by design).
- Alert evaluation, buffering and export, and UI.
- Statistical realism of the signals beyond the bounded, directional checks above.
