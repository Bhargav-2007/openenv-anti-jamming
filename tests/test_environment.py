"""
Unit tests for Anti-Jamming Environment
Tests core environment functionality and OpenEnv compliance
"""

import pytest
import asyncio
from anti_jamming_env import (
    AntiJammingEnv,
    AntiJammingAction,
    AntiJammingObservation,
    AntiJammingState
)


@pytest.mark.asyncio
async def test_environment_initialization():
    """Test environment can be created with different tasks."""
    for task in ["easy", "medium", "hard"]:
        env = AntiJammingEnv(task=task, max_steps=10)
        assert env.task_name == task
        assert env.max_steps == 10
        await env.close()


@pytest.mark.asyncio
async def test_reset_returns_valid_observation():
    """Test reset() returns valid StepResult with observation."""
    env = AntiJammingEnv(task="easy", max_steps=10)
    
    result = await env.reset()
    
    assert result.observation is not None
    assert isinstance(result.observation, AntiJammingObservation)
    assert result.reward == 0.0
    assert result.done is False
    
    await env.close()


@pytest.mark.asyncio
async def test_step_executes_action():
    """Test step() executes action and returns valid result."""
    env = AntiJammingEnv(task="easy", max_steps=10, random_seed=42)
    
    await env.reset()
    
    action = AntiJammingAction(
        frequency_channel=32,
        tx_power_dbm=20.0,
        modulation="QPSK",
        coding_rate="2/3",
        beam_direction=0,
        enable_fhss=True,
        enable_dsss=False,
        enable_notch_filter=True
    )
    
    result = await env.step(action)
    
    assert result.observation is not None
    assert isinstance(result.reward, (int, float))
    assert isinstance(result.done, bool)
    assert "step" in result.info
    
    await env.close()


@pytest.mark.asyncio
async def test_episode_completes():
    """Test full episode runs to completion."""
    env = AntiJammingEnv(task="easy", max_steps=5, random_seed=42)
    
    await env.reset()
    
    for _ in range(5):
        action = AntiJammingAction(
            frequency_channel=10,
            tx_power_dbm=15.0,
            modulation="BPSK",
            coding_rate="1/2",
            beam_direction=0,
            enable_fhss=False,
            enable_dsss=False,
            enable_notch_filter=False
        )
        
        result = await env.step(action)
    
    assert result.done is True
    
    await env.close()


@pytest.mark.asyncio
async def test_state_returns_complete_state():
    """Test state() returns valid State object."""
    env = AntiJammingEnv(task="medium", max_steps=10, random_seed=42)
    
    await env.reset()
    
    state = env.state()
    
    assert isinstance(state, AntiJammingState)
    assert state.current_step == 0
    assert state.max_steps == 10
    assert state.task_name == "medium"
    assert len(state.full_channel_snr) == 64
    assert len(state.full_channel_interference) == 64
    
    await env.close()


@pytest.mark.asyncio
async def test_reward_in_expected_range():
    """Test rewards fall within expected range."""
    env = AntiJammingEnv(task="easy", max_steps=10, random_seed=42)
    
    await env.reset()
    
    rewards = []
    for _ in range(10):
        action = AntiJammingAction(
            frequency_channel=20,
            tx_power_dbm=18.0,
            modulation="QPSK",
            coding_rate="3/4",
            beam_direction=2,
            enable_fhss=True,
            enable_dsss=True,
            enable_notch_filter=True
        )
        
        result = await env.step(action)
        rewards.append(result.reward)
    
    # Rewards should be in approximately [-2, 5] range
    assert all(-5.0 <= r <= 10.0 for r in rewards)
    
    await env.close()


@pytest.mark.asyncio
async def test_different_tasks_have_different_jammers():
    """Test different difficulty levels use different jammers."""
    easy_env = AntiJammingEnv(task="easy", random_seed=42)
    medium_env = AntiJammingEnv(task="medium", random_seed=42)
    hard_env = AntiJammingEnv(task="hard", random_seed=42)
    
    # Jammer types should differ
    assert easy_env.jammer.jammer_type.value != hard_env.jammer.jammer_type.value
    
    await easy_env.close()
    await medium_env.close()
    await hard_env.close()


def test_action_validation():
    """Test action model validates parameters."""
    # Valid action
    valid_action = AntiJammingAction(
        frequency_channel=32,
        tx_power_dbm=20.0,
        modulation="QPSK",
        coding_rate="2/3",
        beam_direction=4,
        enable_fhss=True,
        enable_dsss=False,
        enable_notch_filter=True
    )
    assert valid_action.frequency_channel == 32
    
    # Invalid frequency (out of range)
    with pytest.raises(Exception):
        invalid_action = AntiJammingAction(
            frequency_channel=100,  # Out of range
            tx_power_dbm=20.0,
            modulation="QPSK",
            coding_rate="2/3",
            beam_direction=0,
            enable_fhss=False,
            enable_dsss=False,
            enable_notch_filter=False
        )