"""
Pydantic models for Anti-Jamming Environment
Defines Action, Observation, and State structures
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# ACTION MODEL - What the agent can do
# ═══════════════════════════════════════════════════════════════════

class AntiJammingAction(BaseModel):
    """
    Agent's action in the anti-jamming communication system.
    
    The agent controls transmission parameters to avoid jamming:
    - Frequency selection (which channel to use)
    - Power level (transmission strength)
    - Modulation scheme (how to encode data)
    - Coding rate (error correction strength)
    - Beam direction (spatial filtering, simplified)
    """
    
    frequency_channel: int = Field(
        ...,
        ge=0,
        lt=64,  # 64 frequency channels (like WiFi channels)
        description="Frequency channel index (0-63) for transmission"
    )
    
    tx_power_dbm: float = Field(
        ...,
        ge=0.0,
        le=30.0,  # 1 mW to 1 W
        description="Transmit power in dBm (0-30 dBm)"
    )
    
    modulation: Literal["BPSK", "QPSK", "16QAM", "64QAM"] = Field(
        ...,
        description="Modulation scheme: BPSK (robust) to 64QAM (high rate)"
    )
    
    coding_rate: Literal["1/2", "2/3", "3/4", "5/6"] = Field(
        ...,
        description="Forward error correction rate (1/2 = strong, 5/6 = weak)"
    )
    
    beam_direction: int = Field(
        ...,
        ge=0,
        lt=8,  # 8 beam directions (simplified beamforming)
        description="Beam direction index (0-7) for spatial selectivity"
    )
    
    enable_fhss: bool = Field(
        default=False,
        description="Enable Frequency Hopping Spread Spectrum"
    )
    
    enable_dsss: bool = Field(
        default=False,
        description="Enable Direct Sequence Spread Spectrum"
    )
    
    enable_notch_filter: bool = Field(
        default=False,
        description="Enable adaptive notch filtering"
    )


# ═══════════════════════════════════════════════════════════════════
# OBSERVATION MODEL - What the agent sees
# ═══════════════════════════════════════════════════════════════════

class ChannelState(BaseModel):
    """Current state of the wireless channel for each frequency."""
    
    frequency_index: int = Field(..., description="Channel index")
    snr_db: float = Field(..., description="Signal-to-Noise Ratio in dB")
    sinr_db: float = Field(..., description="Signal-to-Interference-plus-Noise Ratio")
    interference_power_dbm: float = Field(..., description="Detected interference power")
    packet_error_rate: float = Field(..., ge=0.0, le=1.0, description="Recent PER")
    is_jammed: bool = Field(..., description="Is this channel currently jammed?")


class JammerState(BaseModel):
    """Observable information about jammer activity."""
    
    detected_jammer_type: Optional[str] = Field(
        default=None,
        description="Detected jammer type (if identifiable)"
    )
    jammer_power_dbm: float = Field(..., description="Estimated jammer power")
    jammer_bandwidth_mhz: float = Field(..., description="Estimated jammer bandwidth")
    jammer_center_freq_idx: Optional[int] = Field(
        default=None,
        description="Estimated jammer center frequency"
    )
    attack_pattern: str = Field(
        default="unknown",
        description="Observed attack pattern (constant, sweep, reactive, etc.)"
    )


class AntiJammingObservation(BaseModel):
    """
    What the agent observes from the environment.
    
    Includes:
    - Spectrum sensing data (SNR, interference per channel)
    - Channel quality indicators
    - Jammer detection and classification
    - Historical performance metrics
    """
    
    current_step: int = Field(..., description="Current timestep in episode")
    
    # Spectrum information (simplified to top 16 channels for LLM compatibility)
    channel_states: List[ChannelState] = Field(
        ...,
        max_length=16,
        description="Current state of top 16 channels"
    )
    
    # Current transmission result
    last_transmission_success: bool = Field(
        ...,
        description="Was the last transmission successful?"
    )
    last_sinr_db: float = Field(..., description="SINR achieved in last transmission")
    last_throughput_mbps: float = Field(..., ge=0.0, description="Last achieved throughput")
    last_energy_consumed_mj: float = Field(..., ge=0.0, description="Energy used last step")
    
    # Jammer intelligence
    jammer_state: JammerState = Field(..., description="Current jammer activity")
    
    # Historical metrics (last 5 steps)
    recent_success_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Success rate over last 5 transmissions"
    )
    recent_avg_sinr_db: float = Field(..., description="Average SINR last 5 steps")
    
    # Task-specific guidance
    task_difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Current task difficulty level"
    )
    task_description: str = Field(..., description="Human-readable task goal")


# ═══════════════════════════════════════════════════════════════════
# STATE MODEL - Complete internal state (for rendering/debugging)
# ═══════════════════════════════════════════════════════════════════

class AntiJammingState(BaseModel):
    """
    Complete internal state of the environment.
    Used for state() method and debugging.
    """
    
    # Episode metadata
    episode_id: str = Field(..., description="Unique episode identifier")
    current_step: int = Field(..., description="Current step in episode")
    max_steps: int = Field(..., description="Maximum steps per episode")
    task_name: str = Field(..., description="Task being executed")
    
    # Physical state (full 64 channels)
    full_channel_snr: List[float] = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SNR for all 64 channels"
    )
    full_channel_interference: List[float] = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Interference power for all 64 channels"
    )
    
    # Agent state
    current_frequency: int = Field(..., description="Currently selected frequency")
    current_tx_power: float = Field(..., description="Current transmit power")
    cumulative_throughput: float = Field(..., description="Total successful data transferred")
    cumulative_energy: float = Field(..., description="Total energy consumed")
    
    # Jammer complete state
    jammer_type: str = Field(..., description="Actual jammer type")
    jammer_active_channels: List[int] = Field(..., description="Channels jammer is attacking")
    jammer_strategy: str = Field(..., description="Jammer's current strategy")
    
    # Performance tracking
    successful_transmissions: int = Field(default=0, description="Count of successful TX")
    failed_transmissions: int = Field(default=0, description="Count of failed TX")
    total_reward_accumulated: float = Field(default=0.0, description="Cumulative reward")
    
    # History (for analysis)
    action_history: List[dict] = Field(
        default_factory=list,
        description="History of all actions taken"
    )
    reward_history: List[float] = Field(
        default_factory=list,
        description="History of rewards received"
    )