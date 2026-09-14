from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    email: str
    full_name: str
    role: str


class CaseListItem(BaseModel):
    id: UUID
    case_number: str
    title: str
    status: str
    risk_level: str
    original_recommended_qty: int
    scenario_key: str
    product_sku: str
    product_name: str
    node_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceSnapshot(BaseModel):
    inventory: dict | None = None
    forecast: dict | None = None
    open_pos: dict | None = None
    supplier: dict | None = None
    budget: dict | None = None
    storage: dict | None = None
    replenishment: dict | None = None


class DecisionOut(BaseModel):
    id: UUID
    decision: str
    recommended_quantity: int
    confidence: float
    risk_level: str
    requires_approval: bool
    reason_codes: list[str]
    explanation: str
    action: str
    policy_citations: list[str]
    financial_impact: float
    created_at: datetime


class ToolCallOut(BaseModel):
    id: UUID
    tool_name: str
    status: str
    duration_ms: int | None
    input_json: dict
    output_json: dict
    summary: str
    created_at: datetime


class ValidationOut(BaseModel):
    id: UUID
    passed: bool
    expected_json: dict
    actual_json: dict
    violations: list
    recovery_required: bool
    created_at: datetime


class AgentRunOut(BaseModel):
    id: UUID
    case_id: UUID
    status: str
    stage: str
    duration_ms: int | None
    error: str | None
    tool_calls: list[ToolCallOut] = Field(default_factory=list)
    decision: DecisionOut | None = None
    validations: list[ValidationOut] = Field(default_factory=list)


class CaseDetail(BaseModel):
    id: UUID
    case_number: str
    title: str
    status: str
    risk_level: str
    original_recommended_qty: int
    scenario_key: str
    product_sku: str
    product_name: str
    node_code: str
    node_name: str
    supplier_code: str
    supplier_name: str
    current_po_number: str | None
    latest_run: AgentRunOut | None = None
    evidence: EvidenceSnapshot | None = None


class ApprovalRequest(BaseModel):
    comment: str = ""


class DashboardStats(BaseModel):
    pending_ai_decisions: int
    awaiting_approval: int
    open_purchase_orders: int
    failed_validations: int
    active_investigations: int
    budget_amount: float
    budget_spent: float
    inventory_risk_skus: int
    supplier_risk_count: int
    recommendations_by_status: dict[str, int]
    recent_runs: list[dict]
    inventory_coverage: list[dict]
    supplier_fulfillment: list[dict]


class AuditItem(BaseModel):
    id: UUID
    case_id: UUID | None
    run_id: UUID | None
    event_type: str
    actor: str
    payload: dict
    created_at: datetime
