"""Baseline inference script for Anti-Jamming Environment."""

import json
import os
import re
import sys
import textwrap
from typing import Any, Dict, List, Optional

from openai import OpenAI

from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode
from anti_jamming_env.tasks import TASKS


API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

TEMPERATURE = 0.7
MAX_TOKENS = 200

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

    Respond ONLY with a valid JSON object.
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
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


def build_user_prompt(step: int, obs: Any, last_reward: float, history: List[str]) -> str:
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
        Step: {step}
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
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


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


def get_model_action(
    client: Optional[OpenAI],
    step: int,
    obs: Any,
    last_reward: float,
    history: List[str],
) -> tuple[AntiJammingAction, Optional[str]]:
    if client is None:
        return _default_action(), "missing_api_key"

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
        if action_dict is None:
            return _default_action(), "parse_error"
        return AntiJammingAction(**action_dict), None
    except Exception as exc:
        print(f"model_error: {exc}", file=sys.stderr)
        return _default_action(), "model_error"


def run_single_task(task_name: str) -> Dict[str, Any]:
    api_key = HF_TOKEN or OPENAI_API_KEY
    client = OpenAI(base_url=API_BASE_URL, api_key=api_key) if api_key else None

    task_config = TASKS[task_name]
    env = AntiJammingEnv(task=task_name, max_steps=task_config.max_steps)

    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env="anti_jamming_comm", model=MODEL_NAME)

    try:
        obs = env.reset()
        last_reward = 0.0

        for step in range(1, task_config.max_steps + 1):
            if obs.done:
                break

            action, error = get_model_action(client, step, obs, last_reward, history)
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
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            tx_ok = getattr(obs, "last_transmission_success", False)
            history.append(
                f"Step {step}: {action_str} -> "
                f"{'OK' if tx_ok else 'FAIL'} reward={reward:+.2f}"
            )

            if done:
                break

        final_state = env.state
        grading = grade_episode(final_state, task_config)
        score = float(grading["score"])
        success = bool(grading["success"])
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task": task_name,
        "success": success,
        "steps": steps_taken,
        "score": score,
        "rewards": rewards,
    }


def main() -> None:
    for task_name in ["easy", "medium", "hard"]:
        run_single_task(task_name)


if __name__ == "__main__":
    main()
