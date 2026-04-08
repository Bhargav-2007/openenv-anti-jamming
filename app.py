"""
Enhanced OpenEnv Server with WebSocket Support and REST API
Provides both HTTP REST API and WebSocket for interactive frontend
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Set
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from anti_jamming_env import AntiJammingEnv, AntiJammingAction
from anti_jamming_env.graders import grade_episode

# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════

class CreateSessionRequest(BaseModel):
    task: str = "easy"
    max_steps: int = 50
    seed: Optional[int] = None

class SessionInfo(BaseModel):
    session_id: str
    task: str
    step: int
    max_steps: int
    done: bool
    cumulative_reward: float

class ActionRequest(BaseModel):
    action: Dict[str, Any]

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]
    step: int

class EpisodeResults(BaseModel):
    success: bool
    steps: int
    score: float
    rewards: list
    metrics: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════
# SESSION MANAGER
# ═══════════════════════════════════════════════════════════════════

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_session(self, task: str, max_steps: int, seed: Optional[int] = None) -> str:
        """Create a new environment session"""
        from uuid import uuid4
        
        session_id = str(uuid4())[:8]
        
        try:
            env = AntiJammingEnv(task=task, max_steps=max_steps, random_seed=seed)
            initial_result = await env.reset()
            
            self.sessions[session_id] = {
                "env": env,
                "task": task,
                "max_steps": max_steps,
                "step": 0,
                "done": False,
                "total_reward": 0.0,
                "rewards": [],
                "actions": [],
                "observations": [initial_result.observation],
                "created_at": datetime.now(),
            }
            
            return session_id
        except Exception as e:
            raise ValueError(f"Failed to create session: {str(e)}")
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id]
    
    async def step_session(self, session_id: str, action_dict: Dict[str, Any]) -> StepResponse:
        """Execute one step in the session"""
        session = self.get_session(session_id)
        
        if session["done"]:
            raise ValueError("Episode is already done. Reset the session.")
        
        try:
            # Parse action
            action = AntiJammingAction(**action_dict)
            
            # Execute step
            env = session["env"]
            result = await env.step(action)
            
            # Update session state
            session["step"] += 1
            session["done"] = result.done
            session["total_reward"] += result.reward
            session["rewards"].append(result.reward)
            session["actions"].append(action_dict)
            session["observations"].append(result.observation)
            
            return StepResponse(
                observation=result.observation,
                reward=result.reward,
                done=result.done,
                info=result.info,
                step=session["step"]
            )
        except Exception as e:
            raise ValueError(f"Step failed: {str(e)}")
    
    async def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset the environment"""
        session = self.get_session(session_id)
        env = session["env"]
        result = await env.reset()
        
        # Reset tracking data
        session["step"] = 0
        session["done"] = False
        session["total_reward"] = 0.0
        session["rewards"] = []
        session["actions"] = []
        session["observations"] = [result.observation]
        
        return result.observation
    
    async def close_session(self, session_id: str) -> EpisodeResults:
        """Finalize and grade episode"""
        session = self.get_session(session_id)
        env = session["env"]
        
        # Grade the episode
        score, metrics = grade_episode(
            rewards=session["rewards"],
            actions=session["actions"],
            observations=session["observations"],
            task=session["task"],
            steps=session["step"]
        )
        
        # Close environment
        await env.close()
        
        # Remove session
        del self.sessions[session_id]
        
        return EpisodeResults(
            success=metrics.get("success", False),
            steps=session["step"],
            score=score,
            rewards=session["rewards"],
            metrics=metrics
        )
    
    def get_all_sessions(self) -> Dict[str, SessionInfo]:
        """Get info about all active sessions"""
        result = {}
        for session_id, session in self.sessions.items():
            result[session_id] = SessionInfo(
                session_id=session_id,
                task=session["task"],
                step=session["step"],
                max_steps=session["max_steps"],
                done=session["done"],
                cumulative_reward=session["total_reward"]
            )
        return result


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET HANDLER
# ═══════════════════════════════════════════════════════════════════

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════
# FASTAPI APP SETUP
# ═══════════════════════════════════════════════════════════════════

session_manager = SessionManager()
ws_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Anti-Jamming OpenEnv Server...")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Anti-Jamming OpenEnv",
    description="Real-world wireless communication environment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(session_manager.sessions)
    }

@app.post("/api/sessions", response_model=Dict[str, str])
async def create_session(request: CreateSessionRequest):
    """Create a new training session"""
    session_id = await session_manager.create_session(
        task=request.task,
        max_steps=request.max_steps,
        seed=request.seed
    )
    
    await ws_manager.broadcast({
        "type": "session_created",
        "session_id": session_id,
        "task": request.task
    })
    
    return {"session_id": session_id}

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return session_manager.get_all_sessions()

@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information"""
    session = session_manager.get_session(session_id)
    return SessionInfo(
        session_id=session_id,
        task=session["task"],
        step=session["step"],
        max_steps=session["max_steps"],
        done=session["done"],
        cumulative_reward=session["total_reward"]
    )

@app.post("/api/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a session"""
    observation = await session_manager.reset_session(session_id)
    return {"observation": observation}

@app.post("/api/sessions/{session_id}/step", response_model=StepResponse)
async def step_session(session_id: str, request: ActionRequest):
    """Execute one environment step"""
    result = await session_manager.step_session(session_id, request.action)
    
    # Broadcast update
    await ws_manager.broadcast({
        "type": "step_executed",
        "session_id": session_id,
        "step": result.step,
        "reward": result.reward,
        "done": result.done
    })
    
    return result

@app.post("/api/sessions/{session_id}/close", response_model=EpisodeResults)
async def close_session(session_id: str):
    """Close session and get results"""
    results = await session_manager.close_session(session_id)
    
    await ws_manager.broadcast({
        "type": "session_closed",
        "session_id": session_id,
        "score": results.score,
        "steps": results.steps
    })
    
    return results


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back a pong
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except Exception:
        pass
    finally:
        ws_manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════
# FRONTEND SERVING (Using StaticFiles for efficiency)
# ═══════════════════════════════════════════════════════════════════

# Get the absolute path to frontend directory
frontend_dir = Path(__file__).parent / "frontend"

@app.get("/")
async def root():
    """Serve the frontend root"""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend not found"}

# Mount static files
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    
    print(f"Starting OpenEnv Server on {host}:{port}")
    print(f"🌐 Frontend: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"WebSocket: ws://localhost:{port}/ws")
    print("")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════

class CreateSessionRequest(BaseModel):
    task: str = "easy"
    max_steps: int = 50
    seed: Optional[int] = None

class SessionInfo(BaseModel):
    session_id: str
    task: str
    step: int
    max_steps: int
    done: bool
    cumulative_reward: float

class ActionRequest(BaseModel):
    action: Dict[str, Any]

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]
    step: int

class EpisodeResults(BaseModel):
    success: bool
    steps: int
    score: float
    rewards: list
    metrics: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════
# SESSION MANAGER
# ═══════════════════════════════════════════════════════════════════

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_session(self, task: str, max_steps: int, seed: Optional[int] = None) -> str:
        """Create a new environment session"""
        from uuid import uuid4
        
        session_id = str(uuid4())[:8]
        
        try:
            env = AntiJammingEnv(task=task, max_steps=max_steps, random_seed=seed)
            initial_result = await env.reset()
            
            self.sessions[session_id] = {
                "env": env,
                "task": task,
                "max_steps": max_steps,
                "step": 0,
                "done": False,
                "total_reward": 0.0,
                "rewards": [],
                "actions": [],
                "observations": [initial_result.observation],
                "created_at": datetime.now(),
            }
            
            return session_id
        except Exception as e:
            raise ValueError(f"Failed to create session: {str(e)}")
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id]
    
    async def step_session(self, session_id: str, action_dict: Dict[str, Any]) -> StepResponse:
        """Execute one step in the session"""
        session = self.get_session(session_id)
        
        if session["done"]:
            raise ValueError("Episode is already done. Reset the session.")
        
        try:
            # Parse action
            action = AntiJammingAction(**action_dict)
            
            # Execute step
            env = session["env"]
            result = await env.step(action)
            
            # Update session state
            session["step"] += 1
            session["done"] = result.done
            session["total_reward"] += result.reward
            session["rewards"].append(result.reward)
            session["actions"].append(action_dict)
            session["observations"].append(result.observation)
            
            return StepResponse(
                observation=result.observation,
                reward=result.reward,
                done=result.done,
                info=result.info,
                step=session["step"]
            )
        except Exception as e:
            raise ValueError(f"Step failed: {str(e)}")
    
    async def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset the environment"""
        session = self.get_session(session_id)
        env = session["env"]
        result = await env.reset()
        
        # Reset tracking data
        session["step"] = 0
        session["done"] = False
        session["total_reward"] = 0.0
        session["rewards"] = []
        session["actions"] = []
        session["observations"] = [result.observation]
        
        return result.observation
    
    async def close_session(self, session_id: str) -> EpisodeResults:
        """Finalize and grade episode"""
        session = self.get_session(session_id)
        env = session["env"]
        
        # Grade the episode
        score, metrics = grade_episode(
            rewards=session["rewards"],
            actions=session["actions"],
            observations=session["observations"],
            task=session["task"],
            steps=session["step"]
        )
        
        # Close environment
        await env.close()
        
        # Remove session
        del self.sessions[session_id]
        
        return EpisodeResults(
            success=metrics.get("success", False),
            steps=session["step"],
            score=score,
            rewards=session["rewards"],
            metrics=metrics
        )
    
    def get_all_sessions(self) -> Dict[str, SessionInfo]:
        """Get info about all active sessions"""
        result = {}
        for session_id, session in self.sessions.items():
            result[session_id] = SessionInfo(
                session_id=session_id,
                task=session["task"],
                step=session["step"],
                max_steps=session["max_steps"],
                done=session["done"],
                cumulative_reward=session["total_reward"]
            )
        return result


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET HANDLER
# ═══════════════════════════════════════════════════════════════════

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════
# FASTAPI APP SETUP
# ═══════════════════════════════════════════════════════════════════

session_manager = SessionManager()
ws_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Anti-Jamming OpenEnv Server...")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Anti-Jamming OpenEnv",
    description="Real-world wireless communication environment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(session_manager.sessions)
    }

@app.post("/api/sessions", response_model=Dict[str, str])
async def create_session(request: CreateSessionRequest):
    """Create a new training session"""
    session_id = await session_manager.create_session(
        task=request.task,
        max_steps=request.max_steps,
        seed=request.seed
    )
    
    await ws_manager.broadcast({
        "type": "session_created",
        "session_id": session_id,
        "task": request.task
    })
    
    return {"session_id": session_id}

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return session_manager.get_all_sessions()

@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information"""
    session = session_manager.get_session(session_id)
    return SessionInfo(
        session_id=session_id,
        task=session["task"],
        step=session["step"],
        max_steps=session["max_steps"],
        done=session["done"],
        cumulative_reward=session["total_reward"]
    )

@app.post("/api/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a session"""
    observation = await session_manager.reset_session(session_id)
    return {"observation": observation}

@app.post("/api/sessions/{session_id}/step", response_model=StepResponse)
async def step_session(session_id: str, request: ActionRequest):
    """Execute one environment step"""
    result = await session_manager.step_session(session_id, request.action)
    
    # Broadcast update
    await ws_manager.broadcast({
        "type": "step_executed",
        "session_id": session_id,
        "step": result.step,
        "reward": result.reward,
        "done": result.done
    })
    
    return result

@app.post("/api/sessions/{session_id}/close", response_model=EpisodeResults)
async def close_session(session_id: str):
    """Close session and get results"""
    results = await session_manager.close_session(session_id)
    
    await ws_manager.broadcast({
        "type": "session_closed",
        "session_id": session_id,
        "score": results.score,
        "steps": results.steps
    })
    
    return results


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back a pong
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except Exception:
        pass
    finally:
        ws_manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════
# FRONTEND SERVING
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse("frontend/index.html")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    host = os.getenv("OPENENV_HOST", "0.0.0.0")
    port = int(os.getenv("OPENENV_PORT", "8000"))
    
    print(f"Starting OpenEnv Server on {host}:{port}")
    print(f"Frontend: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
