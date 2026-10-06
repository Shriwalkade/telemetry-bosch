# Vehicle Telemetry Demo - Implementation Plan

**Based on:** [TECH_SPEC.md](TECH_SPEC.md) (approved)
**Scope:** MVP / POC only. No production capabilities.

---

## Phase Overview

| Phase | Name | Outcome | Depends on |
|-------|------|---------|------------|
| 0 | Project setup | Runnable skeleton, tooling configured | - |
| 1 | Data model | Validated `Reading` type | 0 |
| 2 | Simulator | Deterministic synthetic readings | 1 |
| 3 | Alerts | Threshold checks with boundary tests | 1 |
| 4 | Session state and export | In-memory buffer, CSV export, config | 1, 2, 3 |
| 5 | Dashboard | Working Streamlit UI with controls | 2, 3, 4 |
| 6 | Quality and docs | Green tests/lint, README, demo script | 5 |

Phases 2 and 3 are independent and can be done in either order.

## Design Decisions

- **Simulator is pure.** `Simulator` holds only generator state (RNG, last values) and returns one `Reading` per call. It does not use threads or timers. This differs from the `start()`/`stop()` methods in the spec's pseudocode.
- **Run state lives in the UI.** Start, stop, and reset are handled with `st.session_state` in `app.py`, because background threads do not work reliably with Streamlit reruns.
- **Refresh mechanism.** Use `st.fragment(run_every=...)` for periodic refresh. This needs Streamlit 1.37 or newer; confirm the installed version in Phase 0.
- **Smooth signals.** Each metric is a bounded random walk from the previous value, not independent random numbers, so trend charts look realistic.
- **Buffer.** A `collections.deque(maxlen=1000)` holds readings. Oldest readings are discarded automatically.

---

## Phase 0 - Project Setup

**Goal:** A repository where `pytest`, `ruff`, and `streamlit run app.py` all execute, even if they do nothing useful yet.

**Tasks**
1. Create a virtual environment: `python -m venv .venv` and activate it.
2. Create `requirements.txt` with `streamlit`, `pandas`, `pytest`, `ruff`. Install, then pin the exact installed versions (`pip freeze`) per the security instructions.
3. Create `pyproject.toml` with Ruff config (line length 100, import sorting enabled) and pytest config (`testpaths = ["tests"]`).
4. Create `.gitignore` containing `.venv/`, `.env`, `exports/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.
5. Create the folder skeleton: `telemetry/__init__.py`, `tests/`, `exports/` (with a `.gitkeep` so the folder exists, while contents stay ignored).
6. Add a placeholder `app.py` that renders a title.

**Deliverables:** `requirements.txt`, `pyproject.toml`, `.gitignore`, empty package and test folders, placeholder `app.py`.

**Exit criteria**
- `pytest` runs (reports "no tests ran" without error).
- `ruff check .` and `ruff format --check .` pass.
- `streamlit run app.py` shows the placeholder page.

---

## Phase 1 - Data Model

**Goal:** One validated, immutable representation of a telemetry reading.

**Tasks** (`telemetry/models.py`)
1. Define a frozen `Reading` dataclass: `timestamp` (UTC-aware `datetime`), `vehicle_id` (str), `speed_kmh` (float), `rpm` (int), `engine_temp_c` (float), `fuel_pct` (float).
2. Define range constants in one place: speed 0-200, RPM 0-7000, temperature 20-120, fuel 0-100.
3. Implement `validate_reading(reading) -> None` that raises `ValueError` with a clear message for: naive timestamp, empty `vehicle_id`, out-of-range value, NaN or non-numeric value.
4. Implement `reading_to_dict(reading)` returning CSV-friendly column names (`timestamp`, `vehicle_id`, `speed_kmh`, `rpm`, `engine_temp_c`, `fuel_pct`).

**Deliverables:** `telemetry/models.py`, `tests/test_models.py`.

**Tests**
- Valid reading passes.
- Each field is rejected just outside its range and accepted exactly at both limits.
- Naive (timezone-less) timestamp is rejected.
- NaN is rejected.

**Exit criteria:** All model tests pass; type hints on all public functions.

---

## Phase 2 - Telemetry Simulator

**Goal:** Reproducible synthetic readings that stay in range and move plausibly.

**Tasks** (`telemetry/simulator.py`)
1. Create `SimulatorConfig` dataclass: `vehicle_id` (default `"VEH-001"`), `seed` (optional int), per-metric min/max, per-metric max step size.
2. Create `Simulator(config)` with `get_next_reading(now: datetime | None = None) -> Reading`. The `now` parameter lets tests inject a timestamp; default is `datetime.now(timezone.utc)`.
3. Update each metric as a bounded random walk, clamped to its range:
   - Speed changes by a small step; RPM is derived from speed plus noise.
   - Temperature rises slowly with RPM and decays toward a baseline.
   - Fuel decreases monotonically by a small amount per reading, never below 0.
4. Add `reset()` that restores initial values and reseeds the RNG.
5. Use a private `random.Random(seed)` instance, not the global RNG.

**Deliverables:** `telemetry/simulator.py`, `tests/test_simulator.py`.

**Tests**
- Same seed produces an identical sequence of 100 readings.
- 1000 readings all pass `validate_reading`.
- Fuel never increases between consecutive readings.
- Consecutive speed difference never exceeds the configured step.
- `reset()` reproduces the original sequence.

**Exit criteria:** Tests pass; a 1000-reading loop in a Python shell runs without errors.

---

## Phase 3 - Alerts

**Goal:** Configurable threshold checks with exact boundary behavior.

**Tasks** (`telemetry/alerts.py`)
1. Create `AlertThresholds` dataclass: `high_temp_c` (default 100.0), `low_fuel_pct` (default 10.0). Validate that values are inside the metric ranges.
2. Create `AlertResult` dataclass: `high_temp: bool`, `low_fuel: bool`, with an `any_active` property.
3. Implement `check_alerts(reading, thresholds) -> AlertResult`.
   - High temperature triggers at `>=` threshold.
   - Low fuel triggers at `<=` threshold.
4. Keep this module free of Streamlit and simulator imports.

**Deliverables:** `telemetry/alerts.py`, `tests/test_alerts.py`.

**Tests** (parametrized)
- Temperature at threshold minus 0.1, at threshold, and above.
- Fuel at threshold plus 0.1, at threshold, and below.
- Both alerts active together; neither active.
- Invalid thresholds raise `ValueError`.

**Exit criteria:** Boundary tests pass and match the spec defaults (100 C, 10%).

---

## Phase 4 - Session State, Export, Config

**Goal:** Everything the dashboard needs that is not drawing.

**Tasks**
1. `telemetry/buffer.py`: `ReadingBuffer` wrapping `deque(maxlen=1000)` with `append(reading)`, `clear()`, `latest()`, `recent(n)`, and `to_dataframe()` (columns match `reading_to_dict`; empty buffer yields an empty DataFrame with those columns).
2. `telemetry/export.py`: `export_csv(buffer, directory="exports", now=None) -> Path`.
   - Filename `readings_<UTC timestamp>.csv` (for example `readings_20261005T143000Z.csv`).
   - Create the directory if missing.
   - Raise a clear error when the buffer is empty.
   - Resolve the output path and confirm it stays inside the export directory.
3. `telemetry/config.py`: `AppConfig` dataclass with defaults for thresholds, interval (seconds), and speed preset (slow 2.0 s, normal 1.0 s, fast 0.5 s). Optional override from environment variables with validation; no secrets are involved.

**Deliverables:** three modules plus `tests/test_buffer.py`, `tests/test_export.py`, `tests/test_config.py`.

**Tests**
- Buffer drops the oldest item after 1000 appends.
- `recent(n)` with fewer than n items returns what exists.
- Export writes a CSV whose columns and row count match the buffer (use `tmp_path`).
- Export of an empty buffer raises the expected error.
- Invalid config values (negative interval, unknown preset) are rejected.

**Exit criteria:** Tests pass; no file is written outside `exports/` during tests.

---

## Phase 5 - Streamlit Dashboard

**Goal:** Single-page UI wiring Phases 2-4 together.

**Tasks** (`app.py`)
1. Initialize `st.session_state` once: `simulator`, `buffer`, `running` (False), `last_export_path` (None).
2. Sidebar:
   - Sliders for high-temp threshold (range per model constants) and low-fuel threshold.
   - Select box for speed preset (slow, normal, fast).
3. Control row: **Start**, **Stop**, **Reset**, **Export CSV** buttons.
   - Start sets `running = True`; Stop sets it False.
   - Reset stops the run, clears the buffer, and calls `simulator.reset()`.
   - Export calls `export_csv`; show `st.success` with the filename, or `st.error` on failure (including the empty buffer case).
   - Offer `st.download_button` for the exported file contents.
4. Live area in an `st.fragment(run_every=interval)` function, active only while `running`:
   - Generate one reading, validate, append to buffer.
   - Show `st.metric` tiles for speed, RPM, temperature, fuel.
   - Show alert banners (`st.warning` or `st.error`) from `check_alerts`, with the message "Demo indicator only".
   - Show line charts of the last 30 readings for each metric.
5. Show a status label (Running / Stopped) and the reading count.
6. When the buffer is empty, show a "Press Start" message instead of empty charts.

**Deliverables:** `app.py`.

**Manual verification checklist**
- Start produces updating values and charts roughly every interval.
- Stop freezes the display; Start resumes without losing history.
- Lowering the temperature threshold below the current value shows the alert immediately.
- Reset clears charts and counts.
- Export creates a file in `exports/` and the download button works.
- Export with no data shows an error message, not a stack trace.

**Exit criteria:** Every checklist item passes in a browser run of `streamlit run app.py`.

---

## Phase 6 - Quality, Documentation, Demo Readiness

**Goal:** A clean repository someone else can run in a few minutes.

**Tasks**
1. Run `pytest`; fix failures; review coverage of boundary cases from the instruction files.
2. Run `ruff check .` and `ruff format .`; resolve all findings.
3. Write `README.md`: purpose and demo disclaimer, prerequisites (Python 3.11+), setup commands, run command (`streamlit run app.py`), test and lint commands, folder overview, known limitations.
4. Confirm `requirements.txt` is pinned and contains only used packages.
5. Security pass against `.github/instructions/security.instructions.md`: no real VINs, GPS, or credentials; `.env`, `.venv/`, `exports/` ignored; export path confined.
6. Write a short demo script (in the README): start, show trend, trigger alert by lowering threshold, export CSV, reset.
7. Test on a clean clone: new virtual environment, install, run.

**Deliverables:** `README.md`, passing test and lint runs.

**Exit criteria:** Spec section 6 acceptance criteria are all checked.

---

## Spec Acceptance Mapping

| Acceptance criterion (spec section 6) | Verified in |
|---|---|
| Simulator readings correct types and ranges | Phase 2 tests |
| Dashboard shows values and trends | Phase 5 checklist |
| Alerts trigger at thresholds | Phase 3 tests, Phase 5 checklist |
| Export produces valid CSV | Phase 4 tests, Phase 5 checklist |
| Start/Stop/Reset work | Phase 5 checklist |
| Config persists during session | Phase 5 checklist (`st.session_state`) |
| Tests pass | Phase 6 |
| Lint passes | Phase 6 |
| No hard-coded credentials or real VINs | Phase 6 security pass |

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Streamlit reruns reset objects | Keep simulator and buffer in `st.session_state`, created once |
| Auto-refresh unavailable in older Streamlit | Check version in Phase 0; fall back to a rerun loop with `time.sleep` if needed |
| Charts flicker on refresh | Chart only the last 30 rows; update inside the fragment only |
| Scope creep (multi-vehicle, database) | Treat anything in spec section 8 as out of scope |
