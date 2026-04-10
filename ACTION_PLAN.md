# 🎯 ACTION PLAN - Get Your App Running

## 5-Minute Quick Start

### Step 1: Verify Your Setup (1 min)

```bash
# From your project root
ls -la
# You should see:
# ✓ Dockerfile
# ✓ requirements.txt
# ✓ app.py or server.py
# ✓ anti_jamming_env/
# ✓ README.md
```

### Step 2: Test Locally (2 min)

**Option A: Direct Python**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# or
python server.py

# Visit: http://localhost:8000
```

**Option B: Docker**
```bash
# Build
docker build -t anti-jamming .

# Run
docker run -p 8000:8000 anti-jamming

# Visit: http://localhost:8000
```

### Step 3: Deploy to Hugging Face (2 min)

```bash
# 1. Ensure you're in git repo
git status

# 2. Commit your code
git add .
git commit -m "Initial commit - ready for deployment"

# 3. Add Hugging Face remote
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

# 4. Push to Space
git push hf main

# 5. Wait 2-5 minutes for build
# Monitor at: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs

# 6. Access your live app
# https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
```

---

## Step-by-Step: First Time Setup

### Phase 1: Create Hugging Face Resources (5 min)

#### Space (for your running app)

1. Go to: https://huggingface.co/new-space
2. Fill in:
   - **Space name**: `anti-jamming-env`
   - **License**: Choose (e.g., MIT, Apache 2.0)
   - **Space SDK**: **Docker** (important!)
   - **Visibility**: Public (or Private)
3. Click "Create Space"
4. You get a URL: `https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env`

#### Model Repository (optional, for storing trained models)

1. Go to: https://huggingface.co/new
2. Fill in:
   - **Model name**: `anti-jamming-env`
   - **License**: Choose same as Space
   - **Visibility**: Public
3. Click "Create model"
4. You get a URL: `https://huggingface.co/Bhargav-2007/anti-jamming-env`

### Phase 2: Setup Git Remotes (2 min)

```bash
cd /workspaces/openenv-anti-jamming

# Add Space remote
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env

# Add Model remote (optional)
git remote add hf-model https://huggingface.co/Bhargav-2007/anti-jamming-env

# Verify
git remote -v
# Should show:
# hf  https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env (fetch)
# hf  https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env (push)
# hf-model  https://huggingface.co/Bhargav-2007/anti-jamming-env (fetch)
# hf-model  https://huggingface.co/Bhargav-2007/anti-jamming-env (push)
```

### Phase 3: Test Docker Locally (5 min)

```bash
# Build Docker image
docker build -t anti-jamming-local .

# Run container
docker run -p 8000:8000 anti-jamming-local

# In another terminal, test
curl http://localhost:8000/api/health

# Or visit browser: http://localhost:8000
```

If you see your app → Ready to deploy! Press Ctrl+C to stop.

### Phase 4: Deploy to HF Space (1 min)

```bash
# Make sure everything is committed
git status

# If there are changes:
git add .
git commit -m "Deploy to Hugging Face Space"

# Push to Space (this triggers auto-deployment)
git push hf main

# Output should show: (everything up-to-date) or (new commits pushed)
```

### Phase 5: Monitor Deployment (2-5 min wait)

Visit your Space logs:
https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs

You'll see:
```
Building...
2024-XX-XX Building app...
2024-XX-XX Building Docker image...
2024-XX-XX Running container...
2024-XX-XX App running on port 8000
Status: ✓ Running
```

### Phase 6: Access Your Live App! (1 min)

Once status shows "Running":
- Visit: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
- You should see your FastAPI interface
- Try creating a session
- Test the environment

### Phase 7 (Optional): Deploy Models (3 min)

If you trained models locally:

```bash
# Create models directory
mkdir -p models/trained_agents

# Copy your trained models
cp ./training_results/*.pth models/trained_agents/

# Setup Git LFS for large files
git lfs install
git lfs track "*.pth"
git add .gitattributes

# Commit
git add models/
git commit -m "Add trained agent models"

# Push to Model repo
git push hf-model main

# Now others can download:
# from huggingface_hub import hf_hub_download
# model = hf_hub_download("Bhargav-2007/anti-jamming-env", "models/trained_agents/agent.pth")
```

---

## Common Issues & Fixes

### 1. Docker Build Fails

**Issue**: "ERROR: Could not find..."

**Fix**:
```bash
# Check requirements.txt is valid
pip install -r requirements.txt  # Test locally first

# Check Dockerfile PATH is correct
# Make sure anti_jamming_env/ directory exists
ls anti_jamming_env/
```

### 2. Space Build is Stuck

**Issue**: Building for more than 10 minutes

**Fix**:
- Check logs at: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
- Click "Build logs" tab
- Look for error message
- Common: Missing dependency in requirements.txt

### 3. Running but App Not Working

**Issue**: Space is running but page is blank/error

**Fix**:
```bash
# Check app.py port
grep "port" app.py
# Should use port 8000

# Check if FastAPI is the server
grep -i "fastapi\|uvicorn" app.py

# Test locally first
docker run -p 8000:8000 anti-jamming
curl http://localhost:8000/api/health
```

### 4. Can't Find My Model

**Issue**: Model repo not showing files

**Fix**:
- Model repo is at: https://huggingface.co/Bhargav-2007/anti-jamming-env (no /spaces/)
- Space and Model are different repositories
- Files you push to Model repo don't appear in Space

---

## Workflow After Deployment

### Making Updates

```bash
# Edit your code
vim app.py

# Test locally
docker build -t test .
docker run -p 8000:8000 test
# Test in browser...

# If OK, push to Space
git add app.py
git commit -m "Fix: Updated endpoint response"
git push hf main

# Wait 2-5 min for rebuild
# Check: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs
```

### Reverting Changes

```bash
# If something breaks, revert last commit
git revert HEAD
git push hf main

# Or rollback to specific version
git log                           # See history
git checkout <commit-hash> .      # Revert to that version
git commit -m "Rollback to working version"
git push hf main
```

---

## Files to Monitor/Update

After deployment, these files matter:

| File | Purpose | When to Update |
|------|---------|----------------|
| `README.md` | Space config + docs | When adding features |
| `Dockerfile` | Container config | When changing dependencies |
| `requirements.txt` | Python dependencies | When adding packages |
| `app.py` / `server.py` | Main app logic | Frequently (features, fixes) |
| `anti_jamming_env/` | Core package | For environment changes |
| `.gitignore` | Avoid committing build files | Setup once |

---

## Success Indicators

✓ **You've succeeded when**:

1. Docker builds locally without errors
2. App runs on http://localhost:8000 locally
3. Space deployment completes (green checkmark)
4. You can access https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
5. You can interact with your app in the browser
6. Updates push cleanly with `git push hf main`

✓ **Optional**: Models upload to Model repo

---

## Next Steps

1. **Choose SDK**: Your README.md is already set for Docker ✓
2. **Create Space**: https://huggingface.co/new-space
3. **Setup Git**: Run `git remote add hf ...`
4. **Test Locally**: Run `docker build && docker run`
5. **Deploy**: Run `git push hf main`
6. **Monitor**: Watch logs for 5 minutes
7. **Access**: Visit your Space URL

You're ready to go! 🚀

