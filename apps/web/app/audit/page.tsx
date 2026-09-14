"use client";

import { useQuery } from "@tanstack/react-query";
import { Check, FileClock } from "lucide-react";
import { AuthGate } from "@/components/auth-gate";
import { EmptyState, ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";

export default function AuditPage() {
  const q = useQuery({
    queryKey: ["audit"],
    queryFn: () =>
      api<
        {
          id: string;
          event_type: string;
          actor: string;
          created_at: string;
          case_id: string | null;
        }[]
      >("/api/audit"),
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
            <p className="eyebrow">Immutable operations history</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
              Audit logs
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
              Tool calls, decisions, approvals, actions, validation outcomes, and recovery steps in
              chronological order.
            </p>
          </header>
          {q.data.length === 0 ? (
            <EmptyState
              title="No audit events"
              description="Events appear when a case investigation begins."
            />
          ) : (
            <section className="panel p-5 sm:p-8">
              <ol className="relative border-l border-border">
                {q.data.map((event, index) => (
                  <li
                    key={event.id}
                    className="relative ml-7 border-b border-border py-5 first:pt-0 last:border-0 last:pb-0"
                  >
                    <span className="absolute -left-[2.2rem] top-5 grid h-6 w-6 place-items-center rounded-full border border-border bg-card first:top-0">
                      {index === 0 ? (
                        <FileClock className="h-3.5 w-3.5" />
                      ) : (
                        <Check className="h-3 w-3 text-primary" />
                      )}
                    </span>
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h2 className="text-sm font-semibold capitalize">
                        {event.event_type.replaceAll("_", " ")}
                      </h2>
                      <time className="font-mono text-[10px] text-muted-foreground">
                        {new Date(event.created_at).toLocaleString()}
                      </time>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Actor: {event.actor}
                      {event.case_id ? ` · Case ${event.case_id.slice(0, 8)}` : ""}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </PageReveal>
      )}
    </AuthGate>
  );
}
