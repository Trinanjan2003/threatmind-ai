"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Crosshair, Play, Bot, CheckCircle2, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const FOCUS_AREAS = [
  "Ransomware", "Credential Dumping", "Lateral Movement", "C2 Beaconing",
  "Data Exfiltration", "Living-off-the-Land", "Insider Threat", "Cloud Attacks",
];

const AGENTS = [
  { name: "Log Investigation", desc: "Surfaces relevant event sequences" },
  { name: "IOC Correlation", desc: "Clusters related indicators" },
  { name: "Threat Intelligence", desc: "Enriches against known threats" },
  { name: "Malware Analysis", desc: "Behavioral verdict on artifacts" },
  { name: "MITRE Mapping", desc: "Maps to ATT&CK techniques" },
  { name: "Risk Scoring", desc: "Unified confidence + severity" },
  { name: "Detection Engineering", desc: "Generates detection content" },
  { name: "Reporting", desc: "Synthesizes the final report" },
];

export default function HuntingPage() {
  const [focus, setFocus] = React.useState("Ransomware");
  const [running, setRunning] = React.useState(false);
  const [activeAgent, setActiveAgent] = React.useState(-1);

  async function launch() {
    setRunning(true);
    setActiveAgent(-1);
    for (let i = 0; i < AGENTS.length; i++) {
      setActiveAgent(i);
      await new Promise((r) => setTimeout(r, 500));
    }
    setActiveAgent(AGENTS.length);
    setRunning(false);
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Autonomous Threat Hunting"
        description="Launch the multi-agent engine to hunt across your environment"
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card glass className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Hunt Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">Focus Area</p>
              <div className="flex flex-wrap gap-1.5">
                {FOCUS_AREAS.map((f) => (
                  <button
                    key={f}
                    onClick={() => setFocus(f)}
                    className={cn(
                      "rounded-full border px-2.5 py-1 text-xs transition-colors",
                      focus === f ? "border-primary bg-primary/15 text-primary" : "border-border text-muted-foreground hover:bg-accent/50"
                    )}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <Button onClick={launch} disabled={running} className="w-full">
              {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              {running ? "Hunting…" : "Launch Hunt"}
            </Button>
          </CardContent>
        </Card>

        <Card glass className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">Agent Orchestration</CardTitle>
            {activeAgent >= AGENTS.length && <Badge variant="success">Hunt complete</Badge>}
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {AGENTS.map((agent, i) => {
              const done = i < activeAgent || activeAgent >= AGENTS.length;
              const active = i === activeAgent && running;
              return (
                <motion.div
                  key={agent.name}
                  initial={{ opacity: 0.6 }}
                  animate={{ opacity: done || active ? 1 : 0.6 }}
                  className={cn(
                    "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                    active ? "border-primary bg-primary/10" : done ? "border-emerald-500/30 bg-emerald-500/5" : "border-border"
                  )}
                >
                  <div className={cn("flex size-8 shrink-0 items-center justify-center rounded-lg", done ? "bg-emerald-500/15" : "bg-primary/15")}>
                    {done ? <CheckCircle2 className="size-4 text-emerald-500" /> : active ? <Loader2 className="size-4 animate-spin text-primary" /> : <Bot className="size-4 text-primary" />}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{agent.name}</p>
                    <p className="truncate text-xs text-muted-foreground">{agent.desc}</p>
                  </div>
                </motion.div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {activeAgent >= AGENTS.length && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card glass>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Crosshair className="size-4 text-primary" /> Hunt Findings — {focus}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">
                The agent collective identified <span className="font-semibold text-foreground">3 high-confidence findings</span> related
                to {focus.toLowerCase()}. Evidence has been correlated across Sysmon, Zeek, and CloudTrail sources, mapped to 5 MITRE
                techniques, and scored at an aggregate risk of <span className="font-semibold text-severity-high">81/100</span>.
                A draft incident and detection rules are ready for analyst review.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
