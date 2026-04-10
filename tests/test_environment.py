"""
Unit tests for Anti-Jamming Environment
Tests core environment functionality and openenv.core compliance
"""

import pytest

from anti_jamming_env import (
    AntiJammingEnv,
    AntiJammingAction,
    AntiJammingObservation,
    AntiJammingState,
)
from openenv.core import Environment, Action, Observation, State


def make_action(**overrides) -> AntiJammingAction:
    defaults = dict(
        frequency_channel=32,
        tx_power_dbm=15.0,
        modulation="QPSK",
        coding_rate="1/2",
        beam_direction=0,
        enable_fhss=True,
        enable_dsss=False,
        enable_notch_filter=True,
    )
    defaults.update(overrides)
    return AntiJammingAction(**defaults)


# ── Type hierarchy ────────────────────────────────────────────────

def test_subclassing():
    """Environment and models must subclass openenv base types."""
    assert issubclass(AntiJammingEnv, Environment)
    assert issubclass(AntiJammingAction, Action)
    assert issubclass(AntiJammingObservation, Observation)
    assert issubclass(AntiJammingState, State)


# ── Initialisation ────────────────────────────────────────────────

def test_environment_initialization():
    """Environment can be created for each task difficulty."""
    for task in ["easy", "medium", "hard"]:
        env = AntiJammingEnv(task=task, max_steps=10)
        assert env.task_name == task
        assert env.max_steps == 10


# ── reset() ───────────────────────────────────────────────────────

def test_reset_returns_valid_observation():
    """reset() returns AntiJammingObservation with done=False, reward=0."""
    env = AntiJammingEnv(task="easy", max_steps=10)
    obs = env.reset()

    assert isinstance(obs, AntiJammingObservation)
    assert obs.done is False
    assert obs.reward == 0.0


def test_reset_with_seed():
    """reset(seed=) produces reproducible initial observations."""
    env = AntiJammingEnv(task="easy")
    obs_a = env.reset(seed=42)
    obs_b = env.reset(seed=42)
    assert obs_a.current_step == obs_b.current_step


# ── step() ────────────────────────────────────────────────────────

def test_step_executes_action():
    """step() returns an observation with reward and done flag."""
    env = AntiJammingEnv(task="easy", max_steps=10, random_seed=42)
    env.reset()

    obs = env.step(make_action())

    assert isinstance(obs, AntiJammingObservation)
    assert isinstance(obs.reward, (int, float))
    assert isinstance(obs.done, bool)


def test_episode_completes():
    """Episode terminates after max_steps steps."""
    env = AntiJammingEnv(task="easy", max_steps=5, random_seed=42)
    env.reset()

    for _ in range(5):
        obs = env.step(make_action(frequency_channel=10, enable_fhss=False))

    assert obs.done is True


def test_step_after_done_raises():
    """Calling step() on a done episode must raise RuntimeError."""
    env = AntiJammingEnv(task="easy", max_steps=1, random_seed=0)
    env.reset()
    env.step(make_action())  # last step
    with pytest.raises(RuntimeError):
        env.step(make_action())


# ── state property ────────────────────────────────────────────────

def test_state_returns_complete_state():
    """state property returns AntiJammingState with all fields."""
    env = AntiJammingEnv(task="medium", max_steps=10, random_seed=42)
    env.reset()

    st = env.state
    assert isinstance(st, AntiJammingState)
    assert st.step_count == 0
    assert st.max_steps == 10
    assert st.task_name == "medium"
    assert len(st.full_channel_snr) == 64
    assert len(st.full_channel_interference) == 64


def test_state_updates_after_step():
    """state.step_count increments with each step."""
    env = AntiJammingEnv(task="easy", max_steps=10, random_seed=7)
    env.reset()

    for i in range(3):
        env.step(make_action())

    assert env.state.step_count == 3


# ── Reward range ──────────────────────────────────────────────────

def test_reward_in_expected_range():
    """Rewards fall within the declared [-2, 5] range."""
    env = AntiJammingEnv(task="easy", max_steps=10, random_seed=42)
    env.reset()

    for _ in range(10):
        obs = env.step(make_action(
            frequency_channel=20,
            tx_power_dbm=18.0,
            modulation="QPSK",
            coding_rate="3/4",
            beam_direction=2,
            enable_fhss=True,
            enable_dsss=True,
            enable_notch_filter=True,
        ))
        assert -5.0 <= float(obs.reward) <= 10.0


# ── Different jammers per difficulty ─────────────────────────────

def test_different_tasks_have_different_jammers():
    """Easy and hard tasks use different jammer types."""
    easy_env = AntiJammingEnv(task="easy", random_seed=42)
    hard_env = AntiJammingEnv(task="hard", random_seed=42)
    assert easy_env.jammer.jammer_type.value != hard_env.jammer.jammer_type.value


# ── Action validation ─────────────────────────────────────────────

def test_action_validation_valid():
    """Valid actions are accepted without exception."""
    action = make_action()
    assert action.frequency_channel == 32


def test_action_validation_invalid_frequency():
    """Out-of-range frequency channel is rejected."""
    with pytest.raises(Exception):
        AntiJammingAction(
            frequency_channel=100,  # > 63
            tx_power_dbm=20.0,
            modulation="QPSK",
            coding_rate="2/3",
            beam_direction=0,
            enable_fhss=False,
            enable_dsss=False,
            enable_notch_filter=False,
        )
