"""
Baseline Inference Script for Anti-Jamming Environment
=======================================================
MANDATORY REQUIREMENTS:
- Named ``inference.py``, placed in the repository root.
- Uses the OpenAI client for all LLM calls.
- Emits exactly three line types to stdout: [START], [STEP], [END].
- Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional

from openai import OpenAI

from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode
from anti_jamming_env.tasks import TASKS

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

TASK_NAME = os.getenv("ANTI_JAMMING_TASK", "easy")
BENCHMARK = os.getenv("ANTI_JAMMING_BENCHMARK", "anti_jamming_comm")

MAX_STEPS = 50
TEMPERATURE = 0.7
MAX_TOKENS = 200
SUCCESS_SCORE_THRESHOLD = 0.6

_MAX_REWARD_PER_STEP = 5.0

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are controlling an AI-powered wireless transmitter in a contested electromagnetic environment.
    Your mission: Maintain communication with a receiver while under attack from an intelligent jammer.

    At each step, choose transmission parameters:
    - frequency_channel: integer 0-63 (which frequency to use)
    - tx_power_dbm: float 0.0-30.0 (transmit power in dBm)
    - modulation: one of "BPSK", "QPSK", "16QAM", "64QAM"
    - coding_rate: one of "1/2", "2/3", "3/4", "5/6"
    - beam_direction: integer 0-7
    - enable_fhss: boolean
    - enable_dsss: boolean
    - enable_notch_filter: boolean

    Respond ONLY with a valid JSON object. Example:
    {
        "frequency_channel": 42,
        "tx_power_dbm": 20.0,
        "modulation": "QPSK",
        "coding_rate": "2/3",
        "beam_direction": 3,
        "enable_fhss": true,
        "enable_dsss": false,
        "enable_notch_filter": true
    }
    """
).strip()

# ═══════════════════════════════════════════════════════════════════
# LOGGING (exact [START/STEP/END] format)
# ═══════════════════════════════════════════════════════════════════


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ═══════════════════════════════════════════════════════════════════
# AGENT LOGIC
# ═══════════════════════════════════════════════════════════════════


def build_user_prompt(
    step: int,
    obs: Any,
    last_reward: float,
    history: List[str],
) -> str:
    obs_dict = obs.model_dump() if hasattr(obs, "model_dump") else dict(obs)

    channels_info = []
    for ch in obs_dict.get("channel_states", [])[:8]:
        channels_info.append(
            f"  Ch{ch['frequency_index']}: SINR={ch['sinr_db']:.1f}dB "
            f"{'[JAMMED]' if ch['is_jammed'] else ''} PER={ch['packet_error_rate']:.2f}"
        )
    channels_summary = "\n".join(channels_info) or "No data"

    jammer = obs_dict.get("jammer_state", {})

    return textwrap.dedent(
        f"""
        Step: {step}/{MAX_STEPS}
        Task: {obs_dict.get('task_description', '')}

        LAST TRANSMISSION:
        - Success: {obs_dict.get('last_transmission_success')}
        - SINR: {obs_dict.get('last_sinr_db', 0):.1f} dB
        - Throughput: {obs_dict.get('last_throughput_mbps', 0):.2f} Mbps
        - Reward: {last_reward:.2f}

        CHANNEL CONDITIONS (top 8):
        {channels_summary}

        JAMMER:
        - Type: {jammer.get('detected_jammer_type', 'unknown')}
        - Pattern: {jammer.get('attack_pattern', 'unknown')}

        RECENT:
        - Success Rate (last 5): {obs_dict.get('recent_success_rate', 0):.1%}
        - Avg SINR: {obs_dict.get('recent_avg_sinr_db', 0):.1f} dB

        HISTORY:
        {chr(10).join(history[-3:]) or 'None'}

        Respond with a JSON action object.
        """
    ).strip()


def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from LLM text without eval."""
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def get_model_action(
    client: OpenAI,
    step: int,
    obs: Any,
    last_reward: float,
    history: List[str],
) -> AntiJammingAction:
    user_prompt = build_user_prompt(step, obs, last_reward, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        response_text = (completion.choices[0].message.content or "").strip()
        action_dict = _safe_parse_json(response_text)
        if action_dict is not None:
            return AntiJammingAction(**action_dict)
    except Exception as exc:
        print(f"[DEBUG] model error: {exc}", flush=True)
    return _default_action()


def _default_action() -> AntiJammingAction:
    return AntiJammingAction(
        frequency_channel=32,
        tx_power_dbm=15.0,
        modulation="QPSK",
        coding_rate="1/2",
        beam_direction=0,
        enable_fhss=True,
        enable_dsss=False,
        enable_notch_filter=True,
    )


# ═══════════════════════════════════════════════════════════════════
# EPISODE RUNNER
# ═══════════════════════════════════════════════════════════════════


def run_single_task(task_name: str) -> Dict[str, Any]:
    """Run one episode for *task_name* and return results."""
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = AntiJammingEnv(task=task_name, max_steps=MAX_STEPS)

    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env.reset()
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            action = get_model_action(client, step, obs, last_reward, history)

            obs = env.step(action)
            reward = float(obs.reward or 0.0)
            done = bool(obs.done)

            rewards.append(reward)
            steps_taken = step
            last_reward = reward

            action_str = (
                f"freq={action.frequency_channel},"
                f"pow={action.tx_power_dbm:.1f}dBm,"
                f"mod={action.modulation}"
            )
            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            tx_ok = getattr(obs, "last_transmission_success", False)
            history.append(
                f"Step {step}: {action_str} -> "
                f"{'OK' if tx_ok else 'FAIL'} reward={reward:+.2f}"
            )

            if done:
                break

        # Grade the episode
        final_state = env.state
        score, _ = grade_episode(
            task_config=TASKS[task_name],
            successful_transmissions=final_state.successful_transmissions,
            failed_transmissions=final_state.failed_transmissions,
            sinr_history=final_state.reward_history,
            throughput_total=final_state.cumulative_throughput,
            energy_total=final_state.cumulative_energy,
            max_steps=MAX_STEPS,
        )
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task": task_name,
        "success": success,
        "steps": steps_taken,
        "score": score,
        "rewards": rewards,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════


def main() -> None:
    all_results = []
    for task_name in ["easy", "medium", "hard"]:
        print(f"\n{'='*60}", flush=True)
        print(f"Running Task: {task_name.upper()}", flush=True)
        print(f"{'='*60}\n", flush=True)
        result = run_single_task(task_name)
        all_results.append(result)

    print(f"\n{'='*60}", flush=True)
    print("BASELINE EVALUATION SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for result in all_results:
        avg_r = sum(result["rewards"]) / len(result["rewards"]) if result["rewards"] else 0.0
        print(
            f"\n{result['task'].upper()}: success={result['success']} "
            f"score={result['score']:.3f} steps={result['steps']} avg_reward={avg_r:.2f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
