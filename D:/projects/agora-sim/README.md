# 🏛️ Agora - Social Simulation

A local social simulation with 2 AI agents who chat, trade, and have feelings. Everything runs locally on your laptop using Ollama. No cloud, no external APIs.

## What is Agora?

Agora is a small experimental world where two AI agents (Mira and Leo) interact in turn-based rounds. They can:
- **Trade** items (fish and bread) using coins
- **Chat** with each other using LLM-generated dialogue
- **Refuse** or **Accept** offers
- Experience **mood changes** based on their interactions

All state persists in SQLite between sessions.

## Requirements

1. **Python 3.11+** installed
2. **Ollama** running locally with the `llama3.2:3b` model

### Install Ollama (if not already installed)
1. Download from https://ollama.ai
2. Install and run Ollama
3. Pull the model:
   ```bash
   ollama pull llama3.2:3b
   ```

## Quick Start

### Option 1: One-click (Windows)
Double-click `run.bat` or run in terminal:
```batch
run.bat
```

### Option 2: Manual setup
```bash
cd D:\projects\agora-sim

# Create virtual environment (first time only)
python -m venv venv

# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn backend.main:app --reload
```

Then open **http://localhost:8000** in your browser.

## Dashboard Layout

The dashboard has 3 columns:

| Left | Center | Right |
|------|--------|-------|
| **Agents Panel** - Shows Mira and Leo's stats (traits, mood, coins, inventory) | **Chat Feed** - Scrollable list of recent events with color-coded actions | **Controls** - Round number, Next Round button, Auto toggle, Reset button, Event log |

## Controls

- **Next Round**: Manually advance one round (both agents act)
- **Auto: ON/OFF**: Toggle automatic rounds every 5 seconds
- **Reset World**: Wipe database and restart with fresh agents

## Agents

| Agent | Traits | Starts With |
|-------|--------|-------------|
| **Mira** | proud, greedy, curious | 20 coins + 3 fish |
| **Leo** | cautious, friendly, honest | 20 coins + 3 bread |

## Trade Rules

- **Fish**: 5 coins (fixed price)
- **Bread**: 4 coins (fixed price)
- Buyers can haggle once (offer price - 1)
- Successful trade → both agents become "happy"
- Refused trade → refuser "annoyed", offerer "sad"

## Mood System

Moods affect dialogue tone:
- `happy` → positive, friendly dialogue
- `neutral` → normal dialogue
- `annoyed` → curt, dismissive dialogue
- `sad` → melancholic dialogue

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serves frontend dashboard |
| GET | `/state` | Returns current game state (round, agents, recent events) |
| POST | `/next-round` | Runs one round, returns 2 new events |
| POST | `/reset` | Wipes DB and reinitializes agents |
| GET | `/events` | Returns all events for log panel |

## Changing the Model

To use a different Ollama model:

1. Edit `backend/agents.py`
2. Change the `MODEL` variable:
   ```python
   MODEL = "llama3.2:3b"  # Change to any installed Ollama model
   ```
3. Restart the server

Example models:
- `llama3.1:8b` - Larger, more capable
- `mistral:7b` - Alternative model
- `phi3:3.8b` - Microsoft's Phi-3

## Resetting the World

To reset without using the UI button:

```bash
# Delete the database file
del agora.db  # Windows
rm agora.db   # macOS/Linux

# Restart server - it will recreate with fresh agents
```

## Troubleshooting

### "LLM call failed" errors
- Make sure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Check Ollama is accessible at http://localhost:11434

### Port 8000 already in use
- Change port in `run.bat` or command line:
  ```bash
  python -m uvicorn backend.main:app --port 8001
  ```

### Database locked
- Close any other processes using `agora.db`
- Delete `agora.db` and restart

## Project Structure

```
D:\projects\agora-sim\
├── backend\
│   ├── main.py          # FastAPI app + endpoints
│   ├── agents.py        # Agent rules + LLM calls
│   ├── db.py            # SQLite helpers
│   ├── prompts.py       # LLM prompt templates
│   └── engine.py        # Round loop, trade resolution
├── frontend\
│   └── index.html       # Single-page dashboard
├── agora.db             # SQLite database (created on first run)
├── requirements.txt     # Python dependencies
├── run.bat              # One-click launcher
└── README.md            # This file
```

## License

MIT - Do whatever you want with it.
