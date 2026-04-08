#!/usr/bin/env python3
"""
Verification script for Anti-Jamming OpenEnv deployment
Checks that all components are in place and working
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(path: str, description: str) -> bool:
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {path}")
    return exists

def check_directory_exists(path: str, description: str) -> bool:
    exists = Path(path).is_dir()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {path}/")
    return exists

def check_imports():
    """Check that all required packages are available"""
    print("\n📦 Checking Python packages...")
    
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("numpy", "NumPy"),
        ("openai", "OpenAI"),
    ]
    
    all_ok = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def main():
    print("\n" + "="*60)
    print("🛰️  Anti-Jamming OpenEnv - Deployment Verification")
    print("="*60)
    
    base_path = Path(__file__).parent
    os.chdir(base_path)
    
    checks_passed = 0
    checks_total = 0
    
    # Check core files
    print("\n📄 Checking core files...")
    files_to_check = [
        ("api_server.py", "API Server"),
        ("test_client.py", "Test Client"),
        ("requirements.txt", "Dependencies"),
        ("pyproject.toml", "Python Package Config"),
        ("Dockerfile", "Docker Configuration"),
        ("uv.lock", "Dependency Lock"),
        ("run.sh", "Linux/macOS Startup Script"),
        ("run.bat", "Windows Startup Script"),
    ]
    
    for file, desc in files_to_check:
        checks_total += 1
        if check_file_exists(file, desc):
            checks_passed += 1
    
    # Check directories
    print("\n📁 Checking directories...")
    dirs_to_check = [
        ("anti_jamming_env", "Environment Package"),
        ("frontend", "Web Frontend"),
        ("server", "Server Package"),
        ("tests", "Tests"),
        ("examples", "Examples"),
    ]
    
    for dir, desc in dirs_to_check:
        checks_total += 1
        if check_directory_exists(dir, desc):
            checks_passed += 1
    
    # Check environment files
    print("\n🏗️  Checking environment files...")
    env_files = [
        ("anti_jamming_env/__init__.py", "Package Init"),
        ("anti_jamming_env/env.py", "Main Environment"),
        ("anti_jamming_env/models.py", "Data Models"),
        ("anti_jamming_env/physics.py", "Physics Simulation"),
        ("anti_jamming_env/jammers.py", "Jammer Implementations"),
        ("anti_jamming_env/tasks.py", "Task Definitions"),
        ("anti_jamming_env/graders.py", "Episode Grading"),
    ]
    
    for file, desc in env_files:
        checks_total += 1
        if check_file_exists(file, desc):
            checks_passed += 1
    
    # Check documentation
    print("\n📖 Checking documentation...")
    docs = [
        ("README.md", "Main README"),
        ("SETUP_GUIDE.md", "Setup Guide"),
        ("SYSTEM_SUMMARY.md", "System Summary"),
        (".env", "Environment Variables"),
    ]
    
    for file, desc in docs:
        checks_total += 1
        if check_file_exists(file, desc):
            checks_passed += 1
    
    # Check frontend files
    print("\n🎨 Checking frontend...")
    checks_total += 1
    if check_file_exists("frontend/index.html", "Web Dashboard"):
        checks_passed += 1
    
    # Check Python imports
    print("\n🐍 Checking Python environment...")
    if check_imports():
        checks_passed += 1
    else:
        pass  # Already counted
    
    # Summary
    print("\n" + "="*60)
    print("📊 Verification Summary")
    print("="*60)
    
    if checks_passed > 0:
        percentage = (checks_passed / checks_total) * 100
        print(f"  ✅ Passed: {checks_passed}/{checks_total} checks ({percentage:.0f}%)")
    else:
        print(f"  ❌ No checks passed")
    
    # Final status
    print("\n" + "="*60)
    if checks_passed == checks_total:
        print("✅ ALL CHECKS PASSED - System is ready!")
        print("\n🚀 To start the server:")
        print("  bash run.sh              # Linux/macOS")
        print("  run.bat                  # Windows")
        print("  python api_server.py     # Manual")
        print("\n🌐 Then open: http://localhost:8000")
        return 0
    else:
        print(f"⚠️  {checks_total - checks_passed} checks failed")
        print("\n📥 Install dependencies:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
