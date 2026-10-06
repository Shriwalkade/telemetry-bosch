import random
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from telemetry.models import Reading, validate_reading
from telemetry.simulator import Simulator, SimulatorConfig

FIXED_TIME = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)
SEED = 42
FLOAT_TOLERANCE = 1e-9


def collect(config: SimulatorConfig, count: int) -> list[Reading]:
    """Return `count` readings from a new simulator using the fixed timestamp."""
    simulator = Simulator(config)
    return [simulator.get_next_reading(FIXED_TIME) for _ in range(count)]


def step_sizes(values: list[float]) -> list[float]:
    """Return absolute differences between consecutive values."""
    return [abs(later - earlier) for earlier, later in zip(values, values[1:], strict=False)]


def test_same_seed_produces_identical_sequence() -> None:
    """TSC-01: the same seed gives the same sequence.
    Two simulators with seed 42 produce equal 100-reading sequences.
    """
    assert collect(SimulatorConfig(seed=SEED), 100) == collect(SimulatorConfig(seed=SEED), 100)


def test_different_seeds_produce_different_sequences() -> None:
    """TSC-02: different seeds give different sequences.
    Seeds 1 and 2 produce unequal 20-reading sequences.
    """
    assert collect(SimulatorConfig(seed=1), 20) != collect(SimulatorConfig(seed=2), 20)


def test_reset_reproduces_original_sequence() -> None:
    """TSC-03: reset restores the original sequence.
    Generating 100, resetting, and generating 100 again gives equal sequences.
    """
    simulator = Simulator(SimulatorConfig(seed=SEED))
    original = [simulator.get_next_reading(FIXED_TIME) for _ in range(100)]
    simulator.reset()
    assert [simulator.get_next_reading(FIXED_TIME) for _ in range(100)] == original


def test_reset_mid_run_restores_initial_state() -> None:
    """TSC-04: reset in the middle of a run restores the initial state.
    The first reading after reset equals the first reading of a fresh simulator.
    """
    simulator = Simulator(SimulatorConfig(seed=SEED))
    expected = Simulator(SimulatorConfig(seed=SEED)).get_next_reading(FIXED_TIME)
    for _ in range(10):
        simulator.get_next_reading(FIXED_TIME)
    simulator.reset()
    assert simulator.get_next_reading(FIXED_TIME) == expected


def test_simulator_ignores_global_random_state() -> None:
    """TSC-05: the simulator uses a private RNG.
    Different global seeds do not change the sequence of same-seed simulators.
    """
    config = SimulatorConfig(seed=SEED)
    first_simulator = Simulator(config)
    random.seed(1)
    first = [first_simulator.get_next_reading(FIXED_TIME) for _ in range(50)]
    second_simulator = Simulator(config)
    random.seed(2)
    second = [second_simulator.get_next_reading(FIXED_TIME) for _ in range(50)]
    assert first == second


def test_seed_none_is_accepted() -> None:
    """TSC-06: a missing seed is allowed.
    Ten readings are generated and all pass validation.
    """
    for reading in collect(SimulatorConfig(seed=None), 10):
        validate_reading(reading)


def test_readings_stay_valid_over_1000_steps() -> None:
    """TSC-07: long runs stay valid.
    All 1000 readings pass validate_reading.
    """
    for reading in collect(SimulatorConfig(seed=SEED), 1000):
        validate_reading(reading)


def test_readings_stay_in_range_with_extreme_steps() -> None:
    """TSC-08: clamping keeps readings valid with extreme steps.
    Speed step 100 and temperature step 50 still pass validation.
    """
    config = SimulatorConfig(seed=SEED, max_speed_step_kmh=100.0, max_temp_step_c=50.0)
    for reading in collect(config, 1000):
        validate_reading(reading)


@pytest.mark.parametrize("initial_kmh", [0.0, 200.0])
def test_speed_clamps_at_both_limits(initial_kmh: float) -> None:
    """TSC-09: speed never leaves its configured limits.
    Starting at either limit with a large step stays within min and max.
    """
    config = SimulatorConfig(seed=SEED, speed_initial_kmh=initial_kmh, max_speed_step_kmh=100.0)
    for reading in collect(config, 200):
        assert config.speed_min_kmh <= reading.speed_kmh <= config.speed_max_kmh


def test_rpm_stays_in_range_and_is_int_with_high_noise() -> None:
    """TSC-10: RPM stays inside its range as an int.
    High noise and gain over 1000 readings never leave [rpm_min, rpm_max].
    """
    config = SimulatorConfig(seed=SEED, rpm_noise=5000, rpm_per_kmh=100.0)
    for reading in collect(config, 1000):
        assert isinstance(reading.rpm, int)
        assert config.rpm_min <= reading.rpm <= config.rpm_max


def test_readings_respect_narrowed_custom_ranges() -> None:
    """TSC-11: tighter custom ranges are respected.
    All metrics stay inside the narrowed minimum and maximum.
    """
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


def test_fuel_never_increases() -> None:
    """TSC-12: fuel is monotonically non-increasing.
    Each of 1000 readings has fuel at or below the previous one.
    """
    fuel = [reading.fuel_pct for reading in collect(SimulatorConfig(seed=SEED), 1000)]
    assert all(later <= earlier for earlier, later in zip(fuel, fuel[1:], strict=False))


def test_fuel_never_drops_below_zero() -> None:
    """TSC-13: fuel is clamped at its minimum.
    Starting at 0.5 % with step 0.4 reaches exactly 0.0 and never goes below.
    """
    config = SimulatorConfig(seed=SEED, fuel_initial_pct=0.5, max_fuel_step_pct=0.4)
    assert min(reading.fuel_pct for reading in collect(config, 100)) == 0.0


def test_first_reading_fuel_is_at_or_below_initial_value() -> None:
    """TSC-14: the first reading never exceeds the initial fuel.
    fuel_pct is at most fuel_initial_pct.
    """
    config = SimulatorConfig(seed=SEED, fuel_initial_pct=75.0)
    assert collect(config, 1)[0].fuel_pct <= 75.0


def test_zero_fuel_step_keeps_fuel_constant() -> None:
    """TSC-15: a zero fuel step keeps fuel constant.
    All readings equal the initial fuel level.
    """
    config = SimulatorConfig(seed=SEED, fuel_initial_pct=75.0, max_fuel_step_pct=0.0)
    assert {reading.fuel_pct for reading in collect(config, 50)} == {75.0}


def test_consecutive_speed_change_never_exceeds_configured_step() -> None:
    """TSC-16: speed changes by at most the configured step.
    With step 3.0, every consecutive difference stays within 3.0.
    """
    config = SimulatorConfig(seed=SEED, max_speed_step_kmh=3.0)
    speeds = [reading.speed_kmh for reading in collect(config, 1000)]
    assert max(step_sizes(speeds)) <= 3.0 + FLOAT_TOLERANCE


def test_consecutive_temperature_change_never_exceeds_configured_step() -> None:
    """TSC-17: temperature changes by at most the configured step.
    With step 0.5, every consecutive difference stays within 0.5.
    """
    config = SimulatorConfig(seed=SEED, max_temp_step_c=0.5)
    temps = [reading.engine_temp_c for reading in collect(config, 1000)]
    assert max(step_sizes(temps)) <= 0.5 + FLOAT_TOLERANCE


def test_zero_speed_step_keeps_speed_constant() -> None:
    """TSC-18: a zero speed step keeps speed constant.
    All readings equal the initial speed.
    """
    config = SimulatorConfig(seed=SEED, speed_initial_kmh=60.0, max_speed_step_kmh=0.0)
    assert {reading.speed_kmh for reading in collect(config, 50)} == {60.0}


def test_rpm_follows_speed_without_noise() -> None:
    """TSC-19: RPM is derived from speed when noise is zero.
    rpm equals the clamped round(800 + speed * 30).
    """
    config = SimulatorConfig(seed=SEED, rpm_noise=0, rpm_idle=800, rpm_per_kmh=30.0)
    for reading in collect(config, 200):
        expected = min(max(round(800 + reading.speed_kmh * 30.0), config.rpm_min), config.rpm_max)
        assert reading.rpm == expected


def test_temperature_decays_toward_baseline_without_heat_gain() -> None:
    """TSC-20: temperature cools toward the baseline.
    Starting above baseline with no heat gain, values fall and stay at or above baseline.
    """
    config = SimulatorConfig(seed=SEED, temp_initial_c=110.0, temp_heat_gain_c=0.0)
    temps = [reading.engine_temp_c for reading in collect(config, 20)]
    assert all(later < earlier for earlier, later in zip(temps, temps[1:], strict=False))
    assert min(temps) >= config.temp_baseline_c - FLOAT_TOLERANCE


def test_temperature_rises_under_load_without_cooling() -> None:
    """TSC-21: temperature rises under load.
    Starting below baseline with no cooling, every reading is warmer than the last.
    """
    config = SimulatorConfig(
        seed=SEED,
        temp_initial_c=30.0,
        temp_cooling_rate=0.0,
        max_speed_step_kmh=0.0,
        rpm_noise=0,
    )
    temps = [reading.engine_temp_c for reading in collect(config, 20)]
    assert temps[0] > config.temp_initial_c
    assert all(later > earlier for earlier, later in zip(temps, temps[1:], strict=False))


def test_injected_timestamp_and_vehicle_id_are_used() -> None:
    """TSC-22: the injected timestamp and vehicle ID appear in the reading.
    now=FIXED_TIME and VEH-002 are carried through.
    """
    reading = collect(SimulatorConfig(seed=SEED, vehicle_id="VEH-002"), 1)[0]
    assert reading.timestamp == FIXED_TIME
    assert reading.vehicle_id == "VEH-002"


def test_default_timestamp_is_utc_aware() -> None:
    """TSC-23: the default timestamp is timezone-aware.
    Without now, utcoffset() is not None.
    """
    reading = Simulator(SimulatorConfig(seed=SEED)).get_next_reading()
    assert reading.timestamp.utcoffset() is not None


def test_default_vehicle_id_is_veh_001() -> None:
    """TSC-24: the default vehicle ID is synthetic.
    SimulatorConfig() uses VEH-001.
    """
    assert SimulatorConfig().vehicle_id == "VEH-001"


def test_naive_now_is_flagged_by_validation() -> None:
    """TSC-25: the simulator passes a naive now through for validation to catch.
    validate_reading raises ValueError matching timestamp.
    """
    reading = Simulator(SimulatorConfig(seed=SEED)).get_next_reading(datetime(2026, 10, 5, 12))
    with pytest.raises(ValueError, match="timestamp"):
        validate_reading(reading)


def test_simulator_without_config_yields_valid_reading() -> None:
    """TSC-26: a simulator works without a config.
    Simulator() returns a reading that passes validation.
    """
    validate_reading(Simulator().get_next_reading(FIXED_TIME))


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
    ids=[f"TSC-{number}" for number in range(27, 36)],
)
def test_invalid_config_is_rejected(overrides: dict) -> None:
    """TSC-27 to TSC-35: invalid configurations are rejected at construction.
    Each override raises ValueError; the case ID is the parameter ID.
    """
    with pytest.raises(ValueError):
        SimulatorConfig(**overrides)


def test_equal_min_and_max_are_rejected() -> None:
    """TSC-36: a range needs min below max.
    speed_min_kmh equal to speed_max_kmh raises ValueError matching speed.
    """
    with pytest.raises(ValueError, match="speed"):
        SimulatorConfig(speed_min_kmh=50.0, speed_max_kmh=50.0)


@pytest.mark.parametrize("temp_initial_c", [49.9, 100.1])
def test_temp_initial_outside_configured_range_is_rejected(temp_initial_c: float) -> None:
    """TSC-37: the initial temperature must lie inside the configured range.
    Values just outside 50-100 raise ValueError matching temp_initial_c.
    """
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
    """TSC-38: step, noise, gain, and rate parameters must not be negative.
    A negative value raises ValueError matching the parameter name.
    """
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
    """TSC-39: initial values exactly at a limit are accepted.
    Minimum and maximum of speed, temperature, and fuel create a config.
    """
    SimulatorConfig(**overrides)


def test_simulator_config_is_frozen() -> None:
    """TSC-40: SimulatorConfig is a frozen dataclass.
    Assigning to a field raises FrozenInstanceError.
    """
    config = SimulatorConfig()
    with pytest.raises(FrozenInstanceError):
        config.vehicle_id = "VEH-999"  # type: ignore[misc]
