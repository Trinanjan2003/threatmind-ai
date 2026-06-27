"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  DoorOpen,
  Terminal,
  Anchor,
  ArrowUpCircle,
  EyeOff,
  KeyRound,
  Network,
  FolderSearch,
  Radio,
  Upload,
  Bomb,
  type LucideIcon,
} from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockTimeline } from "@/lib/mock";

const PHASE_ICON: Record<string, LucideIcon> = {
  initial_access: DoorOpen,
  execution: Terminal,
  persistence: Anchor,
  privilege_escalation: ArrowUpCircle,
  defense_evasion: EyeOff,
  credential_access: KeyRound,
  lateral_movement: Network,
  collection: FolderSearch,
  c2: Radio,
  exfiltration: Upload,
  impact: Bomb,
};

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "UTC" });
}

export default function TimelinePage() {
  const steps = React.useMemo(() => mockTimeline(), []);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Attack Timeline Reconstruction"
        description="Incident INC-2026-0042 · LockBit-style ransomware · 14 hosts impacted"
        actions={<Badge variant="destructive">Critical · Risk 94</Badge>}
      />

      <div className="relative pl-4">
        <div className="absolute bottom-4 left-[27px] top-4 w-px bg-gradient-to-b from-primary via-severity-high to-severity-critical" />
        <div className="space-y-4">
          {steps.map((step, i) => {
            const Icon = PHASE_ICON[step.phase] ?? Terminal;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="relative flex gap-4"
              >
                <div className="z-10 flex size-12 shrink-0 items-center justify-center rounded-full border border-border bg-card shadow-lg">
                  <Icon className="size-5 text-primary" />
                </div>
                <Card glass className="flex-1">
                  <CardContent className="flex flex-col gap-1 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px] capitalize">{step.phase.replace("_", " ")}</Badge>
                        {step.technique_id && (
                          <span className="font-mono text-[10px] text-primary">{step.technique_id}</span>
                        )}
                      </div>
                      <p className="mt-1 font-medium">{step.title}</p>
                      <p className="text-sm text-muted-foreground">{step.description}</p>
                    </div>
                    <span className="shrink-0 font-mono text-xs text-muted-foreground">{fmtTime(step.occurred_at)} UTC</span>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
