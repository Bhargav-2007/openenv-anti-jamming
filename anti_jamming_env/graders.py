"""
Deterministic grading for Anti-Jamming tasks.
Scores are normalized to [0.0, 1.0].
"""

from typing import Any, Dict
import numpy as np

from anti_jamming_env.models import AntiJammingState
from anti_jamming_env.tasks import TaskConfig


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def grade_episode(final_state: AntiJammingState, task_config: TaskConfig) -> Dict[str, Any]:
    """
    Grade a completed episode deterministically.

    Returns:
        Dict with score, success flag, breakdown, and metrics.
    """
    total_tx = final_state.successful_transmissions + final_state.failed_transmissions
    total_tx = max(total_tx, 1)

    success_rate = final_state.successful_transmissions / total_tx
    avg_sinr = _safe_mean(final_state.sinr_history)

    max_possible_throughput = max(final_state.max_steps, 1) * 50.0
    throughput_score = min(final_state.cumulative_throughput / max_possible_throughput, 1.0)

    if final_state.cumulative_energy > 0:
        efficiency = final_state.cumulative_throughput / final_state.cumulative_energy
        energy_efficiency_score = min(efficiency / 10.0, 1.0)
    else:
        energy_efficiency_score = 0.0

    sinr_quality_score = min(max(avg_sinr / 20.0, 0.0), 1.0)

    adaptation_score = 0.0
    if "adaptation" in task_config.grading_weights:
        channels_used = {action.get("frequency_channel") for action in final_state.action_history}
        channels_used.discard(None)
        adaptation_score = min(len(channels_used) / 10.0, 1.0)

    unpredictability_score = 0.0
    if "unpredictability" in task_config.grading_weights and final_state.action_history:
        freq_sequence = [
            action.get("frequency_channel", 0) for action in final_state.action_history
        ]
        transitions: Dict[tuple[int, int], int] = {}
        for idx in range(len(freq_sequence) - 1):
            pair = (freq_sequence[idx], freq_sequence[idx + 1])
            transitions[pair] = transitions.get(pair, 0) + 1
        total_transitions = sum(transitions.values())
        if total_transitions:
            entropy = 0.0
            for count in transitions.values():
                p = count / total_transitions
                entropy -= p * np.log2(p + 1e-10)
            unpredictability_score = min(entropy / 6.0, 1.0)

    component_scores = {
        "throughput": throughput_score,
        "success_rate": success_rate,
        "energy_efficiency": energy_efficiency_score,
        "sinr_quality": sinr_quality_score,
    }

    if "adaptation" in task_config.grading_weights:
        component_scores["adaptation"] = adaptation_score
    if "unpredictability" in task_config.grading_weights:
        component_scores["unpredictability"] = unpredictability_score

    final_score = 0.0
    for component, weight in task_config.grading_weights.items():
        final_score += component_scores.get(component, 0.0) * weight
    final_score = max(0.0, min(1.0, final_score))

    return {
        "score": round(final_score, 3),
        "success": final_score >= task_config.success_threshold,
        "breakdown": {k: round(v, 3) for k, v in component_scores.items()},
        "metrics": {
            "success_rate": round(success_rate, 3),
            "avg_sinr_db": round(avg_sinr, 2),
            "total_throughput_mbps": round(final_state.cumulative_throughput, 2),
            "total_energy_mj": round(final_state.cumulative_energy, 2),
            "successful_transmissions": final_state.successful_transmissions,
            "failed_transmissions": final_state.failed_transmissions,
        },
    }