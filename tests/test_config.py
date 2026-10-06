import pytest

from telemetry.alerts import AlertThresholds
from telemetry.config import AppConfig


def test_defaults() -> None:
    config = AppConfig()
    assert config.thresholds == AlertThresholds()
    assert config.thresholds.high_temp_c == 100.0
    assert config.thresholds.low_fuel_pct == 10.0
    assert config.speed_preset == "normal"
    assert config.interval_sec == 1.0


@pytest.mark.parametrize(
    ("preset", "interval_sec"),
    [("slow", 2.0), ("normal", 1.0), ("fast", 0.5)],
)
def test_preset_sets_refresh_interval(preset: str, interval_sec: float) -> None:
    assert AppConfig(speed_preset=preset).interval_sec == interval_sec


@pytest.mark.parametrize("interval_sec", [-1.0, 0.0])
def test_non_positive_interval_is_rejected(interval_sec: float) -> None:
    with pytest.raises(ValueError, match="interval"):
        AppConfig(interval_sec=interval_sec)


@pytest.mark.parametrize("preset", ["turbo", "", "NORMAL"])
def test_unknown_preset_is_rejected(preset: str) -> None:
    with pytest.raises(ValueError, match="preset"):
        AppConfig(speed_preset=preset)
