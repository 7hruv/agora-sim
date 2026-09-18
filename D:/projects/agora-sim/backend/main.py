from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import backend.db as db
from backend.engine import run_round

app = FastAPI(title="Agora Social Simulation")

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Initialize DB on startup
db.init_db()

@app.get("/")
async def root():
    """Serve the frontend dashboard."""
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))

@app.get("/state")
async def get_state():
    """Return current game state."""
    agents = db.get_agents()
    events = db.get_events(limit=30)
    current_round = db.get_current_round()
    
    return {
        "round": current_round,
        "agents": agents,
        "recent_events": events
    }

@app.post("/next-round")
async def next_round():
    """Run one round and return the 2 new events."""
    try:
        events = run_round()
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_world():
    """Reset the database and reinitialize agents."""
    try:
        db.reset_db()
        return {"message": "World reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_all_events():
    """Return all events for the log panel."""
    return {"events": db.get_all_events()}

if __name__ == "__main__":
    import uvicorn
    print("Agora running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
