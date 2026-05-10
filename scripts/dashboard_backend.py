from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import json
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.live_inference import LiveInferenceEngine

app = FastAPI(title="EdgePulse FireStick Telemetry Dashboard")

# Enable CORS for React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Dashboard UI
dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")
app.mount("/static", StaticFiles(directory=dashboard_path), name="static")

@app.get("/")
async def serve_dashboard():
    return FileResponse(os.path.join(dashboard_path, "index.html"))

# Global Inference Engine
engine = LiveInferenceEngine()

@app.on_event("startup")
async def startup_event():
    print("Starting Live Inference Engine...")
    engine.start()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": engine.model is not None}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    print("Dashboard Connected")
    try:
        while True:
            # Get latest stats from engine
            stats = engine.get_latest_stats()
            if stats:
                await websocket.send_json(stats)
            await asyncio.sleep(0.5) # Update at 2Hz
    except WebSocketDisconnect:
        print("Dashboard Disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
