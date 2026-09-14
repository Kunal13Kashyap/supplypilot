import { cn } from "@/lib/utils";

export function DecisionBadge({ value, inverse = false }: { value: string; inverse?: boolean }) {
  const map: Record<string, string> = {
    ACCEPT: "border-emerald-600/20 bg-emerald-600/10 text-emerald-800 dark:text-emerald-300",
    MODIFY: "border-amber-600/20 bg-amber-500/10 text-amber-800 dark:text-amber-300",
    REJECT: "border-red-600/20 bg-red-500/10 text-red-800 dark:text-red-300",
    INVESTIGATE: "border-sky-600/20 bg-sky-500/10 text-sky-800 dark:text-sky-300",
  };
  return (
    <span
      className={cn(
        "inline-flex border px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.12em]",
        inverse
          ? "border-background/20 bg-background/10 text-background"
          : (map[value] ?? "border-border bg-muted"),
      )}
    >
      {value}
    </span>
  );
}

export function RiskBadge({ value }: { value: string }) {
  const map: Record<string, string> = {
    LOW: "text-emerald-700 before:bg-emerald-600",
    MEDIUM: "text-amber-700 before:bg-amber-500",
    HIGH: "text-red-700 before:bg-red-600",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide before:h-1.5 before:w-1.5 before:rounded-full",
        map[value] ?? "text-muted-foreground before:bg-border",
      )}
    >
      {value}
    </span>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase().replaceAll(" ", "_");
  const positive = [
    "validated",
    "completed",
    "open",
    "validated_success",
    "recovery_successful",
  ].includes(normalized);
  const alert = ["failed", "escalated", "validation_failed", "recovery_required"].includes(
    normalized,
  );
  return (
    <span
      className={cn(
        "inline-flex border px-2 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.12em]",
        positive && "border-primary/20 bg-primary/10 text-primary",
        alert && "border-red-500/20 bg-red-500/10 text-destructive",
        !positive && !alert && "border-border bg-muted text-muted-foreground",
      )}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}

export const StatusPill = StatusBadge;
