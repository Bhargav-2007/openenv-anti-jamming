# AI-Powered Anti-Jamming Communication System

An OpenEnv reinforcement learning environment for training AI agents to maintain wireless communication links under intelligent jamming attacks. This environment simulates realistic radio frequency physics and implements sophisticated jamming strategies from electronic warfare scenarios.

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with web frontend
python api_server.py

# 3. Open http://localhost:8000
```

That's it! Try the interactive dashboard with professional UI featuring real-time visualization and live episode training.

---

## Overview

In contested electromagnetic environments, maintaining reliable communication requires adaptive strategies to combat intelligent jamming. This environment challenges AI agents to learn real-world anti-jamming techniques through interaction with a physics-based wireless channel simulator.

**Key Features:**
- 🎨 **Professional Web Frontend** - Real-time visualization dashboard
- ✨ **Realistic RF Physics** - Path loss, fading, interference, SINR calculations
- 🧠 **Multiple Jamming Strategies** - Spot, barrage, sweep, reactive, learning-based
- 📊 **Dense Reward Signals** - For effective RL training
- 🏆 **Three Difficulty Levels** - Beginner to advanced
- 📡 **Standard OpenEnv API** - step() / reset() / state()
- 🔗 **REST API** - For remote agents
- 🐳 **Docker Ready** - Easy deployment
- Realistic RF physics (path loss, fading, interference, SINR calculations)
- Multiple jamming strategies (spot, barrage, sweep, reactive, learning-based)
- Three difficulty levels with increasing sophistication
- Dense reward signals for learning progression
- Deterministic grading system for reproducible evaluation

## Environment Details

### Action Space

The agent controls a wireless transmitter with the following parameters:

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `frequency_channel` | int | 0-63 | Which frequency channel to use |
| `tx_power_dbm` | float | 0.0-30.0 | Transmit power in dBm |
| `modulation` | enum | BPSK, QPSK, 16QAM, 64QAM | Modulation scheme (trade-off: robustness vs data rate) |
| `coding_rate` | enum | 1/2, 2/3, 3/4, 5/6 | Error correction strength |
| `beam_direction` | int | 0-7 | Spatial beam direction |
| `enable_fhss` | bool | - | Enable frequency hopping |
| `enable_dsss` | bool | - | Enable direct sequence spread spectrum |
| `enable_notch_filter` | bool | - | Enable adaptive interference filtering |

### Observation Space

The agent receives:

**Channel States** (16 representative channels):
- Signal-to-Noise Ratio (SNR)
- Signal-to-Interference-plus-Noise Ratio (SINR)
- Interference power detected
- Packet error rate
- Jamming status

**Jammer Intelligence:**
- Detected jammer type and pattern
- Estimated jammer power and bandwidth
- Center frequency of attack

**Performance Metrics:**
- Recent transmission success rate
- Average SINR over last 5 steps
- Throughput and energy consumption

### Reward Function

The reward combines multiple objectives:
Components:
- **Throughput**: Primary objective, normalized to approximately 0-1
- **Energy Cost**: Penalty for excessive power consumption
- **Success Bonus**: Plus one for successful transmission, minus 0.5 for failure
- **SINR Bonus**: Quality incentive for maintaining good signal quality
- **Technique Bonus**: Encourages using anti-jamming features

Range: approximately minus two to plus five per step

## Tasks

### Easy: Basic Defense

**Objective**: Defend against simple spot jamming attack  
**Jammer**: Fixed single-frequency constant jamming  
**Target**: Eighty percent transmission success rate  
**Recommended Techniques**: Basic frequency hopping, power control  

**Success Criteria:**
- Success rate greater than or equal to eighty percent
- Average SINR greater than or equal to twelve dB
- Cumulative throughput greater than or equal to forty Mbps
- Energy consumption less than five hundred mJ

### Medium: Adaptive Defense

**Objective**: Handle barrage and sweep jamming  
**Jammer**: Multi-frequency attacks with sweeping patterns  
**Target**: Seventy percent transmission success rate  
**Recommended Techniques**: Adaptive hopping, beamforming, notch filters  

**Success Criteria:**
- Success rate greater than or equal to seventy percent
- Average SINR greater than or equal to ten dB
- Cumulative throughput greater than or equal to thirty Mbps
- Energy consumption less than six hundred mJ

### Hard: Sophisticated Defense

**Objective**: Survive intelligent learning jammer  
**Jammer**: Learns agent patterns and predicts next moves  
**Target**: Sixty percent transmission success rate  
**Recommended Techniques**: Game-theoretic strategies, randomization, full anti-jam arsenal  

**Success Criteria:**
- Success rate greater than or equal to sixty percent
- Average SINR greater than or equal to eight dB
- Cumulative throughput greater than or equal to twenty Mbps
- Energy consumption less than seven hundred mJ

## Installation and Setup

### Local Development (GitHub Codespaces)

```bash
# Clone repository
git clone https://github.com/Bhargav-2007/openenv-anti-jamming.git
cd openenv-anti-jamming

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HF_TOKEN="your_huggingface_token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
```

### Docker Deployment

```bash
# Build Docker image
docker build -t bhargav-2007/anti-jamming-env:latest .

# Run container
docker run -p 8000:8000 \
  -e HF_TOKEN="your_token" \
  bhargav-2007/anti-jamming-env:latest

# Test health endpoint
curl http://localhost:8000/health
```

## Running Baseline Inference

The baseline inference script demonstrates performance across all three tasks:

```bash
# Run all tasks
python inference.py

# Run specific task
ANTI_JAMMING_TASK=easy python inference.py
ANTI_JAMMING_TASK=medium python inference.py
ANTI_JAMMING_TASK=hard python inference.py
```

**Expected Baseline Scores** (with Qwen2.5-72B-Instruct):
- Easy: approximately 0.65
- Medium: approximately 0.45
- Hard: approximately 0.30

## Example Usage

### Random Agent

```python
import asyncio
from anti_jamming_env import AntiJammingEnv, AntiJammingAction
import random

async def run_random_agent():
    env = AntiJammingEnv(task="easy", max_steps=50)
    result = await env.reset()
    
    total_reward = 0.0
    
    for step in range(50):
        # Random action
        action = AntiJammingAction(
            frequency_channel=random.randint(0, 63),
            tx_power_dbm=random.uniform(10.0, 25.0),
            modulation=random.choice(["BPSK", "QPSK", "16QAM", "64QAM"]),
            coding_rate=random.choice(["1/2", "2/3", "3/4", "5/6"]),
            beam_direction=random.randint(0, 7),
            enable_fhss=random.choice([True, False]),
            enable_dsss=False,
            enable_notch_filter=True
        )
        
        result = await env.step(action)
        total_reward += result.reward
        
        if result.done:
            break
    
    print(f"Total reward: {total_reward:.2f}")
    await env.close()

asyncio.run(run_random_agent())
```

### Heuristic Agent (Frequency Hopper)

```python
async def run_heuristic_agent():
    env = AntiJammingEnv(task="medium", max_steps=50)
    result = await env.reset()
    
    # Track jammed channels
    jammed_channels = set()
    current_freq = 0
    
    for step in range(50):
        obs = result.observation
        
        # Update jammed channel list
        for ch_state in obs.channel_states:
            if ch_state.is_jammed:
                jammed_channels.add(ch_state.frequency_index)
        
        # Find clear channel
        clear_channels = [i for i in range(64) if i not in jammed_channels]
        if clear_channels:
            current_freq = random.choice(clear_channels)
        
        # Adaptive action
        action = AntiJammingAction(
            frequency_channel=current_freq,
            tx_power_dbm=20.0,
            modulation="QPSK",
            coding_rate="2/3",
            beam_direction=step % 8,  # Rotate beam
            enable_fhss=True,
            enable_dsss=True,
            enable_notch_filter=True
        )
        
        result = await env.step(action)
        
        if result.done:
            break
    
    await env.close()

asyncio.run(run_heuristic_agent())
```

## Validation

Verify environment compliance with OpenEnv specification:

```bash
# Install OpenEnv CLI
pip install openenv[cli]

# Validate environment
openenv validate .

# Expected output:
# ✓ openenv.yaml found and valid
# ✓ Action/Observation models properly defined
# ✓ reset() returns StepResult
# ✓ step() returns StepResult
# ✓ state() returns State
# ✓ Dockerfile builds successfully
```

## Training an RL Agent

Example using Stable-Baselines3:

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# This requires a Gym wrapper (not included in base package)
# See examples/train_with_sb3.py for complete implementation

# Pseudocode:
# env = make_vec_env(lambda: GymWrapper(AntiJammingEnv(task="easy")), n_envs=4)
# model = PPO("MlpPolicy", env, verbose=1)
# model.learn(total_timesteps=100000)
# model.save("anti_jamming_ppo")
```

## Deployment to Hugging Face Spaces

```bash
# Login to Hugging Face
huggingface-cli login --token $HF_TOKEN

# Create Space
huggingface-cli repo create anti-jamming-env --type space --space_sdk docker

# Push to Space
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
git push hf main

# Space will auto-build from Dockerfile
# Access at: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
```

## Performance Benchmarks

| Task | Random Agent | Heuristic Agent | LLM Baseline (Qwen2.5-72B) |
|------|--------------|-----------------|----------------------------|
| Easy | 0.15 | 0.55 | 0.65 |
| Medium | 0.08 | 0.35 | 0.45 |
| Hard | 0.05 | 0.20 | 0.30 |

## Technical Details

### Physics Simulation

The environment implements:
- **Free-space path loss**: FSPL = twenty log ten of distance plus twenty log ten of frequency plus constant
- **Rayleigh fading**: Time-varying multipath channel
- **AWGN**: Thermal noise based on bandwidth and noise figure
- **SINR calculation**: Accounts for signal, interference, and noise
- **Modulation-specific BER**: Bit error rate models for each modulation scheme
- **Throughput**: Shannon-like capacity with practical constraints

### Jammer Implementations

Six jammer types with increasing sophistication:
1. **Spot Jammer**: Single frequency, high power
2. **Barrage Jammer**: Wide bandwidth, distributed power
3. **Sweep Jammer**: Time-varying frequency coverage
4. **Reactive Jammer**: Follows transmitter frequency
5. **Pulse Jammer**: Intermittent on-off pattern
6. **Smart Learning Jammer**: Pattern recognition and prediction

## Contributing

Contributions welcome. Please ensure:
- Code passes all tests: `pytest tests/`
- OpenEnv validation succeeds: `openenv validate .`
- Baseline script reproduces scores
- Documentation updated for new features

## License

MIT License. See LICENSE file for details.

## Citation

```bibtex
@software{anti_jamming_env_2026,
  author = {Bhargav-2007},
  title = {AI-Powered Anti-Jamming Communication System},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/Bhargav-2007/openenv-anti-jamming}
}
```

## Contact

- GitHub: [@Bhargav-2007](https://github.com/Bhargav-2007)
- Hugging Face: [Bhargav-2007](https://huggingface.co/Bhargav-2007)
- Environment: [anti-jamming-env](https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env)

## Acknowledgments

Built for the OpenEnv Hackathon. Special thanks to Meta AI and Hugging Face for the OpenEnv framework and infrastructure support.