"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen, Database } from "lucide-react";
import { AuthGate } from "@/components/auth-gate";
import {
  ErrorState,
  PageReveal,
  PageSkeleton,
  RevealItem,
  StaggerGrid,
} from "@/components/ui/primitives";
import { api } from "@/lib/utils";

export default function KnowledgePage() {
  const q = useQuery({
    queryKey: ["knowledge"],
    queryFn: () =>
      api<{ id: string; title: string; source: string; body: string }[]>("/api/knowledge"),
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
          <header className="grid gap-6 border-b border-border pb-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">Policy retrieval</p>
              <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
                Knowledge base
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
                Procurement SOPs and policies retrieved through PostgreSQL pgvector and cited by
                agent decisions.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Database className="h-4 w-4" />
              {q.data.length} indexed documents
            </div>
          </header>
          <StaggerGrid className="grid gap-4 lg:grid-cols-2">
            {q.data.map((document) => (
              <RevealItem key={document.id}>
                <article className="panel min-h-64 p-6 sm:p-7">
                  <div className="flex items-start justify-between">
                    <BookOpen className="h-5 w-5 text-primary" />
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {document.source}
                    </span>
                  </div>
                  <h2 className="mt-8 text-2xl font-semibold tracking-tight">{document.title}</h2>
                  <p className="mt-4 text-sm leading-6 text-muted-foreground">{document.body}</p>
                </article>
              </RevealItem>
            ))}
          </StaggerGrid>
        </PageReveal>
      )}
    </AuthGate>
  );
}
