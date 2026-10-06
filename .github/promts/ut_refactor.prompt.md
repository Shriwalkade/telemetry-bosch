# Unit Test Refactor Prompt Template (one feature / story at a time)

How to use: copy this file, replace every `{{PLACEHOLDER}}` in the Inputs table, then send it. Do not leave any placeholder unresolved; if one is missing, stop and ask.

## Inputs (fill before use)

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| `{{STORY_ID}}` | Story / feature ID; the only unit of work in this run | `PH2-SIM` |
| `{{FEATURE_NAME}}` | Human-readable feature name | `Telemetry Simulator` |
| `{{FEATURE_SLUG}}` | Lowercase `snake_case` key used in every file name | `simulator` |
| `{{SOURCE_MODULE}}` | Production file the tests cover (read-only) | `telemetry/simulator.py` |
| `{{SPEC_FILE}}` | Test spec that is the source of truth | `docs/TEST_SPEC_PHASE2.md` |
| `{{TEST_FILE}}` | Existing test file to refactor, in the `tests/` folder | `tests/test_{{FEATURE_SLUG}}.py` |

Planned naming (fixed; do not invent other names):
- Test spec: `docs/TEST_SPEC_<PHASE or FEATURE_SLUG>.md`
- Test file: `tests/test_{{FEATURE_SLUG}}.py`
- Test IDs: `<PREFIX>-NN` as listed in `{{SPEC_FILE}}` (for example `SIM-01`)

---

Role:
You are a software engineer refactoring the existing pytest unit tests of the Vehicle Telemetry Demo (Python 3.11+, pytest, Ruff). This is a behavior-preserving refactoring: the tests must verify exactly what they verified before.

Goal:
For the single story **{{STORY_ID}} - {{FEATURE_NAME}}**, refactor only `{{TEST_FILE}}` (names, docstrings, structure) without changing what it verifies.

Scope (strict, one story only):
- Work only on `{{TEST_FILE}}`. Do not edit any other file in `tests/`, any file under `telemetry/`, or `app.py`.
- If a function in `{{TEST_FILE}}` is named in the request, refactor only that function.
- Do not add, remove, or move tests across files; new coverage belongs to the unit test prompt, not this one.

Spec as source of truth and file placement:
1. Read `{{SPEC_FILE}}` first. Take the test file path from its `Test file:` header; it must equal `{{TEST_FILE}}`. If they differ or the header is missing, stop and report the mismatch.
2. Refactor in place at exactly `{{TEST_FILE}}`. Do not create, rename, or duplicate test files, and no new folders.
3. Keep each test traceable to its spec ID: if a docstring already carries an ID (for example `SIM-04`), preserve it in line 1; do not invent IDs. Do not change the spec status.
4. Keep `docs/REQUIREMENTS_TEST_CASES.csv` references valid for this story (see rule 2 below).

Refactoring rules (strict):
1. Preserve behavior.
   - Do not change what a test arranges, executes, or asserts: inputs, seeds, constants, expected values, tolerances, and expected exceptions stay identical.
   - Do not add, remove, merge, or split tests; keep the same parametrized cases and the same number of collected tests.
   - Do not weaken, strengthen, or reorder assertions in a way that changes pass/fail outcomes.
   - Use `@pytest.mark.parametrize` `ids` or helper extraction only if it leaves the test count and semantics unchanged.
2. Naming.
   - Test functions: `test_<unit>_<behavior>_<condition>` in `snake_case`, describing the expected behavior (for example `test_low_fuel_alert_triggers_below_threshold`), not the implementation.
   - Fixtures, helpers, and variables: descriptive `snake_case`; constants in `UPPER_SNAKE_CASE`; no single-letter or ambiguous names (`r`, `x`, `tmp`) except trivial comprehension variables.
   - Rename using IDE symbol rename so all references are updated; keep names unique within a module.
   - Keep the test ID mapping to `docs/REQUIREMENTS_TEST_CASES.csv` valid: if a test is renamed, update the `Test_Case` reference only when the CSV names the function.
3. Docstrings.
   - Every test function gets a docstring of exactly two lines: line 1 states what is verified; line 2 states the condition or expected outcome.
   - Imperative or present tense, no trailing details about implementation, 100-character line limit.
   - Fixtures and helpers get a one-line docstring.
4. Style and quality.
   - Follow `.github/instructions/test.instructions.md`, `dev.instructions.md`, `lint.instructions.md`, and `security.instructions.md`.
   - Keep Arrange, Act, Assert structure with one behavior per test; add type hints; remove only dead code and unused imports.
   - Do not introduce mocks, new dependencies, clock access, network access, or real data; keep seeded RNG and injected `FIXED_TIME`.
   - Make no other changes (no logic rewrites, no new coverage, no formatting-only churn beyond Ruff).

Verification (run from the project root in the project virtual environment):
1. Before refactoring, run `pytest {{TEST_FILE}} -q` and record the pass count and the list from `pytest {{TEST_FILE}} --collect-only -q`.
2. After refactoring, run both commands again: the pass/fail counts must be identical and every test must still be collected (only names differ).
3. Run `pytest -q` as a regression check; the full-suite result must match its pre-refactor result.
4. Run `ruff check {{TEST_FILE}}` and `ruff format --check {{TEST_FILE}}` with no findings.
5. Confirm that no file other than `{{TEST_FILE}}` changed.

Expected Output:
- The refactored `{{TEST_FILE}}`; no other files.
- A short report for `{{STORY_ID}}`: old-to-new test name mapping, before/after test counts, commands run and results, and any test left unchanged with the reason.
