"""
OpenEnv server entry-point for the Anti-Jamming environment.

Starts a FastAPI application (provided by openenv-core) that exposes the
standard OpenEnv WebSocket / REST API on the configured host and port.

Environment variables:
    OPENENV_HOST           Bind address (default: 0.0.0.0)
    OPENENV_PORT           TCP port      (default: 8000)
    ANTI_JAMMING_TASK      Task name     (default: easy)
    ENABLE_WEB_INTERFACE   Set "true" to enable the optional Gradio UI
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
    """Factory called by openenv-core for each new session."""
    return AntiJammingEnv(task=_TASK_NAME)


app = create_app(
    env=_make_env,
    action_cls=AntiJammingAction,
    observation_cls=AntiJammingObservation,
    env_name="anti-jamming-comm",
)


def main() -> None:
    """Start the OpenEnv server (used by [project.scripts] and Docker CMD)."""
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
