from pydantic import BaseModel, Field

from app.domain.enums import ActionType, DecisionType, RiskLevel


class ToolInventoryOut(BaseModel):
    on_hand: int
    reserved: int
    node_code: str
    sku: str


class ToolForecastOut(BaseModel):
    quantity: int
    horizon_days: int
    source: str


class ToolOpenPOLine(BaseModel):
    po_number: str
    quantity: int
    status: str


class ToolOpenPOOut(BaseModel):
    total_inbound: int
    orders: list[ToolOpenPOLine]


class ToolSupplierOut(BaseModel):
    code: str
    name: str
    reliability_score: float
    status: str
    moq: int | None
    lead_time_days: int | None
    unit_price: float
    max_available: int | None
    is_primary: bool


class ToolBudgetOut(BaseModel):
    amount: float
    spent: float
    remaining: float
    currency: str


class ToolStorageOut(BaseModel):
    additional_units_available: int
    used_units: int


class ToolRulesOut(BaseModel):
    rules: dict[str, str]


class KnowledgeHit(BaseModel):
    title: str
    source: str
    excerpt: str
    score: float


class DecisionOutput(BaseModel):
    decision: DecisionType
    recommended_quantity: int
    confidence: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    requires_approval: bool
    reason_codes: list[str]
    evidence: dict
    explanation: str
    action: ActionType
    policy_citations: list[str] = Field(default_factory=list)
    financial_impact: float = 0
