---
description: Unit testing standards for the telemetry demo
applyTo: "tests/**/*.py"
---

# Test Instructions

- Use `pytest`; place tests in `tests/` named `test_<module>.py`.
- Cover reading validation, simulator value ranges, and alert threshold boundaries (just below, at, and above).
- Seed random generators so tests are deterministic.
- Use `pytest.mark.parametrize` for boundary cases; avoid network, filesystem, or clock dependencies (use `tmp_path` and injected timestamps).
- Test names should describe behavior, e.g. `test_low_fuel_alert_triggers_below_threshold`.
- Run with `pytest` before committing.
