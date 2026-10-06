from dataclasses import FrozenInstanceError

import pytest

from telemetry.alerts import AlertThresholds
from telemetry.config import (
    ENV_HIGH_TEMP_C,
    ENV_INTERVAL_SEC,
    ENV_LOW_FUEL_PCT,
    ENV_SPEED_PRESET,
    AppConfig,
)


def test_defaults_match_the_spec() -> None:
    """TAC-01: default settings match the spec.
    Thresholds 100.0 C and 10.0 %, normal preset, 1.0 s interval.
    """
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
    """TAC-02: each preset sets its refresh interval.
    slow is 2.0 s, normal 1.0 s, fast 0.5 s.
    """
    assert AppConfig(speed_preset=preset).interval_sec == interval_sec


def test_custom_thresholds_are_kept() -> None:
    """TAC-03: custom thresholds are stored unchanged.
    The config exposes the values it was given.
    """
    thresholds = AlertThresholds(high_temp_c=95.0, low_fuel_pct=15.0)
    assert AppConfig(thresholds=thresholds).thresholds == thresholds


@pytest.mark.parametrize("interval_sec", [-1.0, 0.0])
def test_non_positive_interval_is_rejected(interval_sec: float) -> None:
    """TAC-04: an interval of zero or less is rejected.
    ValueError matches interval.
    """
    with pytest.raises(ValueError, match="interval"):
        AppConfig(interval_sec=interval_sec)


@pytest.mark.parametrize("preset", ["turbo", "", "NORMAL"])
def test_unknown_preset_is_rejected(preset: str) -> None:
    """TAC-05: unknown or differently cased presets are rejected.
    ValueError matches preset.
    """
    with pytest.raises(ValueError, match="preset"):
        AppConfig(speed_preset=preset)


def test_smallest_positive_interval_is_accepted() -> None:
    """TAC-06: any interval above zero is accepted.
    0.001 s creates a config.
    """
    assert AppConfig(interval_sec=0.001).interval_sec == 0.001


def test_app_config_is_frozen() -> None:
    """TAC-07: AppConfig is a frozen dataclass.
    Assigning to a field raises FrozenInstanceError.
    """
    config = AppConfig()
    with pytest.raises(FrozenInstanceError):
        config.speed_preset = "fast"  # type: ignore[misc]


def test_from_env_without_overrides_gives_defaults() -> None:
    """TAC-08: no environment overrides gives the defaults.
    An empty environment, or blank values, equal AppConfig().
    """
    assert AppConfig.from_env({}) == AppConfig()
    assert AppConfig.from_env({ENV_SPEED_PRESET: "  ", ENV_HIGH_TEMP_C: ""}) == AppConfig()


def test_from_env_applies_valid_overrides() -> None:
    """TAC-09: valid environment overrides are applied.
    Preset, thresholds, and interval reflect the variables.
    """
    config = AppConfig.from_env(
        {
            ENV_SPEED_PRESET: "fast",
            ENV_HIGH_TEMP_C: "95",
            ENV_LOW_FUEL_PCT: "15.5",
            ENV_INTERVAL_SEC: "0.25",
        }
    )
    assert config.speed_preset == "fast"
    assert config.thresholds == AlertThresholds(high_temp_c=95.0, low_fuel_pct=15.5)
    assert config.interval_sec == 0.25


@pytest.mark.parametrize(
    ("variable", "value", "message"),
    [
        (ENV_SPEED_PRESET, "turbo", "preset"),
        (ENV_INTERVAL_SEC, "-1", "interval"),
        (ENV_INTERVAL_SEC, "fast", ENV_INTERVAL_SEC),
        (ENV_HIGH_TEMP_C, "500", "high_temp_c"),
        (ENV_LOW_FUEL_PCT, "abc", ENV_LOW_FUEL_PCT),
    ],
)
def test_from_env_rejects_invalid_overrides(variable: str, value: str, message: str) -> None:
    """TAC-10: invalid environment overrides are rejected.
    ValueError is raised and names the setting, like direct construction.
    """
    with pytest.raises(ValueError, match=message):
        AppConfig.from_env({variable: value})
