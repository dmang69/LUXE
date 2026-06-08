# 👑 Luxe Collective – Multi-Agent Design Platform

A real-time multi-agent pipeline that takes a fashion creative brief from submission through Boss Agent approval, logo design, garment graphic specification, and print vendor sourcing — all automated.

```
Submit Brief → Agent 01 (Boss) → Agent 02 (Logo) → Agent 03 (Graphic) → Agent 05 (Print Sourcing) → Done
```

## 🚀 Quick Start (5 minutes)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- ~3 GB free disk space

### 1. Clone and configure

```bash
git clone https://github.com/dmang69/LUXE.git
cd LUXE
cp .env.template .env
# Edit .env – at minimum update POSTGRES_PASSWORD and the DATABASE_URL password
# (for a quick local demo the defaults work out of the box)
# Edit USE_MOCK_AI and GENAI_API_KEY if you want real AI generation (optional)
```

> **Local dev defaults:** `docker-compose.yml` ships with fallback credentials
> (`luxe` / `luxe_secret`) so the stack starts immediately without a `.env` file.
> For anything beyond a private local demo, always set your own credentials in `.env`.

### 2. Start the platform

**Windows:**
```
Double-click start-luxe.bat
```

**Mac / Linux:**
```bash
docker compose up --build
```

### 3. Access

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## 🤖 The Agents

| Agent | Role | AI Mode |
|-------|------|---------|
| **Agent 01 – Boss Agent** | Reviews creative brief; approves or rejects with feedback | Mock + Real AI |
| **Agent 02 – Logo Designer** | Generates logo concept (name, symbol, palette, typography) | Mock + Real AI |
| **Agent 03 – Graphic Designer** | Produces full garment graphic spec (placement, technique, layers) | Mock + Real AI |
| **Agent 05 – Print Sourcing** | Queries vendor database, scores quotes, recommends best supplier | Always real logic |

## 🎭 Mock vs Real AI

By default `USE_MOCK_AI=true` in `.env` — agents return instant structured responses so you see the full workflow immediately with no API key.

To enable genuine **Google Gemini** AI generation:
1. Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Edit `.env`:
   ```
   USE_MOCK_AI=false
   GENAI_API_KEY=your-key-here
   ```
3. Restart: `docker compose restart api`

## 📊 Dashboard Screens

1. **Submit Task** – Creative brief form → triggers the full pipeline
2. **Task Queue** – Live status of all tasks with metrics
3. **Task Detail** – Full agent results, colour palettes, layer specs, vendor tables
4. **Print Sourcing** – Interactive vendor comparison charts (cost vs quality vs speed)

## 🏗️ Architecture

```
┌─────────────────┐    HTTP     ┌──────────────────────────────┐
│  Streamlit      │ ──────────> │  FastAPI  (port 8000)        │
│  Dashboard      │             │  • /api/tasks/ CRUD           │
│  (port 8501)    │             │  • Background pipeline runner │
└─────────────────┘             └──────────────┬───────────────┘
                                               │ SQLAlchemy
                                               ▼
                                ┌──────────────────────────────┐
                                │  PostgreSQL 15 (port 5432)   │
                                │  tables: tasks, agent_results│
                                │           task_logs          │
                                └──────────────────────────────┘
```

## 🪟 Windows Installer

To build a distributable `.exe` installer:

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Open `LuxeCollectiveLauncher.iss` in Inno Setup Compiler
3. Press **F9** to compile → `Output/LuxeCollective-Setup.exe`

The installer copies all helper files and creates desktop/Start Menu shortcuts. See `info.txt` for full disclaimer.

## 📁 Project Structure

```
LUXE/
├── api/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy models (Task, AgentResult, TaskLog)
│   ├── schemas.py           # Pydantic schemas (validation: style_description ≥ 20 chars)
│   ├── database.py          # DB connection + session
│   ├── requirements.txt
│   ├── agents/
│   │   ├── boss_agent.py    # Agent 01 – approval/rejection
│   │   ├── logo_agent.py    # Agent 02 – logo concept
│   │   ├── graphic_agent.py # Agent 03 – garment graphic spec
│   │   └── print_agent.py   # Agent 05 – vendor sourcing
│   ├── routers/
│   │   ├── tasks.py         # REST route definitions
│   │   └── pipeline.py      # Multi-agent pipeline orchestration
│   └── tests/
│       ├── test_validation.py  # Schema validation tests
│       └── test_boss_agent.py  # Boss Agent gate tests
├── dashboard.py             # Streamlit 4-screen dashboard
├── dashboard_helpers.py     # API client helpers and UI constants
├── requirements-dashboard.txt
├── Dockerfile.api
├── Dockerfile.dashboard
├── docker-compose.yml
├── .env.template            # Copy to .env and edit
├── start-luxe.bat           # Windows one-click launcher
├── stop-luxe.bat            # Windows stop script
├── LuxeCollectiveLauncher.iss # Inno Setup installer script
└── info.txt                 # Pre-install disclaimer
```

## 🧪 Running Tests

```bash
cd api
DATABASE_URL=sqlite:///./test.db USE_MOCK_AI=true python -m pytest tests/ -v
```

## ⚠️ Disclaimer

This is a **local development and demonstration platform**. It is not suitable for production use, real customer data, or multi-user deployment. See `info.txt` for full details.
