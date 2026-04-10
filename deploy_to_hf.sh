#!/bin/bash

# ============================================================================
# DEPLOY TO NEW HF SPACE - Quick Setup
# ============================================================================

echo "🚀 Deploying Anti-Jamming Environment to Hugging Face Space"
echo "=============================================================="
echo ""

# Step 1: Verify git status
echo "Step 1: Checking git status..."
echo ""
git status
echo ""

# Step 2: Check for uncommitted changes
if [ -z "$(git status --short)" ]; then
    echo "✓ All files committed"
else
    echo "⚠️  Uncommitted changes detected. Committing now..."
    git add .
    git commit -m "Fix: Port migration for HF Spaces (7860) and resolve merge conflicts"
fi

echo ""
echo "Step 2: Setting up HF Space remote..."
echo ""

# Step 3: Remove old remote if exists and add new one
if git remote | grep -q "^hf$"; then
    echo "Removing old 'hf' remote..."
    git remote remove hf
fi

# Option 1: HTTPS (recommended, no SSH key setup needed)
SPACE_REPO="https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"

# Add remote
git remote add hf "$SPACE_REPO"
echo "✓ Added remote 'hf': $SPACE_REPO"
echo ""

# Step 4: Push to Space
echo "Step 3: Pushing code to Space..."
echo ""
echo "Command: git push hf main -f"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push hf main -f
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS! Your Space is deploying!"
        echo ""
        echo "📍 Monitor your Space at:"
        echo "   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs"
        echo ""
        echo "⏱️  It usually takes 2-5 minutes to build and start"
        echo ""
        echo "🌐 Once ready, visit:"
        echo "   https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"
    else
        echo ""
        echo "❌ Push failed. Troubleshooting:"
        echo ""
        echo "1. Make sure you're logged in to HF:"
        echo "   huggingface-cli login"
        echo ""
        echo "2. Or, if SSH key error, use HTTPS:"
        echo "   git remote remove hf"
        echo "   git remote add hf https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"
        echo "   git push hf main"
    fi
else
    echo "Cancelled."
fi

echo ""
