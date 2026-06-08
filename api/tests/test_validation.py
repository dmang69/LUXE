"""
Tests for Pydantic schema validation (TaskCreate).
These run without a database – pure in-memory validation.
"""
import pytest
from pydantic import ValidationError

import sys
import os

# Allow importing from the api/ directory without a package install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# database.py raises at import time if DATABASE_URL is missing, so provide a
# dummy value before importing anything that transitively imports database.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from schemas import TaskCreate  # noqa: E402


VALID_PAYLOAD = {
    "title": "Summer Drop 2025",
    "brand_name": "NOCTURNE",
    "product_type": "T-Shirt",
    "style_description": "Minimalist streetwear with bold typography",
    "quantity": 100,
    "budget_usd": 500,
}


class TestTaskCreateValidation:
    def test_valid_payload_accepted(self):
        task = TaskCreate(**VALID_PAYLOAD)
        assert task.title == "Summer Drop 2025"
        assert task.quantity == 100

    def test_style_description_minimum_20_chars(self):
        # Exactly 20 characters – boundary: should pass
        payload = {**VALID_PAYLOAD, "style_description": "A" * 20}
        task = TaskCreate(**payload)
        assert len(task.style_description) == 20

    def test_style_description_19_chars_rejected(self):
        # One char below minimum – must fail
        payload = {**VALID_PAYLOAD, "style_description": "A" * 19}
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(**payload)
        errors = exc_info.value.errors()
        assert any("style_description" in str(e) for e in errors)

    def test_style_description_empty_rejected(self):
        payload = {**VALID_PAYLOAD, "style_description": ""}
        with pytest.raises(ValidationError):
            TaskCreate(**payload)

    def test_title_too_short_rejected(self):
        payload = {**VALID_PAYLOAD, "title": "AB"}
        with pytest.raises(ValidationError):
            TaskCreate(**payload)

    def test_quantity_below_minimum_rejected(self):
        payload = {**VALID_PAYLOAD, "quantity": 0}
        with pytest.raises(ValidationError):
            TaskCreate(**payload)

    def test_budget_below_minimum_rejected(self):
        payload = {**VALID_PAYLOAD, "budget_usd": 49}
        with pytest.raises(ValidationError):
            TaskCreate(**payload)

    def test_default_quantity_and_budget(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k not in ("quantity", "budget_usd")}
        task = TaskCreate(**payload)
        assert task.quantity == 100
        assert task.budget_usd == 500
