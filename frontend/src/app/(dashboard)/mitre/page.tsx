"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/features/page-header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MITRE_MATRIX } from "@/lib/mitre-data";
import { cn } from "@/lib/utils";

function coverageColor(c: number): string {
  if (c >= 85) return "border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20";
  if (c >= 70) return "border-primary/40 bg-primary/10 hover:bg-primary/20";
  if (c >= 55) return "border-severity-medium/40 bg-severity-medium/10 hover:bg-severity-medium/20";
  return "border-severity-critical/40 bg-severity-critical/10 hover:bg-severity-critical/20";
}

export default function MitrePage() {
  const totalTechniques = MITRE_MATRIX.reduce((s, t) => s + t.techniques.length, 0);
  const avgCoverage = Math.round(
    MITRE_MATRIX.flatMap((t) => t.techniques).reduce((s, t) => s + t.coverage, 0) / totalTechniques
  );

  return (
    <div className="space-y-5">
      <PageHeader
        title="MITRE ATT&CK Coverage Matrix"
        description="Detection coverage mapped across the adversary kill chain"
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="success">{avgCoverage}% avg coverage</Badge>
            <Badge variant="secondary">{totalTechniques} techniques</Badge>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5"><span className="size-3 rounded bg-emerald-500/40" /> Strong (≥85%)</span>
        <span className="flex items-center gap-1.5"><span className="size-3 rounded bg-primary/40" /> Good (70–84%)</span>
        <span className="flex items-center gap-1.5"><span className="size-3 rounded bg-severity-medium/40" /> Partial (55–69%)</span>
        <span className="flex items-center gap-1.5"><span className="size-3 rounded bg-severity-critical/40" /> Gap (&lt;55%)</span>
      </div>

      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-max gap-3">
          {MITRE_MATRIX.map((col, ci) => (
            <div key={col.tactic} className="w-44 shrink-0">
              <div className="mb-2 rounded-lg bg-muted/50 px-2 py-2 text-center">
                <p className="text-xs font-semibold">{col.label}</p>
                <p className="text-[10px] text-muted-foreground">{col.techniques.length} techniques</p>
              </div>
              <div className="space-y-2">
                {col.techniques.map((t, ti) => (
                  <motion.div
                    key={t.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: (ci * 3 + ti) * 0.02 }}
                  >
                    <Card className={cn("cursor-pointer border p-2.5 transition-colors", coverageColor(t.coverage))}>
                      <p className="font-mono text-[10px] text-muted-foreground">{t.id}</p>
                      <p className="mt-0.5 text-xs font-medium leading-tight">{t.name}</p>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[10px] font-semibold">{t.coverage}%</span>
                        {t.alerts > 0 && (
                          <span className="rounded-full bg-background/60 px-1.5 text-[10px] tabular-nums">
                            {t.alerts}
                          </span>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
