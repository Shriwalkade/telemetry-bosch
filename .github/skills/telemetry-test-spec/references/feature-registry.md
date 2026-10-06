# Feature Registry (phase to feature mapping)

Single source for planned names. Test spec, test file, and ID prefix are derived from the slug and must not be invented per run.

Naming rules:
- Slug: lowercase `snake_case`, prefixed `telemetry_`.
- Spec: `docs/TEST_SPEC_<slug>.md`
- Test file: `tests/test_<slug>.py`
- Case IDs: `<PREFIX>-NN` (two digits, unique per spec)

| Phase | Feature (user-facing) | Slug | Prefix | Source module | Module status | Legacy test file |
|-------|-----------------------|------|--------|---------------|---------------|------------------|
| 1 | telemetry-data-model | `telemetry_data_model` | `TDM` | `telemetry/models.py` | Implemented | `tests/test_models.py` |
| 2 | telemetry-simulator-core | `telemetry_simulator_core` | `TSC` | `telemetry/simulator.py` | Implemented | `tests/test_simulator.py` |
| 3 | telemetry-alerts | `telemetry_alerts` | `TAL` | `telemetry/alerts.py` | Implemented | `tests/test_alerts.py` |
| 4 | telemetry-reading-buffer | `telemetry_reading_buffer` | `TRB` | `telemetry/buffer.py` | Implemented | `tests/test_buffer.py` |
| 4 | telemetry-csv-export | `telemetry_csv_export` | `TCE` | `telemetry/export.py` | Implemented | `tests/test_export.py` |
| 4 | telemetry-app-config | `telemetry_app_config` | `TAC` | `telemetry/config.py` | Implemented | `tests/test_config.py` |
| 5 | telemetry-dashboard | `telemetry_dashboard` | `TDB` | `app.py` | Implemented | - |

Not unit-tested:
- Phase 0 (setup) and Phase 6 (quality, docs): verified by tooling and the README checklist.
- Phase 5 visuals and live refresh timing: verified by the manual checklist in `docs/IMPLEMENTATION_PLAN.md`; the headless smoke tests (`telemetry_dashboard`) cover state and wiring only.

Per-feature scope hints (source of cases, besides the module and LLD section):

| Slug | LLD section | Plan section | Key behaviors |
|------|-------------|--------------|---------------|
| `telemetry_data_model` | 3.1 | Phase 1 | Validation order, inclusive range limits, `bool`/NaN/inf rejection, `reading_to_dict` keys, frozen `Reading` |
| `telemetry_simulator_core` | 3.2 | Phase 2 | Determinism, reset, ranges, fuel monotonic, step bounds, config validation |
| `telemetry_alerts` | 3.3 | Phase 3 | `>=` 100.0 and `<=` 10.0 boundaries (99.9/100.0/100.1, 10.1/10.0/9.9), `any_active`, invalid thresholds |
| `telemetry_reading_buffer` | 3.4 | Phase 4 | Max 1000 and oldest dropped, `latest()` empty is `None`, `recent(n)` short, `to_dataframe()` columns and empty frame |
| `telemetry_csv_export` | 3.5 | Phase 4 | Empty buffer raises `ValueError`, filename `readings_<YYYYMMDDTHHMMSSZ>.csv`, columns, row count, path confined to directory, directory created |
| `telemetry_app_config` | 3.6 | Phase 4 | Defaults, presets slow 2.0 / normal 1.0 / fast 0.5, interval > 0, unknown preset rejected, env override validation |
| `telemetry_dashboard` | 4 | Phase 5 | Headless `AppTest` smoke: run state, alerts, export, session state |

Existing `docs/TEST_SPEC_PHASE2.md` is the phase-keyed predecessor of `telemetry_simulator_core`; its `SIM-NN` IDs map to `TSC-NN`.
