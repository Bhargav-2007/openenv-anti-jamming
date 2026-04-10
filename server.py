"""
OpenEnv server entry point.
Minimal module that exposes the environment instance.
"""

import os


_TASK = os.getenv("ANTI_JAMMING_TASK", "easy")
_MAX_STEPS = int(os.getenv("ANTI_JAMMING_MAX_STEPS", "50"))

# OpenEnv expects a module-level environment object.
env = AntiJammingEnv(task=_TASK, max_steps=_MAX_STEPS)
