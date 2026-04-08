"""
Anti-Jamming Communication Environment
Main OpenEnv environment implementation
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
import numpy as np

from pydantic import BaseModel

# ←←← ANTI-JAMMING: Import our models
from anti_jamming_env.models import (
    AntiJammingAction,
    AntiJammingObservation,
    AntiJammingState,
    ChannelState,
    JammerState,
)
from anti_jamming_env.physics import WirelessChannel
from anti_jamming_env.jammers import create_jammer, Jammer
from anti_jamming_env.tasks import TASKS, TaskConfig
from anti_jamming_env.graders import grade_episode

# ←←← ANTI-JAMMING: Import OpenEnv base classes
try:
    from openenv import Env, StepResult
except ImportError:
    # Fallback for development
    class StepResult(BaseModel):
        observation: Any
        reward: float
        done: bool
        info: Dict[str, Any] = {}
    
    class Env:
        async def reset(self) -> StepResult:
            raise NotImplementedError
        
        async def step(self, action: Any) -> StepResult:
            raise NotImplementedError
        
        def state(self) -> Any:
            raise NotImplementedError
        
        async def close(self) -> None:
            pass


class AntiJammingEnv(Env):
    """
    AI-Powered Anti-Jamming Communication System Environment.
    
    The agent controls a wireless transmitter that must maintain communication
    with a receiver while under attack from an intelligent jammer.
    
    Tasks (3 difficulty levels):
    - Easy: Defend against simple spot/constant jamming
    - Medium: Handle barrage/reactive/sweep jamming
    - Hard: Survive sophisticated learning jammers
    
    OpenEnv API:
    - reset() -> StepResult with initial observation
    - step(action) -> StepResult with observation, reward, done, info
    - state() -> Complete internal state
    """
    
    def __init__(
        self,
        task: str = "easy",
        max_steps: int = 50,
        num_channels: int = 64,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize the anti-jamming environment.
        
        Args:
            task: Task difficulty ("easy", "medium", "hard")
            max_steps: Maximum steps per episode
            num_channels: Number of frequency channels available
            random_seed: Random seed for reproducibility
        """
        super().__init__()
        
        # ←←← ANTI-JAMMING: Validate task
        if task not in TASKS:
            raise ValueError(f"Unknown task '{task}'. Valid: {list(TASKS.keys())}")
        
        self.task_name = task
        self.task_config: TaskConfig = TASKS[task]
        self.max_steps = max_steps
        self.num_channels = num_channels
        
        # Random number generator
        self.rng = np.random.RandomState(random_seed)
        
        # ←←← ANTI-JAMMING: Initialize physics simulation
        self.channel = WirelessChannel(
            frequency_ghz=2.4,
            distance_m=100.0,
            bandwidth_mhz=20.0,
            num_channels=num_channels,
            random_seed=random_seed
        )
        
        # ←←← ANTI-JAMMING: Initialize jammer
        self.jammer: Jammer = create_jammer(
            difficulty=task,
            num_channels=num_channels,
            seed=random_seed
        )
        
        # Episode state
        self.episode_id: str = ""
        self.current_step: int = 0
        self.done: bool = False
        
        # Transmission state
        self.current_frequency: int = 0
        self.current_tx_power: float = 15.0
        self.cumulative_throughput: float = 0.0
        self.cumulative_energy: float = 0.0
        
        # Performance tracking
        self.successful_transmissions: int = 0
        self.failed_transmissions: int = 0
        self.total_reward: float = 0.0
        
        # History (last 5 steps for observation)
        self.recent_success: List[bool] = []
        self.recent_sinr: List[float] = []
        self.action_history: List[Dict] = []
        self.reward_history: List[float] = []
        
        # Last transmission results
        self.last_transmission_success: bool = False
        self.last_sinr_db: float = 0.0
        self.last_throughput_mbps: float = 0.0
        self.last_energy_mj: float = 0.0
    
    async def reset(self) -> StepResult:
        """
        Reset environment to initial state.
        
        OpenEnv required method.
        
        Returns:
            StepResult with initial observation
        """
        # Generate new episode ID
        self.episode_id = str(uuid.uuid4())[:8]
        
        # Reset episode counters
        self.current_step = 0
        self.done = False
        
        # Reset transmission state
        self.current_frequency = self.rng.randint(0, self.num_channels)
        self.current_tx_power = 15.0  # Medium power
        self.cumulative_throughput = 0.0
        self.cumulative_energy = 0.0
        
        # Reset performance tracking
        self.successful_transmissions = 0
        self.failed_transmissions = 0
        self.total_reward = 0.0
        
        # Clear history
        self.recent_success = []
        self.recent_sinr = []
        self.action_history = []
        self.reward_history = []
        
        # Reset last transmission
        self.last_transmission_success = True  # Optimistic start
        self.last_sinr_db = 15.0
        self.last_throughput_mbps = 0.0
        self.last_energy_mj = 0.0
        
        # ←←← ANTI-JAMMING: Reset jammer
        self.jammer.reset()
        
        # ←←← ANTI-JAMMING: Initial observation
        initial_obs = self._build_observation()
        
        return StepResult(
            observation=initial_obs,
            reward=0.0,
            done=False,
            info={"episode_id": self.episode_id}
        )
    
    async def step(self, action: AntiJammingAction) -> StepResult:
        """
        Execute one step of the environment.
        
        OpenEnv required method.
        
        Args:
            action: Agent's selected action (frequency, power, modulation, etc.)
        
        Returns:
            StepResult with observation, reward, done flag, and info
        """
        if self.done:
            raise RuntimeError("Episode is done. Call reset() first.")
        
        self.current_step += 1
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Agent transmits with chosen parameters
        # ═══════════════════════════════════════════════════════════
        
        freq_ch = action.frequency_channel
        tx_power = action.tx_power_dbm
        modulation = action.modulation
        coding_rate = action.coding_rate
        
        # Update current state
        self.current_frequency = freq_ch
        self.current_tx_power = tx_power
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: Jammer attacks (observes transmission and jams)
        # ═══════════════════════════════════════════════════════════
        
        self.jammer.observe_transmission(freq_ch, tx_power)
        self.jammer.step()
        
        # Get interference on this channel
        interference_spectrum = self.jammer.get_interference_spectrum()
        interference_power_dbm = interference_spectrum.get(freq_ch, -150.0)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: Calculate SINR and transmission outcome
        # ═══════════════════════════════════════════════════════════
        
        sinr_db, snr_db = self.channel.calculate_sinr(
            tx_power_dbm=tx_power,
            channel_idx=freq_ch,
            interference_power_dbm=interference_power_dbm
        )
        
        # Check transmission success
        tx_success = self.channel.transmission_success(
            sinr_db=sinr_db,
            modulation=modulation,
            enable_notch_filter=action.enable_notch_filter
        )
        
        # Calculate throughput
        throughput_mbps = self.channel.calculate_throughput(
            sinr_db=sinr_db,
            modulation=modulation,
            coding_rate=coding_rate,
            enable_fhss=action.enable_fhss,
            enable_dsss=action.enable_dsss
        )
        
        # Only count throughput if transmission successful
        actual_throughput = throughput_mbps if tx_success else 0.0
        
        # Calculate energy consumed
        energy_mj = self.channel.calculate_energy_consumed(
            tx_power_dbm=tx_power,
            transmission_duration_ms=1.0
        )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: Update statistics
        # ═══════════════════════════════════════════════════════════
        
        if tx_success:
            self.successful_transmissions += 1
        else:
            self.failed_transmissions += 1
        
        self.cumulative_throughput += actual_throughput
        self.cumulative_energy += energy_mj
        
        # Update history
        self.recent_success.append(tx_success)
        self.recent_sinr.append(sinr_db)
        if len(self.recent_success) > 5:
            self.recent_success.pop(0)
            self.recent_sinr.pop(0)
        
        # Save last transmission results
        self.last_transmission_success = tx_success
        self.last_sinr_db = sinr_db
        self.last_throughput_mbps = actual_throughput
        self.last_energy_mj = energy_mj
        
        # ═══════════════════════════════════════════════════════════
        # STEP 5: Calculate reward
        # ═══════════════════════════════════════════════════════════
        
        reward = self._calculate_reward(
            tx_success=tx_success,
            sinr_db=sinr_db,
            throughput_mbps=actual_throughput,
            energy_mj=energy_mj,
            action=action
        )
        
        self.total_reward += reward
        self.reward_history.append(reward)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 6: Check termination
        # ═══════════════════════════════════════════════════════════
        
        self.done = self.current_step >= self.max_steps
        
        # ═══════════════════════════════════════════════════════════
        # STEP 7: Build observation and return
        # ═══════════════════════════════════════════════════════════
        
        observation = self._build_observation()
        
        # Save action to history
        self.action_history.append(action.model_dump())
        
        # Info dict
        info = {
            "episode_id": self.episode_id,
            "step": self.current_step,
            "sinr_db": sinr_db,
            "throughput_mbps": actual_throughput,
            "energy_mj": energy_mj,
            "transmission_success": tx_success,
            "jammer_type": self.jammer.jammer_type.value,
        }
        
        return StepResult(
            observation=observation,
            reward=reward,
            done=self.done,
            info=info
        )
    
    def state(self) -> AntiJammingState:
        """
        Return complete internal state.
        
        OpenEnv required method.
        
        Returns:
            AntiJammingState with full environment state
        """
        # Get full interference spectrum
        interference_spectrum = self.jammer.get_interference_spectrum()
        
        # Calculate SNR and interference for all channels
        full_snr = []
        full_interference = []
        
        for ch in range(self.num_channels):
            # Calculate SINR for this channel
            sinr, snr = self.channel.calculate_sinr(
                tx_power_dbm=self.current_tx_power,
                channel_idx=ch,
                interference_power_dbm=interference_spectrum.get(ch, -150.0)
            )
            full_snr.append(snr)
            full_interference.append(interference_spectrum.get(ch, -150.0))
        
        return AntiJammingState(
            episode_id=self.episode_id,
            current_step=self.current_step,
            max_steps=self.max_steps,
            task_name=self.task_name,
            full_channel_snr=full_snr,
            full_channel_interference=full_interference,
            current_frequency=self.current_frequency,
            current_tx_power=self.current_tx_power,
            cumulative_throughput=self.cumulative_throughput,
            cumulative_energy=self.cumulative_energy,
            jammer_type=self.jammer.jammer_type.value,
            jammer_active_channels=self.jammer.current_channels,
            jammer_strategy=self.jammer.jammer_type.value,
            successful_transmissions=self.successful_transmissions,
            failed_transmissions=self.failed_transmissions,
            total_reward_accumulated=self.total_reward,
            action_history=self.action_history,
            reward_history=self.reward_history,
        )
    
    async def close(self) -> None:
        """Clean up resources (OpenEnv required method)."""
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _build_observation(self) -> AntiJammingObservation:
        """Build observation for agent."""
        
        # Get interference spectrum
        interference_spectrum = self.jammer.get_interference_spectrum()
        
        # Build channel states (top 16 channels for LLM compatibility)
        channel_states = []
        
        # Select 16 representative channels (every 4th channel)
        sampled_channels = list(range(0, self.num_channels, 4))[:16]
        
        for ch in sampled_channels:
            # Calculate metrics for this channel
            interference_power = interference_spectrum.get(ch, -150.0)
            
            sinr, snr = self.channel.calculate_sinr(
                tx_power_dbm=self.current_tx_power,
                channel_idx=ch,
                interference_power_dbm=interference_power
            )
            
            per = self.channel.calculate_packet_error_rate(sinr, "QPSK")
            is_jammed = ch in self.jammer.current_channels
            
            channel_states.append(ChannelState(
                frequency_index=ch,
                snr_db=round(snr, 2),
                sinr_db=round(sinr, 2),
                interference_power_dbm=round(interference_power, 2),
                packet_error_rate=round(per, 3),
                is_jammed=is_jammed
            ))
        
        # Build jammer state
        jammer_state = JammerState(
            detected_jammer_type=self.jammer.jammer_type.value,
            jammer_power_dbm=round(self.jammer.max_power_dbm, 2),
            jammer_bandwidth_mhz=round(len(self.jammer.current_channels) * 20.0 / self.num_channels * 20, 2),
            jammer_center_freq_idx=self.jammer.current_channels[0] if self.jammer.current_channels else None,
            attack_pattern=self.jammer.jammer_type.value
        )
        
        # Calculate recent metrics
        recent_success_rate = sum(self.recent_success) / len(self.recent_success) if self.recent_success else 0.5
        recent_avg_sinr = np.mean(self.recent_sinr) if self.recent_sinr else 0.0
        
        return AntiJammingObservation(
            current_step=self.current_step,
            channel_states=channel_states,
            last_transmission_success=self.last_transmission_success,
            last_sinr_db=round(self.last_sinr_db, 2),
            last_throughput_mbps=round(self.last_throughput_mbps, 3),
            last_energy_consumed_mj=round(self.last_energy_mj, 3),
            jammer_state=jammer_state,
            recent_success_rate=round(recent_success_rate, 3),
            recent_avg_sinr_db=round(recent_avg_sinr, 2),
            task_difficulty=self.task_name,
            task_description=self.task_config.description
        )
    
    def _calculate_reward(
        self,
        tx_success: bool,
        sinr_db: float,
        throughput_mbps: float,
        energy_mj: float,
        action: AntiJammingAction
    ) -> float:
        """
        Calculate reward for this step.
        
        Reward components:
        1. Throughput (primary goal): +throughput / 100
        2. Energy efficiency: -energy / 10
        3. Success bonus: +1.0 if successful, -0.5 if failed
        4. SINR bonus: +0.1 * (sinr - 10) / 10 if sinr > 10 dB
        5. Anti-jam bonus: +0.5 if using advanced techniques
        """
        reward = 0.0
        
        # 1. Throughput reward (main objective)
        reward += throughput_mbps / 100.0  # Normalize to ~0-1 range
        
        # 2. Energy cost (efficiency)
        reward -= energy_mj / 10.0  # Penalize high power
        
        # 3. Success/failure
        if tx_success:
            reward += 1.0  # Successful transmission
        else:
            reward -= 0.5  # Failed transmission penalty
        
        # 4. SINR quality bonus
        if sinr_db > 10:
            reward += 0.1 * min((sinr_db - 10) / 10.0, 1.0)
        
        # 5. Anti-jamming technique usage bonus
        if action.enable_fhss or action.enable_dsss or action.enable_notch_filter:
            reward += 0.2  # Encourage using anti-jam techniques
        
        # Clip reward to reasonable range
        reward = max(-2.0, min(5.0, reward))
        
        return reward
    
    # ═══════════════════════════════════════════════════════════════
    # CLASS METHODS (for OpenEnv integration)
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    async def from_docker_image(cls, image_name: str, **kwargs) -> "AntiJammingEnv":
        """
        Create environment from Docker image (OpenEnv pattern).
        
        For local development, this just creates a local instance.
        In production, OpenEnv handles containerization.
        """
        # For now, return local instance
        # OpenEnv will override this with containerized version
        return cls(**kwargs)