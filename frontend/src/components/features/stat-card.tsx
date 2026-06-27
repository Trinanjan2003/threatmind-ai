"use client";

import { motion } from "framer-motion";
import { type LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn, formatCompact } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  delta,
  accent = "primary",
  index = 0,
}: {
  label: string;
  value: number | string;
  icon: LucideIcon;
  delta?: number;
  accent?: "primary" | "critical" | "high" | "success";
  index?: number;
}) {
  const accentMap = {
    primary: "from-primary/15 text-primary",
    critical: "from-severity-critical/15 text-severity-critical",
    high: "from-severity-high/15 text-severity-high",
    success: "from-emerald-500/15 text-emerald-500",
  };
  const up = (delta ?? 0) >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06 }}
    >
      <Card glass className="relative overflow-hidden p-5">
        <div className={cn("absolute -right-6 -top-6 size-24 rounded-full bg-gradient-to-br to-transparent blur-2xl", accentMap[accent])} />
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight">
              {typeof value === "number" ? formatCompact(value) : value}
            </p>
          </div>
          <div className={cn("flex size-10 items-center justify-center rounded-lg bg-gradient-to-br to-transparent", accentMap[accent])}>
            <Icon className="size-5" />
          </div>
        </div>
        {delta !== undefined && (
          <div className="mt-3 flex items-center gap-1 text-xs">
            <span className={cn("flex items-center gap-0.5 font-medium", up ? "text-emerald-500" : "text-severity-critical")}>
              {up ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
              {Math.abs(delta)}%
            </span>
            <span className="text-muted-foreground">vs last 7d</span>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
