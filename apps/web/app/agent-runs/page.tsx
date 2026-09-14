"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bot, Clock3, Workflow } from "lucide-react";
import { AuthGate } from "@/components/auth-gate";
import { StatusBadge } from "@/components/domain/badges";
import { EmptyState, ErrorState, PageReveal, PageSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/utils";

export default function AgentRunsPage() {
  const q = useQuery({
    queryKey: ["runs"],
    queryFn: () =>
      api<
        {
          id: string;
          case_id: string;
          case_number: string;
          status: string;
          stage: string;
          duration_ms: number | null;
        }[]
      >("/api/agent-runs"),
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
            <p className="eyebrow">Agent observability</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
              Agent runs
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
              Every investigation and execution stage, measured and linked to its purchasing case.
            </p>
          </header>
          {q.data.length === 0 ? (
            <EmptyState
              title="No agent runs"
              description="Run a purchasing case investigation to create the first observable agent run."
            />
          ) : (
            <div className="panel overflow-x-auto">
              <table className="w-full min-w-[850px] text-left text-sm">
                <thead className="border-b border-border bg-muted/35">
                  <tr className="eyebrow">
                    <th className="px-5 py-4">Run ID</th>
                    <th>Case</th>
                    <th>Current stage</th>
                    <th>Duration</th>
                    <th className="px-5 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {q.data.map((run) => (
                    <tr key={run.id} className="hover:bg-muted/30">
                      <td className="px-5 py-5">
                        <span className="inline-flex items-center gap-2 font-mono text-xs">
                          <Bot className="h-4 w-4 text-muted-foreground" />
                          {run.id.slice(0, 8)}
                        </span>
                      </td>
                      <td>
                        <Link
                          className="font-semibold hover:underline"
                          href={`/cases/${run.case_id}`}
                        >
                          {run.case_number}
                        </Link>
                      </td>
                      <td>
                        <span className="inline-flex items-center gap-2">
                          <Workflow className="h-4 w-4 text-muted-foreground" />
                          {run.stage.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td>
                        <span className="inline-flex items-center gap-2 text-muted-foreground">
                          <Clock3 className="h-3.5 w-3.5" />
                          {run.duration_ms ?? "—"} ms
                        </span>
                      </td>
                      <td className="px-5 text-right">
                        <StatusBadge value={run.status} />
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
