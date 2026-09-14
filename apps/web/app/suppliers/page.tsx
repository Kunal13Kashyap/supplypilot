"use client";

import { useQuery } from "@tanstack/react-query";
import { Building2, ShieldCheck, TriangleAlert } from "lucide-react";
import { AuthGate } from "@/components/auth-gate";
import { StatusBadge } from "@/components/domain/badges";
import {
  ErrorState,
  PageReveal,
  PageSkeleton,
  RevealItem,
  StaggerGrid,
} from "@/components/ui/primitives";
import { api } from "@/lib/utils";

export default function SuppliersPage() {
  const q = useQuery({
    queryKey: ["suppliers"],
    queryFn: () =>
      api<{ code: string; name: string; reliability_score: number; status: string }[]>(
        "/api/suppliers",
      ),
  });
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
            <p className="eyebrow">Supply network</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
              Suppliers
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
              Monitor supplier reliability and operating status before purchasing actions are
              authorized.
            </p>
          </header>
          <StaggerGrid className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {q.data.map((supplier) => {
              const score = Math.round(supplier.reliability_score * 100);
              const healthy = score >= 85;
              return (
                <RevealItem key={supplier.code}>
                  <article className="panel min-h-64 p-6">
                    <div className="flex items-start justify-between">
                      <span className="grid h-10 w-10 place-items-center bg-muted">
                        <Building2 className="h-5 w-5" />
                      </span>
                      <StatusBadge value={supplier.status} />
                    </div>
                    <h2 className="mt-8 text-xl font-semibold">{supplier.name}</h2>
                    <p className="mt-1 font-mono text-xs text-muted-foreground">{supplier.code}</p>
                    <div className="mt-8 flex items-end justify-between border-t border-border pt-5">
                      <div>
                        <p className="eyebrow">Reliability</p>
                        <p className="mt-2 text-3xl font-semibold">{score}%</p>
                      </div>
                      {healthy ? (
                        <ShieldCheck className="h-5 w-5 text-primary" />
                      ) : (
                        <TriangleAlert className="h-5 w-5 text-amber-600" />
                      )}
                    </div>
                  </article>
                </RevealItem>
              );
            })}
          </StaggerGrid>
        </PageReveal>
      )}
    </AuthGate>
  );
}
