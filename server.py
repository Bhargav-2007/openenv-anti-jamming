"""
OpenEnv Server for Anti-Jamming Environment
Serves the environment via HTTP for remote access
"""

import os
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
    # Get task from environment variable if not provided
    if task is None:
        task = os.getenv("ANTI_JAMMING_TASK", "easy")
    
    # Get max steps from environment
    max_steps = int(os.getenv("MAX_STEPS", "50"))
    
    # Create environment
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
        return
    
    # Get configuration from environment
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    
    print(f"Starting Anti-Jamming Environment Server on {host}:{port}")
    print(f"Default task: {os.getenv('ANTI_JAMMING_TASK', 'easy')}")
    
    # Start server
    serve(
        env_factory=create_env,
        host=host,
        port=port
    )


if __name__ == "__main__":
    main()