"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Siren, ArrowUpRight, Clock, Layers } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { SeverityBadge } from "@/components/features/severity-badge";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockIncidents } from "@/lib/mock";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "success" | "warning" | "destructive"> = {
  open: "destructive",
  investigating: "warning",
  contained: "default",
  closed: "success",
};

export default function IncidentsPage() {
  const incidents = React.useMemo(() => mockIncidents(), []);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Incidents"
        description="Correlated, multi-alert security cases"
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {incidents.map((inc, i) => (
          <motion.div
            key={inc.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Card glass className="group h-full transition-shadow hover:glow-ring">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-severity-critical/15">
                      <Siren className="size-4 text-severity-critical" />
                    </div>
                    <div>
                      <p className="font-mono text-xs text-muted-foreground">{inc.id}</p>
                      <SeverityBadge severity={inc.severity} />
                    </div>
                  </div>
                  <Badge variant={STATUS_VARIANT[inc.status]} className="capitalize">{inc.status}</Badge>
                </div>

                <h3 className="mt-3 font-semibold leading-snug">{inc.title}</h3>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{inc.summary}</p>

                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Layers className="size-3.5" /> {inc.alert_count} alerts</span>
                    <span className="flex items-center gap-1"><Clock className="size-3.5" /> {new Date(inc.opened_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Risk</span>
                    <span className="text-lg font-semibold text-severity-critical">{inc.risk_score}</span>
                  </div>
                </div>

                <Link
                  href="/timeline"
                  className="mt-3 flex items-center gap-1 text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100"
                >
                  View attack timeline <ArrowUpRight className="size-3" />
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
