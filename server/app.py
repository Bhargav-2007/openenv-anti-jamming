"""
OpenEnv Server for Anti-Jamming Environment - Legacy Wrapper
This module provides compatibility with OpenEnv framework.
For full-featured server with frontend, use api_server.py instead.
"""

import os
import sys
from typing import Optional

from anti_jamming_env import AntiJammingEnv

# Import OpenEnv server utilities
try:
    from openenv import serve
except ImportError:
    print("Warning: openenv package not found. Install with: pip install openenv")
    serve = None


def create_env(task: Optional[str] = None, **kwargs) -> AntiJammingEnv:
    """
    Factory function to create environment instances.
    
    Args:
        task: Task difficulty ("easy", "medium", "hard")
        **kwargs: Additional environment parameters
    
    Returns:
        AntiJammingEnv instance
    """
    if task is None:
        task = os.getenv("ANTI_JAMMING_TASK", "easy")
    
    max_steps = int(os.getenv("MAX_STEPS", "50"))
    
    env = AntiJammingEnv(
        task=task,
        max_steps=max_steps,
        **kwargs
    )
    
    return env


def main():
    """Start the OpenEnv server."""
    if serve is None:
        print("ERROR: openenv package not installed")
        print("Install with: pip install openenv")
        print("\nAlternatively, use api_server.py for full-featured server with frontend:")
        print("  python -m api_server")
        return
    
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    
    print(f"Starting Anti-Jamming Environment Server on {host}:{port}")
    print(f"Default task: {os.getenv('ANTI_JAMMING_TASK', 'easy')}")
    
    serve(
        env_factory=create_env,
        host=host,
        port=port
    )


if __name__ == "__main__":
    main()
