"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  XCircle,
  UserPlus,
  FileText,
  ExternalLink,
} from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { SeverityBadge } from "@/components/features/severity-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { mockAlerts } from "@/lib/mock";

export default function AlertDetailPage({ params }: { params: { id: string } }) {
  const alert = React.useMemo(() => {
    const all = mockAlerts();
    return all.find((a) => a.id === params.id) ?? all[0];
  }, [params.id]);

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" asChild className="text-muted-foreground">
        <Link href="/alerts"><ArrowLeft className="size-4" /> Back to alerts</Link>
      </Button>

      <PageHeader
        title={alert.title}
        description={`${alert.host} · ${alert.user_principal} · ${alert.category.replace("_", " ")}`}
        actions={
          <>
            <Button variant="outline" size="sm"><UserPlus className="size-4" /> Assign</Button>
            <Button variant="outline" size="sm"><XCircle className="size-4" /> False Positive</Button>
            <Button size="sm" asChild>
              <Link href="/chat"><Sparkles className="size-4" /> AI Investigate</Link>
            </Button>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <SeverityBadge severity={alert.severity} />
        <Badge variant="default" className="capitalize">{alert.status.replace("_", " ")}</Badge>
        {alert.source !== "rule" && (
          <Badge variant="default" className="gap-1"><Sparkles className="size-3" /> AI-detected</Badge>
        )}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldCheck className="size-4 text-primary" />
          Confidence <span className="font-semibold text-foreground">{alert.confidence}%</span>
          <span className="capitalize">({alert.confidence_label.replace("_", " ")})</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card glass>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="size-4 text-primary" /> AI Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">{alert.explanation}</p>
            </CardContent>
          </Card>

          <Card glass>
            <CardHeader>
              <CardTitle className="text-base">Evidence Chain</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {alert.evidence.map((e, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/30 p-3"
                >
                  <div className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md bg-primary/15 text-xs font-semibold text-primary">
                    {i + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{e.summary}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary" className="text-[10px]">{e.source}</Badge>
                      <span className="font-mono">{e.event_id}</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card glass>
            <CardHeader>
              <CardTitle className="text-base">MITRE ATT&CK</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {alert.techniques.map((t) => (
                <a
                  key={t.technique_id}
                  href={t.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-lg border border-border/50 p-2.5 transition-colors hover:bg-accent/50"
                >
                  <div>
                    <p className="font-mono text-xs text-primary">{t.technique_id}</p>
                    <p className="text-sm">{t.name}</p>
                    <p className="text-xs capitalize text-muted-foreground">{t.tactic.replace("_", " ")}</p>
                  </div>
                  <ExternalLink className="size-3.5 text-muted-foreground" />
                </a>
              ))}
            </CardContent>
          </Card>

          <Card glass>
            <CardHeader>
              <CardTitle className="text-base">Recommended Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {["Isolate affected host from the network", "Reset credentials for impacted identity", "Hunt for the same TTP across the fleet", "Generate a detection rule"].map((rec) => (
                <div key={rec} className="flex items-start gap-2">
                  <ShieldCheck className="mt-0.5 size-4 shrink-0 text-emerald-500" />
                  <span className="text-muted-foreground">{rec}</span>
                </div>
              ))}
              <Separator className="my-2" />
              <Button variant="outline" size="sm" className="w-full">
                <FileText className="size-4" /> Generate Incident Report
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
