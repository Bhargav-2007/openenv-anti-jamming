# 🚀 Deploy Your App to New HF Space (3 Easy Steps)

## What I Fixed For You ✅

1. **Resolved merge conflicts** in `requirements.txt`
2. **Updated port** from 8000 → **7860** (HF Spaces requirement)
3. Updated `Dockerfile` to use port 7860

Your app is now ready for HF Spaces!

---

## 3-Step Deployment

### Step 1: Commit Changes

```bash
git add .
git commit -m "Format for HF Spaces deployment"
```

### Step 2: Add HF Space Remote

```bash
# Option A: HTTPS (recommended - no SSH keys needed)
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

# Option B: SSH (if you have SSH keys set up at https://huggingface.co/settings/keys)
git remote add hf git@hf.co:spaces/Bhargav-2007/anti-jamming-env
```

### Step 3: Push to Space

```bash
git push hf main -f
```

**That's it!** 🎉

---

## Monitor Deployment

1. **Watch the build logs** (updated every 5 seconds):
   ```
   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
   ```

2. **Wait for "Running" status** (usually 2-5 minutes)

3. **Access your app**:
   ```
   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
   ```

---

## Troubleshooting

### ❌ "fatal: not a git repository"
**Solution**: You're not in the right directory
```bash
cd /workspaces/openenv-anti-jamming
```

### ❌ "permission denied (publickey)" (SSH error)
**Solution**: Use HTTPS instead
```bash
git remote remove hf
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
git push hf main
```

### ❌ "fatal: The remote already exists"
**Solution**: Remove the old remote
```bash
git remote remove hf
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
```

### ❌ Build still failing after push?
**Check**:
- App must listen on port **7860** ✓ (I fixed this)
- `Dockerfile` exists ✓
- `requirements.txt` exists ✓
- No merge conflict markers ✓ (I fixed this)

Visit logs page for exact error:
```
https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
```

---

## Quick One-Liner Deployment

```bash
cd /workspaces/openenv-anti-jamming && git add . && git commit -m "Deploy to HF" && git remote remove hf 2>/dev/null; git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env && git push hf main
```

---

## What I Changed

### requirements.txt
- Removed git merge conflict markers (<<<<<<, ======, >>>>>>>)
- Kept latest versions:
  - openenv-core[cli]>=0.4.0
  - numpy>=1.26.0
  - scipy>=1.13.0
  - openai>=1.58.1

### Dockerfile
- Port: 8000 → **7860** (HF Spaces requirement)
- ENV OPENENV_PORT: 8000 → 7860
- EXPOSE: 8000 → 7860

---

## After Deployment

### If app works ✅
- Keep using it at Space URL
- Update code anytime with: `git push hf main`

### If app has issues ❌
- Check logs: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
- Common issues:
  - Docker build errors → check requirements.txt syntax
  - App crashes → check app.py listens on port 7860
  - Timeout → app taking too long to start (check HEALTHCHECK)

---

## Next: Store Models (Optional)

You also have a Model repo for storing trained agents:

```bash
# Add model remote
git remote add hf-model https://huggingface.co/Bhargav-2007/anti-jamming-env

# Store models
mkdir -p models/trained_agents
cp trained_agent.pth models/trained_agents/

# Push
git add models/
git commit -m "Add trained models"
git push hf-model main
```

---

## Your Remotes Now

After setup, you'll have:

```
origin  → GitHub (your backup)
hf      → HF Space (running app)
hf-model → HF Model repo (trained models storage)
```

---

**Ready?** Run: `git push hf main` 🚀

