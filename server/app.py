"""
OpenEnv server entry-point for the Anti-Jamming environment.
"""

import os

import uvicorn

from openenv.core import create_app
from anti_jamming_env import AntiJammingEnv, AntiJammingAction, AntiJammingObservation
from anti_jamming_env.tasks import TASKS

_TASK_NAME = os.getenv("ANTI_JAMMING_TASK", "easy")
if _TASK_NAME not in TASKS:
    raise ValueError(
        f"ANTI_JAMMING_TASK='{_TASK_NAME}' is invalid. "
        f"Choose from: {list(TASKS.keys())}"
    )


def _make_env() -> AntiJammingEnv:
    return AntiJammingEnv(task=_TASK_NAME)


app = create_app(
    env=_make_env,
    action_cls=AntiJammingAction,
    observation_cls=AntiJammingObservation,
    env_name="anti-jamming-comm",
)


def main() -> None:
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
