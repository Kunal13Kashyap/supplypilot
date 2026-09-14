"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Database, Play, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import { AuthGate } from "@/components/auth-gate";
import { RiskBadge, StatusBadge } from "@/components/domain/badges";
import {
  AgentTimeline,
  ApprovalPanel,
  ConstraintCard,
  DecisionPanel,
  EvidenceCard,
  SourceReference,
  ValidationResult,
} from "@/components/domain/operational";
import {
  EmptyState,
  ErrorState,
  LoadingButton,
  PageReveal,
  PageSkeleton,
} from "@/components/ui/primitives";
import { api } from "@/lib/utils";
import type { AgentRun, CaseDetail } from "@/types";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["case", params.id],
    queryFn: () => api<CaseDetail>(`/api/cases/${params.id}`),
    refetchInterval: 1500,
  });

  const runMut = useMutation({
    mutationFn: () => api<AgentRun>(`/api/cases/${params.id}/agent/run`, { method: "POST" }),
    onSuccess: () => {
      toast.success("Investigation complete", {
        description: "Decision and evidence are ready for review.",
      });
      qc.invalidateQueries({ queryKey: ["case", params.id] });
    },
    onError: (error) => toast.error("Investigation failed", { description: error.message }),
  });

  const approveMut = useMutation({
    mutationFn: (decisionId: string) =>
      api<AgentRun>(`/api/decisions/${decisionId}/approve`, {
        method: "POST",
        body: JSON.stringify({ comment: "Approved from console" }),
      }),
    onSuccess: () => {
      toast.success("Purchase action validated");
      qc.invalidateQueries({ queryKey: ["case", params.id] });
    },
    onError: (error) => toast.error("Approval failed", { description: error.message }),
  });

  const rejectMut = useMutation({
    mutationFn: (decisionId: string) =>
      api(`/api/decisions/${decisionId}/reject`, {
        method: "POST",
        body: JSON.stringify({ comment: "Rejected from console" }),
      }),
    onSuccess: () => {
      toast.info("Recommendation rejected");
      qc.invalidateQueries({ queryKey: ["case", params.id] });
    },
  });

  const reMut = useMutation({
    mutationFn: (decisionId: string) =>
      api<AgentRun>(`/api/decisions/${decisionId}/reanalyze`, {
        method: "POST",
        body: JSON.stringify({ comment: "Re-analysis requested" }),
      }),
    onSuccess: () => {
      toast.success("Re-analysis complete");
      qc.invalidateQueries({ queryKey: ["case", params.id] });
    },
  });

  const c = q.data;
  const inv = (c?.evidence?.inventory ?? {}) as Record<string, unknown>;
  const fc = (c?.evidence?.forecast ?? {}) as Record<string, unknown>;
  const pos = (c?.evidence?.open_pos ?? {}) as Record<string, unknown>;
  const sup = (c?.evidence?.supplier ?? {}) as Record<string, unknown>;
  const bud = (c?.evidence?.budget ?? {}) as Record<string, unknown>;
  const st = (c?.evidence?.storage ?? {}) as Record<string, unknown>;
  const decision = c?.latest_run?.decision;
  const tools = c?.latest_run?.tool_calls ?? [];
  const validations = c?.latest_run?.validations ?? [];

  return (
    <AuthGate>
      {q.isLoading && <PageSkeleton />}
      {q.isError && (
        <div className="page-container">
          <ErrorState message={(q.error as Error).message} retry={() => q.refetch()} />
        </div>
      )}
      {c && (
        <PageReveal className="page-container space-y-6">
          <Link
            href="/cases"
            className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to purchasing cases
          </Link>
          <header className="grid gap-6 border-b border-border pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="eyebrow">{c.case_number}</span>
                <StatusBadge value={c.status} />
                <RiskBadge value={c.risk_level} />
              </div>
              <h1 className="mt-4 text-4xl font-semibold tracking-[-0.045em] sm:text-6xl">
                {c.product_name}
              </h1>
              <p className="mt-4 text-sm text-muted-foreground">
                {c.product_sku} · {c.node_name} ({c.node_code}) · {c.supplier_name}
              </p>
            </div>
            <LoadingButton pending={runMut.isPending} onClick={() => runMut.mutate()}>
              <Play className="h-4 w-4" />
              {runMut.isPending ? "Investigating…" : "Run AI Investigation"}
            </LoadingButton>
          </header>

          {tools.length > 0 ? (
            <section>
              <div className="mb-4 flex items-end justify-between">
                <div>
                  <p className="eyebrow">Evidence snapshot</p>
                  <h2 className="mt-2 text-2xl font-semibold">What the agent observed</h2>
                </div>
                <span className="hidden text-xs text-muted-foreground sm:block">
                  Live operational sources
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <EvidenceCard
                  label="Current inventory"
                  value={`${String(inv.on_hand ?? "—")} units`}
                  detail={`${String(inv.reserved ?? 0)} reserved`}
                  state="positive"
                />
                <EvidenceCard
                  label="Forecast demand"
                  value={`${String(fc.quantity ?? "—")} units`}
                  detail={`${String(fc.horizon_days ?? "—")}-day horizon`}
                />
                <EvidenceCard
                  label="Open purchase orders"
                  value={`${String(pos.total_inbound ?? "—")} units`}
                  detail="Inbound coverage"
                  state="positive"
                />
                <EvidenceCard
                  label="Supplier constraints"
                  value={`MOQ ${String(sup.moq ?? "—")}`}
                  detail={`${String(sup.lead_time_days ?? "—")} day lead time`}
                />
                <EvidenceCard
                  label="Available budget"
                  value={bud.remaining != null ? `$${Number(bud.remaining).toLocaleString()}` : "—"}
                  detail={`${String(bud.currency ?? "USD")} remaining`}
                  state="positive"
                />
                <EvidenceCard
                  label="Storage capacity"
                  value={`${String(st.additional_units_available ?? "—")} units`}
                  detail="Additional capacity"
                  state={
                    c.original_recommended_qty > Number(st.additional_units_available ?? Infinity)
                      ? "warning"
                      : "positive"
                  }
                />
              </div>
            </section>
          ) : (
            <EmptyState
              title="Investigation not started"
              description="Run the AI investigation to retrieve inventory, demand, open PO, supplier, budget, storage, and policy evidence."
              action={
                <button className="button-secondary" onClick={() => runMut.mutate()}>
                  <Bot className="h-4 w-4" /> Start investigation
                </button>
              }
            />
          )}

          {decision && (
            <>
              <DecisionPanel decision={decision} original={c.original_recommended_qty} />
              <section className="grid gap-4 lg:grid-cols-[1fr_.8fr]">
                <div className="panel p-5 sm:p-6">
                  <p className="eyebrow">Why ProcureAI changed the decision</p>
                  <p className="mt-4 text-base leading-7">{decision.explanation}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {decision.reason_codes.map((code) => (
                      <span
                        key={code}
                        className="border border-border bg-muted/50 px-2.5 py-1.5 font-mono text-[10px] text-muted-foreground"
                      >
                        {code}
                      </span>
                    ))}
                  </div>
                  {decision.policy_citations.length > 0 && (
                    <div className="mt-5 flex flex-wrap gap-2">
                      {decision.policy_citations.map((citation) => (
                        <SourceReference key={citation} title={citation} />
                      ))}
                    </div>
                  )}
                </div>
                <div className="panel p-5 sm:p-6">
                  <p className="eyebrow">Constraint analysis</p>
                  <div className="mt-3">
                    <ConstraintCard
                      label="MOQ satisfied"
                      satisfied={
                        decision.recommended_quantity === 0 ||
                        decision.recommended_quantity >= Number(sup.moq ?? 0)
                      }
                      detail={`Supplier minimum: ${String(sup.moq ?? "unknown")} units`}
                    />
                    <ConstraintCard
                      label="Budget satisfied"
                      satisfied={decision.financial_impact <= Number(bud.remaining ?? 0)}
                      detail={`Financial impact: $${decision.financial_impact.toLocaleString()}`}
                    />
                    <ConstraintCard
                      label="Storage satisfied"
                      satisfied={
                        decision.recommended_quantity <= Number(st.additional_units_available ?? 0)
                      }
                      detail={`${String(st.additional_units_available ?? "—")} units available`}
                    />
                    <ConstraintCard
                      label="Supplier capacity"
                      satisfied={
                        decision.recommended_quantity <= Number(sup.max_available ?? Infinity)
                      }
                      detail={`${String(sup.max_available ?? "Not reported")} units available`}
                    />
                  </div>
                </div>
              </section>
              {c.status === "awaiting_approval" && (
                <ApprovalPanel
                  decision={decision}
                  pending={approveMut.isPending || rejectMut.isPending || reMut.isPending}
                  onApprove={() => approveMut.mutate(decision.id)}
                  onReject={() => rejectMut.mutate(decision.id)}
                  onReanalyze={() => reMut.mutate(decision.id)}
                />
              )}
            </>
          )}

          {tools.length > 0 && <AgentTimeline tools={tools} />}
          <ValidationResult validations={validations} />
          {c.current_po_number && (
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border py-5">
              <span className="text-sm text-muted-foreground">
                Resulting purchase order{" "}
                <strong className="text-foreground">{c.current_po_number}</strong>
              </span>
              <Link href="/purchase-orders" className="button-secondary">
                <Database className="h-4 w-4" /> View purchase orders
              </Link>
            </div>
          )}
          {decision && c.status !== "awaiting_approval" && (
            <div className="flex justify-end">
              <button
                className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground"
                onClick={() => reMut.mutate(decision.id)}
              >
                <RotateCcw className="h-3.5 w-3.5" /> Run a fresh analysis
              </button>
            </div>
          )}
        </PageReveal>
      )}
    </AuthGate>
  );
}
