export type CaseListItem = {
  id: string;
  case_number: string;
  title: string;
  status: string;
  risk_level: string;
  original_recommended_qty: number;
  scenario_key: string;
  product_sku: string;
  product_name: string;
  node_code: string;
  created_at: string;
};

export type ToolCall = {
  id: string;
  tool_name: string;
  status: string;
  duration_ms: number | null;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  summary: string;
  created_at: string;
};

export type Decision = {
  id: string;
  decision: string;
  recommended_quantity: number;
  confidence: number;
  risk_level: string;
  requires_approval: boolean;
  reason_codes: string[];
  explanation: string;
  action: string;
  policy_citations: string[];
  financial_impact: number;
  created_at: string;
};

export type Validation = {
  id: string;
  passed: boolean;
  expected_json: Record<string, unknown>;
  actual_json: Record<string, unknown>;
  violations: { code?: string; message?: string }[];
  recovery_required: boolean;
  created_at: string;
};

export type AgentRun = {
  id: string;
  case_id: string;
  status: string;
  stage: string;
  duration_ms: number | null;
  error: string | null;
  tool_calls: ToolCall[];
  decision: Decision | null;
  validations: Validation[];
};

export type CaseDetail = {
  id: string;
  case_number: string;
  title: string;
  status: string;
  risk_level: string;
  original_recommended_qty: number;
  scenario_key: string;
  product_sku: string;
  product_name: string;
  node_code: string;
  node_name: string;
  supplier_code: string;
  supplier_name: string;
  current_po_number: string | null;
  latest_run: AgentRun | null;
  evidence: {
    inventory?: Record<string, unknown>;
    forecast?: Record<string, unknown>;
    open_pos?: Record<string, unknown>;
    supplier?: Record<string, unknown>;
    budget?: Record<string, unknown>;
    storage?: Record<string, unknown>;
  } | null;
};

export type DashboardStats = {
  pending_ai_decisions: number;
  awaiting_approval: number;
  open_purchase_orders: number;
  failed_validations: number;
  active_investigations: number;
  budget_amount: number;
  budget_spent: number;
  inventory_risk_skus: number;
  supplier_risk_count: number;
  recommendations_by_status: Record<string, number>;
  recent_runs: { id: string; status: string; stage: string; duration_ms: number | null }[];
  inventory_coverage: { case: string; on_hand: number; recommended: number }[];
  supplier_fulfillment: { supplier: string; reliability: number }[];
};
