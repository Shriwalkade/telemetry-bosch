# Test Spec - Telemetry Dashboard (headless smoke)

**Feature:** telemetry-dashboard (`FEATURE_SLUG = telemetry_dashboard`, `STORY_ID = TDB`)
**Scope:** `app.py` (Streamlit UI wiring), exercised headless with `streamlit.testing.v1.AppTest`
**Test file:** `tests/test_telemetry_dashboard.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 5 manual checklist, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section 4, [test.instructions.md](../.github/instructions/test.instructions.md)
**Related:** Complements, and does not replace, the manual browser checklist in the Implementation Plan (visual layout, chart rendering, live refresh timing).

---

## Conventions

- Each test runs the app with `AppTest.from_file` from a `tmp_path` working directory, so `exports/` is a temp folder and the real folder is never touched.
- `TELEMETRY_*` environment variables are cleared by the fixture unless a case sets them (via `monkeypatch`).
- No network, real clock assertions, or real browser. Values are never asserted exactly, only structure and state.
- Test names describe behavior; each docstring starts with the case ID (`TDB-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.

## Test Cases

### A. Run state and controls

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| TDB-01 | Opens in the stopped, empty state | Run the app | No exception; `Status: Stopped | Readings: 0`; "Press Start" message | Done |
| TDB-02 | Start shows current values | Click Start | `Status: Running | Readings: 1`; four metric tiles with the metric labels | Done |
| TDB-03 | Stop freezes the display | Start, then Stop | Readings stay at 1; status Stopped | Done |
| TDB-04 | Start after Stop resumes without losing history | Start, Stop, Start | Readings grow from 1 to 2 | Done |
| TDB-05 | Reset clears everything | Start, then Reset | Stopped, 0 readings, "Press Start" message | Done |

### B. Alerts

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| TDB-06 | Lower temperature threshold shows the alert immediately | Start, set the temperature slider to its minimum | Error banner with "High engine temperature" and "Demo indicator only" | Done |
| TDB-07 | Higher fuel threshold shows the low fuel warning | Start, set the fuel slider to its maximum | Warning banner with "Low fuel" and "Demo indicator only" | Done |

### C. Export

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| TDB-08 | Export with no data shows an error, not an exception | Click Export CSV on an empty buffer | Error text "Export failed"; no exception | Done |
| TDB-09 | Export with data writes a file and offers a download | Start, then Export CSV | One `readings_*.csv` in the temp `exports/`; success message with its name; download button present | Done |

### D. Configuration and session

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| TDB-10 | Invalid environment settings fall back to defaults | `TELEMETRY_SPEED_PRESET=turbo` | No exception; error notice about invalid environment settings; preset select shows `normal` | Done |
| TDB-11 | Buffer persists across reruns | Rerun the app | Same `ReadingBuffer` object in `session_state` | Done |

## Coverage Summary

| Area | Total | Done | Done |
|------|-------|------|---------|
| A. Run state and controls | 5 | 5 | 0 |
| B. Alerts | 2 | 2 | 0 |
| C. Export | 2 | 2 | 0 |
| D. Configuration and session | 2 | 2 | 0 |
| **Total** | **11** | **11** | **0** |

## Exit Criteria

- All `TDB-NN` tests pass under `pytest tests/test_telemetry_dashboard.py`.
- Every `TDB-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.

## Out of Scope

- Visual layout, chart appearance, and real-time refresh cadence (manual browser checklist).
- Dashboard response time under 2 seconds (measured manually or in the quality phase).
- Logic already covered by the module specs (alerts, buffer, export, config, simulator).
