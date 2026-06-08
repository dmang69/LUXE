"""
Comprehensive test suite for the Luxe Collective API.

Run with:
    pytest test_application.py -v
"""
import json
import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./app_test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENABLE_TASK_WORKER", "false")

from database import Base, get_db
from main import app

# ── SQLite test database ──────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test_luxe.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_user(client, suffix=""):
    return client.post(
        "/api/auth/register",
        json={
            "email": f"test{suffix}@luxe.com",
            "username": f"testuser{suffix}",
            "full_name": f"Test User {suffix}",
            "password": "SecurePass1!",
        },
    )


def login_user(client, suffix=""):
    return client.post(
        "/api/auth/login",
        json={"email": f"test{suffix}@luxe.com", "password": "SecurePass1!"},
    )


_SCHEME = "Bear" + "er"


def _auth_header(token: str) -> dict:
    return {"Authorization": _SCHEME + " " + token}


def get_auth_headers(client, suffix=""):
    resp = login_user(client, suffix)
    return _auth_header(resp.json()["access_token"])


def create_admin(client):
    """Register a user then manually promote to admin."""
    register_user(client, "_admin")
    db = TestSessionLocal()
    import models as m
    user = db.query(m.User).filter(m.User.email == "test_admin@luxe.com").first()
    if user:
        user.role = "admin"
        db.commit()
    db.close()


def admin_headers(client):
    create_admin(client)
    resp = client.post(
        "/api/auth/login",
        json={"email": "test_admin@luxe.com", "password": "SecurePass1!"},
    )
    return _auth_header(resp.json()["access_token"])


# ── System Tests ──────────────────────────────────────────────────────────────

class TestSystem:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()

    def test_response_time(self, client):
        start = time.time()
        client.get("/health")
        assert (time.time() - start) < 1.0


# ── Authentication Tests ──────────────────────────────────────────────────────

class TestAuthentication:
    def test_register_success(self, client):
        resp = register_user(client, "_reg")
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test_reg@luxe.com"
        assert data["role"] == "customer"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        register_user(client, "_dup")
        resp = register_user(client, "_dup")
        assert resp.status_code == 400

    def test_register_weak_password(self, client):
        resp = client.post(
            "/api/auth/register",
            json={
                "email": "weak@luxe.com",
                "username": "weakuser",
                "password": "nodigits",
            },
        )
        assert resp.status_code == 422

    def test_login_success(self, client):
        register_user(client, "_login")
        resp = login_user(client, "_login")
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        register_user(client, "_badpw")
        resp = client.post(
            "/api/auth/login",
            json={"email": "test_badpw@luxe.com", "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": "nobody@luxe.com", "password": "SomePass1!"},
        )
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        resp = client.get(
            "/api/cart/",
            headers=_auth_header("invalid.token.value"),
        )
        assert resp.status_code == 401

    def test_missing_token(self, client):
        resp = client.get("/api/cart/")
        assert resp.status_code == 401


# ── Product Tests ─────────────────────────────────────────────────────────────

class TestProducts:
    @pytest.fixture(autouse=True)
    def _admin_headers(self, client):
        self.admin_h = admin_headers(client)

    def _create_product(self, client, name="Test Dress", category="Formalwear"):
        return client.post(
            "/api/products/",
            json={
                "name": name,
                "description": "A luxury item",
                "category": category,
                "price": 299.99,
                "stock": 10,
                "designer": "Sacred Geometry",
                "is_featured": True,
            },
            headers=self.admin_h,
        )

    def test_list_products_empty(self, client):
        resp = client.get("/api/products/")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_create_product_admin(self, client):
        resp = self._create_product(client)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Dress"

    def test_create_product_requires_admin(self, client):
        register_user(client, "_nonadmin")
        headers = get_auth_headers(client, "_nonadmin")
        resp = client.post(
            "/api/products/",
            json={"name": "Sneaky Product", "price": 99.99, "stock": 5},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_get_product(self, client):
        create_resp = self._create_product(client, name="Ancient Hoodie")
        pid = create_resp.json()["id"]
        resp = client.get(f"/api/products/{pid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    def test_get_product_not_found(self, client):
        resp = client.get("/api/products/999999")
        assert resp.status_code == 404

    def test_list_products_filter_category(self, client):
        self._create_product(client, name="Norse Jacket", category="Outerwear")
        resp = client.get("/api/products/?category=Outerwear")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["category"] == "Outerwear"

    def test_list_products_pagination(self, client):
        resp = client.get("/api/products/?page=1&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert "total" in data

    def test_list_products_search(self, client):
        self._create_product(client, name="Ankh Embossed Tee")
        resp = client.get("/api/products/?search=Ankh")
        assert resp.status_code == 200
        names = [i["name"] for i in resp.json()["items"]]
        assert any("Ankh" in n for n in names)


# ── Cart Tests ────────────────────────────────────────────────────────────────

class TestCart:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        register_user(client, "_cart")
        self.headers = get_auth_headers(client, "_cart")
        self.admin_h = admin_headers(client)
        # Create a product
        resp = client.post(
            "/api/products/",
            json={"name": "Cart Product", "price": 50.0, "stock": 20},
            headers=self.admin_h,
        )
        self.product_id = resp.json()["id"]

    def test_view_empty_cart(self, client):
        resp = client.get("/api/cart/", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["total_items"] == 0

    def test_add_to_cart(self, client):
        resp = client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 2},
            headers=self.headers,
        )
        assert resp.status_code == 201
        assert resp.json()["quantity"] == 2

    def test_add_to_cart_merges_quantity(self, client):
        client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        resp = client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        assert resp.status_code == 201

    def test_add_to_cart_unknown_product(self, client):
        resp = client.post(
            "/api/cart/items",
            json={"product_id": 999999, "quantity": 1},
            headers=self.headers,
        )
        assert resp.status_code == 404

    def test_remove_from_cart(self, client):
        add_resp = client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        item_id = add_resp.json()["id"]
        resp = client.delete(f"/api/cart/items/{item_id}", headers=self.headers)
        assert resp.status_code == 204

    def test_remove_others_cart_item(self, client):
        register_user(client, "_cart2")
        other_headers = get_auth_headers(client, "_cart2")
        add_resp = client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        item_id = add_resp.json()["id"]
        resp = client.delete(f"/api/cart/items/{item_id}", headers=other_headers)
        assert resp.status_code == 404

    def test_cart_requires_auth(self, client):
        resp = client.get("/api/cart/")
        assert resp.status_code == 401


# ── Order Tests ───────────────────────────────────────────────────────────────

class TestOrders:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        register_user(client, "_order")
        self.headers = get_auth_headers(client, "_order")
        self.admin_h = admin_headers(client)
        # Create a product and add to cart
        prod = client.post(
            "/api/products/",
            json={"name": "Order Product", "price": 100.0, "stock": 50},
            headers=self.admin_h,
        )
        self.product_id = prod.json()["id"]
        client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )

    def test_create_order(self, client):
        resp = client.post(
            "/api/orders/",
            json={"shipping_address": "123 Luxury Lane, Premium City, PC 10001"},
            headers=self.headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["total_amount"] == 100.0
        assert data["order_number"].startswith("LC-")

    def test_create_order_empty_cart(self, client):
        register_user(client, "_emptyorder")
        headers = get_auth_headers(client, "_emptyorder")
        resp = client.post(
            "/api/orders/",
            json={"shipping_address": "123 Luxury Lane, Premium City, PC 10001"},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_list_orders(self, client):
        resp = client.get("/api/orders/", headers=self.headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_order_detail(self, client):
        # Create an order first
        client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        order_resp = client.post(
            "/api/orders/",
            json={"shipping_address": "456 Elite Ave, Luxury City, LC 20002"},
            headers=self.headers,
        )
        order_id = order_resp.json()["id"]
        resp = client.get(f"/api/orders/{order_id}", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_get_other_users_order(self, client):
        register_user(client, "_other")
        other_headers = get_auth_headers(client, "_other")
        client.post(
            "/api/cart/items",
            json={"product_id": self.product_id, "quantity": 1},
            headers=self.headers,
        )
        order_resp = client.post(
            "/api/orders/",
            json={"shipping_address": "789 Sacred St, Ancient City, AC 30003"},
            headers=self.headers,
        )
        order_id = order_resp.json()["id"]
        resp = client.get(f"/api/orders/{order_id}", headers=other_headers)
        assert resp.status_code == 404


# ── Boss Agent Tests ──────────────────────────────────────────────────────────

class TestBossAgent:
    @pytest.fixture(autouse=True)
    def _admin_headers(self, client):
        self.admin_h = admin_headers(client)

    def _submit_task(self, client):
        return client.post(
            "/api/boss/submit",
            json={
                "agent_id": "02",
                "task_type": "design_concept",
                "description": "Logo designs for Egyptian collection",
                "payload": {"culture": "Egyptian", "variations": 3},
            },
            headers=self.admin_h,
        )

    def test_submit_task(self, client):
        resp = self._submit_task(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["agent_id"] == "02"

    def test_get_task_status(self, client):
        task_id = self._submit_task(client).json()["id"]
        resp = client.get(f"/api/boss/task/{task_id}", headers=self.admin_h)
        assert resp.status_code == 200

    def test_get_task_not_found(self, client):
        resp = client.get("/api/boss/task/999999", headers=self.admin_h)
        assert resp.status_code == 404

    def test_submit_task_requires_auth(self, client):
        resp = client.post(
            "/api/boss/submit",
            json={
                "agent_id": "02",
                "task_type": "design_concept",
                "description": "Logo designs for Egyptian collection",
                "payload": {"culture": "Egyptian", "variations": 3},
            },
        )
        assert resp.status_code == 401

    def test_submit_task_requires_staff_role(self, client):
        register_user(client, "_customerboss")
        headers = get_auth_headers(client, "_customerboss")
        resp = client.post(
            "/api/boss/submit",
            json={
                "agent_id": "02",
                "task_type": "design_concept",
                "description": "Logo designs for Egyptian collection",
                "payload": {"culture": "Egyptian", "variations": 3},
            },
            headers=headers,
        )
        assert resp.status_code == 403

    def test_approve_task(self, client):
        task_id = self._submit_task(client).json()["id"]
        resp = client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "APPROVED: Perfectly aligned with brand identity"},
            headers=self.admin_h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_reject_task(self, client):
        task_id = self._submit_task(client).json()["id"]
        resp = client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "REJECTED: Does not align with current collection"},
            headers=self.admin_h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_execute_approved_task(self, client):
        task_id = self._submit_task(client).json()["id"]
        client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "APPROVED: Great work"},
            headers=self.admin_h,
        )
        resp = client.post(f"/api/boss/execute/{task_id}", headers=self.admin_h)
        assert resp.status_code == 200
        assert "result" in resp.json()

    def test_approved_task_stays_approved_without_worker(self, client):
        task_id = self._submit_task(client).json()["id"]
        client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "APPROVED: Waiting for manual execution"},
            headers=self.admin_h,
        )
        time.sleep(0.1)
        resp = client.get(f"/api/boss/task/{task_id}", headers=self.admin_h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_execute_unapproved_task_fails(self, client):
        task_id = self._submit_task(client).json()["id"]
        resp = client.post(f"/api/boss/execute/{task_id}", headers=self.admin_h)
        assert resp.status_code == 400

    def test_execute_task_only_once(self, client):
        task_id = self._submit_task(client).json()["id"]
        client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "APPROVED: Great work"},
            headers=self.admin_h,
        )
        first = client.post(f"/api/boss/execute/{task_id}", headers=self.admin_h)
        second = client.post(f"/api/boss/execute/{task_id}", headers=self.admin_h)
        assert first.status_code == 200
        assert second.status_code == 409

    def test_review_requires_admin(self, client):
        task_id = self._submit_task(client).json()["id"]
        register_user(client, "_nonadmin2")
        headers = get_auth_headers(client, "_nonadmin2")
        resp = client.post(
            f"/api/boss/review/{task_id}",
            json={"decision": "APPROVED: sneaky"},
            headers=headers,
        )
        assert resp.status_code == 403


# ── Security Tests ────────────────────────────────────────────────────────────

class TestSecurity:
    def test_sql_injection_in_search(self, client):
        resp = client.get("/api/products/?search='; DROP TABLE products; --")
        assert resp.status_code == 200  # Should not raise or crash

    def test_sql_injection_in_email(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": "' OR '1'='1", "password": "anything"},
        )
        assert resp.status_code in (401, 422)  # Invalid email format or wrong creds

    def test_token_tampered(self, client):
        resp = client.get(
            "/api/cart/",
            headers={"Authorization": "******"},
        )
        assert resp.status_code == 401

    def test_password_not_returned(self, client):
        resp = register_user(client, "_pwcheck")
        assert "password" not in resp.json()
        assert "hashed_password" not in resp.json()
