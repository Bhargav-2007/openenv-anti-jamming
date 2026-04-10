#!/bin/bash
# Quick HF Setup Helper - Run this to get started

echo "════════════════════════════════════════════════════════════"
echo "  🚀 Hugging Face Deployment Setup Assistant"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "IMPORTANT: Have you created your Hugging Face resources?"
echo ""
echo "Space:  https://huggingface.co/new-space"
echo "          - Name: anti-jamming-env"
echo "          - SDK: Docker"
echo ""
echo "Model:  https://huggingface.co/new (OPTIONAL)"
echo "          - Name: anti-jamming-env"
echo "          - Type: Model"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Ask if resources are ready
read -p "Have you created the Space? (y/n): " -n 1 -r space_ready
echo
read -p "Have you created the Model repo? (y/n): " -n 1 -r model_ready
echo
echo ""

# Configure based on answers
if [[ $space_ready =~ ^[Yy]$ ]]; then
    echo "Setting up Space deployment..."
    
    if git remote | grep -q "^hf$"; then
        git remote remove hf
        echo "  ✓ Updated hf remote"
    else
        git remote add hf "https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env"
        echo "  ✓ Added hf remote"
    fi
fi

if [[ $model_ready =~ ^[Yy]$ ]]; then
    echo "Setting up Model repo..."
    
    if git remote | grep -q "^hf-model$"; then
        git remote remove hf-model
        echo "  ✓ Updated hf-model remote"
    else
        git remote add hf-model "https://huggingface.co/Bhargav-2007/anti-jamming-env"
        echo "  ✓ Added hf-model remote"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "════════════════════════════════════════════════════════════"
echo ""

if [[ $space_ready =~ ^[Yy]$ ]]; then
    echo "✓ To Deploy Your App to Space:"
    echo ""
    echo "  $ git add ."
    echo "  $ git commit -m 'Deploy to Hugging Face Space'"
    echo "  $ git push hf main"
    echo ""
    echo "  Then watch the logs:"
    echo "  https://huggingface.co/spaces/Bhargav-2007/anti-jamming-env/logs"
    echo ""
fi

if [[ $model_ready =~ ^[Yy]$ ]]; then
    echo "✓ To Upload Trained Models to Model Repo:"
    echo ""
    echo "  $ mkdir -p models/trained_agents"
    echo "  $ cp your_trained_model.pth models/trained_agents/"
    echo "  $ git add models/"
    echo "  $ git commit -m 'Add trained models'"
    echo "  $ git push hf-model main"
    echo ""
fi

if [[ ! ($space_ready =~ ^[Yy]$) && ! ($model_ready =~ ^[Yy]$) ]]; then
    echo "❌ Please create your resources first:"
    echo ""
    echo "  1. Create Space:  https://huggingface.co/new-space"
    echo "  2. Create Model:  https://huggingface.co/new"
    echo ""
    echo "Then run this script again."
    echo ""
fi

echo "════════════════════════════════════════════════════════════"
echo "  Helpful Documentation"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Read these files in your project:"
echo "  • ACTION_PLAN.md          - Step-by-step first-time guide"
echo "  • QUICK_REFERENCE.md      - Space vs Model differences"
echo "  • HF_DEPLOYMENT_GUIDE.md  - Complete reference"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

git remote -v
echo ""
