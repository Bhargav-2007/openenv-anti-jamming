#!/bin/bash
# Quick startup script for Anti-Jamming OpenEnv

set -e

echo "🛰️  Anti-Jamming OpenEnv - Quick Setup"
echo "======================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [ ! -f ".deps_installed" ]; then
    echo ""
    echo "📥 Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch .deps_installed
    echo "✅ Dependencies installed"
fi

# Run server
echo ""
echo "🚀 Starting Anti-Jamming OpenEnv Server..."
echo ""
echo "🌐 Frontend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "WebSocket: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python api_server.py
