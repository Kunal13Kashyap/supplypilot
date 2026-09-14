"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Filter, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { AuthGate } from "@/components/auth-gate";
import { DecisionBadge, RiskBadge, StatusBadge } from "@/components/domain/badges";
import { EmptyState, ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";
import type { CaseDetail, CaseListItem } from "@/types";

type CaseRow = CaseListItem & { detail?: CaseDetail };

export default function CasesPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const q = useQuery({
    queryKey: ["cases", "enriched"],
    queryFn: async () => {
      const rows = await api<CaseListItem[]>("/api/cases");
      const details = await Promise.all(
        rows.map((row) => api<CaseDetail>(`/api/cases/${row.id}`).catch(() => undefined)),
      );
      return rows.map((row, index) => ({ ...row, detail: details[index] })) as CaseRow[];
    },
  });
  const rows = useMemo(() => {
    const term = search.toLowerCase().trim();
    return (q.data ?? []).filter((row) => {
      const matchesSearch =
        !term ||
        [row.case_number, row.product_sku, row.product_name, row.node_code]
          .join(" ")
          .toLowerCase()
          .includes(term);
      return matchesSearch && (status === "all" || row.status === status);
    });
  }, [q.data, search, status]);

  return (
    <AuthGate>
      {q.isLoading && <PageSkeleton />}
      {q.isError && (
        <div className="page-container">
          <ErrorState message={(q.error as Error).message} retry={() => q.refetch()} />
        </div>
      )}
      {q.data && (
        <PageReveal className="page-container space-y-8">
          <header className="grid gap-6 border-b border-border pb-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">Decision workspace</p>
              <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
                Purchasing cases
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
                Review system recommendations against inventory, demand, supplier, budget, and
                storage evidence.
              </p>
            </div>
            <Link
              href={
                q.data.find((row) => row.case_number === "PC-1001")
                  ? `/cases/${q.data.find((row) => row.case_number === "PC-1001")?.id}`
                  : "#"
              }
              className="button-primary"
            >
              Open golden case <ArrowUpRight className="h-4 w-4" />
            </Link>
          </header>

          <section className="flex flex-col gap-3 sm:flex-row">
            <label className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                className="input-base pl-10"
                placeholder="Search case, SKU, product or node"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <label className="relative sm:w-52">
              <Filter className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <select
                className="input-base appearance-none pl-10"
                value={status}
                onChange={(event) => setStatus(event.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="open">Open</option>
                <option value="awaiting_approval">Awaiting approval</option>
                <option value="validated">Validated</option>
                <option value="escalated">Escalated</option>
              </select>
            </label>
          </section>

          {rows.length === 0 ? (
            <EmptyState title="No cases match" description="Adjust your search or status filter." />
          ) : (
            <div className="panel overflow-x-auto">
              <table className="w-full min-w-[1040px] text-left">
                <thead className="border-b border-border bg-muted/35">
                  <tr className="eyebrow">
                    <th className="px-5 py-4">Case / product</th>
                    <th className="px-4 py-4">Supplier / node</th>
                    <th className="px-4 py-4">System rec.</th>
                    <th className="px-4 py-4">AI decision</th>
                    <th className="px-4 py-4">Confidence</th>
                    <th className="px-4 py-4">Impact</th>
                    <th className="px-4 py-4">Risk</th>
                    <th className="px-5 py-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rows.map((row) => {
                    const decision = row.detail?.latest_run?.decision;
                    return (
                      <tr
                        key={row.id}
                        className="group text-sm transition-colors hover:bg-muted/30"
                      >
                        <td className="px-5 py-5">
                          <Link className="font-semibold hover:underline" href={`/cases/${row.id}`}>
                            {row.case_number}
                          </Link>
                          <div className="mt-1 text-xs text-muted-foreground">
                            {row.product_sku} · {row.product_name}
                          </div>
                        </td>
                        <td className="px-4 py-5">
                          <div>{row.detail?.supplier_name ?? "—"}</div>
                          <div className="mt-1 text-xs text-muted-foreground">{row.node_code}</div>
                        </td>
                        <td className="px-4 py-5 font-medium tabular-nums">
                          {row.original_recommended_qty} units
                        </td>
                        <td className="px-4 py-5">
                          {decision ? (
                            <DecisionBadge value={decision.decision} />
                          ) : (
                            <span className="text-xs text-muted-foreground">Not investigated</span>
                          )}
                        </td>
                        <td className="px-4 py-5 tabular-nums">
                          {decision ? `${Math.round(decision.confidence * 100)}%` : "—"}
                        </td>
                        <td className="px-4 py-5 tabular-nums">
                          {decision ? `$${decision.financial_impact.toLocaleString()}` : "—"}
                        </td>
                        <td className="px-4 py-5">
                          <RiskBadge value={row.risk_level} />
                        </td>
                        <td className="px-5 py-5 text-right">
                          <StatusBadge value={row.status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Showing {rows.length} of {q.data.length} purchasing cases · Updated from FastAPI
          </p>
        </PageReveal>
      )}
    </AuthGate>
  );
}
