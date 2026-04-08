"""
Task definitions for Anti-Jamming Environment
Defines easy, medium, and hard difficulty levels
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class TaskConfig(BaseModel):
    """Configuration for a specific task difficulty level."""
    
    name: str = Field(..., description="Task identifier")
    description: str = Field(..., description="Human-readable task description")
    max_steps: int = Field(50, description="Maximum steps per episode")
    
    # Success criteria
    target_success_rate: float = Field(..., ge=0.0, le=1.0, description="Required transmission success rate")
    target_avg_sinr_db: float = Field(..., description="Target average SINR in dB")
    target_throughput_mbps: float = Field(..., description="Target cumulative throughput")
    max_energy_budget_mj: float = Field(..., description="Maximum allowed energy consumption")
    
    # Jammer configuration
    jammer_difficulty: str = Field(..., description="Jammer type for this task")
    jammer_power_dbm: float = Field(..., description="Jammer maximum power")
    
    # Hints for agents
    recommended_techniques: List[str] = Field(
        default_factory=list,
        description="Suggested anti-jamming techniques"
    )


# ═══════════════════════════════════════════════════════════════════
# TASK DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

TASK_EASY = TaskConfig(
    name="easy",
    description=(
        "Defend against basic spot jamming attack. "
        "The jammer targets a single fixed frequency with constant power. "
        "Goal: Achieve 80% transmission success rate using frequency hopping."
    ),
    max_steps=50,
    target_success_rate=0.80,
    target_avg_sinr_db=12.0,
    target_throughput_mbps=40.0,
    max_energy_budget_mj=500.0,
    jammer_difficulty="easy",
    jammer_power_dbm=25.0,
    recommended_techniques=[
        "Basic frequency hopping (FHSS)",
        "Power control (moderate levels)",
        "QPSK modulation for reliability",
        "Medium coding rate (2/3 or 3/4)"
    ]
)

TASK_MEDIUM = TaskConfig(
    name="medium",
    description=(
        "Handle sophisticated barrage and sweep jamming. "
        "The jammer attacks multiple frequencies simultaneously or sweeps across the spectrum. "
        "Goal: Maintain 70% success rate using adaptive hopping and beamforming."
    ),
    max_steps=50,
    target_success_rate=0.70,
    target_avg_sinr_db=10.0,
    target_throughput_mbps=30.0,
    max_energy_budget_mj=600.0,
    jammer_difficulty="medium",
    jammer_power_dbm=28.0,
    recommended_techniques=[
        "Adaptive frequency hopping (AFH)",
        "Directional beamforming",
        "Adaptive notch filters",
        "DSSS for interference rejection",
        "Dynamic modulation selection",
        "Channel sensing and avoidance"
    ]
)

TASK_HARD = TaskConfig(
    name="hard",
    description=(
        "Survive intelligent learning jammer with reactive capabilities. "
        "The jammer learns your patterns and predicts your next move. "
        "Goal: Achieve 60% success rate using game-theoretic strategies and randomization."
    ),
    max_steps=50,
    target_success_rate=0.60,
    target_avg_sinr_db=8.0,
    target_throughput_mbps=20.0,
    max_energy_budget_mj=700.0,
    jammer_difficulty="hard",
    jammer_power_dbm=30.0,
    recommended_techniques=[
        "Randomized frequency hopping patterns",
        "Game-theoretic channel selection",
        "MIMO spatial diversity",
        "Cognitive radio spectrum sensing",
        "Low-probability-of-intercept (LPI) modes",
        "Hybrid FHSS + DSSS",
        "Dynamic power adaptation",
        "Beam direction randomization",
        "Temporal pattern breaking"
    ]
)

# Task registry
TASKS: Dict[str, TaskConfig] = {
    "easy": TASK_EASY,
    "medium": TASK_MEDIUM,
    "hard": TASK_HARD,
}


def get_task(task_name: str) -> TaskConfig:
    """
    Retrieve task configuration by name.
    
    Args:
        task_name: One of "easy", "medium", "hard"
    
    Returns:
        TaskConfig instance
    
    Raises:
        ValueError: If task_name is not recognized
    """
    if task_name not in TASKS:
        raise ValueError(
            f"Unknown task '{task_name}'. Valid tasks: {list(TASKS.keys())}"
        )
    return TASKS[task_name]