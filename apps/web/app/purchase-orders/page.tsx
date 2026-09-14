"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileText, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { AuthGate } from "@/components/auth-gate";
import { StatusBadge } from "@/components/domain/badges";
import { EmptyState, ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";

type PurchaseOrderRow = {
  id: string;
  po_number: string;
  status: string;
  supplier: string;
  quantity: number;
  created_at: string;
};

export default function PurchaseOrdersPage() {
  const [search, setSearch] = useState("");
  const q = useQuery({
    queryKey: ["pos"],
    queryFn: () => api<PurchaseOrderRow[]>("/api/purchase-orders"),
  });
  const rows = useMemo(() => {
    const term = search.toLowerCase();
    return (q.data ?? []).filter((row) =>
      `${row.po_number} ${row.supplier}`.toLowerCase().includes(term),
    );
  }, [q.data, search]);
  return (
    <AuthGate>
      {q.isLoading && <PageSkeleton />}
      {q.isError && (
        <div className="page-container">
          <ErrorState message={(q.error as Error).message} />
        </div>
      )}
      {q.data && (
        <PageReveal className="page-container space-y-8">
          <header className="border-b border-border pb-8">
            <p className="eyebrow">Execution ledger</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
              Purchase orders
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
              Created and modified procurement actions with resulting quantities and
              validation-ready state.
            </p>
          </header>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel p-5">
              <p className="eyebrow">Total orders</p>
              <p className="mt-5 text-4xl font-semibold">{q.data.length}</p>
            </div>
            <div className="panel p-5">
              <p className="eyebrow">Open quantity</p>
              <p className="mt-5 text-4xl font-semibold">
                {q.data.filter((p) => p.status === "open").reduce((sum, p) => sum + p.quantity, 0)}
              </p>
            </div>
            <div className="panel p-5">
              <p className="eyebrow">Active suppliers</p>
              <p className="mt-5 text-4xl font-semibold">
                {new Set(q.data.map((p) => p.supplier)).size}
              </p>
            </div>
          </div>
          <label className="relative block max-w-xl">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <input
              className="input-base pl-10"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search PO number or supplier"
            />
          </label>
          {rows.length === 0 ? (
            <EmptyState title="No purchase orders found" description="Try a different search." />
          ) : (
            <div className="panel overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b border-border bg-muted/35">
                  <tr className="eyebrow">
                    <th className="px-5 py-4">Purchase order</th>
                    <th>Supplier</th>
                    <th>Quantity</th>
                    <th>Created</th>
                    <th className="px-5 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rows.map((po) => (
                    <tr key={po.id} className="transition-colors hover:bg-muted/30">
                      <td className="px-5 py-5">
                        <Link
                          href={`/purchase-orders/${po.id}`}
                          className="inline-flex items-center gap-2 font-semibold hover:underline"
                        >
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          {po.po_number}
                        </Link>
                      </td>
                      <td>{po.supplier}</td>
                      <td className="font-medium tabular-nums">{po.quantity} units</td>
                      <td className="text-xs text-muted-foreground">
                        {new Date(po.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 text-right">
                        <StatusBadge value={po.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </PageReveal>
      )}
    </AuthGate>
  );
}
