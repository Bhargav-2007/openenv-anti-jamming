#!/bin/bash
# Push HF Spaces configuration update to GitHub

cd /workspaces/openenv-anti-jamming

echo "📤 Pushing README update to GitHub..."
git add README.md
git commit -m "chore: Add Hugging Face Spaces configuration block"
git push origin main

echo "✅ Push complete!"
echo ""
echo "🔄 Hugging Face Space will rebuild automatically..."
echo "📍 Monitor at: https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"
