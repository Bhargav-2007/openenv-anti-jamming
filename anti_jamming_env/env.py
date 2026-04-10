"""
Anti-Jamming Communication Environment
Implements the openenv.core.Environment interface with typed Action/Observation/State.
"""

import uuid
from typing import Optional, List, Dict

import numpy as np

from openenv.core import Environment

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


class AntiJammingEnv(
    Environment[AntiJammingAction, AntiJammingObservation, AntiJammingState]
):
    """
    AI-Powered Anti-Jamming Communication System Environment.

    The agent controls a wireless transmitter that must maintain communication
    with a receiver while under attack from an intelligent jammer.

    Tasks (3 difficulty levels):
    - easy:   Defend against simple spot/constant jamming
    - medium: Handle barrage/reactive/sweep jamming
    - hard:   Survive sophisticated learning jammers

    OpenEnv API (openenv.core.Environment):
    - reset(seed, episode_id, **kwargs) -> AntiJammingObservation
    - step(action, timeout_s, **kwargs) -> AntiJammingObservation
    - state (property) -> AntiJammingState
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(
        self,
        task: str = "easy",
        max_steps: int = 50,
        num_channels: int = 64,
        random_seed: Optional[int] = None,
    ) -> None:
        """
        Initialise the anti-jamming environment.

        Args:
            task: Task difficulty – one of "easy", "medium", "hard".
            max_steps: Maximum steps per episode.
            num_channels: Number of frequency channels available.
            random_seed: Random seed for reproducibility.
        """
        super().__init__()

        if task not in TASKS:
            raise ValueError(f"Unknown task '{task}'. Valid: {list(TASKS.keys())}")

        self.task_name = task
        self.task_config: TaskConfig = TASKS[task]
        self.max_steps = max_steps
        self.num_channels = num_channels

        # Random number generator (may be replaced in reset())
        self._base_seed = random_seed
        self.rng = np.random.RandomState(random_seed)

        # Physics simulation
        self.channel = WirelessChannel(
            frequency_ghz=2.4,
            distance_m=100.0,
            bandwidth_mhz=20.0,
            num_channels=num_channels,
            random_seed=random_seed,
        )

        # Jammer
        self.jammer: Jammer = create_jammer(
            difficulty=task,
            num_channels=num_channels,
            seed=random_seed,
        )

        # Episode state (initialised properly in reset())
        self._episode_id: str = ""
        self._step_count: int = 0
        self._done: bool = False

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
<<<<<<< HEAD

=======
        self.sinr_history: List[float] = []
        
>>>>>>> 5242213f (Changes)
        # Last transmission results
        self.last_transmission_success: bool = False
        self.last_sinr_db: float = 0.0
        self.last_throughput_mbps: float = 0.0
        self.last_energy_mj: float = 0.0

    # ═══════════════════════════════════════════════════════════════
    # OPENENV REQUIRED INTERFACE
    # ═══════════════════════════════════════════════════════════════

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> AntiJammingObservation:
        """
        Reset the environment to its initial state.

        Args:
            seed: Optional random seed for this episode.
            episode_id: Optional explicit episode identifier.

        Returns:
            Initial AntiJammingObservation (done=False, reward=0.0).
        """
        effective_seed = seed if seed is not None else self._base_seed
        self.rng = np.random.RandomState(effective_seed)

        # Update channel and jammer RNG as well
        self.channel.rng = np.random.RandomState(effective_seed)
        self.channel.fading_coefficients = self.channel.rng.rayleigh(
            1.0, self.num_channels
        )
        self.jammer.rng = np.random.RandomState(effective_seed)

        self._episode_id = episode_id or str(uuid.uuid4())[:8]
        self._step_count = 0
        self._done = False

        # Reset transmission state
        self.current_frequency = int(self.rng.randint(0, self.num_channels))
        self.current_tx_power = 15.0
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
<<<<<<< HEAD

=======
        self.sinr_history = []
        
>>>>>>> 5242213f (Changes)
        # Reset last transmission
        self.last_transmission_success = True
        self.last_sinr_db = 15.0
        self.last_throughput_mbps = 0.0
        self.last_energy_mj = 0.0

        self.jammer.reset()

        obs = self._build_observation(reward=0.0, done=False)
        return obs

    def step(
        self,
        action: AntiJammingAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> AntiJammingObservation:
        """
        Execute one environment step.

        Args:
            action: Agent's chosen transmission parameters.
            timeout_s: Unused; present for API compatibility.

        Returns:
            AntiJammingObservation with updated channel state, reward, and done flag.
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        self._step_count += 1

        # ── 1. Agent transmits ──────────────────────────────────────
        freq_ch = action.frequency_channel
        tx_power = action.tx_power_dbm
        modulation = action.modulation
        coding_rate = action.coding_rate

        self.current_frequency = freq_ch
        self.current_tx_power = tx_power

        # ── 2. Jammer attacks ───────────────────────────────────────
        self.jammer.observe_transmission(freq_ch, tx_power)
        self.jammer.step()

        interference_spectrum = self.jammer.get_interference_spectrum()
        interference_power_dbm = interference_spectrum.get(freq_ch, -150.0)

        # ── 3. Wireless physics ─────────────────────────────────────
        sinr_db, _ = self.channel.calculate_sinr(
            tx_power_dbm=tx_power,
            channel_idx=freq_ch,
            interference_power_dbm=interference_power_dbm,
        )

        tx_success = self.channel.transmission_success(
            sinr_db=sinr_db,
            modulation=modulation,
            enable_notch_filter=action.enable_notch_filter,
        )

        throughput_mbps = self.channel.calculate_throughput(
            sinr_db=sinr_db,
            modulation=modulation,
            coding_rate=coding_rate,
            enable_fhss=action.enable_fhss,
            enable_dsss=action.enable_dsss,
        )
        actual_throughput = throughput_mbps if tx_success else 0.0

        energy_mj = self.channel.calculate_energy_consumed(
            tx_power_dbm=tx_power,
            transmission_duration_ms=1.0,
        )

        # ── 4. Update statistics ─────────────────────────────────────
        if tx_success:
            self.successful_transmissions += 1
        else:
            self.failed_transmissions += 1

        self.cumulative_throughput += actual_throughput
        self.cumulative_energy += energy_mj

        self.recent_success.append(tx_success)
        self.recent_sinr.append(sinr_db)
        self.sinr_history.append(sinr_db)
        if len(self.recent_success) > 5:
            self.recent_success.pop(0)
            self.recent_sinr.pop(0)

        self.last_transmission_success = tx_success
        self.last_sinr_db = sinr_db
        self.last_throughput_mbps = actual_throughput
        self.last_energy_mj = energy_mj

        # ── 5. Dense reward ─────────────────────────────────────────
        reward = self._calculate_reward(
            tx_success=tx_success,
            sinr_db=sinr_db,
            throughput_mbps=actual_throughput,
            energy_mj=energy_mj,
            action=action,
        )
        self.total_reward += reward
        self.reward_history.append(reward)

        # ── 6. Termination ───────────────────────────────────────────
        self._done = self._step_count >= self.max_steps

        # ── 7. Record action ────────────────────────────────────────
        self.action_history.append(action.model_dump())

        obs = self._build_observation(reward=reward, done=self._done)
        return obs

    @property
    def state(self) -> AntiJammingState:
        """
        Return complete internal state (openenv.core.Environment required property).

        Returns:
            AntiJammingState with full channel and performance information.
        """
        interference_spectrum = self.jammer.get_interference_spectrum()

        full_snr: List[float] = []
        full_interference: List[float] = []

        for ch in range(self.num_channels):
            sinr, snr = self.channel.calculate_sinr(
                tx_power_dbm=self.current_tx_power,
                channel_idx=ch,
                interference_power_dbm=interference_spectrum.get(ch, -150.0),
            )
            full_snr.append(round(snr, 2))
            full_interference.append(round(interference_spectrum.get(ch, -150.0), 2))

        return AntiJammingState(
            episode_id=self._episode_id,
            step_count=self._step_count,
            max_steps=self.max_steps,
            task_name=self.task_name,
            full_channel_snr=full_snr,
            full_channel_interference=full_interference,
            current_frequency=self.current_frequency,
            current_tx_power=self.current_tx_power,
            cumulative_throughput=self.cumulative_throughput,
            cumulative_energy=self.cumulative_energy,
            jammer_type=self.jammer.jammer_type.value,
            jammer_active_channels=list(self.jammer.current_channels),
            jammer_strategy=self.jammer.jammer_type.value,
            successful_transmissions=self.successful_transmissions,
            failed_transmissions=self.failed_transmissions,
<<<<<<< HEAD
            total_reward_accumulated=round(self.total_reward, 4),
            action_history=list(self.action_history),
            reward_history=list(self.reward_history),
=======
            total_reward_accumulated=self.total_reward,
            action_history=self.action_history,
            reward_history=self.reward_history,
            sinr_history=self.sinr_history,
>>>>>>> 5242213f (Changes)
        )

    # ═══════════════════════════════════════════════════════════════
    # GRADING HELPER
    # ═══════════════════════════════════════════════════════════════

    def grade(self) -> tuple:
        """
        Grade the current episode using the task grader.

        Returns:
            (final_score, component_scores) – score in [0.0, 1.0].
        """
        return grade_episode(
            task_config=self.task_config,
            successful_transmissions=self.successful_transmissions,
            failed_transmissions=self.failed_transmissions,
            sinr_history=self.recent_sinr,
            throughput_total=self.cumulative_throughput,
            energy_total=self.cumulative_energy,
            max_steps=self.max_steps,
        )

    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _build_observation(
        self, reward: float, done: bool
    ) -> AntiJammingObservation:
        """Build typed observation for the agent."""

        interference_spectrum = self.jammer.get_interference_spectrum()

        channel_states: List[ChannelState] = []
        sampled_channels = list(range(0, self.num_channels, 4))[:16]

        for ch in sampled_channels:
            interference_power = interference_spectrum.get(ch, -150.0)
            sinr, snr = self.channel.calculate_sinr(
                tx_power_dbm=self.current_tx_power,
                channel_idx=ch,
                interference_power_dbm=interference_power,
            )
            per = self.channel.calculate_packet_error_rate(sinr, "QPSK")
            is_jammed = ch in self.jammer.current_channels

            channel_states.append(
                ChannelState(
                    frequency_index=ch,
                    snr_db=round(snr, 2),
                    sinr_db=round(sinr, 2),
                    interference_power_dbm=round(interference_power, 2),
                    packet_error_rate=round(per, 3),
                    is_jammed=is_jammed,
                )
            )

        num_jammed = len(self.jammer.current_channels)
        jammer_bw = round(num_jammed * 20.0 / self.num_channels * 20, 2)

        jammer_state = JammerState(
            detected_jammer_type=self.jammer.jammer_type.value,
            jammer_power_dbm=round(self.jammer.max_power_dbm, 2),
            jammer_bandwidth_mhz=jammer_bw,
            jammer_center_freq_idx=(
                self.jammer.current_channels[0]
                if self.jammer.current_channels
                else None
            ),
            attack_pattern=self.jammer.jammer_type.value,
        )

        recent_success_rate = (
            sum(self.recent_success) / len(self.recent_success)
            if self.recent_success
            else 0.5
        )
        recent_avg_sinr = (
            float(np.mean(self.recent_sinr)) if self.recent_sinr else 0.0
        )

        return AntiJammingObservation(
            done=done,
            reward=reward,
            current_step=self._step_count,
            channel_states=channel_states,
            last_transmission_success=self.last_transmission_success,
            last_sinr_db=round(self.last_sinr_db, 2),
            last_throughput_mbps=round(self.last_throughput_mbps, 3),
            last_energy_consumed_mj=round(self.last_energy_mj, 3),
            jammer_state=jammer_state,
            recent_success_rate=round(recent_success_rate, 3),
            recent_avg_sinr_db=round(recent_avg_sinr, 2),
            task_difficulty=self.task_name,
            task_description=self.task_config.description,
        )

    def _calculate_reward(
        self,
        tx_success: bool,
        sinr_db: float,
        throughput_mbps: float,
        energy_mj: float,
        action: AntiJammingAction,
    ) -> float:
        """
        Dense reward combining throughput, energy, success, SINR, and technique usage.

        Range: approximately [-2.0, +5.0] per step.
        """
        reward = 0.0

        # Throughput (primary objective) – normalised to ~0..1 range
        reward += throughput_mbps / 100.0

        # Energy efficiency penalty
        reward -= energy_mj / 10.0

        # Transmission outcome
        if tx_success:
            reward += 1.0
        else:
            reward -= 0.5

        # SINR quality bonus
        if sinr_db > 10:
            reward += 0.1 * min((sinr_db - 10) / 10.0, 1.0)

        # Anti-jamming technique usage bonus
        if action.enable_fhss or action.enable_dsss or action.enable_notch_filter:
            reward += 0.2

        return float(max(-2.0, min(5.0, reward)))
