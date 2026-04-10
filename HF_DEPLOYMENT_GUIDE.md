# 🚀 Hugging Face Deployment Guide - Space vs Model

## Understanding Your Resources

### 1. **Hugging Face SPACE** 🎮 (Running Application)
- **URL:** `https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env`
- **Purpose:** Your **live interactive web application**
- **What runs here:** Docker container with your FastAPI server
- **Users access via:** Browser interface
- **Configured in:** README.md (has HF Space YAML frontmatter)

```yaml
# From README.md (HF Space config)
---
title: Anti-Jamming OpenEnv
emoji: shield
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000
---
```

### 2. **Hugging Face MODEL** 📦 (Repository/Storage)
- **URL:** `https://huggingface.co/Bhargav-2007/anti-jamming-env`
- **Purpose:** Store trained models, checkpoints, datasets, artifacts
- **What goes here:** Weights, trained agents, evaluation results
- **Types:** Models, Datasets, Spaces (yes, they show up here too)
- **Access via:** Git/API

---

## How They Work Together

```
Your Local Development
         ↓
    Git Commit/Push
         ↓
    ━━━━╋━━━━
    ↙         ↘
Space Model   (Both repos)
(Live App)   (Artifacts)
    ↓           ↓
Users run     Agents load
the app       trained weights
```

---

## 📋 Step-by-Step Deployment

### Option 1: Deploy to Hugging Face Space (RECOMMENDED)

#### Prerequisites
1. **Hugging Face Account**: https://huggingface.co/join
2. **Create a Space**: https://huggingface.co/new-space
   - Space name: `anti-jamming-env`
   - License: Choose one
   - Space SDK: **Docker**
   - Visibility: Public/Private

#### Method A: Via Git (Recommended)

```bash
# 1. Add Hugging Face remote
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

# 2. Push your code
git push hf main

# Note: Hugging Face automatically:
# - Builds your Dockerfile
# - Runs the container
# - Exposes port 8000
# - Creates a public URL in ~2-5 minutes
```

#### Method B: Via Hugging Face CLI

```bash
# 1. Install CLI
pip install huggingface-hub

# 2. Login
huggingface-cli login

# 3. Create Space programmatically
from huggingface_hub import create_repo
repo = create_repo(
    repo_id="anti-jamming-env",
    repo_type="space",
    space_sdk="docker",
    private=False
)

# 4. Push files
from huggingface_hub import upload_folder
upload_folder(
    repo_id="anti-jamming-env",
    repo_type="space",
    folder_path=".",
    path_in_repo=""
)
```

---

### Option 2: Deploy Model Repository (for artifacts)

This is where you store trained models and results.

```bash
# 1. Add model remote
git remote add hf-model https://huggingface.co/Bhargav-2007/anti-jamming-env

# 2. Create specific branch for models
git checkout -b models

# 3. Create model directory
mkdir -p models/trained_agents
# (Add your .pth, .pkl, .h5 files here)

# 4. Add Large File Support (LFS) for model files
git lfs install
git lfs track "*.pth"
git lfs track "*.pkl"

# 5. Commit and push
git add .
git commit -m "Add trained agent models"
git push hf-model models
```

---

## 🎮 Configuration Reference

### Your Space Configuration (Already Set)

Your `README.md` acts as the Space config:

```yaml
---
title: Anti-Jamming OpenEnv
emoji: shield
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000          # ← Port FastAPI runs on
---
```

### Optional: Create `README.md` for Model Repo

```markdown
---
language: en
license: mit
---

# Anti-Jamming Environment - Trained Models

Repository for trained agents and evaluation results.

## Files

- `models/trained_agents/` - Trained model checkpoints
- `results/` - Evaluation metrics
- `datasets/` - Training datasets
```

---

## 🔄 Update Workflow

### Push Updates to Space

```bash
# Make changes to your code
# Edit files...

# Commit
git add .
git commit -m "Update feature X"

# Push to Space (automatically deploys)
git push hf main

# Monitor at: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
```

### Push Models to Model Repo

```bash
# Switch to models branch
git checkout models

# Add trained weights
cp trained_agent.pth models/trained_agents/

# Commit
git add .
git commit -m "Add trained agent v1.0"

# Push
git push hf-model models
```

---

## 🧪 Testing Before Deployment

### Local Test
```bash
# Test Docker build
docker build -t anti-jamming-test .
docker run -p 8000:8000 anti-jamming-test

# Visit: http://localhost:8000
```

### Test via API
```bash
# Health check
curl http://localhost:8000/api/health

# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"task":"easy","max_steps":50}'
```

---

## 📊 Folder Structure for Deployment

```
your-repo/
├── README.md                       # Space config + docs
├── Dockerfile                      # Container config ✓
├── requirements.txt                # Dependencies ✓
├── app.py / server.py / api_server.py
├── anti_jamming_env/               # Your package
│   ├── env.py
│   ├── models.py
│   ├── physics.py
│   ├── jammers.py
│   ├── tasks.py
│   └── graders.py
├── frontend/
│   └── index.html
├── .gitignore
│
├── models/                         # (For Model repo)
│   ├── trained_agents/
│   │   ├── agent_v1.pth
│   │   └── agent_v2.pth
│   └── README.md
│
└── results/                        # (Track experiments)
    ├── runs/
    └── metrics.json
```

---

## 🎯 Environment Variables on Space

Hugging Face Spaces support secrets. Set these in Space settings:

```bash
# Via Space UI: Settings → Secrets and variables

OPENENV_HOST=0.0.0.0
OPENENV_PORT=8000
ANTI_JAMMING_TASK=easy
HF_TOKEN=<your_token>              # For model downloads
```

Your Dockerfile already includes these:
```dockerfile
ENV OPENENV_HOST=0.0.0.0
ENV OPENENV_PORT=8000
ENV ANTI_JAMMING_TASK=easy
```

---

## ❓ FAQ

### Q: Can I have different code for Space vs Model?
**A:** Yes! Use git branches:
- `main` → Space (app code)
- `models` → Model repo (artifacts + evaluation code)

### Q: How do I see logs?
**A:** Hugging Face Space logs: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs

### Q: Can models download from Model repo?
**A:** Yes! In your code:
```python
from huggingface_hub import hf_hub_download
model = hf_hub_download(repo_id="Bhargav-2007/anti-jamming-env", filename="models/agent.pth")
```

### Q: Private vs Public?
**A:** 
- **Public:** Anyone can see and use
- **Private:** Only you can access

### Q: How to rollback?
**A:** Git version control!
```bash
git log                    # See history
git revert <commit_id>     # Undo specific commit
git push hf main           # Push rollback
```

---

## ✅ Quick Checklist

- [ ] Create Hugging Face Space
- [ ] Create Model repository (optional, for artifacts)
- [ ] Test Docker build locally
- [ ] Test FastAPI locally
- [ ] Add HF remotes to git
- [ ] Push to Space
- [ ] Monitor logs at HF
- [ ] Share public URL with users
- [ ] (Optional) Store trained models in Model repo

---

## 🔗 Helpful Links

- **Create Space:** https://huggingface.co/new-space
- **Your Space:** https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
- **Your Model:** https://huggingface.co/Bhargav-2007/anti-jamming-env
- **HF Documentation:** https://huggingface.co/docs/hub/spaces
- **HF CLI:** https://huggingface.co/docs/hub/security-tokens

