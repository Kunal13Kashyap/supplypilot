"use client";

import { useQuery } from "@tanstack/react-query";
import { Boxes, Search, TriangleAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { AuthGate } from "@/components/auth-gate";
import { ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";

export default function InventoryPage() {
  const [search, setSearch] = useState("");
  const q = useQuery({
    queryKey: ["inventory"],
    queryFn: () =>
      api<{ sku: string; product: string; node: string; on_hand: number; reserved: number }[]>(
        "/api/inventory",
      ),
  });
  const rows = useMemo(
    () =>
      (q.data ?? []).filter((row) =>
        `${row.sku} ${row.product} ${row.node}`.toLowerCase().includes(search.toLowerCase()),
      ),
    [q.data, search],
  );
  const available = (q.data ?? []).reduce(
    (sum, row) => sum + Math.max(row.on_hand - row.reserved, 0),
    0,
  );
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
            <p className="eyebrow">Network position</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
              Inventory
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
              Current on-hand and reserved stock by fulfillment node.
            </p>
          </header>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel p-5">
              <Boxes className="h-4 w-4 text-muted-foreground" />
              <p className="eyebrow mt-5">Tracked SKUs</p>
              <p className="mt-2 text-4xl font-semibold">{q.data.length}</p>
            </div>
            <div className="panel p-5">
              <p className="eyebrow">Available units</p>
              <p className="mt-8 text-4xl font-semibold">{available.toLocaleString()}</p>
            </div>
            <div className="panel p-5">
              <TriangleAlert className="h-4 w-4 text-amber-600" />
              <p className="eyebrow mt-5">Low stock</p>
              <p className="mt-2 text-4xl font-semibold">
                {q.data.filter((r) => r.on_hand - r.reserved < 100).length}
              </p>
            </div>
          </div>
          <label className="relative block max-w-xl">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <input
              className="input-base pl-10"
              placeholder="Search SKU, product, or node"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <div className="panel overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-border bg-muted/35">
                <tr className="eyebrow">
                  <th className="px-5 py-4">SKU</th>
                  <th>Product</th>
                  <th>Node</th>
                  <th>On hand</th>
                  <th>Reserved</th>
                  <th className="px-5 text-right">Available</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rows.map((row) => {
                  const net = row.on_hand - row.reserved;
                  return (
                    <tr key={`${row.sku}-${row.node}`} className="hover:bg-muted/30">
                      <td className="px-5 py-5 font-mono text-xs">{row.sku}</td>
                      <td className="font-medium">{row.product}</td>
                      <td>{row.node}</td>
                      <td>{row.on_hand}</td>
                      <td className="text-muted-foreground">{row.reserved}</td>
                      <td className="px-5 text-right">
                        <span className={net < 100 ? "text-amber-700" : "text-primary"}>
                          {net} units
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </PageReveal>
      )}
    </AuthGate>
  );
}
