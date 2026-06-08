from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)

    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


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


class ProductResponse(BaseModel):
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

    class Config:
        from_attributes = True


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


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    added_at: datetime
    product: ProductResponse

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    subtotal: float


# ── Order Schemas ─────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=10)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ProductResponse

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


# ── Agent Task Schemas ────────────────────────────────────────────────────────

class AgentTaskSubmit(BaseModel):
    agent_id: str = Field(..., pattern=r"^\d{2}$")
    task_type: str
    description: str
    payload: dict


class AgentTaskReview(BaseModel):
    decision: str = Field(..., description="'APPROVED: reason' or 'REJECTED: reason'")


class AgentTaskResponse(BaseModel):
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

    class Config:
        from_attributes = True


class AgentTaskDetailResponse(AgentTaskResponse):
    payload: dict
