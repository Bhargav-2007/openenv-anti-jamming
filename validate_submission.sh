#!/usr/bin/env bash
set -euo pipefail

required_vars=(API_BASE_URL MODEL_NAME HF_TOKEN SPACE_URL)
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing env var: $var" >&2
    exit 1
  fi
done

echo "[INFO] openenv validate ."
openenv validate .

echo "[INFO] docker build -t anti-jamming-env ."
docker build -t anti-jamming-env .

echo "[INFO] ping Space URL"
curl -fsS "$SPACE_URL/health" >/dev/null
curl -fsS -X POST "$SPACE_URL/reset" -H "Content-Type: application/json" -d '{"task":"easy","seed":123}' >/dev/null

echo "[INFO] run baseline"
python inference.py --baseline

echo "[INFO] grade checks"
python - <<'PY'
from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode
from anti_jamming_env.tasks import TASKS
from inference import _fallback_action

def run_task(name, seed):
    env = AntiJammingEnv(task=name, seed=seed)
    state = env.reset()
    episode = []
    done = False
    while not done:
        action_dict = _fallback_action(state.observation.model_dump())
        action = AntiJammingAction.model_validate(action_dict)
        step = env.step(action)
        episode.append({"reward": step.reward, "info": step.info.model_dump()})
        done = step.done
        state = env.state()
    return grade_episode(episode)

scores = {}
for name, config in TASKS.items():
    score = run_task(name, int(config["seed"]))
    if not (0.0 <= score <= 1.0):
        raise SystemExit(f"Score out of range for {name}: {score}")
    scores[name] = score

print({"grader_scores": scores})
PY

echo "[INFO] validation complete"
