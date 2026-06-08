import json
import math
import uuid
from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from dependencies import get_current_user, require_admin, require_staff_user
from security import hash_password, verify_password, create_access_token
from boss_agent_service import boss_agent_service
from workers.task_executor import TaskExecutor


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

# ── Auth ──────────────────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = models.User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        phone=user_in.phone,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@auth_router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


# ── Products ──────────────────────────────────────────────────────────────────

products_router = APIRouter(prefix="/api/products", tags=["products"])


@products_router.get("/", response_model=schemas.ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    designer: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    if designer:
        q = q.filter(models.Product.designer == designer)
    if min_price is not None:
        q = q.filter(models.Product.price >= min_price)
    if max_price is not None:
        q = q.filter(models.Product.price <= max_price)
    if is_featured is not None:
        q = q.filter(models.Product.is_featured == is_featured)
    if search:
        q = q.filter(
            models.Product.name.ilike(f"%{search}%")
            | models.Product.description.ilike(f"%{search}%")
        )
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 0,
    }


@products_router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@products_router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    product = models.Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@products_router.patch("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


# ── Cart ──────────────────────────────────────────────────────────────────────

cart_router = APIRouter(prefix="/api/cart", tags=["cart"])


@cart_router.get("/", response_model=schemas.CartResponse)
def view_cart(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == current_user.id)
        .all()
    )
    subtotal = sum(
        (item.product.discount_price or item.product.price) * item.quantity
        for item in items
    )
    return {"items": items, "total_items": len(items), "subtotal": round(subtotal, 2)}


@cart_router.post("/items", response_model=schemas.CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item_in: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    existing = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == current_user.id,
            models.CartItem.product_id == item_in.product_id,
        )
        .first()
    )
    if existing:
        if product.stock < existing.quantity + item_in.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        existing.quantity += item_in.quantity
        db.commit()
        db.refresh(existing)
        return existing

    cart_item = models.CartItem(
        user_id=current_user.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


@cart_router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id,
            models.CartItem.user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


# ── Orders ────────────────────────────────────────────────────────────────────

orders_router = APIRouter(prefix="/api/orders", tags=["orders"])


@orders_router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == current_user.id)
        .all()
    )
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate stock
    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product '{item.product.name}'",
            )

    total = sum(
        (item.product.discount_price or item.product.price) * item.quantity
        for item in cart_items
    )
    order_number = f"LC-{_utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    order = models.Order(
        user_id=current_user.id,
        order_number=order_number,
        total_amount=round(total, 2),
        shipping_address=order_in.shipping_address,
    )
    db.add(order)
    db.flush()

    for item in cart_items:
        unit_price = item.product.discount_price or item.product.price
        db.add(
            models.OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=unit_price,
            )
        )
        item.product.stock -= item.quantity
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order


@orders_router.get("/", response_model=List[schemas.OrderResponse])
def list_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


@orders_router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id,
            models.Order.user_id == current_user.id,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ── Boss Agent ────────────────────────────────────────────────────────────────

boss_router = APIRouter(prefix="/api/boss", tags=["boss agent"])


@boss_router.post("/submit", response_model=schemas.AgentTaskResponse, status_code=status.HTTP_201_CREATED)
def submit_task(
    task_in: schemas.AgentTaskSubmit,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_staff_user),
):
    task = boss_agent_service.submit_task(
        db=db,
        agent_id=task_in.agent_id,
        task_type=task_in.task_type,
        description=task_in.description,
        payload=task_in.payload,
    )
    return task


@boss_router.get("/pending", response_model=List[schemas.AgentTaskDetailResponse])
def get_pending_tasks(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    tasks = boss_agent_service.get_pending_tasks(db)
    result = []
    for t in tasks:
        data = schemas.AgentTaskDetailResponse.model_validate(t).model_copy(
            update={"payload": json.loads(t.payload)}
        )
        result.append(data)
    return result


@boss_router.post("/review/{task_id}", response_model=schemas.AgentTaskResponse)
def review_task(
    task_id: int,
    review: schemas.AgentTaskReview,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    try:
        task = boss_agent_service.review_task(db, task_id, review.decision)
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT if "pending" in detail.lower() else status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from exc
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@boss_router.get("/task/{task_id}", response_model=schemas.AgentTaskResponse)
def get_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_staff_user),
):
    task = boss_agent_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@boss_router.post("/execute/{task_id}")
def execute_approved_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    task = boss_agent_service.claim_task_for_execution(db, task_id)
    if not task:
        existing_task = boss_agent_service.get_task(db, task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")
        if existing_task.status in {"pending", "rejected"}:
            raise HTTPException(status_code=400, detail="Task not approved for execution")
        raise HTTPException(status_code=409, detail=f"Task is already {existing_task.status}")

    try:
        result = TaskExecutor.execute_task(task)
        boss_agent_service.complete_task(db, task.id, True, result)
        return {"message": "Task executed successfully", "result": result}
    except Exception as exc:
        boss_agent_service.complete_task(db, task.id, False, None, str(exc))
        raise HTTPException(status_code=500, detail=f"Execution failed: {exc}")
