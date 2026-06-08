from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    brand_name: str = Field(..., min_length=1, max_length=255)
    product_type: str = Field(..., min_length=1, max_length=255)
    style_description: str = Field(..., min_length=10)
    quantity: int = Field(default=100, ge=1, le=100_000)
    budget_usd: int = Field(default=500, ge=50, le=1_000_000)


class TaskOut(BaseModel):
    id: int
    title: str
    brand_name: str
    product_type: str
    style_description: str
    quantity: int
    budget_usd: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Agent Result ──────────────────────────────────────────────────────────────

class AgentResultOut(BaseModel):
    id: int
    task_id: int
    agent_id: str
    agent_name: str
    result_type: str
    content: str   # raw JSON string; caller parses as needed
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Task Log ──────────────────────────────────────────────────────────────────

class TaskLogOut(BaseModel):
    id: int
    task_id: int
    agent: Optional[str]
    action: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Task Detail (full) ────────────────────────────────────────────────────────

class TaskDetail(TaskOut):
    results: List[AgentResultOut] = []
    logs: List[TaskLogOut] = []
