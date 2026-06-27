import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names, resolving conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a number with thousands separators. */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/** Compact number formatting (1.2k, 3.4M). */
export function formatCompact(n: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;
export type Severity = (typeof SEVERITY_ORDER)[number];

/** Tailwind text/bg classes for a severity level. */
export function severityClasses(sev: string): { text: string; bg: string; border: string; dot: string } {
  const map: Record<string, { text: string; bg: string; border: string; dot: string }> = {
    critical: { text: "text-severity-critical", bg: "bg-severity-critical/10", border: "border-severity-critical/30", dot: "bg-severity-critical" },
    high: { text: "text-severity-high", bg: "bg-severity-high/10", border: "border-severity-high/30", dot: "bg-severity-high" },
    medium: { text: "text-severity-medium", bg: "bg-severity-medium/10", border: "border-severity-medium/30", dot: "bg-severity-medium" },
    low: { text: "text-severity-low", bg: "bg-severity-low/10", border: "border-severity-low/30", dot: "bg-severity-low" },
    info: { text: "text-severity-info", bg: "bg-severity-info/10", border: "border-severity-info/30", dot: "bg-severity-info" },
  };
  return map[sev] ?? map.info;
}
