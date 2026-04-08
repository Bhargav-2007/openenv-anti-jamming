"""
OpenEnv Server Wrapper - Runs FastAPI Backend
This entry point allows both PyProject.toml and Docker CMD to work correctly.
"""

def main():
    """Start the FastAPI server."""
    from api_server import app
    import uvicorn
    import os
    
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    
    print("🚀 Anti-Jamming OpenEnv Server Starting")
    print(f"📊 Frontend & API: http://{host}:{port}")
    print(f"📖 API Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
