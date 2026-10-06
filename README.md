# Vehicle Telemetry Demo

A small Python demo that simulates vehicle telemetry and shows it in a live Streamlit dashboard.
It is a demonstration only, not a production or vehicle-control system. All data is synthetic.
Alerts are demo indicators, not safety or diagnostic advice.

## Features

- Synthetic readings (vehicle ID, UTC timestamp, speed km/h, RPM, engine temperature C, fuel %).
- Live metrics and trend charts of the last 30 readings.
- High-temperature and low-fuel alerts with configurable thresholds.
- Start, Stop, Reset, and CSV export with a download button.
- Speed presets: slow (2.0 s), normal (1.0 s), fast (0.5 s).

## Prerequisites

- Python 3.11 or newer

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Run

```powershell
streamlit run app.py
```

## Configuration (optional)

Settings can be provided through environment variables. Blank values are ignored and invalid
values fall back to the defaults with an on-screen message. No secrets are used.

| Variable | Meaning | Default |
|----------|---------|---------|
| `TELEMETRY_SPEED_PRESET` | `slow`, `normal`, or `fast` | `normal` |
| `TELEMETRY_INTERVAL_SEC` | Refresh interval in seconds (greater than 0) | from preset |
| `TELEMETRY_HIGH_TEMP_C` | High temperature alert threshold (20-120 C) | `100.0` |
| `TELEMETRY_LOW_FUEL_PCT` | Low fuel alert threshold (0-100 %) | `10.0` |

## Test and lint

```powershell
pytest
ruff check .
ruff format --check .
```

## Project layout

```text
app.py                 Streamlit dashboard (UI only)
telemetry/
    models.py          Reading definition, ranges, validation
    simulator.py       Deterministic synthetic telemetry generator
    alerts.py          Threshold checks
    buffer.py          In-memory buffer of the last 1000 readings
    export.py          CSV export confined to exports/
    config.py          App settings and presets
tests/                 Unit and headless dashboard tests (test_<feature>.py)
docs/                  Tech spec, design, plan, and per-feature test specs
.github/               Instructions and skills for the test workflow
exports/               Generated CSV files (git-ignored)
```

## Demo script

1. Run `streamlit run app.py` and press **Start**; metrics and charts update every interval.
2. Show the trend charts, then press **Stop** and **Start** to pause and resume.
3. Lower the high-temperature threshold in the sidebar below the current temperature to trigger the alert.
4. Press **Export CSV**, then download the file (it is also saved in `exports/`).
5. Press **Reset** to clear the data and start over.

## Known limitations

- Single synthetic vehicle, in-memory data only; restarting the app discards readings.
- No database, cloud service, hardware connection, or notifications.
- Refresh uses `st.fragment(run_every=...)` and needs Streamlit 1.37 or newer.

## Privacy and safety

- Use synthetic data only; never add real VINs, driver details, or GPS traces.
- Never commit credentials, tokens, `.env` files, or generated exports.
