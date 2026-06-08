# Luxe Collective – AI-Powered Fashion Empire API

Production-ready FastAPI e-commerce platform with an integrated **Boss Agent** (Agent 01) approval workflow and a fleet of specialised AI agents.

---

## 🗂 File Structure

```
LUXE/
├── main.py                  # FastAPI app entry point & startup
├── models.py                # SQLAlchemy ORM models
├── schemas.py               # Pydantic request/response schemas
├── security.py              # JWT & password utilities
├── dependencies.py          # FastAPI dependency injection
├── routes.py                # All API routers
├── database.py              # DB engine & session factory
├── boss_agent_service.py    # Boss Agent (Agent 01) service
├── agents/
│   ├── abstract_agent.py    # Base class for specialised agents
│   ├── logo_designer.py     # Agent 02 – Logo designer
│   └── graphic_designer.py  # Agent 03 – Graphic design
├── workers/
│   └── task_executor.py     # Background task execution worker
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── test_application.py
```

---

## 📡 API Endpoints

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and receive JWT |

### Products
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products/` | List products (pagination & filtering) |
| GET | `/api/products/{id}` | Product detail |
| POST | `/api/products/` | Create product *(admin)* |
| PATCH | `/api/products/{id}` | Update product *(admin)* |

### Cart
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cart/` | View cart |
| POST | `/api/cart/items` | Add item to cart |
| DELETE | `/api/cart/items/{id}` | Remove item |

### Orders
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/orders/` | Create order from cart |
| GET | `/api/orders/` | List user orders |
| GET | `/api/orders/{id}` | Order detail |

### Boss Agent
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/boss/submit` | Submit task for approval |
| GET | `/api/boss/pending` | View pending tasks *(admin)* |
| POST | `/api/boss/review/{id}` | Approve/reject task *(admin)* |
| GET | `/api/boss/task/{id}` | Task status |
| POST | `/api/boss/execute/{id}` | Execute approved task *(admin)* |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |
| GET | `/docs` | Swagger UI |

---

## 🗄 Database Schema

```
users            (id, email, username, hashed_password, full_name, phone, role, is_active, created_at, updated_at)
products         (id, name, description, category, price, discount_price, stock, designer, material, color, is_featured, created_at, updated_at)
cart_items       (id, user_id, product_id, quantity, added_at)
orders           (id, user_id, order_number, total_amount, status, shipping_address, created_at, updated_at)
order_items      (id, order_id, product_id, quantity, price)
user_preferences (id, user_id, preferred_categories, preferred_designers, style_profile, created_at)
agent_tasks      (id, agent_id, task_type, description, payload, status, submitted_at, reviewed_at, boss_feedback, approved_by, executed_at)
task_execution_results (id, task_id, success, result_data, error_message, executed_at)
```

---

## 🤖 AI Agent Architecture

```
[Agents 02-10]
      ↓  POST /api/boss/submit
[Boss Agent 01 – Brand Architect]
      ↓  POST /api/boss/review/{id}  (admin)
[TaskExecutor background worker]
      ↓  executes approved work
[E-commerce platform / external services]
```

---

## 🚀 Running the App

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit DATABASE_URL, SECRET_KEY in .env

# 3. Start PostgreSQL (or use docker-compose for DB only)
docker-compose up db -d

# 4. Run
python main.py

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Docker (Recommended)

```bash
docker-compose up --build
```

---

## 🧪 Tests

```bash
pip install pytest
pytest test_application.py -v
```

---

## 🔐 Security

- Bcrypt password hashing
- JWT authentication (HS256)
- Role-based access control (customer / admin / vendor)
- SQLAlchemy ORM prevents SQL injection
- Pydantic input validation
- CORS configurable via `CORS_ORIGINS` env var

---

## 📱 Quick Start Examples

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"luxefan","password":"SecurePass1!"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass1!"}'

# Browse products
curl "http://localhost:8000/api/products/?category=Formalwear&limit=20"

# Add to cart (requires ******
curl -X POST http://localhost:8000/api/cart/items \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":2}'

# Submit an agent task for Boss approval
curl -X POST http://localhost:8000/api/boss/submit \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"02","task_type":"design_concept","description":"Egyptian logo concepts","payload":{"culture":"Egyptian"}}'
```