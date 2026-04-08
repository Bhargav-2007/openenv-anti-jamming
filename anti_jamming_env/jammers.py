"""
Jammer Behavior Strategies
Implements different types of jamming attacks the agent must combat
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from enum import Enum


class JammerType(Enum):
    """Types of jamming attacks."""
    SPOT = "spot"                    # Single frequency
    BARRAGE = "barrage"             # Wideband
    SWEEP = "sweep"                 # Frequency sweeping
    REACTIVE = "reactive"           # Follows transmitter
    PULSE = "pulse"                 # On-off keying
    SMART_LEARNING = "smart"        # Learns agent patterns


class Jammer:
    """
    Base class for jamming strategies.
    
    Jammer observes the spectrum and decides which frequencies to attack
    and with what power.
    """
    
    def __init__(
        self,
        jammer_type: JammerType,
        max_power_dbm: float = 30.0,
        num_channels: int = 64,
        random_seed: Optional[int] = None
    ):
        self.jammer_type = jammer_type
        self.max_power_dbm = max_power_dbm
        self.num_channels = num_channels
        self.rng = np.random.RandomState(random_seed)
        
        # Jammer state
        self.current_channels: List[int] = []
        self.attack_power: Dict[int, float] = {}
        self.step_counter = 0
        
        # History (for reactive/learning jammers)
        self.observed_tx_channels: List[int] = []
        self.channel_usage_count: np.ndarray = np.zeros(num_channels)
    
    def observe_transmission(self, channel: int, tx_power: float) -> None:
        """
        Jammer observes agent's transmission.
        Used by reactive and learning jammers.
        """
        self.observed_tx_channels.append(channel)
        self.channel_usage_count[channel] += 1
        self.step_counter += 1
    
    def get_interference_spectrum(self) -> Dict[int, float]:
        """
        Get current interference power for each channel.
        
        Returns:
            Dict mapping channel_idx -> interference_power_dbm
        """
        return self.attack_power.copy()
    
    def reset(self) -> None:
        """Reset jammer state."""
        self.current_channels = []
        self.attack_power = {}
        self.step_counter = 0
        self.observed_tx_channels = []
        self.channel_usage_count = np.zeros(self.num_channels)
    
    def step(self) -> None:
        """Update jammer strategy (implemented by subclasses)."""
        raise NotImplementedError


class SpotJammer(Jammer):
    """
    Spot Jamming: Attacks a single frequency with high power.
    
    Simple but effective if agent doesn't hop.
    """
    
    def __init__(self, target_channel: int = 32, **kwargs):
        super().__init__(JammerType.SPOT, **kwargs)
        self.target_channel = target_channel
    
    def step(self) -> None:
        """Jam single channel continuously."""
        self.current_channels = [self.target_channel]
        self.attack_power = {
            self.target_channel: self.max_power_dbm
        }


class BarrageJammer(Jammer):
    """
    Barrage Jamming: Attacks wide bandwidth simultaneously.
    
    Spreads power across multiple channels (reduced power per channel).
    """
    
    def __init__(self, num_attack_channels: int = 16, **kwargs):
        super().__init__(JammerType.BARRAGE, **kwargs)
        self.num_attack_channels = num_attack_channels
    
    def step(self) -> None:
        """Jam multiple channels with distributed power."""
        # Select contiguous channels
        start_channel = self.rng.randint(0, self.num_channels - self.num_attack_channels)
        self.current_channels = list(range(start_channel, start_channel + self.num_attack_channels))
        
        # Distribute power
        power_per_channel = self.max_power_dbm - 10 * np.log10(self.num_attack_channels)
        
        self.attack_power = {
            ch: power_per_channel for ch in self.current_channels
        }


class SweepJammer(Jammer):
    """
    Sweep Jamming: Sweeps through frequencies periodically.
    
    Covers all channels over time.
    """
    
    def __init__(self, sweep_width: int = 8, sweep_rate: int = 2, **kwargs):
        super().__init__(JammerType.SWEEP, **kwargs)
        self.sweep_width = sweep_width
        self.sweep_rate = sweep_rate  # channels per step
        self.sweep_position = 0
    
    def step(self) -> None:
        """Sweep jammer across spectrum."""
        # Move sweep position
        self.sweep_position = (self.sweep_position + self.sweep_rate) % self.num_channels
        
        # Jam current sweep window
        self.current_channels = [
            (self.sweep_position + i) % self.num_channels
            for i in range(self.sweep_width)
        ]
        
        self.attack_power = {
            ch: self.max_power_dbm - 3  # Slightly reduced power
            for ch in self.current_channels
        }


class ReactiveJammer(Jammer):
    """
    Reactive Jamming: Follows the transmitter's frequency.
    
    Senses transmission and immediately jams detected frequency.
    Most dangerous for naive agents.
    """
    
    def __init__(self, reaction_delay: int = 1, **kwargs):
        super().__init__(JammerType.REACTIVE, **kwargs)
        self.reaction_delay = reaction_delay  # steps to react
    
    def step(self) -> None:
        """React to observed transmissions."""
        if len(self.observed_tx_channels) >= self.reaction_delay:
            # Jam the last observed channel
            target_channel = self.observed_tx_channels[-self.reaction_delay]
            
            self.current_channels = [target_channel]
            self.attack_power = {
                target_channel: self.max_power_dbm
            }
        else:
            # No transmission observed yet - random jamming
            target_channel = self.rng.randint(0, self.num_channels)
            self.current_channels = [target_channel]
            self.attack_power = {
                target_channel: self.max_power_dbm * 0.5
            }


class PulseJammer(Jammer):
    """
    Pulse Jamming: Intermittent on-off jamming.
    
    Conserves power while still disrupting communication.
    """
    
    def __init__(self, duty_cycle: float = 0.5, pulse_channels: int = 8, **kwargs):
        super().__init__(JammerType.PULSE, **kwargs)
        self.duty_cycle = duty_cycle
        self.pulse_channels = pulse_channels
    
    def step(self) -> None:
        """Pulse jammer with on-off pattern."""
        # Determine if jammer is "on" this step
        is_on = self.rng.random() < self.duty_cycle
        
        if is_on:
            # Random pulse position
            start_ch = self.rng.randint(0, self.num_channels - self.pulse_channels)
            self.current_channels = list(range(start_ch, start_ch + self.pulse_channels))
            
            self.attack_power = {
                ch: self.max_power_dbm for ch in self.current_channels
            }
        else:
            # Jammer off
            self.current_channels = []
            self.attack_power = {}


class SmartLearningJammer(Jammer):
    """
    Smart Learning Jammer: Uses ML/pattern recognition.
    
    Learns agent's frequency selection patterns and predicts next channel.
    Most sophisticated adversary.
    """
    
    def __init__(self, learning_rate: float = 0.1, **kwargs):
        super().__init__(JammerType.SMART_LEARNING, **kwargs)
        self.learning_rate = learning_rate
        
        # Probability distribution over channels (agent's strategy)
        self.channel_probability = np.ones(self.num_channels) / self.num_channels
    
    def step(self) -> None:
        """Learn and predict agent's next move."""
        # Update learned distribution
        if len(self.observed_tx_channels) > 0:
            # Increase probability for recently used channels
            for ch in self.observed_tx_channels[-5:]:  # Last 5 observations
                self.channel_probability[ch] += self.learning_rate
            
            # Normalize
            self.channel_probability /= self.channel_probability.sum()
        
        # Attack top N most likely channels
        top_channels = np.argsort(self.channel_probability)[-4:]  # Top 4
        
        self.current_channels = top_channels.tolist()
        self.attack_power = {
            ch: self.max_power_dbm - 6  # Distributed power
            for ch in self.current_channels
        }


def create_jammer(difficulty: str, num_channels: int = 64, seed: Optional[int] = None) -> Jammer:
    """
    Factory function to create appropriate jammer for task difficulty.
    
    Args:
        difficulty: "easy", "medium", or "hard"
        num_channels: Number of frequency channels
        seed: Random seed
    
    Returns:
        Configured jammer instance
    """
    if difficulty == "easy":
        # Easy: Simple spot jammer
        return SpotJammer(
            target_channel=32,
            max_power_dbm=25.0,
            num_channels=num_channels,
            random_seed=seed
        )
    
    elif difficulty == "medium":
        # Medium: Combination of barrage + sweep
        # Randomly choose one
        rng = np.random.RandomState(seed)
        if rng.random() < 0.5:
            return BarrageJammer(
                num_attack_channels=12,
                max_power_dbm=28.0,
                num_channels=num_channels,
                random_seed=seed
            )
        else:
            return SweepJammer(
                sweep_width=10,
                sweep_rate=3,
                max_power_dbm=27.0,
                num_channels=num_channels,
                random_seed=seed
            )
    
    elif difficulty == "hard":
        # Hard: Smart learning + reactive jammer
        rng = np.random.RandomState(seed)
        if rng.random() < 0.7:
            return SmartLearningJammer(
                learning_rate=0.15,
                max_power_dbm=30.0,
                num_channels=num_channels,
                random_seed=seed
            )
        else:
            return ReactiveJammer(
                reaction_delay=1,
                max_power_dbm=30.0,
                num_channels=num_channels,
                random_seed=seed
            )
    
    else:
        raise ValueError(f"Unknown difficulty: {difficulty}")