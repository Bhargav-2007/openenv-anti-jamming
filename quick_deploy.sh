#!/bin/bash

# One-command deployment to HF Space
# Usage: bash quick_deploy.sh

set -e

cd "$(dirname "$0")"

echo "🚀 Deploying to HF Space..."
echo ""

# 1. Commit changes
echo "1️⃣  Committing changes..."
git add .
git commit -m "Deploy: Fix port (7860) for HF Spaces and resolve merge conflicts" || echo "Nothing new to commit"
echo ""

# 2. Setup remote
echo "2️⃣  Setting up HF Space remote..."
git remote remove hf 2>/dev/null || true
git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env
echo "✓ Remote 'hf' configured"
echo ""

# 3. Push
echo "3️⃣  Pushing to HF Space..."
git push hf main -f
echo ""

# 4. Success!
echo "✅ Deployment initiated!"
echo ""
echo "📍 Monitor at:  https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs"
echo "🌐 Access at:   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"
echo ""
echo "⏱️  Wait 2-5 minutes for build to complete..."
echo ""
