"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  Database,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Decision, ToolCall, Validation } from "@/types";
import { DecisionBadge, RiskBadge, StatusBadge } from "./badges";

export function MetricCard({
  label,
  value,
  detail,
  trend,
  attention,
}: {
  label: string;
  value: string | number;
  detail?: string;
  trend?: "up" | "down";
  attention?: boolean;
}) {
  return (
    <div className={cn("panel min-h-36 p-5", attention && "border-amber-400/50")}>
      <div className="flex items-start justify-between gap-3">
        <span className="eyebrow">{label}</span>
        {trend === "up" && <ArrowUpRight className="h-4 w-4 text-primary" />}
        {trend === "down" && <ArrowDownRight className="h-4 w-4 text-muted-foreground" />}
      </div>
      <div className="mt-7 text-4xl font-semibold tracking-[-0.04em] tabular-nums">{value}</div>
      {detail && <p className="mt-2 text-xs text-muted-foreground">{detail}</p>}
    </div>
  );
}

export function EvidenceCard({
  label,
  value,
  detail,
  state = "neutral",
}: {
  label: string;
  value: React.ReactNode;
  detail?: string;
  state?: "neutral" | "positive" | "warning";
}) {
  return (
    <div className="panel group min-h-36 p-5 transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-center justify-between">
        <span className="eyebrow">{label}</span>
        <span
          className={cn(
            "h-2 w-2 rounded-full bg-border",
            state === "positive" && "bg-primary",
            state === "warning" && "bg-amber-500",
          )}
        />
      </div>
      <div className="mt-7 text-2xl font-semibold tracking-tight">{value}</div>
      {detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}
    </div>
  );
}

export function ConstraintCard({
  label,
  satisfied,
  detail,
}: {
  label: string;
  satisfied: boolean;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-3 border-b border-border py-3 last:border-0">
      <span
        className={cn(
          "mt-0.5 grid h-5 w-5 place-items-center rounded-full",
          satisfied ? "bg-primary/10 text-primary" : "bg-red-50 text-destructive",
        )}
      >
        {satisfied ? <Check className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
      </span>
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

export function ToolExecution({ tool, index }: { tool: ToolCall; index: number }) {
  const [open, setOpen] = useState(false);
  const reduced = useReducedMotion();
  return (
    <motion.li
      initial={reduced ? false : { opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: reduced ? 0 : Math.min(index * 0.035, 0.3) }}
      className="relative pl-9"
    >
      <span className="absolute left-0 top-1 grid h-6 w-6 place-items-center rounded-full border border-primary/20 bg-primary/10 text-primary">
        {tool.status === "succeeded" ? (
          <Check className="h-3.5 w-3.5" />
        ) : (
          <CircleDashed className="h-3.5 w-3.5 animate-spin" />
        )}
      </span>
      <button
        className="group flex w-full items-start justify-between gap-4 border-b border-border pb-4 text-left"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span>
          <span className="block text-sm font-medium">{tool.summary || tool.tool_name}</span>
          <span className="mt-1 block font-mono text-[11px] text-muted-foreground">
            {tool.tool_name}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
          {tool.duration_ms ?? 0} ms
          <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
        </span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mb-4 grid gap-3 bg-muted/55 p-3 text-xs sm:grid-cols-2">
              <div>
                <div className="eyebrow mb-1">Input</div>
                <pre className="whitespace-pre-wrap break-all text-muted-foreground">
                  {JSON.stringify(tool.input_json, null, 2)}
                </pre>
              </div>
              <div>
                <div className="eyebrow mb-1">Evidence returned</div>
                <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-all text-muted-foreground">
                  {JSON.stringify(tool.output_json, null, 2)}
                </pre>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.li>
  );
}

export function AgentTimeline({ tools }: { tools: ToolCall[] }) {
  return (
    <section className="panel p-5 sm:p-6">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <p className="eyebrow">Investigation</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Operational evidence trail</h2>
        </div>
        <span className="hidden text-xs text-muted-foreground sm:block">
          {tools.length} tools completed
        </span>
      </div>
      <ol className="space-y-4">
        {tools.map((tool, index) => (
          <ToolExecution key={tool.id} tool={tool} index={index} />
        ))}
      </ol>
    </section>
  );
}

export function DecisionPanel({ decision, original }: { decision: Decision; original: number }) {
  return (
    <section
      className="overflow-hidden bg-foreground text-background"
      style={{ borderRadius: "var(--radius)" }}
    >
      <div className="grid min-h-[390px] lg:grid-cols-[1.15fr_.85fr]">
        <div className="flex flex-col justify-between p-6 sm:p-9">
          <div>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-background/55">
              ProcureAI intelligence
            </p>
            <div className="mt-8 flex items-baseline gap-5">
              <span className="text-6xl font-semibold tracking-[-0.06em] sm:text-8xl">
                {original}
              </span>
              <span className="text-2xl text-background/35">→</span>
              <span className="text-6xl font-semibold tracking-[-0.06em] text-emerald-300 sm:text-8xl">
                {decision.recommended_quantity}
              </span>
            </div>
            <div className="mt-3 flex gap-10 text-[0.65rem] uppercase tracking-[0.16em] text-background/50">
              <span>Original</span>
              <span>AI recommended</span>
            </div>
          </div>
          <p className="mt-12 max-w-xl text-sm leading-6 text-background/70">
            {decision.explanation}
          </p>
        </div>
        <div className="flex flex-col justify-between border-t border-background/15 p-6 sm:p-9 lg:border-l lg:border-t-0">
          <div>
            <DecisionBadge value={decision.decision} inverse />
            <h2 className="mt-6 text-3xl font-semibold tracking-tight">
              {decision.decision} purchase
            </h2>
          </div>
          <dl className="mt-12 divide-y divide-background/15">
            <div className="flex justify-between py-3 text-sm">
              <dt className="text-background/55">Confidence</dt>
              <dd>{Math.round(decision.confidence * 100)}%</dd>
            </div>
            <div className="flex justify-between py-3 text-sm">
              <dt className="text-background/55">Risk</dt>
              <dd>{decision.risk_level}</dd>
            </div>
            <div className="flex justify-between py-3 text-sm">
              <dt className="text-background/55">Approval</dt>
              <dd>{decision.requires_approval ? "Required" : "Not required"}</dd>
            </div>
            <div className="flex justify-between py-3 text-sm">
              <dt className="text-background/55">Financial impact</dt>
              <dd>${decision.financial_impact.toLocaleString()}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  );
}

export function ApprovalPanel({
  decision,
  pending,
  onApprove,
  onReject,
  onReanalyze,
}: {
  decision: Decision;
  pending: boolean;
  onApprove: () => void;
  onReject: () => void;
  onReanalyze: () => void;
}) {
  return (
    <section className="panel overflow-hidden">
      <div className="grid lg:grid-cols-[1fr_auto]">
        <div className="p-6 sm:p-8">
          <p className="eyebrow">Human review required</p>
          <h2 className="mt-2 text-2xl font-semibold">Authorize procurement action</h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            Approving will {decision.action.toLowerCase().replaceAll("_", " ")} for{" "}
            {decision.recommended_quantity} units. The action is idempotent, audited, and validated
            against the resulting PO.
          </p>
        </div>
        <div className="flex flex-col justify-center gap-2 border-t border-border bg-muted/35 p-6 lg:min-w-64 lg:border-l lg:border-t-0">
          <button className="button-primary" disabled={pending} onClick={onApprove}>
            <ShieldCheck className="h-4 w-4" /> Approve & execute
          </button>
          <button className="button-secondary" disabled={pending} onClick={onReanalyze}>
            Request re-analysis
          </button>
          <button
            className="min-h-9 text-xs text-destructive disabled:opacity-50"
            disabled={pending}
            onClick={onReject}
          >
            Reject recommendation
          </button>
        </div>
      </div>
    </section>
  );
}

export function ValidationResult({ validations }: { validations: Validation[] }) {
  if (!validations.length) return null;
  const latest = validations[validations.length - 1];
  const recovered = validations.length > 1 && !validations[0].passed && latest.passed;
  return (
    <section className="panel overflow-hidden">
      <div
        className={cn(
          "flex flex-wrap items-center justify-between gap-4 border-b border-border p-5 sm:p-6",
          latest.passed ? "bg-primary/[0.06]" : "bg-red-50",
        )}
      >
        <div className="flex items-center gap-3">
          {latest.passed ? (
            <CheckCircle2 className="h-6 w-6 text-primary" />
          ) : (
            <XCircle className="h-6 w-6 text-destructive" />
          )}
          <div>
            <p className="eyebrow">Post-action validation</p>
            <h2 className="mt-1 text-xl font-semibold">
              {recovered
                ? "Recovery successful"
                : latest.passed
                  ? "Validated success"
                  : "Validation failed"}
            </h2>
          </div>
        </div>
        <StatusBadge
          value={
            recovered
              ? "RECOVERY SUCCESSFUL"
              : latest.passed
                ? "VALIDATED SUCCESS"
                : "RECOVERY REQUIRED"
          }
        />
      </div>
      <div className="grid sm:grid-cols-2">
        <div className="border-b border-border p-6 sm:border-b-0 sm:border-r">
          <p className="eyebrow">Expected</p>
          <p className="mt-4 text-4xl font-semibold tracking-tight">
            {String(latest.expected_json.quantity)}{" "}
            <span className="text-base font-normal text-muted-foreground">units</span>
          </p>
        </div>
        <div className="p-6">
          <p className="eyebrow">Actual</p>
          <p
            className={cn(
              "mt-4 text-4xl font-semibold tracking-tight",
              latest.passed ? "text-primary" : "text-destructive",
            )}
          >
            {String(latest.actual_json.quantity)}{" "}
            <span className="text-base font-normal text-muted-foreground">units</span>
          </p>
        </div>
      </div>
      {validations.length > 1 && (
        <div className="border-t border-border px-6 py-4 text-sm text-muted-foreground">
          Initial mismatch: expected {String(validations[0].expected_json.quantity)}, actual{" "}
          {String(validations[0].actual_json.quantity)}. Recovery modified and re-validated the
          purchase order.
        </div>
      )}
    </section>
  );
}

export function SourceReference({ title }: { title: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 border border-border bg-card px-2 py-1 text-xs text-muted-foreground">
      <Database className="h-3 w-3" />
      {title}
    </span>
  );
}
