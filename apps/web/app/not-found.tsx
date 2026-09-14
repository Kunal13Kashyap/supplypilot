import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-center">
      <div>
        <p className="eyebrow">404 · Resource not found</p>
        <h1 className="mt-5 text-5xl font-semibold tracking-[-0.05em]">
          This operation is not available.
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-sm text-muted-foreground">
          The case, purchase order, or route may have moved.
        </p>
        <Link href="/" className="button-primary mt-8">
          Return to control center
        </Link>
      </div>
    </main>
  );
}
