import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    BOSS_REVIEW = "boss_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOGO_DESIGN = "logo_design"
    GRAPHIC_DESIGN = "graphic_design"
    PRINT_SOURCING = "print_sourcing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    brand_name = Column(String(255), nullable=False)
    product_type = Column(String(255), nullable=False)
    style_description = Column(Text, nullable=False)
    quantity = Column(Integer, default=100)
    budget_usd = Column(Integer, default=500)
    status = Column(String(50), default=TaskStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    results = relationship("AgentResult", back_populates="task", order_by="AgentResult.created_at")
    logs = relationship("TaskLog", back_populates="task", order_by="TaskLog.created_at")


class AgentResult(Base):
    __tablename__ = "agent_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent_id = Column(String(20), nullable=False)    # agent_01 … agent_05
    agent_name = Column(String(100), nullable=False)
    result_type = Column(String(50), nullable=False)  # approval | logo_concept | graphic | print_quote
    content = Column(Text, nullable=False)            # JSON payload
    status = Column(String(20), nullable=False)       # success | rejected | error
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="results")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent = Column(String(100))
    action = Column(String(100))
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="logs")
