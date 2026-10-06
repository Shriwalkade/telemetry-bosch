---
name: telemetry-test-spec
description: 'Create a test spec (docs/TEST_SPEC_<feature_slug>.md) for one feature or phase of the Vehicle Telemetry Demo: data model, simulator core, alerts, reading buffer, CSV export, app config. Use when asked to write, draft, or generate a test spec, test plan, or test cases for a telemetry feature, story, or phase.'
argument-hint: 'Feature slug or name, e.g. telemetry_alerts'
---

# Telemetry Test Spec

Creates one test spec for one feature. It never writes test code.

## Inputs

Resolve from the [feature registry](./references/feature-registry.md) using the user's feature name or phase:

| Placeholder | Source |
|-------------|--------|
| `{{FEATURE_NAME}}` | Registry, feature column |
| `{{FEATURE_SLUG}}` | Registry, slug column |
| `{{PREFIX}}` | Registry, prefix column (also the story ID) |
| `{{SOURCE_MODULE}}` | Registry, source module column |

If the feature is not in the registry, or one request names several features, stop and ask which single feature to use. Do not invent a slug, prefix, or file name.

## Procedure

1. Read the source module (if Implemented) or the LLD section for it (if Planned), the matching Plan section, and the registry key behaviors.
2. Read `docs/REQUIREMENTS_TEST_CASES.csv` rows and `docs/TECH_SPEC.md` section 6 for the feature, and the legacy test file if it exists, to avoid contradicting existing behavior.
3. Copy [the template](./assets/test-spec-template.md) to `docs/TEST_SPEC_{{FEATURE_SLUG}}.md` and fill every placeholder. Do not overwrite an existing spec; if the file exists, ask whether to update it.
4. Write cases grouped in lettered areas, IDs `{{PREFIX}}-01` upward with no gaps. Each case has a behavior, method, expected result, and status `Planned`.
5. Cover, where the module has the behavior: happy path; boundaries (just below, at, just above each limit, inclusive/exclusive as specified); invalid input with `ValueError` and field name; edge cases (empty, fewer than requested, overflow, zero, negative); determinism and state; configuration rejection at construction.
6. Add a Phase-keyed predecessor reference column only when a phase spec exists (currently only simulator, see registry).
7. Fill the Coverage Summary with counts that match the tables, plus Exit Criteria and Out of Scope.

## Rules

- Spec only: do not create or edit anything under `tests/` or `telemetry/`.
- The `Test file:` header must be exactly `tests/test_{{FEATURE_SLUG}}.py`.
- One feature per spec. Do not add cases for other modules; put them in Out of Scope.
- Every case must be testable without Streamlit, network, hardware, or the real clock.
- Synthetic data only (`VEH-001`); no real VINs, driver details, GPS traces, or credentials.
- Alerts are demo indicators, not safety or diagnostic advice.
- Valid ranges (inclusive): speed 0-200 km/h, RPM 0-7000, engine temperature 20-120 C, fuel 0-100 %.

## Validation

- IDs are unique and sequential; counts in the Coverage Summary match.
- Boundary cases include below, at, and above for every limit named in the LLD.
- No placeholder (`{{...}}`) remains in the file.
- Report: file path, number of cases per area, and any assumptions or open questions.
