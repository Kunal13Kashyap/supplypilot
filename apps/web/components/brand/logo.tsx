import { cn } from "@/lib/utils";

type LogoProps = {
  className?: string;
  markClassName?: string;
  showWordmark?: boolean;
  inverse?: boolean;
};

/** Defined ProcureAI mark: interlocking supply node + decision arc. */
export function ProcureMark({
  className,
  inverse = false,
}: {
  className?: string;
  inverse?: boolean;
}) {
  const ink = inverse ? "hsl(var(--background))" : "hsl(var(--foreground))";
  const accent = "hsl(var(--primary))";

  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("h-8 w-8 shrink-0", className)}
      aria-hidden
    >
      <rect
        x="1.5"
        y="1.5"
        width="37"
        height="37"
        rx="9"
        stroke={ink}
        strokeWidth="1.5"
        fill={inverse ? "transparent" : "hsl(var(--card))"}
      />
      {/* Supply chain path */}
      <path
        d="M11 26.5C11 20.5 15.2 17 20 17C24.8 17 29 20.5 29 26.5"
        stroke={ink}
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* Decision node */}
      <circle cx="20" cy="13.5" r="3.25" fill={accent} />
      {/* Flow nodes */}
      <circle cx="11" cy="26.5" r="2.1" fill={ink} />
      <circle cx="29" cy="26.5" r="2.1" fill={ink} />
      {/* Subtle link */}
      <path
        d="M20 16.75V21.5"
        stroke={ink}
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.55"
      />
    </svg>
  );
}

export function ProcureLogo({
  className,
  markClassName,
  showWordmark = true,
  inverse = false,
}: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <ProcureMark className={markClassName} inverse={inverse} />
      {showWordmark && (
        <span className="leading-none">
          <span
            className={cn(
              "block text-[15px] font-semibold tracking-[-0.03em]",
              inverse ? "text-background" : "text-foreground",
            )}
          >
            ProcureAI
          </span>
          <span
            className={cn(
              "mt-1 block text-[9px] font-medium uppercase tracking-[0.18em]",
              inverse ? "text-background/55" : "text-muted-foreground",
            )}
          >
            Intelligence
          </span>
        </span>
      )}
    </span>
  );
}
