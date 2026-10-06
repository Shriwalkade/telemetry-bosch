---
name: telemetry-unit-tests
description: 'Write, run, and report pytest unit tests for one feature of the Vehicle Telemetry Demo from its test spec (docs/TEST_SPEC_<feature_slug>.md) into tests/test_<feature_slug>.py. Use when asked to implement, write, add, or generate unit tests for a telemetry feature, story, or phase.'
argument-hint: 'Feature slug or name, e.g. telemetry_alerts'
---

# Telemetry Unit Tests

Implements the test cases of one spec in one test file, runs them, and reports. One feature per run.

## Inputs

Resolve from the [feature registry](../telemetry-test-spec/references/feature-registry.md):

| Placeholder | Value |
|-------------|-------|
| `{{STORY_ID}}` | Registry prefix |
| `{{FEATURE_NAME}}` / `{{FEATURE_SLUG}}` | Registry |
| `{{SOURCE_MODULE}}` | Registry source module |
| `{{SPEC_FILE}}` | `docs/TEST_SPEC_{{FEATURE_SLUG}}.md` |
| `{{TEST_FILE}}` | `tests/test_{{FEATURE_SLUG}}.py` |

If the feature is unknown or several are named, ask for exactly one. If `{{SPEC_FILE}}` does not exist, stop and suggest the `telemetry-test-spec` skill first.

## Scope (strict)

- Touch only `{{SOURCE_MODULE}}` (read), `{{SPEC_FILE}}` (status update), and `{{TEST_FILE}}`.
- Implement only cases in the spec; list missing cases as Gaps in the report instead of adding them.
- Do not edit other files in `tests/`; run them only as a regression check.
- Do not modify production code. Report defects; do not hide or work around them.
- If the module is Planned and absent, write tests from the LLD and report that they are expected to fail until it exists.

## Procedure

1. Read `{{SPEC_FILE}}`. Its `Test file:` header must equal `{{TEST_FILE}}`; if not, stop and report.
2. Read `{{SOURCE_MODULE}}`, the LLD section, and one existing test file in `tests/` for style; reuse `FIXED_TIME` and `SEED`.
3. Create or update exactly `{{TEST_FILE}}`. If it exists, add only `Planned` cases and keep `Done` ones. No other file names or folders.
4. Put the spec ID at the start of each test docstring (for example `TAL-04: ...`); one test (or one parametrized test) per ID.
5. Update the spec: set implemented cases to `Done` and refresh the Coverage Summary.
6. Check `docs/REQUIREMENTS_TEST_CASES.csv` rows for this feature; keep `Test_Case` references valid and do not rename existing tests.
7. Run the verification below and report.

## Test rules

- `pytest`; follow `.github/instructions/test.instructions.md`, `dev.instructions.md`, `lint.instructions.md`, `security.instructions.md`.
- Name by behavior (`test_low_fuel_alert_triggers_below_threshold`); Arrange, Act, Assert; one behavior per test.
- `pytest.mark.parametrize` for boundary and multi-input cases.
- Seed every RNG (`SimulatorConfig(seed=...)`); never use the global RNG.
- Inject a fixed timezone-aware UTC `now`; no network; `tmp_path` for files, never the real `exports/`.
- Float tolerance `1e-9` where arithmetic is involved.
- Type hints, 100-character lines, Ruff rules E, F, I, UP, B; avoid unnecessary mocks.
- Match `ValueError` on the field name. Validation order in `validate_reading`: timezone-aware timestamp, non-blank `vehicle_id`, numeric type (not `bool`), finite, in range.
- Defaults: high temperature when `engine_temp_c >= 100.0`; low fuel when `fuel_pct <= 10.0`.
- Out of scope: Streamlit rendering, network, hardware, cloud, pandas/Streamlit internals.
- Synthetic data only; no real VINs, driver details, GPS traces, credentials.

## Verification (project root, project virtual environment)

1. `pytest {{TEST_FILE}} -q` passes (or fails only as declared for a Planned module).
2. `pytest -q` as a regression check; nothing previously passing breaks.
3. Repeat step 1 and confirm identical results.
4. Optional: `pytest {{TEST_FILE}} --cov={{SOURCE_MODULE}} --cov-report=term-missing`.
5. `ruff check {{TEST_FILE}}` and `ruff format --check {{TEST_FILE}}` clean.
6. Spot-check: temporarily change a threshold, range, or comparison (`>=` to `>`) in `{{SOURCE_MODULE}}`, confirm a test fails, revert exactly.
7. Every `{{STORY_ID}}` row in `{{SPEC_FILE}}` has a test.

## Output

- Updated `{{TEST_FILE}}` and spec status; no other files.
- Short report: IDs implemented, tests added, pass/fail counts, coverage, defects, gaps and assumptions, commands run with results.
