"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, ChevronRight } from "lucide-react";
import { SeverityBadge } from "./severity-badge";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Alert } from "@/lib/types";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "success" | "warning" | "destructive"> = {
  new: "destructive",
  triaging: "warning",
  investigating: "default",
  resolved: "success",
  false_positive: "secondary",
  suppressed: "secondary",
};

function timeAgo(iso?: string | null): string {
  if (!iso) return "—";
  const diff = Date.UTC(2026, 5, 27, 14, 0, 0) - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function AlertTable({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border/60">
      <div className="hidden grid-cols-[110px_1fr_140px_120px_110px_90px_40px] gap-3 border-b border-border/60 bg-muted/30 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
        <span>Severity</span>
        <span>Detection</span>
        <span>Host / User</span>
        <span>Status</span>
        <span>Confidence</span>
        <span>Seen</span>
        <span />
      </div>
      <div className="divide-y divide-border/50">
        {alerts.map((a, i) => (
          <motion.div
            key={a.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.02, 0.3) }}
          >
            <Link
              href={`/alerts/${a.id}`}
              className="grid grid-cols-2 items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-accent/40 md:grid-cols-[110px_1fr_140px_120px_110px_90px_40px]"
            >
              <div><SeverityBadge severity={a.severity} /></div>
              <div className="col-span-2 min-w-0 md:col-span-1">
                <div className="flex items-center gap-1.5">
                  <p className="truncate font-medium">{a.title}</p>
                  {a.source !== "rule" && <Sparkles className="size-3.5 shrink-0 text-primary" aria-label="AI-detected" />}
                </div>
                <div className="mt-0.5 flex flex-wrap gap-1">
                  {a.techniques.slice(0, 2).map((t) => (
                    <span key={t.technique_id} className="font-mono text-[10px] text-muted-foreground">{t.technique_id}</span>
                  ))}
                </div>
              </div>
              <div className="min-w-0 font-mono text-xs">
                <p className="truncate">{a.host}</p>
                <p className="truncate text-muted-foreground">{a.user_principal}</p>
              </div>
              <div>
                <Badge variant={STATUS_VARIANT[a.status]} className="capitalize">
                  {a.status.replace("_", " ")}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full", a.confidence >= 80 ? "bg-severity-critical" : a.confidence >= 60 ? "bg-severity-high" : "bg-severity-medium")}
                    style={{ width: `${a.confidence}%` }}
                  />
                </div>
                <span className="text-xs tabular-nums text-muted-foreground">{a.confidence}%</span>
              </div>
              <span className="text-xs text-muted-foreground">{timeAgo(a.last_seen)}</span>
              <ChevronRight className="hidden size-4 text-muted-foreground md:block" />
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
