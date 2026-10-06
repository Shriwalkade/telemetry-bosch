# Vehicle Telemetry Visualization - Technical Specification
**Status:** Approved (MVP / POC)  
**Date:** 2026-10-05  
**Scope:** Demonstration only

---

## 1. Overview

A lightweight Python-based telemetry dashboard that simulates vehicle sensor readings and displays them in real-time. This MVP prioritizes simplicity and rapid iteration over production features like persistence, multi-user, or cloud integration.

---

## 2. Functional Requirements

### 2.1 Telemetry Simulation
- Generate synthetic readings at configurable intervals:
  - **Vehicle ID** (string): e.g., "VEH-001"
  - **Speed** (km/h): range 0–200
  - **RPM** (revolutions/min): range 0–7000
  - **Engine Temperature** (°C): range 20–120
  - **Fuel Level** (%): range 0–100
- Include UTC timestamp for each reading
- Support start, stop, and reset controls

### 2.2 Real-Time Dashboard
- Display current sensor values
- Show recent trend (last 20–30 readings as line charts)
- Refresh every 1–2 seconds

### 2.3 Alerts & Thresholds
- Flag high engine temperature (configurable, default ≥100°C)
- Flag low fuel level (configurable, default ≤10%)
- Display alert status in the UI

### 2.4 Data Export
- Export recorded readings to CSV (columns: timestamp, vehicle_id, speed, rpm, temperature, fuel)
- Save to `exports/` folder with timestamp in filename

### 2.5 Configuration
- Allow users to set:
  - Alert thresholds
  - Simulation speed (slow, normal, fast)
  - Reading interval (seconds)
- Store config in a simple JSON or YAML file (or UI dropdowns)

---

## 3. Non-Functional Requirements

### 3.1 Technology Stack
- **Language:** Python 3.11+
- **Dashboard UI:** Streamlit (rapid prototyping, built-in widgets)
- **Data Processing:** pandas (CSV export, trending)
- **Testing:** pytest
- **Linting & Format:** Ruff

### 3.2 Performance (MVP)
- In-memory storage only (no database)
- Max 1000 readings in memory; older readings discarded
- Dashboard response time < 2 seconds

### 3.3 Data Safety
- Use synthetic data only; no real VINs or GPS traces
- No credentials or secrets in code
- Local `.env` for configuration (not committed)

### 3.4 Usability
- Single-page Streamlit app
- Self-explanatory controls and labels
- Error messages for invalid configs or export failures

---

## 4. Architecture

### 4.1 Module Breakdown
```
app.py                   # Streamlit UI entry point
telemetry/
  ├─ simulator.py        # Synthetic reading generator
  ├─ models.py           # Data classes and validation
  ├─ alerts.py           # Threshold checks
  └─ config.py           # Configuration loader (optional)
tests/
  ├─ test_simulator.py
  ├─ test_models.py
  └─ test_alerts.py
docs/
  └─ TECH_SPEC.md        # This file
exports/                 # CSV output folder (git-ignored)
requirements.txt         # Dependencies
README.md                # Setup and usage
.gitignore               # .env, venv/, exports/
```

### 4.2 Data Flow
```
Simulator (generate reading)
    ↓
Models (validate & structure)
    ↓
Memory (append to list)
    ↓
Alerts (check thresholds)
    ↓
Streamlit (render UI)
    ↓
User (export or reset)
```

### 4.3 Key Classes/Functions (pseudocode)

**models.py**
```python
@dataclass
class Reading:
    timestamp: datetime
    vehicle_id: str
    speed_kmh: float
    rpm: int
    engine_temp_c: float
    fuel_pct: float

def validate_reading(reading: Reading) -> bool
```

**simulator.py**
```python
class Simulator:
    def __init__(self, interval_sec: float = 1.0)
    def start()
    def stop()
    def get_next_reading() -> Reading
```

**alerts.py**
```python
class AlertChecker:
    def __init__(self, temp_threshold_c: float = 100.0, fuel_threshold_pct: float = 10.0)
    def check(reading: Reading) -> dict  # {"high_temp": bool, "low_fuel": bool}
```

**app.py**
```python
# Streamlit layout
# - Header & status
# - Current readings display
# - Charts (recent trends)
# - Alert banners
# - Control buttons: Start, Stop, Reset, Export
# - Config sidebar: thresholds, interval
```

---

## 5. User Flows

### 5.1 View Dashboard
1. User opens `streamlit run app.py`
2. Dashboard displays "Stopped" state
3. User clicks **Start**
4. Simulation begins; readings update every ~1–2 seconds
5. Charts populate as history builds

### 5.2 Export Data
1. User clicks **Export** button
2. App saves CSV to `exports/readings_<timestamp>.csv`
3. Success message displays with filename
4. User can download file

### 5.3 Configure Alerts
1. User opens sidebar
2. Adjusts **High Temp Threshold** slider (e.g., 105°C)
3. Adjusts **Low Fuel Threshold** slider (e.g., 15%)
4. Changes apply immediately; alerts re-check active readings

---

## 6. Acceptance Criteria

- [ ] Simulator generates 5 readings with correct data types and ranges
- [ ] Dashboard displays current values and trends
- [ ] Alerts trigger at configured thresholds
- [ ] Export produces valid CSV with all readings
- [ ] Start/Stop/Reset controls work
- [ ] Config persists during session (no reload required)
- [ ] All tests pass (`pytest`)
- [ ] Code passes linting (`ruff check .`)
- [ ] No hard-coded credentials or real VINs

---

## 7. Known Limitations (MVP)

- In-memory only; restart loses data
- Single vehicle ID only (no multi-vehicle support)
- No real-time alerts (desktop notifications, email, etc.)
- No database or cloud integration
- Streamlit refresh behavior may vary on slow systems

---

## 8. Future Enhancements (Out of Scope)

- Multi-vehicle dashboard
- Time-range filters and historical queries
- Database persistence (PostgreSQL, SQLite)
- REST API for remote data collection
- WebSocket streaming for multiple users
- Mobile-friendly UI
- Alert webhooks (Slack, email)
