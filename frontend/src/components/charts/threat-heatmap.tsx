"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AlertCategory } from "@/lib/types";

interface HeatCell {
  host: string;
  category: AlertCategory;
  value: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  ransomware: "Ransomware",
  credential_dumping: "Cred. Dumping",
  lateral_movement: "Lateral Move",
  c2: "C2",
  exfiltration: "Exfiltration",
  persistence: "Persistence",
};

function intensity(value: number): string {
  if (value >= 8) return "bg-severity-critical/90 text-white";
  if (value >= 6) return "bg-severity-high/80 text-white";
  if (value >= 4) return "bg-severity-medium/70";
  if (value >= 2) return "bg-severity-low/40";
  if (value >= 1) return "bg-primary/15";
  return "bg-muted/40 text-muted-foreground";
}

export function ThreatHeatmap({ data }: { data: HeatCell[] }) {
  const hosts = Array.from(new Set(data.map((d) => d.host)));
  const categories = Array.from(new Set(data.map((d) => d.category)));
  const lookup = new Map(data.map((d) => [`${d.host}:${d.category}`, d.value]));

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px]">
        <div className="grid" style={{ gridTemplateColumns: `120px repeat(${categories.length}, 1fr)` }}>
          <div />
          {categories.map((c) => (
            <div key={c} className="px-1 pb-2 text-center text-[10px] font-medium text-muted-foreground">
              {CATEGORY_LABELS[c] ?? c}
            </div>
          ))}
          {hosts.map((host, ri) => (
            <React.Fragment key={host}>
              <div className="flex items-center pr-2 font-mono text-xs text-muted-foreground">{host}</div>
              {categories.map((c, ci) => {
                const v = lookup.get(`${host}:${c}`) ?? 0;
                return (
                  <motion.div
                    key={`${host}:${c}`}
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: (ri * categories.length + ci) * 0.008 }}
                    title={`${host} · ${CATEGORY_LABELS[c] ?? c}: ${v}`}
                    className={cn(
                      "m-0.5 flex h-10 items-center justify-center rounded-md text-xs font-semibold transition-transform hover:scale-105 hover:ring-2 hover:ring-primary/40",
                      intensity(v)
                    )}
                  >
                    {v > 0 ? v : ""}
                  </motion.div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
