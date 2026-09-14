"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Building2, CheckCircle2, FileCheck2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AuthGate } from "@/components/auth-gate";
import { StatusBadge } from "@/components/domain/badges";
import { ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";

type PODetail = {
  id: string;
  po_number: string;
  status: string;
  supplier: string;
  lines: { sku: string; name: string; quantity: number; unit_price: number }[];
};

export default function PurchaseOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const query = useQuery({
    queryKey: ["purchase-order", params.id],
    queryFn: () => api<PODetail>(`/api/purchase-orders/${params.id}`),
  });
  const total =
    query.data?.lines.reduce((sum, line) => sum + line.quantity * line.unit_price, 0) ?? 0;

  return (
    <AuthGate>
      {query.isLoading && <PageSkeleton />}
      {query.isError && (
        <div className="page-container">
          <ErrorState message={(query.error as Error).message} />
        </div>
      )}
      {query.data && (
        <PageReveal className="page-container space-y-8">
          <Link
            href="/purchase-orders"
            className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Purchase orders
          </Link>
          <header className="grid gap-6 border-b border-border pb-8 sm:grid-cols-[1fr_auto] sm:items-end">
            <div>
              <p className="eyebrow">Purchase order</p>
              <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em]">
                {query.data.po_number}
              </h1>
              <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-4 w-4" />
                {query.data.supplier}
              </p>
            </div>
            <StatusBadge value={query.data.status} />
          </header>
          <section className="panel overflow-hidden">
            <div className="border-b border-border p-5">
              <p className="eyebrow">Line items</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead className="border-b border-border bg-muted/35">
                  <tr className="eyebrow">
                    <th className="px-5 py-4">Item</th>
                    <th>Quantity</th>
                    <th>Unit price</th>
                    <th className="px-5 text-right">Line total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {query.data.lines.map((line) => (
                    <tr key={line.sku}>
                      <td className="px-5 py-5 font-medium">
                        {line.name}
                        <span className="ml-2 font-mono text-xs text-muted-foreground">
                          {line.sku}
                        </span>
                      </td>
                      <td>{line.quantity}</td>
                      <td>${line.unit_price.toFixed(2)}</td>
                      <td className="px-5 text-right font-medium">
                        ${(line.quantity * line.unit_price).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="border-t border-border bg-muted/25">
                  <tr>
                    <td colSpan={3} className="px-5 py-5 text-right text-sm text-muted-foreground">
                      Order total
                    </td>
                    <td className="px-5 text-right text-xl font-semibold">
                      ${total.toLocaleString()}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>
          <section className="grid gap-4 sm:grid-cols-2">
            <div className="panel p-6">
              <FileCheck2 className="h-5 w-5 text-primary" />
              <p className="mt-5 font-medium">Execution recorded</p>
              <p className="mt-1 text-sm text-muted-foreground">
                The purchase-order write is protected by an idempotency key.
              </p>
            </div>
            <div className="panel p-6">
              <CheckCircle2 className="h-5 w-5 text-primary" />
              <p className="mt-5 font-medium">Validation eligible</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Resulting quantity can be checked against expected action state.
              </p>
            </div>
          </section>
        </PageReveal>
      )}
    </AuthGate>
  );
}
