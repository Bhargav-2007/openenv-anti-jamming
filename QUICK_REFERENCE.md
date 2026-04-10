# Quick Reference - Space vs Model

## The Key Difference

### 🎮 SPACE = Live Application
- **URL Structure**: `huggingface.co/spaces/username/repo-name`
- **What it is**: A running web application (your Docker container)
- **How you access it**: Browser → http://app-url
- **Deployment method**: Git push (auto-builds Dockerfile)
- **What users see**: Interactive web interface
- **Best for**: Hosting your running FastAPI app

### 📦 MODEL = Repository Storage
- **URL Structure**: `huggingface.co/username/repo-name`
- **What it is**: A git repository for storing files
- **How you access it**: API / Git / Download
- **Deployment method**: Git push (manual files)
- **What's stored**: Models, datasets, weights, configs
- **Best for**: Sharing trained models and artifacts

---

## Same Namespace = Different Paths

```
Your Username: Bhargav-2007
Repository: anti-jamming-env

SPACE:  huggingface.co/spaces/Bhargav-2007/anti-jamming-env
        ↑ Notice "spaces" in URL
        → Your running app lives here

MODEL:  huggingface.co/Bhargav-2007/anti-jamming-env
        ↑ No "spaces" in URL
        → For storing trained models, data, etc.
```

**Both can exist simultaneously with the same name!**

---

## Deployment Flowchart

```
You make changes locally
        ↓
   git commit
        ↓
   ╔═══════════════════╗
   ║  What to deploy?  ║
   ╠═══════════════════╣
   ║ App Code/Config   ║  →  Push to SPACE
   ║ (app.py, server.py)     git push hf main
   ║ (Dockerfile,           (auto-deploys)
   ║  requirements.txt)
   │
   ║ Trained Models ║  →  Push to MODEL
   ║ (weights.pth)       git push hf-model main
   ║ (checkpoints)
   ║ (datasets)
   ║ (results)
   └───────────────────┘
```

---

## Console Commands Reference

### For SPACE Deployment

```bash
# Add Space remote
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

# Update and deploy
git add .
git commit -m "Update app"
git push hf main

# View logs
# Go to: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
```

### For MODEL Deployment

```bash
# Add Model remote
git remote add hf-model https://huggingface.co/Bhargav-2007/anti-jamming-env

# Setup Git LFS (for large files)
git lfs install
git lfs track "*.pth" "*.pkl" "*.h5"
git add .gitattributes

# Push models
git add models/
git commit -m "Add trained models"
git push hf-model main
```

---

## File Organization for Clean Deployment

```
Repository Root
├── .git/
├── README.md              ← Space configuration here
├── Dockerfile             ← For Space
├── requirements.txt       ← For Space
├── app.py                 ← For Space
├── server.py              ← For Space
├── anti_jamming_env/      ← For Space
│
├── models/                ← For MODEL repo
│   ├── trained_agents/
│   │   ├── agent_v1.pth
│   │   └── agent_v2.pth
│   └── .gitattributes
│
├── results/               ← For MODEL repo
│   ├── metrics.json
│   └── evaluation.log
│
└── .gitignore             ← Hide build files
    venv/
    __pycache__/
    *.pyc
    .pytest_cache/
```

---

## Real Examples

### Example 1: Deploy App Update to Space

```bash
# Modify your app code
vim app.py

# Stage and commit
git add app.py
git commit -m "Fix API response format"

# Push to Space
git push hf main

# Wait 2-5 minutes, then visit:
# https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
# Your updates are live!
```

### Example 2: Deploy New Trained Model to Model Repo

```bash
# Copy trained model
cp ./training/final_agent.pth ./models/trained_agents/

# Stage and commit
git add models/
git commit -m "Add trained agent v2.0 - 95% success rate"

# Push to Model repo
git push hf-model main

# Model is now available at:
# https://huggingface.co/Bhargav-2007/anti-jamming-env/blob/main/models/trained_agents/final_agent.pth

# Others can download via:
# from huggingface_hub import hf_hub_download
# model = hf_hub_download(
#     repo_id="Bhargav-2007/anti-jamming-env",
#     filename="models/trained_agents/final_agent.pth"
# )
```

### Example 3: Use Both Together

```bash
# Development workflow:
1. Modify app in main branch
2. Train a model locally
3. Test everything locally
4. git push hf main          (app goes live on Space)
5. git push hf-model main    (model saved for download)
6. Users can:
   - Access live app at Space
   - Download trained models from Model repo
   - Use both together!
```

---

## Checklist for First Time Setup

- [ ] **Create Space** at https://huggingface.co/new-space
  - Name: `anti-jamming-env`
  - SDK: `Docker`

- [ ] **Create Model repo** at https://huggingface.co/new
  - Name: `anti-jamming-env`
  - Type: `Model`

- [ ] **Add remotes** to your git config
  ```bash
  git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
  git remote add hf-model https://huggingface.co/Bhargav-2007/anti-jamming-env
  ```

- [ ] **Test Docker locally**
  ```bash
  docker build -t test .
  docker run -p 8000:8000 test
  ```

- [ ] **Deploy to Space**
  ```bash
  git push hf main
  ```

- [ ] **Monitor deployment**
  - Logs: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
  - Status: Wait for green checkmark

- [ ] **Access your app**
  - URL: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

---

## Troubleshooting

**Q: I pushed to Space but it's still building**
A: HF takes 2-5 minutes to build. Check logs:
   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs

**Q: Build failed**
A: Check logs for errors (usually Docker build issues or missing deps)

**Q: I can't see my Model repo listing files**
A: Both repos exist separately. Visit the Model URL directly:
   https://huggingface.co/Bhargav-2007/anti-jamming-env

**Q: How do I push to only Space?**
A: `git push hf main` (not hf-model)

**Q: How do I push to only Model?**
A: `git push hf-model main` (not hf)

