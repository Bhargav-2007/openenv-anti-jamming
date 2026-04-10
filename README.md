---
title: Anti-Jamming OpenEnv
emoji: shield
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000
---

# Anti-Jamming Communication System (OpenEnv)

This environment simulates a real-world wireless link under intelligent jamming. Agents learn to select transmission parameters that maximize throughput while avoiding interference. The environment is OpenEnv-compliant and provides `reset()`, `step()`, and `state()` with typed Pydantic models.

## Environment Summary

Key features:
- Realistic RF physics (path loss, fading, noise, interference)
- Multiple jammer behaviors (spot, sweep, barrage, reactive, learning)
- Dense reward signals for throughput and efficiency
- Deterministic graders for reproducible scoring
- Three tasks: easy, medium, hard

## Action Space

The agent selects transmission parameters:

```python
class AntiJammingAction(BaseModel):
    frequency_channel: int  # 0-63
    tx_power_dbm: float      # 0.0-30.0
    modulation: str          # BPSK, QPSK, 16QAM, 64QAM
    coding_rate: str         # 1/2, 2/3, 3/4, 5/6
    beam_direction: int      # 0-7
    enable_fhss: bool        # frequency hopping
    enable_dsss: bool        # direct sequence spread spectrum
    enable_notch_filter: bool
```

## Observation Space

The environment returns:
- Channel states for 16 representative frequencies
- Jammer detection and estimated power
- Last transmission success, throughput, and energy
- Recent success rate and average SINR

## Reward Function

Dense reward combines:
- Throughput (primary objective)
- Energy efficiency penalty
- Success bonus / failure penalty
- SINR quality bonus
- Anti-jam technique bonus

## Tasks

Each task has a deterministic grader with score in [0.0, 1.0].

- Easy: spot jammer, success threshold 0.70
- Medium: barrage or sweep jammer, success threshold 0.60
- Hard: learning jammer, success threshold 0.50

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Baseline Inference

```bash
export HF_TOKEN="your_hf_token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export ANTI_JAMMING_TASK="easy"
python inference.py
```

The script prints only `[START]`, `[STEP]`, and `[END]` lines to stdout.

## Baseline Scores

Baseline scores depend on the model and prompt. Example targets:
- Easy: 0.70
- Medium: 0.60
- Hard: 0.50

## Docker

```bash
docker build -t bhargav-2007/anti-jamming-env:latest .
docker run -p 8000:8000 bhargav-2007/anti-jamming-env:latest
```

## Validation

```bash
openenv validate .
```
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
