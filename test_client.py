#!/usr/bin/env python3
"""
Test client for Anti-Jamming OpenEnv API
Demonstrates how to interact with the environment via REST API
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class AntiJammingClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = None
        self.episode_history = []
    
    def health_check(self) -> bool:
        """Check if server is running"""
        try:
            resp = requests.get(f"{self.base_url}/api/health")
            return resp.status_code == 200
        except:
            return False
    
    def create_session(self, task: str = "easy", max_steps: int = 50) -> str:
        """Create a new training session"""
        resp = requests.post(
            f"{self.base_url}/api/sessions",
            json={"task": task, "max_steps": max_steps}
        )
        resp.raise_for_status()
        self.session_id = resp.json()["session_id"]
        print(f"✅ Created session: {self.session_id} (task={task})")
        return self.session_id
    
    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one step"""
        if not self.session_id:
            raise ValueError("No active session")
        
        resp = requests.post(
            f"{self.base_url}/api/sessions/{self.session_id}/step",
            json={"action": action}
        )
        resp.raise_for_status()
        return resp.json()
    
    def reset(self) -> Dict[str, Any]:
        """Reset episode"""
        if not self.session_id:
            raise ValueError("No active session")
        
        resp = requests.post(f"{self.base_url}/api/sessions/{self.session_id}/reset")
        resp.raise_for_status()
        return resp.json()
    
    def close(self) -> Dict[str, Any]:
        """Close session and get results"""
        if not self.session_id:
            raise ValueError("No active session")
        
        resp = requests.post(f"{self.base_url}/api/sessions/{self.session_id}/close")
        resp.raise_for_status()
        results = resp.json()
        self.session_id = None
        return results
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions"""
        resp = requests.get(f"{self.base_url}/api/sessions")
        resp.raise_for_status()
        return resp.json()


def simple_agent_policy(step: int, observation: Dict) -> Dict[str, Any]:
    """
    Simple agent policy: rotate through frequencies, adjust power based on SINR
    """
    # Rotate through channels
    frequency = (step * 3) % 64
    
    # Adaptive power: increase power if SINR is low
    try:
        sinr = observation.get("sinr_db", 10)
        tx_power = 15 if sinr > 10 else 25
    except:
        tx_power = 20
    
    return {
        "frequency_channel": frequency,
        "tx_power_dbm": tx_power,
        "modulation": "QPSK",
        "coding_rate": "3/4",
        "beam_direction": step % 8,
        "enable_fhss": step % 2 == 0,
        "enable_dsss": True,
        "enable_notch_filter": step % 3 == 0
    }


def run_episode(client: AntiJammingClient, task: str = "easy", max_steps: int = 50):
    """Run a complete episode"""
    print(f"\n{'='*60}")
    print(f"🚀 Running Episode: {task}")
    print(f"{'='*60}")
    
    client.create_session(task=task, max_steps=max_steps)
    
    rewards = []
    sinrs = []
    
    for step in range(max_steps):
        # Get agent policy
        action = simple_agent_policy(step, {})
        
        # Execute step
        result = client.step(action)
        
        rewards.append(result["reward"])
        obs = result.get("observation", {})
        sinr = obs.get("sinr_db", 0)
        sinrs.append(sinr)
        
        # Print progress
        status = "✓" if result["reward"] > 0 else "✗"
        print(f"Step {step+1:2d}: {status} Reward={result['reward']:6.2f} SINR={sinr:6.1f}dB Done={result['done']}")
        
        if result["done"]:
            print(f"Episode ended at step {step+1}")
            break
    
    # Close and get results
    results = client.close()
    
    # Print summary
    print(f"\n{'─'*60}")
    print("📊 Episode Summary:")
    print(f"{'─'*60}")
    print(f"Success:           {results['success']}")
    print(f"Steps:             {results['steps']}")
    print(f"Score:             {results['score']:.3f}")
    print(f"Total Reward:      {sum(rewards):.2f}")
    print(f"Avg Reward:        {sum(rewards)/len(rewards):.2f}")
    print(f"Max Reward:        {max(rewards):.2f}")
    print(f"Min Reward:        {min(rewards):.2f}")
    print(f"Avg SINR:          {sum(sinrs)/len(sinrs):.1f} dB")
    
    if "metrics" in results:
        print(f"\nMetrics:")
        for key, value in results["metrics"].items():
            print(f"  {key:.<30} {value}")
    
    return results


def benchmark_all_tasks(client: AntiJammingClient):
    """Run all tasks and compare performance"""
    print(f"\n{'='*60}")
    print("🏆 Running Full Benchmark")
    print(f"{'='*60}\n")
    
    tasks = ["easy", "medium", "hard"]
    results_summary = {}
    
    for task in tasks:
        results = run_episode(client, task=task, max_steps=50)
        results_summary[task] = results
    
    # Print comparison
    print(f"\n{'='*60}")
    print("📈 Benchmark Results:")
    print(f"{'='*60}")
    print(f"{'Task':<10} {'Success':<10} {'Score':<10} {'Steps':<10}")
    print(f"{'-'*40}")
    
    for task in tasks:
        r = results_summary[task]
        print(f"{task:<10} {'✓' if r['success'] else '✗':<10} {r['score']:<10.3f} {r['steps']:<10}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
        # Run full benchmark
        client = AntiJammingClient()
        
        if not client.health_check():
            print("❌ Server is not running!")
            print("Start it with: python api_server.py")
            return 1
        
        benchmark_all_tasks(client)
    else:
        # Run single episode
        client = AntiJammingClient()
        
        if not client.health_check():
            print("❌ Server is not running!")
            print("Start it with: python api_server.py")
            return 1
        
        task = sys.argv[1] if len(sys.argv) > 1 else "easy"
        run_episode(client, task=task, max_steps=50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
