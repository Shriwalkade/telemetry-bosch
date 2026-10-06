# Test Spec - {{FEATURE_NAME}}

**Feature:** {{FEATURE_NAME}} (`FEATURE_SLUG = {{FEATURE_SLUG}}`, `STORY_ID = {{PREFIX}}`)
**Scope:** `{{SOURCE_MODULE}}` ({{PUBLIC_SYMBOLS}})
**Test file:** `tests/test_{{FEATURE_SLUG}}.py`
**Based on:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) {{PLAN_SECTION}}, [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) section {{LLD_SECTION}}, [test.instructions.md](../.github/instructions/test.instructions.md)

---

## Conventions

- Fixed seed `SEED = 42`; fixed timestamp `FIXED_TIME = 2026-10-05T12:00:00Z` injected via `now`.
- No clock, network, or real filesystem dependencies; use `tmp_path` for file output.
- Boundary and invalid-input cases use `pytest.mark.parametrize`.
- Float comparisons use `FLOAT_TOLERANCE = 1e-9`.
- Test names describe behavior; each docstring starts with the case ID (`{{PREFIX}}-NN`).
- Status: **Planned** = to be written in the test file; **Done** = exists in it.
- Synthetic vehicle IDs only (`VEH-001`).

## Test Cases

### A. {{AREA_NAME}}

| ID | Behavior | Method | Expected | Status |
|----|----------|--------|----------|--------|
| {{PREFIX}}-01 | {{BEHAVIOR}} | {{METHOD}} | {{EXPECTED}} | Planned |

## Coverage Summary

| Area | Total | Done | Planned |
|------|-------|------|---------|
| A. {{AREA_NAME}} | 1 | 0 | 1 |
| **Total** | **1** | **0** | **1** |

## Exit Criteria

- All `{{PREFIX}}-NN` tests pass under `pytest tests/test_{{FEATURE_SLUG}}.py`.
- Every `{{PREFIX}}-NN` ID appears in exactly one test docstring.
- `ruff check` and `ruff format --check` pass for the test file.
- Acceptance criteria from `docs/TECH_SPEC.md` section 6 that relate to this feature are covered.

## Out of Scope

- {{OUT_OF_SCOPE}}
