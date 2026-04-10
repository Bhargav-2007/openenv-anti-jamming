"""
OpenEnv server entry point.
Minimal module that exposes the environment instance.
"""

import os
from anti_jamming_env import AntiJammingEnv

_TASK = os.getenv("ANTI_JAMMING_TASK", "easy")
_MAX_STEPS = int(os.getenv("ANTI_JAMMING_MAX_STEPS", "50"))

env = AntiJammingEnv(task=_TASK, max_steps=_MAX_STEPS)
