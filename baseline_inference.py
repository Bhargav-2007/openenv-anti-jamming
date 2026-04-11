"""Run a baseline agent and report deterministic scores for all tasks."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from openai import OpenAI

from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or HF_TOKEN


def _fallback_action(obs: Dict[str, Any]) -> Dict[str, Any]:
    channels = obs.get("channel_powers_dbm") or [0.0] * 16
    min_index = int(min(range(len(channels)), key=lambda i: channels[i]))
    freq = int(min_index * 4)
    return {
        "frequency_channel": freq,
        "tx_power_dbm": 18.0,
        "modulation": "QPSK",
        "coding_rate": "3/4",
        "beam_direction": 0,
        "enable_fhss": True,
        "enable_dsss": False,
        "enable_notch_filter": True,
    }


def _llm_action(obs: Dict[str, Any]) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return _fallback_action(obs)

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=API_BASE_URL)
    prompt = (
        "Select a safe anti-jamming action as JSON with fields: "
        "frequency_channel, tx_power_dbm, modulation, coding_rate, "
        "beam_direction, enable_fhss, enable_dsss, enable_notch_filter."
    )
    response = client.responses.create(
        model=MODEL_NAME,
        input=[{"role": "user", "content": prompt + "\nObservation: " + json.dumps(obs)}],
        temperature=0.0,
    )
    action = {}
    try:
        action = json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError):
        return _fallback_action(obs)
    return action if action else _fallback_action(obs)


def run_task(task: str, seed: int) -> float:
    env = AntiJammingEnv(task=task, seed=seed)
    state = env.reset()
    episode: List[Dict[str, Any]] = []

    done = False
    while not done:
        action_dict = _llm_action(state.observation.model_dump())
        action = AntiJammingAction.model_validate(action_dict)
        step = env.step(action)
        episode.append({"reward": step.reward, "info": step.info.model_dump()})
        done = step.done
        state = env.state()

    return grade_episode(episode)


def main() -> None:
    tasks = [("easy", 123), ("medium", 456), ("hard", 789)]
    results: Dict[str, float] = {}
    for name, seed in tasks:
        results[name] = run_task(name, seed)

    print("Baseline scores (deterministic seeds):")
    for name in ("easy", "medium", "hard"):
        print(f"- {name}: {results[name]:.3f}")


if __name__ == "__main__":
    main()
