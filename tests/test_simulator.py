import random
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from telemetry.models import validate_reading
from telemetry.simulator import Simulator, SimulatorConfig

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
SEED = 42
FLOAT_TOLERANCE = 1e-9


def make_readings(simulator: Simulator, count: int) -> list:
    return [simulator.get_next_reading(FIXED_TIME) for _ in range(count)]


def test_same_seed_produces_identical_sequence() -> None:
    first = make_readings(Simulator(SimulatorConfig(seed=SEED)), 100)
    second = make_readings(Simulator(SimulatorConfig(seed=SEED)), 100)
    assert first == second


def test_different_seeds_produce_different_sequences() -> None:
    first = make_readings(Simulator(SimulatorConfig(seed=1)), 20)
    second = make_readings(Simulator(SimulatorConfig(seed=2)), 20)
    assert first != second


def test_readings_stay_valid_over_1000_steps() -> None:
    for reading in make_readings(Simulator(SimulatorConfig(seed=SEED)), 1000):
        validate_reading(reading)


def test_readings_stay_in_range_with_extreme_steps() -> None:
    config = SimulatorConfig(seed=SEED, max_speed_step_kmh=100.0, max_temp_step_c=50.0)
    for reading in make_readings(Simulator(config), 1000):
        validate_reading(reading)


def test_fuel_never_increases() -> None:
    readings = make_readings(Simulator(SimulatorConfig(seed=SEED)), 1000)
    fuel = [r.fuel_pct for r in readings]
    assert all(later <= earlier for earlier, later in zip(fuel, fuel[1:], strict=False))


def test_fuel_never_drops_below_zero() -> None:
    config = SimulatorConfig(seed=SEED, fuel_initial_pct=0.5, max_fuel_step_pct=0.4)
    readings = make_readings(Simulator(config), 100)
    assert min(r.fuel_pct for r in readings) == 0.0


def test_consecutive_speed_change_never_exceeds_configured_step() -> None:
    config = SimulatorConfig(seed=SEED, max_speed_step_kmh=3.0)
    speeds = [r.speed_kmh for r in make_readings(Simulator(config), 1000)]
    steps = [abs(b - a) for a, b in zip(speeds, speeds[1:], strict=False)]
    assert max(steps) <= 3.0 + FLOAT_TOLERANCE


def test_consecutive_temperature_change_never_exceeds_configured_step() -> None:
    config = SimulatorConfig(seed=SEED, max_temp_step_c=0.5)
    temps = [r.engine_temp_c for r in make_readings(Simulator(config), 1000)]
    steps = [abs(b - a) for a, b in zip(temps, temps[1:], strict=False)]
    assert max(steps) <= 0.5 + FLOAT_TOLERANCE


def test_reset_reproduces_original_sequence() -> None:
    simulator = Simulator(SimulatorConfig(seed=SEED))
    original = make_readings(simulator, 100)
    simulator.reset()
    assert make_readings(simulator, 100) == original


def test_injected_timestamp_and_vehicle_id_are_used() -> None:
    simulator = Simulator(SimulatorConfig(seed=SEED, vehicle_id="VEH-002"))
    reading = simulator.get_next_reading(FIXED_TIME)
    assert reading.timestamp == FIXED_TIME
    assert reading.vehicle_id == "VEH-002"


def test_default_timestamp_is_utc_aware() -> None:
    reading = Simulator(SimulatorConfig(seed=SEED)).get_next_reading()
    assert reading.timestamp.utcoffset() is not None


@pytest.mark.parametrize(
    "overrides",
    [
        {"vehicle_id": " "},
        {"speed_min_kmh": 100.0, "speed_max_kmh": 50.0},
        {"speed_max_kmh": 250.0},
        {"rpm_max": 9000},
        {"temp_min_c": 10.0},
        {"fuel_min_pct": -1.0},
        {"speed_initial_kmh": 300.0},
        {"fuel_initial_pct": 101.0},
        {"max_speed_step_kmh": -1.0},
    ],
)
def test_invalid_config_is_rejected(overrides: dict) -> None:
    with pytest.raises(ValueError):
        SimulatorConfig(**overrides)


def collect(config: SimulatorConfig, count: int) -> list:
    return make_readings(Simulator(config), count)


def test_default_vehicle_id_is_veh_001() -> None:
    assert SimulatorConfig().vehicle_id == "VEH-001"


def test_simulator_without_config_yields_valid_reading() -> None:
    validate_reading(Simulator().get_next_reading(FIXED_TIME))


@pytest.mark.parametrize("initial_kmh", [0.0, 200.0])
def test_speed_clamps_at_both_limits(initial_kmh: float) -> None:
    config = SimulatorConfig(seed=SEED, speed_initial_kmh=initial_kmh, max_speed_step_kmh=100.0)
    for reading in collect(config, 200):
        assert config.speed_min_kmh <= reading.speed_kmh <= config.speed_max_kmh


def test_rpm_stays_in_range_and_is_int_with_high_noise() -> None:
    config = SimulatorConfig(seed=SEED, rpm_noise=5000, rpm_per_kmh=100.0)
    for reading in collect(config, 1000):
        assert isinstance(reading.rpm, int)
        assert config.rpm_min <= reading.rpm <= config.rpm_max


def test_readings_respect_narrowed_custom_ranges() -> None:
    config = SimulatorConfig(
        seed=SEED,
        speed_min_kmh=20.0,
        speed_max_kmh=80.0,
        speed_initial_kmh=50.0,
        rpm_min=1000,
        rpm_max=5000,
        temp_min_c=60.0,
        temp_max_c=100.0,
        temp_initial_c=80.0,
        fuel_min_pct=20.0,
        fuel_max_pct=90.0,
        fuel_initial_pct=80.0,
        max_fuel_step_pct=1.0,
    )
    for reading in collect(config, 500):
        assert 20.0 <= reading.speed_kmh <= 80.0
        assert 1000 <= reading.rpm <= 5000
        assert 60.0 <= reading.engine_temp_c <= 100.0
        assert 20.0 <= reading.fuel_pct <= 90.0


def test_reset_mid_run_restores_initial_state() -> None:
    simulator = Simulator(SimulatorConfig(seed=SEED))
    expected = Simulator(SimulatorConfig(seed=SEED)).get_next_reading(FIXED_TIME)
    make_readings(simulator, 10)
    simulator.reset()
    assert simulator.get_next_reading(FIXED_TIME) == expected


def test_simulator_ignores_global_random_state() -> None:
    config = SimulatorConfig(seed=SEED)
    first_simulator = Simulator(config)
    random.seed(1)
    first = make_readings(first_simulator, 50)
    second_simulator = Simulator(config)
    random.seed(2)
    second = make_readings(second_simulator, 50)
    assert first == second


def test_seed_none_is_accepted() -> None:
    for reading in collect(SimulatorConfig(seed=None), 10):
        validate_reading(reading)


def test_zero_fuel_step_keeps_fuel_constant() -> None:
    config = SimulatorConfig(seed=SEED, fuel_initial_pct=75.0, max_fuel_step_pct=0.0)
    assert {r.fuel_pct for r in collect(config, 50)} == {75.0}


def test_rpm_follows_speed_without_noise() -> None:
    config = SimulatorConfig(seed=SEED, rpm_noise=0, rpm_idle=800, rpm_per_kmh=30.0)
    for reading in collect(config, 200):
        expected = min(max(round(800 + reading.speed_kmh * 30.0), config.rpm_min), config.rpm_max)
        assert reading.rpm == expected


def test_temperature_decays_toward_baseline_without_heat_gain() -> None:
    config = SimulatorConfig(seed=SEED, temp_initial_c=110.0, temp_heat_gain_c=0.0)
    temps = [r.engine_temp_c for r in collect(config, 20)]
    assert all(later < earlier for earlier, later in zip(temps, temps[1:], strict=False))
    assert min(temps) >= config.temp_baseline_c - FLOAT_TOLERANCE


def test_temperature_rises_under_load_without_cooling() -> None:
    config = SimulatorConfig(
        seed=SEED,
        temp_initial_c=30.0,
        temp_cooling_rate=0.0,
        max_speed_step_kmh=0.0,
        rpm_noise=0,
    )
    temps = [r.engine_temp_c for r in collect(config, 20)]
    assert temps[0] > config.temp_initial_c
    assert all(later > earlier for earlier, later in zip(temps, temps[1:], strict=False))


def test_equal_min_and_max_are_rejected() -> None:
    with pytest.raises(ValueError, match="speed"):
        SimulatorConfig(speed_min_kmh=50.0, speed_max_kmh=50.0)


@pytest.mark.parametrize("temp_initial_c", [49.9, 100.1])
def test_temp_initial_outside_configured_range_is_rejected(temp_initial_c: float) -> None:
    with pytest.raises(ValueError, match="temp_initial_c"):
        SimulatorConfig(temp_min_c=50.0, temp_max_c=100.0, temp_initial_c=temp_initial_c)


@pytest.mark.parametrize(
    "name",
    [
        "rpm_noise",
        "rpm_per_kmh",
        "temp_heat_gain_c",
        "temp_cooling_rate",
        "max_temp_step_c",
        "max_fuel_step_pct",
    ],
)
def test_negative_parameter_is_rejected(name: str) -> None:
    with pytest.raises(ValueError, match=name):
        SimulatorConfig(**{name: -0.1})


@pytest.mark.parametrize(
    "overrides",
    [
        {"speed_initial_kmh": 0.0},
        {"speed_initial_kmh": 200.0},
        {"temp_initial_c": 20.0},
        {"temp_initial_c": 120.0},
        {"fuel_initial_pct": 0.0},
        {"fuel_initial_pct": 100.0},
    ],
)
def test_initial_values_at_range_limits_are_accepted(overrides: dict) -> None:
    SimulatorConfig(**overrides)


def test_simulator_config_is_frozen() -> None:
    config = SimulatorConfig()
    with pytest.raises(FrozenInstanceError):
        config.vehicle_id = "VEH-999"  # type: ignore[misc]
