# Unit Test Prompt Template (one feature / story at a time)

How to use: copy this file, replace every `{{PLACEHOLDER}}` in the Inputs table, then send it. Do not leave any placeholder unresolved; if one is missing, stop and ask.

## Inputs (fill before use)

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| `{{STORY_ID}}` | Story / feature ID; the only unit of work in this run | `PH2-SIM` |
| `{{FEATURE_NAME}}` | Human-readable feature name | `Telemetry Simulator` |
| `{{FEATURE_SLUG}}` | Lowercase `snake_case` key used in every file name | `simulator` |
| `{{SOURCE_MODULE}}` | Production file under test | `telemetry/simulator.py` |
| `{{SPEC_FILE}}` | Test spec that is the source of truth | `docs/TEST_SPEC_PHASE2.md` |
| `{{TEST_FILE}}` | Test file to create or update, in the existing `tests/` folder | `tests/test_{{FEATURE_SLUG}}.py` |

Planned naming (fixed; do not invent other names):
- Test spec: `docs/TEST_SPEC_<PHASE or FEATURE_SLUG>.md`
- Test file: `tests/test_{{FEATURE_SLUG}}.py`
- Test IDs: `<PREFIX>-NN` as listed in `{{SPEC_FILE}}` (for example `SIM-01`)

---

Role:
You are a software tester responsible for writing, executing, and reporting unit tests for the Vehicle Telemetry Demo (Python 3.11+, Streamlit, pandas, pytest, Ruff). The project is a demonstration only, not a production or vehicle-control system.

Goal:
For the single story **{{STORY_ID}} - {{FEATURE_NAME}}**, write clear, deterministic, and maintainable unit tests in `{{TEST_FILE}}` that implement the test cases in `{{SPEC_FILE}}`, then run them and report the results.

Scope (strict, one story only):
- Work only on `{{SOURCE_MODULE}}`, `{{SPEC_FILE}}`, and `{{TEST_FILE}}`. Do not write or edit tests for any other feature or module.
- Implement only the test cases in `{{SPEC_FILE}}` that belong to `{{STORY_ID}}`. If a case is missing from the spec, list it under "Gaps" in the report instead of adding it.
- Do not touch other files in `tests/`; run them only as a regression check.
- Do not modify production code. If a defect is found, report it; do not hide it or work around it.

Spec as source of truth and file placement:
1. Read `{{SPEC_FILE}}` first. Take the target path from its `Test file:` header; it must equal `{{TEST_FILE}}`. If they differ or the header is missing, stop and report the mismatch.
2. Create or update exactly `{{TEST_FILE}}` (folder `tests/`, name `test_{{FEATURE_SLUG}}.py`). Do not create alternative, duplicate, or differently named files, and no new folders.
3. If `{{TEST_FILE}}` exists, add only cases with status `Gap` and keep `Done` cases unchanged. If it does not exist, create it with all cases for the story.
4. Put the spec ID in each test docstring (for example `SIM-04: ...`) so every spec row maps to one test. Update the spec status (`Gap` to `Done`) and its Coverage Summary only for cases you implemented.
5. Check `docs/REQUIREMENTS_TEST_CASES.csv` for rows of this story; keep its `Test_Case` references valid and do not rename existing tests.

Project Context (read before writing tests):
- Design docs: `docs/TECH_SPEC.md`, `docs/LOW_LEVEL_DESIGN.md`, `docs/IMPLEMENTATION_PLAN.md`. Existing tests in `tests/` show the preferred style; reuse their constants (`FIXED_TIME`, `SEED`) and helpers.
- Modules (all under `telemetry/`; read only the one under test and what it imports):
  - `models.py` (implemented): frozen `Reading` dataclass, `validate_reading` (raises `ValueError`), `reading_to_dict`, and range constants.
  - `simulator.py` (implemented): `SimulatorConfig` (frozen, validated in `__post_init__`) and `Simulator` (`reset()`, `get_next_reading(now)`); no threads or timers, private seeded RNG.
  - `alerts.py` (planned): `AlertThresholds`, `AlertResult`, `check_alerts`.
  - `buffer.py` (planned): `ReadingBuffer` (max 1000, `append`, `clear`, `latest`, `recent`, `to_dataframe`).
  - `export.py` (planned): `export_csv(buffer, directory, now)`.
  - `config.py` (planned): `AppConfig` with presets slow (2.0 s), normal (1.0 s), fast (0.5 s).
  - `app.py`: Streamlit UI only; keep logic out of it.
- Valid ranges (inclusive): speed 0-200 km/h, RPM 0-7000, engine temperature 20-120 C, fuel 0-100 %.
- Alert defaults: high temperature when `engine_temp_c >= 100.0`; low fuel when `fuel_pct <= 10.0`.
- Validation order in `validate_reading`: timezone-aware timestamp, non-blank `vehicle_id`, numeric type (not `bool`), finite value, in range.
- Data safety: synthetic IDs only (for example `VEH-001`); alerts are demo indicators, not safety or diagnostic advice.
- If `{{SOURCE_MODULE}}` is marked planned and does not exist yet, write tests from the Low-Level Design and report that they are expected to fail until it is implemented.

Coverage rules (apply only where the spec for `{{STORY_ID}}` lists the behavior):
- Cover, for each public function/class of `{{SOURCE_MODULE}}`:
  - Normal (happy-path) behavior with typical inputs.
  - Boundary values: just below, at, and just above each limit or threshold (for example 99.9, 100.0, 100.1 C for the temperature alert; 10.1, 10.0, 9.9 % for the fuel alert; and min/max of every valid range).
  - Invalid input and the expected `ValueError`: naive timestamp, blank `vehicle_id`, `bool`, string, `None`, NaN, infinity, out-of-range values. Match on the field name in the message.
  - Edge cases: empty buffer, fewer readings than requested, buffer overflow at 1000 (oldest dropped), zero and negative values.
  - Determinism and state: same seed gives the same sequence, `reset()` restores the original sequence, values never leave their ranges, fuel never increases, per-step change never exceeds the configured step.
  - Export (when present): empty buffer raises, filename pattern `readings_<YYYYMMDDTHHMMSSZ>.csv`, CSV columns `timestamp, vehicle_id, speed_kmh, rpm, engine_temp_c, fuel_pct`, path stays inside the export directory.
  - Configuration: invalid configs are rejected at construction (`min < max` within model limits, initial values inside range, no negative step/noise/rate, interval greater than 0).
- Out of scope: Streamlit rendering, network, hardware, cloud services, and pandas/Streamlit internals.

Constraints:
- Use `pytest`; follow `.github/instructions/test.instructions.md`, `dev.instructions.md`, `lint.instructions.md`, and `security.instructions.md`.
- Name tests by behavior, for example `test_low_fuel_alert_triggers_below_threshold`.
- Keep each test small and focused on one behavior (Arrange, Act, Assert).
- Use `pytest.mark.parametrize` for boundary and multi-input cases.
- Seed every random generator (`SimulatorConfig(seed=...)`); never rely on the global RNG.
- Pass a fixed, timezone-aware UTC `now` instead of reading the real clock; do not touch the network. Use `tmp_path` for any file output, never the real `exports/` folder.
- Compare floats with a tolerance (for example `1e-9`) where arithmetic is involved.
- Use type hints, 100-character lines, and Ruff rules E, F, I, UP, B; avoid unnecessary mocks.
- Never use real VINs, driver details, GPS traces, credentials, or private telemetry files.

Verification & Validation (run from the project root in the project virtual environment):
1. `pytest {{TEST_FILE}} -q` - all tests for this story pass (or fail only as declared for a planned module).
2. `pytest -q` - full suite as a regression check; no previously passing test breaks.
3. Run step 1 twice and confirm identical results (determinism).
4. Optionally `pytest {{TEST_FILE}} --cov={{SOURCE_MODULE}} --cov-report=term-missing` and review uncovered lines.
5. `ruff check {{TEST_FILE}}` and `ruff format --check {{TEST_FILE}}` with no errors.
6. Spot-check fault detection: temporarily change a threshold, range, or comparison (`>=` to `>`) in `{{SOURCE_MODULE}}`, confirm a test fails, then revert exactly.
7. Confirm every `{{STORY_ID}}` row in `{{SPEC_FILE}}` has a test and the related acceptance criteria in `docs/TECH_SPEC.md` section 6 are covered.

Expected Output:
- The created or updated `{{TEST_FILE}}` and the status update in `{{SPEC_FILE}}`; no other files.
- A short report for `{{STORY_ID}}`: spec IDs implemented, tests added, pass/fail counts, coverage summary, defects found, gaps or assumptions, and the commands run with their results.