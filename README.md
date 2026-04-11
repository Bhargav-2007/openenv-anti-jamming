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

## Deployment to Hugging Face Spaces

```bash
# Login to Hugging Face
huggingface-cli login --token $HF_TOKEN

# Create Space
huggingface-cli repo create anti-jamming-env --type space --space_sdk docker

# Push to Space
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
git push hf main
```

## License

MIT License. See LICENSE file for details.
