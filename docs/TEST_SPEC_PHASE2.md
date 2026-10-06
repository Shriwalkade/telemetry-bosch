# Phase 2 Test Spec - Telemetry Simulator

**Scope:** `telemetry/simulator.py` (`SimulatorConfig`, `Simulator`)
**Test file:** `tests/test_simulator.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 2, [test.instructions.md](../.github/instructions/test.instructions.md)

---

## Conventions

- Fixed seed `SEED = 42`; fixed timestamp `FIXED_TIME = 2026-10-05T12:00:00Z` injected via `now`.
- No clock, network, or filesystem dependencies. The only clock-dependent test (default timestamp) asserts timezone awareness, not value.
- Boundary and invalid-input cases use `pytest.mark.parametrize`.
- Float step comparisons use `FLOAT_TOLERANCE = 1e-9`.
- Test names describe behavior (`test_<subject>_<expected behavior>`).

## Test Cases

Status: **Done** = exists in `tests/test_simulator.py`; **Gap** = to be added.

### A. Determinism and reset

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| SIM-01 | Same seed gives same sequence | Two simulators, seed 42, 100 readings each | Sequences equal | Done |
| SIM-02 | Different seeds differ | Seeds 1 and 2, 20 readings | Sequences not equal | Done |
| SIM-03 | `reset()` reproduces sequence | Generate 100, `reset()`, generate 100 | Both sequences equal | Done |
| SIM-04 | `reset()` mid-run restores initial state | Generate 10, `reset()`, take first reading | Equals first reading of a fresh simulator | Gap |
| SIM-05 | Simulator does not use the global RNG | Seed `random` globally to different values between two same-seed simulators | Sequences still equal | Gap |
| SIM-06 | `seed=None` is accepted | Generate 10 readings | All pass `validate_reading`; no exception | Gap |

### B. Range and validity

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| SIM-07 | 1000 readings are valid | `validate_reading` on each | No exception | Done |
| SIM-08 | Stays in range with extreme steps | `max_speed_step_kmh=100`, `max_temp_step_c=50` | All valid (clamping works) | Done |
| SIM-09 | Speed clamps at limits | Initial speed at max (and min), large step, 200 readings | `min_kmh <= speed <= max_kmh` on all | Gap |
| SIM-10 | RPM stays within `[rpm_min, rpm_max]` | High `rpm_noise` and `rpm_per_kmh`, 1000 readings | All in range; values are `int` | Gap |
| SIM-11 | Narrowed custom ranges are respected | Config with tighter min/max for every metric | All readings inside the custom ranges | Gap |

### C. Fuel behavior

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| SIM-12 | Fuel never increases | 1000 readings | `fuel[n+1] <= fuel[n]` | Done |
| SIM-13 | Fuel never below minimum | `fuel_initial_pct=0.5`, step 0.4, 100 readings | Minimum is exactly `0.0` | Done |
| SIM-14 | Fuel starts at or below initial value | First reading | `fuel <= fuel_initial_pct` | Gap |
| SIM-15 | Zero fuel step keeps fuel constant | `max_fuel_step_pct=0` | All fuel values equal initial | Gap |

### D. Step limits and signal behavior

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| SIM-16 | Speed step bounded | `max_speed_step_kmh=3.0`, 1000 readings | `abs(delta) <= 3.0 + tol` | Done |
| SIM-17 | Temperature step bounded | `max_temp_step_c=0.5`, 1000 readings | `abs(delta) <= 0.5 + tol` | Done |
| SIM-18 | Zero speed step keeps speed constant | `max_speed_step_kmh=0` | All speeds equal initial | Gap |
| SIM-19 | RPM follows speed | Zero RPM noise, `rpm_idle=800`, `rpm_per_kmh=30` | `rpm == round(800 + speed * 30)` (clamped) | Gap |
| SIM-20 | Temperature decays toward baseline | `temp_initial_c` well above baseline, heat gain 0 | Temperature decreases monotonically toward baseline | Gap |
| SIM-21 | Temperature rises under load | `temp_initial_c` below baseline, high speed, cooling rate 0 | Temperature trends upward | Gap |

### E. Output metadata

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| SIM-22 | Injected timestamp and vehicle ID used | `now=FIXED_TIME`, `vehicle_id="VEH-002"` | Reading carries both | Done |
| SIM-23 | Default timestamp is UTC-aware | No `now` | `timestamp.utcoffset() is not None` | Done |
| SIM-24 | Default `vehicle_id` | `SimulatorConfig()` | `"VEH-001"` | Gap |
| SIM-25 | Naive `now` is flagged by validation | Pass naive datetime | `validate_reading` raises `ValueError` | Gap |
| SIM-26 | `Simulator()` with no config works | `Simulator()` | Returns a valid reading | Gap |

### F. Configuration validation

`SimulatorConfig(**overrides)` must raise `ValueError` for each case (parametrized).

| ID | Override | Status |
|----|----------|--------|
| SIM-27 | `vehicle_id=" "` | Done |
| SIM-28 | `speed_min_kmh=100, speed_max_kmh=50` (min > max) | Done |
| SIM-29 | `speed_max_kmh=250` (above model limit) | Done |
| SIM-30 | `rpm_max=9000` | Done |
| SIM-31 | `temp_min_c=10.0` | Done |
| SIM-32 | `fuel_min_pct=-1.0` | Done |
| SIM-33 | `speed_initial_kmh=300.0` | Done |
| SIM-34 | `fuel_initial_pct=101.0` | Done |
| SIM-35 | `max_speed_step_kmh=-1.0` | Done |
| SIM-36 | `speed_min_kmh == speed_max_kmh` (min must be < max) | Gap |
| SIM-37 | `temp_initial_c` outside the configured temp range | Gap |
| SIM-38 | Each remaining negative parameter: `rpm_noise`, `rpm_per_kmh`, `temp_heat_gain_c`, `temp_cooling_rate`, `max_temp_step_c`, `max_fuel_step_pct` | Gap |
| SIM-39 | Boundary acceptance: initial values exactly at min and max are accepted | Gap |
| SIM-40 | `SimulatorConfig` is frozen (assignment raises `FrozenInstanceError`) | Gap |

## Coverage Summary

| Area | Total | Done | Gap |
|------|-------|------|-----|
| A. Determinism and reset | 6 | 3 | 3 |
| B. Range and validity | 5 | 2 | 3 |
| C. Fuel | 4 | 2 | 2 |
| D. Steps and signals | 6 | 2 | 4 |
| E. Metadata | 5 | 2 | 3 |
| F. Config validation | 14 | 9 | 5 |
| **Total** | **40** | **20** | **20** |

## Exit Criteria (from Implementation Plan)

- All Phase 2 tests pass under `pytest`.
- Five plan-required tests are present: same-seed determinism (SIM-01), 1000 valid readings (SIM-07), fuel never increases (SIM-12), speed step bound (SIM-16), reset reproduces sequence (SIM-03).
- `ruff check .` and `ruff format --check .` pass.
- A 1000-reading loop in a Python shell runs without errors.

## Out of Scope

- Threads, timers, or real-time pacing (the simulator is pure by design).
- Alert evaluation (Phase 3), buffering and export (Phase 4), UI (Phase 5).
- Statistical realism of the signals beyond the bounded, directional checks above.
