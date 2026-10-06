---
description: Compliance and sensitive data handling
applyTo: "**"
---

# Security and Compliance Instructions

- Use synthetic data only; never include real VINs, driver details, or GPS traces.
- Never hard-code or commit credentials, tokens, or private telemetry files.
- Load configuration from environment variables or ignored `.env` files; keep `.env`, `.venv/`, and generated exports in `.gitignore`.
- Validate and sanitize any user input (uploads, parameters) before use.
- Pin dependencies in `requirements.txt` and avoid unmaintained packages.
- Treat alerts as demo indicators, not safety or diagnostic advice.
