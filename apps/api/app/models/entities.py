import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(128), default="general")
    unit_cost: Mapped[float] = mapped_column(Float)


class FulfillmentNode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fulfillment_nodes"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(64), default="NA")


class Inventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "node_id"),)

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"), index=True)
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)


class DemandForecast(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "demand_forecasts"

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"), index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=21)
    quantity: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(64), default="statistical")


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    reliability_score: Mapped[float] = mapped_column(Float, default=0.9)
    status: Mapped[str] = mapped_column(String(32), default="active")


class SupplierProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "supplier_products"
    __table_args__ = (UniqueConstraint("supplier_id", "product_id"),)

    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    moq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[float] = mapped_column(Float)
    max_available: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)


class Budget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "budgets"

    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    spent: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")


class StorageCapacity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storage_capacities"

    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"), unique=True)
    additional_units_available: Mapped[int] = mapped_column(Integer)
    used_units: Mapped[int] = mapped_column(Integer, default=0)


class BusinessRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_rules"

    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536), nullable=True)


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (Index("ix_po_status", "status"),)

    po_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"))
    status: Mapped[str] = mapped_column(String(32), default="open")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    force_qty_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(back_populates="purchase_order")


class PurchaseOrderLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class PurchasingCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchasing_cases"
    __table_args__ = (Index("ix_cases_status", "status"),)

    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fulfillment_nodes.id"), index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    original_recommended_qty: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    scenario_key: Mapped[str] = mapped_column(String(64), index=True)
    current_po_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    force_validation_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (Index("ix_runs_case", "case_id", "created_at"),)

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchasing_cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(64), default="START")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ToolCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_calls"

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")


class Decision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decisions"

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchasing_cases.id"), index=True)
    decision: Mapped[str] = mapped_column(String(32), index=True)
    recommended_quantity: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(16))
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    reason_codes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    explanation: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(64))
    policy_citations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    financial_impact: Mapped[float] = mapped_column(Float, default=0)


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approvals"

    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decisions.id"), index=True)
    actor_email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    comment: Mapped[str] = mapped_column(Text, default="")


class AgentAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_actions"

    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decisions.id"), index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchasing_cases.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    result_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ValidationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validation_events"

    action_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_actions.id"), nullable=True, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    expected_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    actual_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    violations: Mapped[list] = mapped_column(JSONB, default=list)
    recovery_required: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_case_ts", "case_id", "created_at"),)

    case_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="system")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
