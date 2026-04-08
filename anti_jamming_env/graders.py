"""
Grading functions for Anti-Jamming tasks
Each task has a deterministic grader that scores performance from 0.0 to 1.0
"""

import numpy as np
from typing import Dict, List, Tuple
from anti_jamming_env.tasks import TaskConfig, TASKS


def grade_episode(
    task_config: TaskConfig,
    successful_transmissions: int,
    failed_transmissions: int,
    sinr_history: List[float],
    throughput_total: float,
    energy_total: float,
    max_steps: int
) -> Tuple[float, Dict[str, float]]:
    """
    Grade an episode based on task-specific criteria.
    
    Grading components:
    1. Transmission success rate (40% weight)
    2. Average SINR quality (25% weight)
    3. Throughput achievement (25% weight)
    4. Energy efficiency (10% weight)
    
    Args:
        task_config: Task configuration with targets
        successful_transmissions: Count of successful transmissions
        failed_transmissions: Count of failed transmissions
        sinr_history: List of SINR values achieved
        throughput_total: Total throughput in Mbps
        energy_total: Total energy consumed in mJ
        max_steps: Maximum steps in episode
    
    Returns:
        Tuple of (final_score, component_scores_dict)
        final_score: Overall score in [0.0, 1.0]
        component_scores: Breakdown of score components
    """
    
    total_transmissions = successful_transmissions + failed_transmissions
    
    # Avoid division by zero
    if total_transmissions == 0:
        return 0.0, {
            "success_rate_score": 0.0,
            "sinr_score": 0.0,
            "throughput_score": 0.0,
            "energy_score": 0.0,
            "final_score": 0.0
        }
    
    # ═══════════════════════════════════════════════════════════════
    # Component 1: Transmission Success Rate (40% weight)
    # ═══════════════════════════════════════════════════════════════
    
    actual_success_rate = successful_transmissions / total_transmissions
    target_success_rate = task_config.target_success_rate
    
    # Score: 1.0 if meeting target, 0.0 if zero success, linear interpolation
    if actual_success_rate >= target_success_rate:
        success_rate_score = 1.0
    else:
        success_rate_score = actual_success_rate / target_success_rate
    
    # ═══════════════════════════════════════════════════════════════
    # Component 2: Average SINR Quality (25% weight)
    # ═══════════════════════════════════════════════════════════════
    
    if len(sinr_history) > 0:
        avg_sinr = np.mean(sinr_history)
    else:
        avg_sinr = 0.0
    
    target_sinr = task_config.target_avg_sinr_db
    
    # Score: 1.0 if meeting target, scaled for values above/below
    # Use sigmoid-like scaling
    if avg_sinr >= target_sinr:
        sinr_score = 1.0
    else:
        # Linear decay from target to 0
        sinr_score = max(0.0, avg_sinr / target_sinr)
    
    # ═══════════════════════════════════════════════════════════════
    # Component 3: Throughput Achievement (25% weight)
    # ═══════════════════════════════════════════════════════════════
    
    target_throughput = task_config.target_throughput_mbps
    
    # Score: 1.0 if meeting target, proportional otherwise
    if throughput_total >= target_throughput:
        throughput_score = 1.0
    else:
        throughput_score = throughput_total / target_throughput
    
    # ═══════════════════════════════════════════════════════════════
    # Component 4: Energy Efficiency (10% weight)
    # ═══════════════════════════════════════════════════════════════
    
    max_energy_budget = task_config.max_energy_budget_mj
    
    # Score: 1.0 if under budget, penalty for exceeding
    if energy_total <= max_energy_budget:
        energy_score = 1.0
    else:
        # Penalty for exceeding budget
        overage_ratio = energy_total / max_energy_budget
        energy_score = max(0.0, 2.0 - overage_ratio)  # Goes to 0 at 2x budget
    
    # ═══════════════════════════════════════════════════════════════
    # Final Score: Weighted combination
    # ═══════════════════════════════════════════════════════════════
    
    weights = {
        "success_rate": 0.40,
        "sinr": 0.25,
        "throughput": 0.25,
        "energy": 0.10
    }
    
    final_score = (
        weights["success_rate"] * success_rate_score +
        weights["sinr"] * sinr_score +
        weights["throughput"] * throughput_score +
        weights["energy"] * energy_score
    )
    
    # Clamp to [0, 1]
    final_score = max(0.0, min(1.0, final_score))
    
    # Component breakdown
    component_scores = {
        "success_rate_score": round(success_rate_score, 3),
        "sinr_score": round(sinr_score, 3),
        "throughput_score": round(throughput_score, 3),
        "energy_score": round(energy_score, 3),
        "final_score": round(final_score, 3),
        "actual_success_rate": round(actual_success_rate, 3),
        "actual_avg_sinr_db": round(avg_sinr, 2),
        "actual_throughput_mbps": round(throughput_total, 2),
        "actual_energy_mj": round(energy_total, 2)
    }
    
    return final_score, component_scores


def grade_easy_task(
    successful_transmissions: int,
    failed_transmissions: int,
    sinr_history: List[float],
    throughput_total: float,
    energy_total: float,
    max_steps: int = 50
) -> Tuple[float, Dict[str, float]]:
    """Grade performance on easy task."""
    return grade_episode(
        task_config=TASKS["easy"],
        successful_transmissions=successful_transmissions,
        failed_transmissions=failed_transmissions,
        sinr_history=sinr_history,
        throughput_total=throughput_total,
        energy_total=energy_total,
        max_steps=max_steps
    )


def grade_medium_task(
    successful_transmissions: int,
    failed_transmissions: int,
    sinr_history: List[float],
    throughput_total: float,
    energy_total: float,
    max_steps: int = 50
) -> Tuple[float, Dict[str, float]]:
    """Grade performance on medium task."""
    return grade_episode(
        task_config=TASKS["medium"],
        successful_transmissions=successful_transmissions,
        failed_transmissions=failed_transmissions,
        sinr_history=sinr_history,
        throughput_total=throughput_total,
        energy_total=energy_total,
        max_steps=max_steps
    )


def grade_hard_task(
    successful_transmissions: int,
    failed_transmissions: int,
    sinr_history: List[float],
    throughput_total: float,
    energy_total: float,
    max_steps: int = 50
) -> Tuple[float, Dict[str, float]]:
    """Grade performance on hard task."""
    return grade_episode(
        task_config=TASKS["hard"],
        successful_transmissions=successful_transmissions,
        failed_transmissions=failed_transmissions,
        sinr_history=sinr_history,
        throughput_total=throughput_total,
        energy_total=energy_total,
        max_steps=max_steps
    )