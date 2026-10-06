"""Streamlit dashboard for the synthetic vehicle telemetry demo (not a vehicle-control system)."""

import streamlit as st

from telemetry.alerts import AlertThresholds, check_alerts
from telemetry.buffer import ReadingBuffer
from telemetry.config import SPEED_PRESETS_SEC, AppConfig
from telemetry.export import export_csv
from telemetry.models import (
    ENGINE_TEMP_C_MAX,
    ENGINE_TEMP_C_MIN,
    FUEL_PCT_MAX,
    FUEL_PCT_MIN,
    Reading,
    validate_reading,
)
from telemetry.simulator import Simulator, SimulatorConfig

DISCLAIMER = "Demo indicator only - not safety or diagnostic advice."
CHART_POINTS = 30
METRIC_LABELS: dict[str, str] = {
    "speed_kmh": "Speed (km/h)",
    "rpm": "RPM",
    "engine_temp_c": "Engine temperature (C)",
    "fuel_pct": "Fuel level (%)",
}


def init_state() -> None:
    """Create the simulator, buffer, and run flags once per browser session."""
    if "simulator" in st.session_state:
        return
    st.session_state.simulator = Simulator(SimulatorConfig())
    st.session_state.buffer = ReadingBuffer()
    st.session_state.running = False
    st.session_state.export_path = None
    st.session_state.notice = None
    try:
        st.session_state.config = AppConfig.from_env()
    except ValueError as error:
        st.session_state.config = AppConfig()
        st.session_state.notice = ("error", f"Ignoring invalid environment settings: {error}")


def render_sidebar(base: AppConfig) -> AppConfig:
    """Show threshold and preset controls and return the resulting config."""
    st.sidebar.header("Settings")
    high_temp_c = st.sidebar.slider(
        "High temperature alert (C)",
        ENGINE_TEMP_C_MIN,
        ENGINE_TEMP_C_MAX,
        base.thresholds.high_temp_c,
        step=1.0,
    )
    low_fuel_pct = st.sidebar.slider(
        "Low fuel alert (%)", FUEL_PCT_MIN, FUEL_PCT_MAX, base.thresholds.low_fuel_pct, step=1.0
    )
    presets = list(SPEED_PRESETS_SEC)
    preset = st.sidebar.selectbox(
        "Speed preset",
        presets,
        index=presets.index(base.speed_preset),
        format_func=lambda name: f"{name} ({SPEED_PRESETS_SEC[name]} s)",
    )
    interval_sec = base.interval_sec if preset == base.speed_preset else None
    return AppConfig(AlertThresholds(high_temp_c, low_fuel_pct), preset, interval_sec)


def handle_controls() -> None:
    """Draw Start, Stop, Reset, and Export buttons and apply the clicked action."""
    start_col, stop_col, reset_col, export_col = st.columns(4)
    if start_col.button("Start", use_container_width=True):
        st.session_state.running = True
        st.session_state.notice = None
    if stop_col.button("Stop", use_container_width=True):
        st.session_state.running = False
        st.session_state.notice = None
    if reset_col.button("Reset", use_container_width=True):
        st.session_state.running = False
        st.session_state.buffer.clear()
        st.session_state.simulator.reset()
        st.session_state.export_path = None
        st.session_state.notice = None
    if export_col.button("Export CSV", use_container_width=True):
        export_readings()


def export_readings() -> None:
    """Export the buffer and record a success or error notice for the user."""
    try:
        path = export_csv(st.session_state.buffer)
    except (ValueError, OSError) as error:
        st.session_state.export_path = None
        st.session_state.notice = ("error", f"Export failed: {error}")
    else:
        st.session_state.export_path = path
        st.session_state.notice = ("success", f"Exported {path.name}")


def render_notice() -> None:
    """Show the last notice and a download button for the exported file."""
    notice = st.session_state.notice
    if notice:
        level, text = notice
        (st.success if level == "success" else st.error)(text)
    path = st.session_state.export_path
    if path is not None and path.is_file():
        st.download_button("Download CSV", data=path.read_bytes(), file_name=path.name)


def advance_simulation() -> None:
    """Generate one reading, validate it, and store it; invalid readings are skipped."""
    reading = st.session_state.simulator.get_next_reading()
    try:
        validate_reading(reading)
    except ValueError as error:
        st.error(f"Invalid reading skipped: {error}")
        return
    st.session_state.buffer.append(reading)


def render_metrics(reading: Reading) -> None:
    """Show the current value of every metric."""
    values = {
        "speed_kmh": f"{reading.speed_kmh:.1f}",
        "rpm": f"{reading.rpm}",
        "engine_temp_c": f"{reading.engine_temp_c:.1f}",
        "fuel_pct": f"{reading.fuel_pct:.1f}",
    }
    for column, (name, label) in zip(st.columns(4), METRIC_LABELS.items(), strict=True):
        column.metric(label, values[name])


def render_alerts(reading: Reading, thresholds: AlertThresholds) -> None:
    """Show alert banners for the current reading."""
    result = check_alerts(reading, thresholds)
    if result.high_temp:
        st.error(
            f"High engine temperature: {reading.engine_temp_c:.1f} C "
            f"(threshold {thresholds.high_temp_c:.1f} C). {DISCLAIMER}"
        )
    if result.low_fuel:
        st.warning(
            f"Low fuel: {reading.fuel_pct:.1f} % "
            f"(threshold {thresholds.low_fuel_pct:.1f} %). {DISCLAIMER}"
        )


def render_charts(buffer: ReadingBuffer) -> None:
    """Draw one line chart per metric for the most recent readings."""
    frame = buffer.to_dataframe().tail(CHART_POINTS).set_index("timestamp")
    for left, right in (("speed_kmh", "rpm"), ("engine_temp_c", "fuel_pct")):
        for column, name in zip(st.columns(2), (left, right), strict=True):
            column.caption(METRIC_LABELS[name])
            column.line_chart(frame[name])


def live_view(thresholds: AlertThresholds) -> None:
    """Advance the simulation while running, then draw status, values, alerts, and charts."""
    buffer: ReadingBuffer = st.session_state.buffer
    if st.session_state.running:
        advance_simulation()
    status = "Running" if st.session_state.running else "Stopped"
    st.caption(f"Status: {status} | Readings: {len(buffer)}")
    latest = buffer.latest()
    if latest is None:
        st.info("Press Start to begin the simulation.")
        return
    render_metrics(latest)
    render_alerts(latest, thresholds)
    render_charts(buffer)


def main() -> None:
    """Render the dashboard."""
    st.set_page_config(page_title="Vehicle Telemetry Demo", layout="wide")
    st.title("Vehicle Telemetry Demo")
    st.caption(f"Synthetic data only. {DISCLAIMER}")
    init_state()
    config = render_sidebar(st.session_state.config)
    handle_controls()
    render_notice()
    run_every = config.interval_sec if st.session_state.running else None
    st.fragment(run_every=run_every)(live_view)(config.thresholds)


main()
