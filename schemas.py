from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(ORMModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


# ── Product Schemas ───────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = Field(None, gt=0)
    stock: int = Field(0, ge=0)
    designer: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    discount_price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    designer: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    is_featured: Optional[bool] = None


class ProductResponse(ORMModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    discount_price: Optional[float]
    stock: int
    designer: Optional[str]
    material: Optional[str]
    color: Optional[str]
    is_featured: bool
    created_at: datetime
    updated_at: datetime

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int


# ── Cart Schemas ──────────────────────────────────────────────────────────────

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)


class CartItemResponse(ORMModel):
    id: int
    product_id: int
    quantity: int
    added_at: datetime
    product: ProductResponse

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    subtotal: float


# ── Order Schemas ─────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=10)


class OrderItemResponse(ORMModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ProductResponse

class OrderResponse(ORMModel):
    id: int
    order_number: str
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

# ── Agent Task Schemas ────────────────────────────────────────────────────────

class AgentTaskSubmit(BaseModel):
    agent_id: str = Field(..., pattern=r"^\d{2}$")
    task_type: str
    description: str
    payload: dict


class AgentTaskReview(BaseModel):
    decision: str = Field(..., description="'APPROVED: reason' or 'REJECTED: reason'")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        decision = value.strip()
        decision_upper = decision.upper()
        if not (decision_upper.startswith("APPROVED") or decision_upper.startswith("REJECTED")):
            raise ValueError("Decision must start with 'APPROVED' or 'REJECTED'")
        return decision


class AgentTaskResponse(ORMModel):
    id: int
    agent_id: str
    task_type: str
    description: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    boss_feedback: Optional[str]
    approved_by: Optional[str]
    executed_at: Optional[datetime]

class AgentTaskDetailResponse(AgentTaskResponse):
    payload: dict
