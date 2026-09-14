"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/primitives";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <main className="page-container">
      <ErrorState message="The operations console encountered an unexpected error." retry={reset} />
    </main>
  );
}
