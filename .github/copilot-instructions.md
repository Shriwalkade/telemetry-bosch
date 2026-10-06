# Vehicle Telemetry Demo

## Project Goal
Build a simple Python application that simulates vehicle telemetry and displays it in a live dashboard. This is a demonstration only, not a production or vehicle-control system.

## Demo Scope
- Simulate timestamped readings for vehicle ID, speed (km/h), RPM, engine temperature (C), and fuel level (%).
- Display current readings and recent trends.
- Flag configurable high-temperature and low-fuel thresholds.
- Provide start, stop, and reset controls for the simulation.
- Export recorded readings to CSV.

## Suggested Tech Stack
- Python 3.11 or newer.
- Streamlit for the dashboard.
- pandas for tabular data and CSV export.
- pytest for unit tests and Ruff for linting and formatting.
- Use an isolated virtual environment and list dependencies in `requirements.txt`.

## Suggested Folder Structure 
```text
app.py                 Streamlit entry point
telemetry/
    simulator.py       Synthetic telemetry generation
    models.py          Reading definitions and validation
    alerts.py          Threshold checks
tests/                 Unit tests
requirements.txt       Dependencies
README.md              Setup and run instructions
```

## Implementation Guidelines
- Keep simulation and alert logic separate from the dashboard.
- Use descriptive names, type hints, and small functions.
- Use UTC timestamps and explicit units for every metric.
- Validate inputs and handle missing or invalid readings gracefully.
- Keep simulation ranges and alert thresholds configurable.
- Use reproducible random seeds in tests.
- Avoid hardware connections, cloud services, and unnecessary abstractions for the initial demo.

## Testing and Quality
- Test reading validation, simulation ranges, and alert threshold boundaries.
- Run tests with `pytest`.
- Check linting with `ruff check .` and formatting with `ruff format --check .`.
- Document installation and the dashboard command, `streamlit run app.py`, in the README.

## Privacy and Safety
- Use synthetic data only; do not collect real VINs, driver information, or GPS traces.
- Never commit credentials, tokens, or private telemetry files.
- Keep local environments, secrets, and generated exports out of version control.
- Treat alerts as demo indicators, not safety or diagnostic advice.

## Detailed Instruction Files
Follow these file-scoped instructions in addition to this document:
- [Development](instructions/dev.instructions.md) for `**/*.py`
- [Testing](instructions/test.instructions.md) for `tests/**/*.py`
- [Linting](instructions/lint.instructions.md) for `**/*.py`
- [Security and compliance](instructions/security.instructions.md) for all files