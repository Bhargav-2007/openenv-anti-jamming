"""
Baseline Inference Script for Anti-Jamming Environment
===================================
MANDATORY REQUIREMENTS:
- This file must be named `inference.py` and placed in the root directory
- Must use OpenAI Client for all LLM calls
- Must emit exactly three line types to stdout: [START], [STEP], [END]
- Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

This script demonstrates baseline performance across all three tasks (easy, medium, hard).
"""

import asyncio
import os
import textwrap
from typing import List, Optional, Dict, Any

from openai import OpenAI

# ←←← ANTI-JAMMING: Import our environment
from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode
from anti_jamming_env.tasks import TASKS

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

IMAGE_NAME = os.getenv("IMAGE_NAME")  # Docker image (if using containerized env)
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

# Task configuration
TASK_NAME = os.getenv("ANTI_JAMMING_TASK", "easy")  # ←←← ANTI-JAMMING: Task selection
BENCHMARK = os.getenv("ANTI_JAMMING_BENCHMARK", "anti_jamming_comm")

MAX_STEPS = 50
TEMPERATURE = 0.7
MAX_TOKENS = 200
SUCCESS_SCORE_THRESHOLD = 0.6  # Score threshold for "success"

# Maximum possible reward per step (for normalization)
# ←←← ANTI-JAMMING: Reward range is approximately -2 to +5 per step
_MAX_REWARD_PER_STEP = 5.0
MAX_TOTAL_REWARD = MAX_STEPS * _MAX_REWARD_PER_STEP

# ←←← ANTI-JAMMING: System prompt for the LLM agent
SYSTEM_PROMPT = textwrap.dedent(
    """
    You are controlling an AI-powered wireless transmitter in a contested electromagnetic environment.
    Your mission: Maintain communication with a receiver while under attack from an intelligent jammer.
    
    At each step, you must select transmission parameters:
    - frequency_channel: Integer from 0-63 (which frequency to use)
    - tx_power_dbm: Float from 0.0-30.0 (transmit power in dBm)
    - modulation: One of "BPSK", "QPSK", "16QAM", "64QAM" (higher = faster but less robust)
    - coding_rate: One of "1/2", "2/3", "3/4", "5/6" (lower = more error correction)
    - beam_direction: Integer from 0-7 (directional antenna pointing)
    - enable_fhss: Boolean (enable frequency hopping)
    - enable_dsss: Boolean (enable direct sequence spread spectrum)
    - enable_notch_filter: Boolean (enable adaptive interference filtering)
    
    You will receive observations about:
    - Channel states (SNR, interference, packet error rates)
    - Jammer activity and patterns
    - Recent transmission success rates
    
    Your goal: Maximize throughput while minimizing energy consumption and avoiding jamming.
    
    Respond with a valid JSON object containing your action parameters. Example:
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
# LOGGING FUNCTIONS (EXACT FORMAT FROM ORIGINAL)
# ═══════════════════════════════════════════════════════════════════

def log_start(task: str, env: str, model: str) -> None:
    """Log episode start."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log individual step."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log episode end."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ═══════════════════════════════════════════════════════════════════
# AGENT LOGIC
# ═══════════════════════════════════════════════════════════════════

def build_user_prompt(step: int, observation: Any, last_reward: float, history: List[str]) -> str:
    """
    Build prompt for the LLM agent based on current observation.
    
    ←←← ANTI-JAMMING: Customized for wireless communication domain
    """
    # Extract key information from observation
    obs_dict = observation.model_dump() if hasattr(observation, 'model_dump') else observation
    
    # Get channel information summary
    channels_info = []
    for ch_state in obs_dict.get("channel_states", [])[:8]:  # Show top 8 channels
        channels_info.append(
            f"  Ch{ch_state['frequency_index']}: SINR={ch_state['sinr_db']:.1f}dB, "
            f"Jammed={'YES' if ch_state['is_jammed'] else 'NO'}, "
            f"PER={ch_state['packet_error_rate']:.2f}"
        )
    
    channels_summary = "\n".join(channels_info) if channels_info else "No channel data"
    
    # Jammer information
    jammer_info = obs_dict.get("jammer_state", {})
    jammer_type = jammer_info.get("detected_jammer_type", "unknown")
    jammer_pattern = jammer_info.get("attack_pattern", "unknown")
    
    # Recent performance
    recent_success_rate = obs_dict.get("recent_success_rate", 0.0)
    recent_avg_sinr = obs_dict.get("recent_avg_sinr_db", 0.0)
    
    # Last transmission result
    last_success = obs_dict.get("last_transmission_success", False)
    last_sinr = obs_dict.get("last_sinr_db", 0.0)
    last_throughput = obs_dict.get("last_throughput_mbps", 0.0)
    
    # History summary
    history_block = "\n".join(history[-3:]) if history else "None"
    
    prompt = textwrap.dedent(
        f"""
        Step: {step}/{MAX_STEPS}
        Task: {obs_dict.get('task_description', 'Unknown')}
        
        LAST TRANSMISSION:
        - Success: {last_success}
        - SINR: {last_sinr:.1f} dB
        - Throughput: {last_throughput:.2f} Mbps
        - Reward: {last_reward:.2f}
        
        CHANNEL CONDITIONS (top 8):
        {channels_summary}
        
        JAMMER INTELLIGENCE:
        - Type: {jammer_type}
        - Pattern: {jammer_pattern}
        
        RECENT PERFORMANCE:
        - Success Rate (last 5): {recent_success_rate:.1%}
        - Avg SINR: {recent_avg_sinr:.1f} dB
        
        HISTORY:
        {history_block}
        
        Based on this information, choose your next transmission parameters.
        Return ONLY a valid JSON object with your action.
        """
    ).strip()
    
    return prompt


def parse_action_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse action JSON from LLM response.
    
    ←←← ANTI-JAMMING: Extract JSON from response text
    """
    import json
    import re
    
    # Try to find JSON in response
    json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
    if json_match:
        try:
            action_dict = json.loads(json_match.group(0))
            return action_dict
        except json.JSONDecodeError:
            pass
    
    return None


def get_model_action(
    client: OpenAI,
    step: int,
    observation: Any,
    last_reward: float,
    history: List[str]
) -> AntiJammingAction:
    """
    Query LLM for next action based on current observation.
    
    ←←← ANTI-JAMMING: Uses OpenAI client to get wireless transmission parameters
    """
    user_prompt = build_user_prompt(step, observation, last_reward, history)
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        response_text = (completion.choices[0].message.content or "").strip()
        
        # Parse action from response
        action_dict = parse_action_from_response(response_text)
        
        if action_dict:
            # Create action object
            return AntiJammingAction(**action_dict)
        else:
            # Fallback: safe default action
            print(f"[DEBUG] Failed to parse action from LLM response, using default", flush=True)
            return get_default_action()
    
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}, using default action", flush=True)
        return get_default_action()


def get_default_action() -> AntiJammingAction:
    """
    Return a safe default action for fallback.
    
    ←←← ANTI-JAMMING: Conservative transmission parameters
    """
    return AntiJammingAction(
        frequency_channel=32,  # Middle of spectrum
        tx_power_dbm=15.0,     # Medium power
        modulation="QPSK",     # Robust modulation
        coding_rate="1/2",     # Strong error correction
        beam_direction=0,      # Default direction
        enable_fhss=True,      # Enable hopping
        enable_dsss=False,
        enable_notch_filter=True
    )


# ═══════════════════════════════════════════════════════════════════
# MAIN INFERENCE LOOP
# ═══════════════════════════════════════════════════════════════════

async def run_single_task(task_name: str) -> Dict[str, Any]:
    """
    Run inference on a single task.
    
    ←←← ANTI-JAMMING: Runs one episode of anti-jamming task
    
    Returns:
        Dictionary with episode results
    """
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Create environment (using from_docker_image if IMAGE_NAME is set)
    if IMAGE_NAME:
        env = await AntiJammingEnv.from_docker_image(IMAGE_NAME, task=task_name)
    else:
        env = AntiJammingEnv(task=task_name, max_steps=MAX_STEPS)
    
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        # Reset environment
        result = await env.reset()
        observation = result.observation
        last_reward = 0.0
        
        # Episode loop
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            
            # Get action from model
            action = get_model_action(client, step, observation, last_reward, history)
            
            # Execute action
            result = await env.step(action)
            observation = result.observation
            reward = result.reward or 0.0
            done = result.done
            error = None  # No action errors in this environment
            
            rewards.append(reward)
            steps_taken = step
            last_reward = reward
            
            # Log step
            action_str = f"freq={action.frequency_channel},pow={action.tx_power_dbm:.1f}dBm,mod={action.modulation}"
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)
            
            # Update history
            tx_success = observation.last_transmission_success if hasattr(observation, 'last_transmission_success') else False
            history.append(
                f"Step {step}: {action_str} -> "
                f"{'SUCCESS' if tx_success else 'FAILED'}, reward={reward:+.2f}"
            )
            
            if done:
                break
        
        # Get final state for grading
        final_state = env.state()
        
        # Calculate score using grader
        task_config = TASKS[task_name]
        final_score, score_breakdown = grade_episode(
            task_config=task_config,
            successful_transmissions=final_state.successful_transmissions,
            failed_transmissions=final_state.failed_transmissions,
            sinr_history=[r for r in final_state.reward_history if r > -1000],  # Valid SINR values
            throughput_total=final_state.cumulative_throughput,
            energy_total=final_state.cumulative_energy,
            max_steps=MAX_STEPS
        )
        
        score = final_score
        success = score >= SUCCESS_SCORE_THRESHOLD
        
        return {
            "task": task_name,
            "success": success,
            "steps": steps_taken,
            "score": score,
            "rewards": rewards,
            "score_breakdown": score_breakdown
        }
    
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


async def main() -> None:
    """
    Main entry point - runs all three tasks.
    
    ←←← ANTI-JAMMING: Baseline evaluation across all difficulty levels
    """
    # Run all three tasks
    tasks_to_run = ["easy", "medium", "hard"]
    
    all_results = []
    
    for task_name in tasks_to_run:
        print(f"\n{'='*60}", flush=True)
        print(f"Running Task: {task_name.upper()}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        result = await run_single_task(task_name)
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*60}", flush=True)
    print("BASELINE EVALUATION SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    
    for result in all_results:
        print(f"\n{result['task'].upper()} Task:", flush=True)
        print(f"  Success: {result['success']}", flush=True)
        print(f"  Score: {result['score']:.3f}", flush=True)
        print(f"  Steps: {result['steps']}", flush=True)
        print(f"  Avg Reward: {sum(result['rewards'])/len(result['rewards']):.2f}", flush=True)
        
        if 'score_breakdown' in result:
            breakdown = result['score_breakdown']
            print(f"  Breakdown:", flush=True)
            print(f"    Success Rate: {breakdown.get('success_rate_score', 0):.2f}", flush=True)
            print(f"    SINR Quality: {breakdown.get('sinr_score', 0):.2f}", flush=True)
            print(f"    Throughput: {breakdown.get('throughput_score', 0):.2f}", flush=True)
            print(f"    Energy Eff.: {breakdown.get('energy_score', 0):.2f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())