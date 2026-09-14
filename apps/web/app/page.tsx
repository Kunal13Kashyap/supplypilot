"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bot, CircleAlert, Clock3, ShieldCheck } from "lucide-react";
import { AuthGate } from "@/components/auth-gate";
import { MetricCard } from "@/components/domain/operational";
import { StatusBadge } from "@/components/domain/badges";
import {
  ErrorState,
  PageReveal,
  PageSkeleton,
  RevealItem,
  StaggerGrid,
} from "@/components/ui/primitives";
import { api } from "@/lib/utils";
import type { DashboardStats } from "@/types";

const DecisionChart = dynamic(
  () => import("@/components/domain/dashboard-charts").then((mod) => mod.DecisionChart),
  { ssr: false },
);
const BudgetChart = dynamic(
  () => import("@/components/domain/dashboard-charts").then((mod) => mod.BudgetChart),
  { ssr: false },
);

export default function DashboardPage() {
  const q = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<DashboardStats>("/api/dashboard"),
  });

  return (
    <AuthGate>
      {q.isLoading && <PageSkeleton />}
      {q.isError && (
        <div className="page-container">
          <ErrorState message={(q.error as Error).message} retry={() => q.refetch()} />
        </div>
      )}
      {q.data && (
        <PageReveal className="page-container space-y-10">
          <section
            className="relative grid min-h-[380px] overflow-hidden bg-foreground text-background lg:grid-cols-[1.35fr_.65fr]"
            style={{ borderRadius: "calc(var(--radius) + 2px)" }}
          >
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 opacity-[0.08]"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 12% 18%, #3d8e68 0%, transparent 40%), radial-gradient(circle at 92% 80%, #f7f6f3 0%, transparent 34%)",
              }}
            />
            <div className="relative flex flex-col justify-between p-8 sm:p-10 lg:p-12">
              <div className="flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-background/55">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" /> Live operational
                intelligence
              </div>
              <div className="my-12 sm:my-14">
                <h1 className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.055em] sm:text-6xl xl:text-[5.75rem]">
                  ProcureAI
                  <br />
                  <span className="text-background/42">Intelligence.</span>
                </h1>
              </div>
              <p className="max-w-2xl text-[15px] leading-7 text-background/65">
                {q.data.pending_ai_decisions} purchasing cases are ready for constrained review.
                Every recommendation is investigated, authorized, executed, and validated against
                resulting state.
              </p>
            </div>
            <div className="relative flex flex-col justify-between border-t border-background/12 p-8 lg:border-l lg:border-t-0 lg:p-10">
              <div>
                <p className="text-[0.68rem] uppercase tracking-[0.18em] text-background/45">
                  Control loop
                </p>
                <div className="mt-6 space-y-3 text-sm">
                  {["Observe", "Reason", "Decide", "Act", "Validate", "Recover"].map(
                    (item, index) => (
                      <div
                        key={item}
                        className="flex items-center justify-between border-b border-background/12 pb-3"
                      >
                        <span>{item}</span>
                        <span className="font-mono text-xs text-background/35">0{index + 1}</span>
                      </div>
                    ),
                  )}
                </div>
              </div>
              <Link
                href="/cases"
                className="mt-10 inline-flex items-center justify-between border-t border-background/12 pt-5 text-sm transition-opacity hover:opacity-80"
              >
                Open case queue <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <StaggerGrid className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <RevealItem>
              <MetricCard
                label="Pending decisions"
                value={q.data.pending_ai_decisions}
                detail="Ready for AI investigation"
              />
            </RevealItem>
            <RevealItem>
              <MetricCard
                label="Approval required"
                value={q.data.awaiting_approval}
                detail="Human authorization gate"
                attention={q.data.awaiting_approval > 0}
              />
            </RevealItem>
            <RevealItem>
              <MetricCard
                label="Active investigations"
                value={q.data.active_investigations}
                detail="LangGraph runs in progress"
              />
            </RevealItem>
            <RevealItem>
              <MetricCard
                label="Validation failures"
                value={q.data.failed_validations}
                detail="Detected after execution"
                attention={q.data.failed_validations > 0}
              />
            </RevealItem>
            <RevealItem>
              <MetricCard
                label="Budget utilization"
                value={`${Math.round((q.data.budget_spent / (q.data.budget_amount || 1)) * 100)}%`}
                detail={`$${q.data.budget_spent.toLocaleString()} committed`}
              />
            </RevealItem>
            <RevealItem>
              <MetricCard
                label="Inventory risk"
                value={q.data.inventory_risk_skus}
                detail="SKUs below operating threshold"
              />
            </RevealItem>
          </StaggerGrid>

          <section className="grid gap-4 xl:grid-cols-[1.25fr_.75fr]">
            <div className="panel p-5 sm:p-7">
              <div className="mb-4">
                <p className="eyebrow">Decision mix</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                  Purchase recommendations by outcome
                </h2>
              </div>
              <DecisionChart data={q.data.recommendations_by_status} />
            </div>
            <div className="panel p-5 sm:p-7">
              <p className="eyebrow">Capital control</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">Budget utilization</h2>
              <BudgetChart amount={q.data.budget_amount} spent={q.data.budget_spent} />
              <div className="flex justify-between border-t border-border pt-4 text-xs text-muted-foreground">
                <span>Committed ${q.data.budget_spent.toLocaleString()}</span>
                <span>Total ${q.data.budget_amount.toLocaleString()}</span>
              </div>
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1fr_.7fr]">
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-border p-5 sm:px-7">
                <div>
                  <p className="eyebrow">Agent operations</p>
                  <h2 className="mt-1 text-xl font-semibold">Recent intelligence runs</h2>
                </div>
                <Link
                  href="/agent-runs"
                  className="text-xs font-medium text-muted-foreground hover:text-foreground"
                >
                  View all
                </Link>
              </div>
              {q.data.recent_runs.length === 0 ? (
                <div className="p-8 text-sm text-muted-foreground">
                  No runs yet. Start with PC-1001.
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {q.data.recent_runs.slice(0, 6).map((run) => (
                    <div key={run.id} className="flex items-center gap-4 px-5 py-4 sm:px-7">
                      <span className="grid h-9 w-9 place-items-center bg-muted">
                        <Bot className="h-4 w-4" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-mono text-xs">{run.id.slice(0, 8)}</p>
                        <p className="text-xs text-muted-foreground">
                          {run.stage.replaceAll("_", " ")}
                        </p>
                      </div>
                      <StatusBadge value={run.status} />
                      <span className="hidden text-xs text-muted-foreground sm:block">
                        {run.duration_ms ?? 0} ms
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="panel p-5 sm:p-7">
              <div className="flex items-center gap-2">
                <CircleAlert className="h-4 w-4 text-amber-600" />
                <p className="eyebrow">Needs attention</p>
              </div>
              <div className="mt-5 space-y-3">
                <Link href="/cases" className="flex items-start gap-3 border-b border-border pb-4">
                  <Clock3 className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <span>
                    <span className="block text-sm font-medium">
                      {q.data.pending_ai_decisions} cases await investigation
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Recommendations have not been validated.
                    </span>
                  </span>
                </Link>
                <Link href="/audit" className="flex items-start gap-3 border-b border-border pb-4">
                  <CircleAlert className="mt-0.5 h-4 w-4 text-amber-600" />
                  <span>
                    <span className="block text-sm font-medium">
                      {q.data.failed_validations} validation exception
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Review mismatch and recovery evidence.
                    </span>
                  </span>
                </Link>
                <div className="flex items-start gap-3">
                  <ShieldCheck className="mt-0.5 h-4 w-4 text-primary" />
                  <span>
                    <span className="block text-sm font-medium">Controls operational</span>
                    <span className="text-xs text-muted-foreground">
                      Budget, storage and MOQ gates are active.
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </section>
        </PageReveal>
      )}
    </AuthGate>
  );
}
