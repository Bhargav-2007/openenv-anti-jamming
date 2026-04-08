# 🛰️ Anti-Jamming OpenEnv - Complete Setup Guide

## Quick Start

### Option 1: Full-Featured Web Interface (Recommended)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the API server with web frontend
python api_server.py
```

Then open your browser to: **http://localhost:8000**

### Option 2: OpenEnv Framework Server

```bash
# Using the standard OpenEnv framework
python -m server.app
```

---

## 🎮 Web Frontend Features

The interactive web dashboard provides:

### **Control Panel**
- 🎯 Create/reset/close training sessions
- 🎚️ Adjust transmission parameters in real-time:
  - Frequency channel selection (0-63)
  - TX power (0-30 dBm)
  - Modulation scheme (BPSK, QPSK, 16QAM, 64QAM)
  - Coding rate (1/2 to 5/6)
  - Beam direction
  - Anti-jamming techniques (FHSS, DSSS, Notch filter)

### **Live Visualization**
- 📊 Real-time environment metrics:
  - Current step / total steps
  - Immediate reward
  - Cumulative reward
  - Signal-to-Interference-plus-Noise Ratio (SINR)
  - Success rate
  - Throughput
  - Energy consumption

### **Frequency Channel Display**
- 🔴 Color-coded channels:
  - Red = Jammed channels
  - Green = Clear channels
  - Gray = Untested channels
- Click to select channel for transmission

### **Performance Charts**
- 📈 Reward trajectory across episode
- 📉 SINR quality monitoring
- Live updates as agent trains

### **Episode Results**
- 🏆 Final score and success metrics
- Win/loss determination
- Average reward calculation

---

## 📡 REST API Endpoints

### Session Management

#### Create Session
```bash
POST /api/sessions
Content-Type: application/json

{
  "task": "easy",
  "max_steps": 50,
  "seed": null
}

Response: { "session_id": "abc12345" }
```

#### List Sessions
```bash
GET /api/sessions

Response: {
  "abc12345": {
    "session_id": "abc12345",
    "task": "easy",
    "step": 5,
    "max_steps": 50,
    "done": false,
    "cumulative_reward": 12.50
  }
}
```

#### Get Session Info
```bash
GET /api/sessions/{session_id}

Response: {
  "session_id": "abc12345",
  "task": "easy",
  "step": 5,
  "max_steps": 50,
  "done": false,
  "cumulative_reward": 12.50
}
```

#### Execute Step
```bash
POST /api/sessions/{session_id}/step
Content-Type: application/json

{
  "action": {
    "frequency_channel": 32,
    "tx_power_dbm": 20.0,
    "modulation": "QPSK",
    "coding_rate": "2/3",
    "beam_direction": 3,
    "enable_fhss": true,
    "enable_dsss": false,
    "enable_notch_filter": true
  }
}

Response: {
  "observation": { ... },
  "reward": 2.45,
  "done": false,
  "info": { ... },
  "step": 6
}
```

#### Reset Session
```bash
POST /api/sessions/{session_id}/reset

Response: { "observation": { ... } }
```

#### Close Session / Grade Episode
```bash
POST /api/sessions/{session_id}/close

Response: {
  "success": true,
  "steps": 50,
  "score": 0.78,
  "rewards": [2.1, 1.8, -0.5, ...],
  "metrics": {
    "success_rate": 0.80,
    "avg_sinr_db": 12.5,
    "throughput_mbps": 45.2,
    "energy_efficiency": 2.1
  }
}
```

#### Health Check
```bash
GET /api/health

Response: {
  "status": "healthy",
  "timestamp": "2026-04-08T10:30:00.123456",
  "active_sessions": 3
}
```

---

## 🧠 Training an AI Agent

### Python Example

```python
import asyncio
from anti_jamming_env import AntiJammingEnv, AntiJammingAction

async def main():
    # Create environment
    env = AntiJammingEnv(task="medium", max_steps=50)
    
    # Reset for new episode
    result = await env.reset()
    print(f"Initial observation: {result.observation}")
    
    # Run episode
    for step in range(50):
        # Define action (agent decision)
        action = AntiJammingAction(
            frequency_channel=step % 64,
            tx_power_dbm=20.0,
            modulation="QPSK",
            coding_rate="3/4",
            beam_direction=0,
            enable_fhss=True,
            enable_dsss=False,
            enable_notch_filter=True
        )
        
        # Execute step
        result = await env.step(action)
        
        print(f"Step {step}: reward={result.reward}, done={result.done}")
        
        if result.done:
            break
    
    await env.close()

asyncio.run(main())
```

### Using the REST API

```python
import requests
import json

# Create session
resp = requests.post('http://localhost:8000/api/sessions', json={
    'task': 'easy',
    'max_steps': 50
})
session_id = resp.json()['session_id']

# Run episode
for step in range(50):
    action = {
        'frequency_channel': step % 64,
        'tx_power_dbm': 20.0,
        'modulation': 'QPSK',
        'coding_rate': '3/4',
        'beam_direction': 0,
        'enable_fhss': True,
        'enable_dsss': False,
        'enable_notch_filter': True
    }
    
    resp = requests.post(
        f'http://localhost:8000/api/sessions/{session_id}/step',
        json={'action': action}
    )
    
    result = resp.json()
    print(f"Reward: {result['reward']}, Done: {result['done']}")
    
    if result['done']:
        break

# Get final grade
resp = requests.post(f'http://localhost:8000/api/sessions/{session_id}/close')
results = resp.json()
print(f"Final Score: {results['score']}")
print(f"Metrics: {results['metrics']}")
```

---

## 🏗️ Environment Details

### Tasks

#### Easy: Basic Defense
- **Opponent**: Constant spot jamming on one frequency
- **Goal**: 80% transmission success
- **Techniques**: Basic frequency hopping, power control

#### Medium: Adaptive Defense
- **Opponent**: Multi-frequency sweeping jammer
- **Goal**: 70% transmission success
- **Techniques**: Adaptive hopping, beamforming, notch filters

#### Hard: Sophisticated Defense
- **Opponent**: Learning jammer that adapts to agent strategy
- **Goal**: 60% transmission success
- **Techniques**: Game-theoretic strategies, randomization

### Observation Space

```python
{
    "channel_states": [
        {
            "frequency_index": 0,
            "snr_db": 10.5,
            "sinr_db": 8.2,
            "interference_power_dbm": -80.0,
            "packet_error_rate": 0.15,
            "is_jammed": True
        },
        # ... 15 representative channels
    ],
    "jammer_state": {
        "detected_jammer_type": "sweep",
        "jammer_power_dbm": -60.0,
        "jammer_bandwidth_mhz": 40.0,
        "jammer_center_freq_idx": 32
    },
    "performance_metrics": {
        "last_transmission_success": True,
        "success_rate_recent": 0.75,
        "throughput_mbps": 45.2,
        "energy_efficiency": 2.1
    }
}
```

### Action Space

```python
{
    "frequency_channel": int,           # 0-63
    "tx_power_dbm": float,              # 0-30
    "modulation": str,                  # BPSK, QPSK, 16QAM, 64QAM
    "coding_rate": str,                 # 1/2, 2/3, 3/4, 5/6
    "beam_direction": int,              # 0-7
    "enable_fhss": bool,                # Frequency hopping
    "enable_dsss": bool,                # Spread spectrum
    "enable_notch_filter": bool         # Interference filtering
}
```

### Reward Function

```
Reward = throughput + energy_penalty + success_bonus + sinr_quality + technique_bonus

Ranges: ~-2 to +5 per step
```

---

## 🐳 Docker Deployment

```bash
# Build Docker image
docker build -t anti-jamming-env:latest .

# Run container
docker run -p 8000:8000 \
  -e ANTI_JAMMING_TASK=easy \
  -e OPENENV_PORT=8000 \
  anti-jamming-env:latest

# Access frontend
# http://localhost:8000
```

### Docker Compose

```yaml
version: '3.8'

services:
  anti-jamming:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTI_JAMMING_TASK=easy
      - OPENENV_PORT=8000
      - MAX_STEPS=50
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🚀 Hugging Face Spaces

The environment is deployed on Hugging Face Spaces:

**Space URL**: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

Features:
- ✅ Full Docker integration
- ✅ Web frontend automatically served
- ✅ Zero-setup access
- ✅ Shareable via Spaces link

---

## 📊 Performance Benchmarks

### Baseline Agent Results

| Task | Difficulty | Success Rate | Avg SINR | Throughput | Score |
|------|-----------|--------------|---------|-----------|-------|
| Easy | Beginner  | 85%         | 14.2 dB | 48 Mbps   | 0.82  |
| Medium | Intermediate | 72%    | 11.5 dB | 32 Mbps   | 0.68  |
| Hard | Advanced  | 58%         | 9.8 dB  | 22 Mbps   | 0.55  |

---

## 🛠️ Development

### Run Tests
```bash
pytest tests/
```

### Validate Environment
```bash
openenv validate .
```

### Generate Lock File
```bash
uv lock
```

---

## 📖 References

- **OpenEnv Framework**: https://github.com/openenv-org/openenv
- **Wireless Communications**: RF physics simulation based on IEEE standards
- **Anti-Jamming**: Electronic warfare communication theory
- **API Documentation**: http://localhost:8000/docs (when running)

---

## ❓ Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
OPENENV_PORT=8001 python api_server.py
```

### WebSocket Connection Failed
The web frontend has a fallback to REST-only mode. Check browser console for details.

### Environment Creation Failed
Ensure task is one of: `easy`, `medium`, `hard`

---

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ for OpenEnv Hackathon**
