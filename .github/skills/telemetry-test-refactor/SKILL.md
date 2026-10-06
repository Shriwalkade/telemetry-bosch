---
name: telemetry-test-refactor
description: 'Behavior-preserving refactor of the pytest tests of one Vehicle Telemetry Demo feature (tests/test_<feature_slug>.py): rename tests, add two-line docstrings, tidy structure, same test count. Use when asked to refactor, rename, clean up, or add docstrings to the unit tests of a telemetry feature, story, or phase.'
argument-hint: 'Feature slug or name, e.g. telemetry_alerts'
---

# Telemetry Test Refactor

Refactors one test file in place without changing what it verifies. One feature per run.

## Inputs

Resolve from the [feature registry](../telemetry-test-spec/references/feature-registry.md):

| Placeholder | Value |
|-------------|-------|
| `{{STORY_ID}}` | Registry prefix |
| `{{FEATURE_NAME}}` / `{{FEATURE_SLUG}}` | Registry |
| `{{SOURCE_MODULE}}` | Registry source module (read-only) |
| `{{SPEC_FILE}}` | `docs/TEST_SPEC_{{FEATURE_SLUG}}.md` |
| `{{TEST_FILE}}` | `tests/test_{{FEATURE_SLUG}}.py` |

If the feature is unknown or several are named, ask for exactly one. If `{{TEST_FILE}}` does not exist, stop and report. For a legacy test file named in the registry (for example `tests/test_simulator.py`), refactor that file only when the user names it explicitly.

## Scope (strict)

- Edit only `{{TEST_FILE}}`. Do not edit other files in `tests/`, `telemetry/`, or `app.py`.
- If a function is named, refactor only that function.
- Do not add, remove, or move tests; new coverage belongs to the `telemetry-unit-tests` skill.
- Read `{{SPEC_FILE}}` first; its `Test file:` header must equal `{{TEST_FILE}}`, else stop and report. Preserve spec IDs already in docstrings; do not invent IDs or change spec status.

## Refactoring rules

1. Preserve behavior: inputs, seeds, constants, expected values, tolerances, and expected exceptions stay identical; same collected test count; do not weaken, strengthen, or reorder assertions in a way that changes outcomes. `parametrize` `ids` or helper extraction only if count and semantics are unchanged.
2. Naming: tests `test_<unit>_<behavior>_<condition>` in `snake_case`, describing behavior not implementation; fixtures, helpers, variables descriptive `snake_case`; constants `UPPER_SNAKE_CASE`; no `r`, `x`, `tmp` (comprehension variables excepted). Rename with IDE symbol rename; names unique per module. Update `docs/REQUIREMENTS_TEST_CASES.csv` `Test_Case` only where it names the function.
3. Docstrings: every test has exactly two lines: line 1 what is verified (spec ID first when present), line 2 condition or expected outcome. Imperative or present tense, 100-character limit. Fixtures and helpers: one line.
4. Style: follow `.github/instructions/*.instructions.md`; keep Arrange, Act, Assert with one behavior per test; add type hints; remove only dead code and unused imports. No new mocks, dependencies, clock or network access, or real data; keep seeded RNG and injected `FIXED_TIME`. No logic rewrites or formatting churn beyond Ruff.

## Verification (project root, project virtual environment)

1. Before: `pytest {{TEST_FILE}} -q` and `pytest {{TEST_FILE}} --collect-only -q`; record counts and names. Also record `pytest -q`.
2. After: repeat; pass/fail counts identical and every test still collected (only names differ). Full-suite result matches the earlier one.
3. `ruff check {{TEST_FILE}}` and `ruff format --check {{TEST_FILE}}` clean.
4. Confirm no file other than `{{TEST_FILE}}` changed.

## Output

- The refactored `{{TEST_FILE}}`; no other files.
- Short report: old-to-new name mapping, before/after counts, commands and results, tests left unchanged with reason.
