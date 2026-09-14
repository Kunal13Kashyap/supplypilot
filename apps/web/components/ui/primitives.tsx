"use client";

import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export function PageReveal({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerGrid({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: reduced ? 0 : 0.045 } } }}
    >
      {children}
    </motion.div>
  );
}

export function RevealItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
      transition={{ duration: 0.24 }}
    >
      {children}
    </motion.div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("skeleton", className)} />;
}

export function PageSkeleton() {
  return (
    <div className="page-container space-y-8" aria-label="Loading page">
      <div className="space-y-3">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-12 w-2/3 max-w-xl" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-36" />
        ))}
      </div>
      <Skeleton className="h-72" />
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="panel flex min-h-60 flex-col items-center justify-center px-6 text-center">
      <span className="mb-4 grid h-10 w-10 place-items-center rounded-full bg-muted">
        <Inbox className="h-4 w-4" />
      </span>
      <h3 className="font-medium">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="panel flex min-h-52 flex-col items-center justify-center px-6 text-center">
      <AlertCircle className="mb-3 h-5 w-5 text-destructive" />
      <h3 className="font-medium">Unable to load this view</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>
      {retry && (
        <button className="button-secondary mt-5" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function LoadingButton({
  pending,
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { pending?: boolean }) {
  return (
    <button
      className={cn("button-primary", className)}
      disabled={pending || props.disabled}
      {...props}
    >
      {pending && <LoaderCircle className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}
