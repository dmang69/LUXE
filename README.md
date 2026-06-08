# LUXE – Luxe Collective Command Center 👑

A production-ready AI agent workforce platform for a luxury fashion brand.
Every agent action must be approved by **Boss Agent 01** before execution.

---

## Architecture

```
Agents (04–10) → /api/boss/submit → Boss approves → Task Executor
                                                          │
                    ┌─────────────────────────────────────┤
                    ▼                                     ▼
               DesignAsset                          ActivityLog
               AccessorySpec                        Campaign
               CXResponse                           AnalyticsResult
               Product (updated)                    Order (unchanged)
                    │
                    ▼
              Streamlit Dashboard (4 screens)
```

## Agents

| ID | Name                  | Task Types                                  |
|----|-----------------------|---------------------------------------------|
| 04 | Accessories Designer  | `design_concept`                            |
| 06 | E-Commerce Architect  | `catalog_update`, `create_product`          |
| 07 | Digital Marketing     | `marketing_campaign`, `promo_code`          |
| 08 | Content Creator       | `content_creation`, `blog_post`             |
| 09 | Data Analyst          | `analysis_request`, `recurring_analysis`    |
| 10 | Customer Experience   | `cx_response`, `cx_outreach`, `return_request` |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# edit .env – set API keys, passwords, etc.
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend auto-creates all tables and seeds demo data on first run.
Default credentials: `boss / boss-luxe` and `admin / admin-luxe`.

API docs: http://localhost:8000/docs

### 4. Start the dashboard

```bash
streamlit run dashboard.py --server.port 8501
```

Open http://localhost:8501 – sign in with `boss / boss-luxe`.

### 5. Docker Compose (single command)

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Dashboard: http://localhost:8501

## Dashboard Screens

| Screen | What you see |
|--------|-------------|
| 🔐 Boss Approval Hub | Pending tasks; approve / reject with comment |
| 📡 Live Activity Log | Real-time feed of every agent event |
| 🎨 Design Gallery   | Approved assets + accessory spec cards |
| 💰 Sales & Performance | Revenue KPIs, 7-day trend chart, top-5 products, active campaigns |

## AI Providers

Set environment variables to enable real AI generation:

| Variable | Provider | Used for |
|----------|----------|----------|
| `GOOGLE_API_KEY` | Google Gemini / Imagen | Text copy, blog posts, image generation |
| `OPENAI_API_KEY` | OpenAI GPT-4o / DALL-E 3 | Fallback for text + image |

If neither is set, the platform uses mock responses so everything still works out of the box.

## Object Storage

| Variable | Description |
|----------|-------------|
| `S3_BUCKET` | Upload generated images to S3 |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `LOCAL_ASSET_DIR` | Local fallback directory (default: `assets/`) |

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
LUXE/
├── backend/
│   ├── main.py              # FastAPI app, lifespan, demo-data seed
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # All ORM models
│   ├── auth.py              # JWT helpers + role-based dependencies
│   ├── routers/
│   │   ├── auth.py          # /api/auth/*
│   │   ├── boss.py          # /api/boss/*
│   │   ├── design.py        # /api/design/*
│   │   ├── activity.py      # /api/activity/*
│   │   ├── sales.py         # /api/admin/sales/*
│   │   └── agents.py        # /api/agents/*
│   ├── agents/
│   │   ├── abstract_agent.py
│   │   ├── accessories_designer.py   # Agent 04
│   │   ├── ecommerce_architect.py    # Agent 06
│   │   ├── digital_marketing.py      # Agent 07
│   │   ├── content_creator.py        # Agent 08
│   │   ├── data_analyst.py           # Agent 09
│   │   └── customer_experience.py    # Agent 10
│   ├── workers/
│   │   └── task_executor.py   # Dispatches approved tasks
│   └── services/
│       ├── ai_image.py        # Gemini / DALL-E image generation
│       ├── ai_text.py         # Gemini / GPT-4 text generation
│       └── storage.py         # S3 / local asset upload
├── dashboard.py              # Streamlit 4-screen dashboard
├── tests/test_e2e.py         # 18 end-to-end tests
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.dashboard
├── requirements.txt
└── .env.example
```
