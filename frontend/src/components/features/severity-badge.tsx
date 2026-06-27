import { cn, severityClasses } from "@/lib/utils";

export function SeverityBadge({ severity, className }: { severity: string; className?: string }) {
  const c = severityClasses(severity);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
        c.bg,
        c.text,
        c.border,
        className
      )}
    >
      <span className={cn("size-1.5 rounded-full", c.dot)} />
      {severity}
    </span>
  );
}
