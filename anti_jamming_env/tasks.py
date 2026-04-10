"""
Task definitions for Anti-Jamming Environment.
Defines easy, medium, and hard difficulty levels with grading weights.
"""

from typing import Dict, Literal
from pydantic import BaseModel, Field


class TaskConfig(BaseModel):
    """Configuration for a specific task difficulty level."""

    name: str = Field(..., description="Task identifier")
    description: str = Field(..., description="Human-readable task description")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty label")
    max_steps: int = Field(50, description="Maximum steps per episode")
    success_threshold: float = Field(
        ..., ge=0.0, le=1.0, description="Minimum score required to pass"
    )
    grading_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights used by the deterministic grader",
    )


TASK_EASY = TaskConfig(
    name="easy",
    description=(
        "Defend against a basic spot jammer. Use frequency hopping and robust "
        "modulation to maintain communication quality."
    ),
    difficulty="easy",
    max_steps=50,
    success_threshold=0.70,
    grading_weights={
        "throughput": 0.40,
        "success_rate": 0.30,
        "energy_efficiency": 0.20,
        "sinr_quality": 0.10,
    },
)

TASK_MEDIUM = TaskConfig(
    name="medium",
    description=(
        "Handle barrage and sweep jamming by adapting across channels and "
        "deploying interference mitigation techniques."
    ),
    difficulty="medium",
    max_steps=50,
    success_threshold=0.60,
    grading_weights={
        "throughput": 0.35,
        "success_rate": 0.25,
        "energy_efficiency": 0.15,
        "sinr_quality": 0.15,
        "adaptation": 0.10,
    },
)

TASK_HARD = TaskConfig(
    name="hard",
    description=(
        "Survive intelligent, learning-based jamming. Require randomized, "
        "unpredictable policies while maintaining link quality."
    ),
    difficulty="hard",
    max_steps=50,
    success_threshold=0.50,
    grading_weights={
        "throughput": 0.30,
        "success_rate": 0.25,
        "energy_efficiency": 0.10,
        "sinr_quality": 0.10,
        "adaptation": 0.15,
        "unpredictability": 0.10,
    },
)

TASKS: Dict[str, TaskConfig] = {
    "easy": TASK_EASY,
    "medium": TASK_MEDIUM,
    "hard": TASK_HARD,
}


def get_task(task_name: str) -> TaskConfig:
    """Retrieve task configuration by name."""
    if task_name not in TASKS:
        raise ValueError(f"Unknown task '{task_name}'. Valid tasks: {list(TASKS.keys())}")
    return TASKS[task_name]
