---
description: Development standards for the Python vehicle telemetry demo
applyTo: "**/*.py"
---

# Development Instructions

- Target Python 3.11 or newer; use type hints on all public functions.
- Keep simulation (`telemetry/simulator.py`), models, and alert logic separate from the Streamlit UI in `app.py`.
- Use UTC timestamps and explicit units in names or fields (`speed_kmh`, `engine_temp_c`, `fuel_pct`).
- Keep simulation ranges and alert thresholds configurable; avoid hard-coded magic numbers.
- Validate readings at module boundaries and handle missing or invalid values gracefully.
- Prefer small, single-purpose functions and descriptive names.
- Do not add hardware, cloud, or database integrations unless requested.
