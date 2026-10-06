from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Button

from telemetry.buffer import ReadingBuffer

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")
DISCLAIMER = "Demo indicator only"


def press(app: AppTest, label: str) -> AppTest:
    """Click the button with the given label and rerun the script."""
    button: Button = next(item for item in app.button if item.label == label)
    return button.click().run()


def readings_status(app: AppTest) -> str:
    """Return the status caption (for example `Status: Running | Readings: 3`)."""
    return next(item.value for item in app.caption if item.value.startswith("Status:"))


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Return a started dashboard whose working directory (and exports/) is a temp folder."""
    monkeypatch.chdir(tmp_path)
    for name in (
        "TELEMETRY_SPEED_PRESET",
        "TELEMETRY_INTERVAL_SEC",
        "TELEMETRY_HIGH_TEMP_C",
        "TELEMETRY_LOW_FUEL_PCT",
    ):
        monkeypatch.delenv(name, raising=False)
    return AppTest.from_file(APP_PATH, default_timeout=15).run()


def test_dashboard_starts_stopped_with_press_start_message(app: AppTest) -> None:
    """TDB-01: the dashboard opens in the stopped, empty state.
    No exception, status Stopped with 0 readings, and a Press Start message.
    """
    assert not app.exception
    assert readings_status(app) == "Status: Stopped | Readings: 0"
    assert "Press Start" in app.info[0].value


def test_start_shows_current_values_for_all_metrics(app: AppTest) -> None:
    """TDB-02: Start produces a reading and shows every metric.
    Status is Running with 1 reading and four metric tiles.
    """
    app = press(app, "Start")
    assert not app.exception
    assert readings_status(app) == "Status: Running | Readings: 1"
    assert [metric.label for metric in app.metric] == [
        "Speed (km/h)",
        "RPM",
        "Engine temperature (C)",
        "Fuel level (%)",
    ]


def test_stop_freezes_the_display(app: AppTest) -> None:
    """TDB-03: Stop halts new readings.
    The count stays at 1 across further reruns.
    """
    app = press(app, "Start")
    app = press(app, "Stop").run()
    assert readings_status(app) == "Status: Stopped | Readings: 1"


def test_start_after_stop_resumes_without_losing_history(app: AppTest) -> None:
    """TDB-04: Start after Stop continues the same history.
    The reading count grows from 1 to 2 instead of restarting.
    """
    app = press(app, "Start")
    app = press(app, "Stop")
    app = press(app, "Start")
    assert readings_status(app) == "Status: Running | Readings: 2"


def test_reset_clears_buffer_and_returns_to_empty_state(app: AppTest) -> None:
    """TDB-05: Reset stops the run and clears the data.
    Status is Stopped with 0 readings and the Press Start message returns.
    """
    app = press(app, "Start")
    app = press(app, "Reset")
    assert readings_status(app) == "Status: Stopped | Readings: 0"
    assert "Press Start" in app.info[0].value


def test_lowering_temperature_threshold_shows_alert_with_disclaimer(app: AppTest) -> None:
    """TDB-06: a threshold below the current temperature raises the alert at once.
    The error banner names high engine temperature and carries the demo disclaimer.
    """
    app = press(app, "Start")
    app.slider[0].set_value(20.0).run()
    banners = [banner.value for banner in app.error]
    assert any("High engine temperature" in text and DISCLAIMER in text for text in banners)


def test_raising_fuel_threshold_shows_low_fuel_warning(app: AppTest) -> None:
    """TDB-07: a fuel threshold above the current level raises the warning.
    The warning banner names low fuel and carries the demo disclaimer.
    """
    app = press(app, "Start")
    app.slider[1].set_value(100.0).run()
    assert any("Low fuel" in item.value and DISCLAIMER in item.value for item in app.warning)


def test_export_without_data_shows_error_not_exception(app: AppTest) -> None:
    """TDB-08: exporting an empty buffer reports a friendly error.
    An error message is shown and the script raises no exception.
    """
    app = press(app, "Export CSV")
    assert not app.exception
    assert any("Export failed" in item.value for item in app.error)


def test_export_with_data_writes_file_and_offers_download(app: AppTest, tmp_path: Path) -> None:
    """TDB-09: exporting buffered data writes a CSV and offers it for download.
    A success message names the file, it exists under exports/, and a download button appears.
    """
    app = press(app, "Start")
    app = press(app, "Export CSV")
    exported = list((tmp_path / "exports").glob("readings_*.csv"))
    assert len(exported) == 1
    assert any(exported[0].name in item.value for item in app.success)
    assert app.get("download_button")


def test_invalid_environment_settings_fall_back_to_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TDB-10: invalid environment settings do not crash the dashboard.
    An error notice is shown and the default preset is used.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEMETRY_SPEED_PRESET", "turbo")
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not app.exception
    assert any("invalid environment settings" in item.value for item in app.error)
    assert app.selectbox[0].value == "normal"


def test_simulator_and_buffer_persist_across_reruns(app: AppTest) -> None:
    """TDB-11: session state keeps one buffer per session.
    The same ReadingBuffer object survives a rerun.
    """
    first = app.session_state["buffer"]
    app.run()
    assert isinstance(first, ReadingBuffer)
    assert app.session_state["buffer"] is first
