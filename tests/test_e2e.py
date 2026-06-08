"""
End-to-end tests for the Luxe Collective Command Center.
Run: pytest tests/ -v
"""
import os
import pytest

# ── App bootstrap ──────────────────────────────────────────────────────────
# Must be set before any backend imports so database.py picks up the URL.
_TEST_DB = "/tmp/test_luxe.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["SECRET_KEY"]   = "test-secret-key-32bytes-xxxxxxxxxxx"

# Remove stale DB from a previous run
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app               # noqa: E402 – must be after env vars


@pytest.fixture(scope="session")
def client():
    """Start the app (triggers lifespan → init_db + seed) and yield the client."""
    with TestClient(app) as c:
        yield c
    # clean up the test DB file after the session
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


# ── Helpers ────────────────────────────────────────────────────────────────

def _boss_token(client) -> str:
    r = client.post(
        "/api/auth/token",
        data={"username": "boss", "password": "boss-luxe"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": "Bearer " + token}


# ── Health ─────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Auth ───────────────────────────────────────────────────────────────────

def test_login_boss(client):
    r = client.post(
        "/api/auth/token",
        data={"username": "boss", "password": "boss-luxe"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    r = client.post(
        "/api/auth/token",
        data={"username": "boss", "password": "wrong"},
    )
    assert r.status_code == 401


# ── Boss workflow ──────────────────────────────────────────────────────────

def test_submit_task(client):
    r = client.post("/api/boss/submit", json={
        "agent_id":    "04",
        "task_type":   "design_concept",
        "description": "Test handbag line",
        "payload":     {"collection": "Test", "category": "handbag", "skus": []},
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"


def test_list_pending_requires_auth(client):
    r = client.get("/api/boss/pending")
    assert r.status_code == 401


def test_list_pending_with_auth(client):
    token = _boss_token(client)
    r = client.get("/api/boss/pending", headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_approve_task(client):
    token = _boss_token(client)

    # Submit a campaign task
    sub = client.post("/api/boss/submit", json={
        "agent_id":    "07",
        "task_type":   "marketing_campaign",
        "description": "Test campaign",
        "payload": {
            "campaign_name":      "Summer Sale",
            "channels":           ["instagram"],
            "budget_usd":         1000,
            "target_audience":    {},
            "creative_asset_ids": [],
            "flight_dates":       {"start": "2025-08-01", "end": "2025-08-14"},
            "kpis":               [],
        },
    })
    task_id = sub.json()["task_id"]

    # Approve
    r = client.post(
        f"/api/boss/review/{task_id}",
        headers=_auth(token),
        json={"approved": True, "comment": "Looks good"},
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("approved", "executed")


def test_reject_task(client):
    token = _boss_token(client)

    sub = client.post("/api/boss/submit", json={
        "agent_id":    "08",
        "task_type":   "content_creation",
        "description": "Reject me",
        "payload":     {},
    })
    task_id = sub.json()["task_id"]

    r = client.post(
        f"/api/boss/review/{task_id}",
        headers=_auth(token),
        json={"approved": False, "comment": "Not ready"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


# ── Activity log ───────────────────────────────────────────────────────────

def test_write_and_read_activity_log(client):
    # Write (no auth – internal agents can call this)
    r = client.post("/api/activity/log", params={
        "agent_id":   "09",
        "event_type": "analysis_requested",
        "summary":    "Test analysis",
    })
    assert r.status_code == 201

    # Read (requires auth)
    token = _boss_token(client)
    r2 = client.get("/api/activity/recent", headers=_auth(token))
    assert r2.status_code == 200
    logs = r2.json()
    assert any(l["event_type"] == "analysis_requested" for l in logs)


# ── Design assets ──────────────────────────────────────────────────────────

def test_design_assets_requires_auth(client):
    r = client.get("/api/design/approved")
    assert r.status_code == 401


def test_design_assets_with_auth(client):
    token = _boss_token(client)
    r = client.get("/api/design/approved", headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Sales endpoints ────────────────────────────────────────────────────────

def test_sales_summary(client):
    token = _boss_token(client)
    r = client.get("/api/admin/sales/summary", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "revenue_30d" in data
    assert "orders_30d" in data
    assert "aov" in data


def test_sales_trend(client):
    token = _boss_token(client)
    r = client.get("/api/admin/sales/trend", params={"days": 7}, headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "labels" in data
    assert len(data["labels"]) == 7


def test_top_products(client):
    token = _boss_token(client)
    r = client.get("/api/admin/sales/top-products", params={"limit": 5}, headers=_auth(token))
    assert r.status_code == 200
    products = r.json()
    assert isinstance(products, list)
    assert len(products) <= 5
    if products:
        assert "Rank" in products[0]
        assert "Revenue" in products[0]


# ── Agent-specific endpoints ───────────────────────────────────────────────

def test_agent04_specs(client):
    token = _boss_token(client)
    r = client.get("/api/agents/04/specs", headers=_auth(token))
    assert r.status_code == 200


def test_agent07_campaigns(client):
    token = _boss_token(client)
    r = client.get("/api/agents/07/campaigns", headers=_auth(token))
    assert r.status_code == 200


def test_agent09_analytics(client):
    token = _boss_token(client)
    r = client.get("/api/agents/09/analytics", headers=_auth(token))
    assert r.status_code == 200


def test_agent10_cx_responses(client):
    token = _boss_token(client)
    r = client.get("/api/agents/10/cx-responses", headers=_auth(token))
    assert r.status_code == 200
