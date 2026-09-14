"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="grid min-h-screen place-items-center bg-white px-6 font-sans text-zinc-950">
        <main className="max-w-lg text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
            ProcureAI · System exception
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight">
            The operations console could not recover.
          </h1>
          <p className="mt-4 text-sm leading-6 text-zinc-600">
            No purchasing action was submitted. Retry the interface or review API readiness.
          </p>
          <button
            className="mt-7 bg-zinc-950 px-5 py-3 text-sm font-medium text-white"
            onClick={reset}
          >
            Retry ProcureAI
          </button>
        </main>
      </body>
    </html>
  );
}
