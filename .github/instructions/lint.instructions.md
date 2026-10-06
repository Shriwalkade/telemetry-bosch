---
description: Linting and formatting standards
applyTo: "**/*.py"
---

# Linting Instructions

- Use Ruff for linting and formatting; configure it in `pyproject.toml`.
- Code must pass `ruff check .` and `ruff format --check .`.
- Line length 100; sort imports; no unused imports or variables.
- Use `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
