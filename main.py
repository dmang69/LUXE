"""
LUXE COLLECTIVE - FastAPI Application
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    from database import Base, engine
    from models import (  # noqa: F401 – ensure models are registered
        Cart,
        CartItem,
        Order,
        OrderItem,
        Product,
        User,
        UserPreference,
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="LUXE COLLECTIVE API",
    description="Premium Fashion E-Commerce Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(","),
)

# ─── Auth Routes ──────────────────────────────────────────────────────────────

from database import get_db
from models import User
from schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
    require_admin,
    verify_password,
)


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=token, user=user)


@app.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ─── Product Routes ───────────────────────────────────────────────────────────

from models import Product
from schemas import ProductCreate, ProductResponse


@app.get("/products", response_model=list[ProductResponse], tags=["Products"])
def list_products(
    category: str = None,
    featured: bool = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if featured is not None:
        query = query.filter(Product.is_featured == featured)
    return query.offset(skip).limit(limit).all()


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def update_product(
    product_id: int,
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()


# ─── Cart Routes ──────────────────────────────────────────────────────────────

from models import CartItem
from schemas import CartItemCreate, CartItemResponse


@app.get("/cart", response_model=list[CartItemResponse], tags=["Cart"])
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(CartItem).filter(CartItem.user_id == current_user.id).all()


@app.post("/cart", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED, tags=["Cart"])
def add_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == item_in.product_id)
        .first()
    )
    if existing:
        existing.quantity += item_in.quantity
        db.commit()
        db.refresh(existing)
        return existing

    cart_item = CartItem(
        user_id=current_user.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


@app.delete("/cart/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Cart"])
def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


# ─── Order Routes ─────────────────────────────────────────────────────────────

from models import Order, OrderItem
from schemas import OrderCreate, OrderResponse


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = 0.0
    order_items = []
    for ci in cart_items:
        product = db.query(Product).filter(Product.id == ci.product_id).first()
        if not product or product.stock < ci.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Product {ci.product_id} unavailable or insufficient stock",
            )
        unit_price = product.discount_price or product.price
        total += unit_price * ci.quantity
        order_items.append(
            OrderItem(product_id=ci.product_id, quantity=ci.quantity, price=unit_price)
        )
        product.stock -= ci.quantity

    order = Order(
        user_id=current_user.id,
        order_number=f"LX-{uuid.uuid4().hex[:8].upper()}",
        total_amount=round(total, 2),
        shipping_address=order_in.shipping_address,
    )
    db.add(order)
    db.flush()  # get order.id

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    # Clear cart
    for ci in cart_items:
        db.delete(ci)

    db.commit()
    db.refresh(order)
    return order


@app.get("/orders", response_model=list[OrderResponse], tags=["Orders"])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "LUXE COLLECTIVE API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
