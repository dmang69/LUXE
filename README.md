# 👑 LUXE COLLECTIVE

Premium Fashion E-Commerce Platform — AI-Powered Boss Agent + FastAPI Backend

---

## 📦 Project Structure

```
luxe-collective/
├── main.py           # FastAPI application (REST API)
├── database.py       # SQLAlchemy engine + session
├── models.py         # ORM models (User, Product, Order, …)
├── schemas.py        # Pydantic request/response schemas
├── security.py       # JWT auth + password hashing
├── boss_agent.py     # Boss Agent + Specialized Agents + Streamlit dashboard
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set DATABASE_URL, SECRET_KEY, GOOGLE_API_KEY
```

### 3. Run the FastAPI backend

```bash
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 4. Run the Boss Agent dashboard

```bash
streamlit run boss_agent.py --server.port 8501
# Dashboard: http://localhost:8501
```

---

## ✅ Feature Overview

| Component | Status | Details |
|---|---|---|
| FastAPI REST API | ✅ Working | Auth, Products, Cart, Orders |
| JWT Authentication | ✅ Working | Register, Login, Protected routes |
| Boss Agent 01 | ✅ Working | Central authority with approval/rejection logic |
| Task Submission System | ✅ Working | Specialized agents submit via `submit_task()` |
| Approval Workflow | ✅ Working | Auto-review + human override |
| Streamlit Dashboard | ✅ Working | Approval Hub, Activity Log, Design Gallery |
| Agent 02 — Logo Designer | ✅ Working | Ancient symbolism logo variations |
| Agent 03 — Graphic Design | ✅ Working | Collection artwork submissions |
| Agents 04-10 | 🔶 Template Ready | Extend `SpecializedAgent` base class |

---

## 🔧 Adding More Agents (04-10)

```python
class AccessoriesDesigner(SpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent-04-accessories",
            name="Accessories Designer",
            specialty="Handbags, footwear, and jewelry design",
        )
    # Add domain-specific methods that call self.submit_task(...)
```

Instantiate in `main()` inside `boss_agent.py` and assign `agent.boss_agent = boss`.

---

## 🗝️ Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (change in production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 30) |
| `GOOGLE_API_KEY` | Gemini API key for AI features |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) |
| `ALLOWED_HOSTS` | Trusted hosts (comma-separated) |
