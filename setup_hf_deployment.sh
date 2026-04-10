#!/bin/bash

# ============================================================================
# Hugging Face Deployment Helper Script
# ============================================================================

set -e

echo "🚀 Hugging Face Deployment Setup"
echo "=================================="
echo ""

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please initialize git first:"
    echo "   git init"
    exit 1
fi

echo "✓ Git repository detected"
echo ""

# Menu
echo "Choose deployment option:"
echo "1) Setup Hugging Face Space remote"
echo "2) Setup Model repository remote"
echo "3) Setup both"
echo "4) Show current remotes"
echo ""
read -p "Enter choice (1-4): " choice

HF_USERNAME="Bhargav-2007"
REPO_NAME="anti-jamming-env"

case $choice in
    1)
        echo ""
        echo "Setting up Hugging Face Space..."
        echo ""
        echo "Step 1: Make sure you have created the Space at:"
        echo "        https://huggingface.co/new-space"
        echo "        - Name: $REPO_NAME"
        echo "        - SDK: Docker"
        echo ""
        read -p "Have you created the Space? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Add remote
            if git remote | grep -q "^hf$"; then
                echo "Removing existing 'hf' remote..."
                git remote remove hf
            fi
            
            git remote add hf "https://huggingface.co/spaces/$HF_USERNAME/$REPO_NAME"
            echo "✓ Remote 'hf' added"
            echo ""
            echo "Next steps:"
            echo "1. git add ."
            echo "2. git commit -m 'Initial deployment'"
            echo "3. git push hf main"
            echo ""
            echo "Your Space will deploy automatically!"
        fi
        ;;
    2)
        echo ""
        echo "Setting up Model repository..."
        echo ""
        echo "Step 1: Make sure you have created the Model repo at:"
        echo "        https://huggingface.co/new"
        echo "        - Name: $REPO_NAME"
        echo "        - Type: Model"
        echo ""
        read -p "Have you created the Model repo? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if git remote | grep -q "^hf-model$"; then
                echo "Removing existing 'hf-model' remote..."
                git remote remove hf-model
            fi
            
            git remote add hf-model "https://huggingface.co/$HF_USERNAME/$REPO_NAME"
            echo "✓ Remote 'hf-model' added"
            echo ""
            echo "For storing large model files, setup Git LFS:"
            echo "1. git lfs install"
            echo "2. git lfs track '*.pth' '*.pkl' '*.bin'"
            echo "3. git add .gitattributes"
            echo "4. git commit -m 'Setup LFS'"
            echo "5. mkdir -p models/trained_agents"
            echo "6. (Add your model files)"
            echo "7. git push hf-model main"
        fi
        ;;
    3)
        echo ""
        echo "Setting up both remotes..."
        echo ""
        read -p "Have you created both the Space and Model repo? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Space
            if git remote | grep -q "^hf$"; then
                git remote remove hf
            fi
            git remote add hf "https://huggingface.co/spaces/$HF_USERNAME/$REPO_NAME"
            echo "✓ Space remote 'hf' added"
            
            # Model
            if git remote | grep -q "^hf-model$"; then
                git remote remove hf-model
            fi
            git remote add hf-model "https://huggingface.co/$HF_USERNAME/$REPO_NAME"
            echo "✓ Model remote 'hf-model' added"
            
            echo ""
            echo "Both remotes configured!"
            echo ""
            echo "Usage:"
            echo "  - Push to Space:  git push hf main"
            echo "  - Push to Model:  git push hf-model main (or models branch)"
        fi
        ;;
    4)
        echo ""
        echo "Current remotes:"
        echo ""
        git remote -v
        echo ""
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✓ Setup complete!"
