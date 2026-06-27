"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Database, Plus, CheckCircle2, CircleSlash } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const SOURCES = [
  { name: "Sysmon", type: "Endpoint", events: "1.2M / day", enabled: true },
  { name: "Windows Event Logs", type: "Endpoint", events: "3.4M / day", enabled: true },
  { name: "Linux auditd", type: "Endpoint", events: "880K / day", enabled: true },
  { name: "CrowdStrike Falcon", type: "EDR", events: "640K / day", enabled: true },
  { name: "AWS CloudTrail", type: "Cloud", events: "210K / day", enabled: true },
  { name: "Azure Activity Logs", type: "Cloud", events: "150K / day", enabled: true },
  { name: "GCP Audit Logs", type: "Cloud", events: "95K / day", enabled: false },
  { name: "Zeek", type: "Network", events: "2.1M / day", enabled: true },
  { name: "Suricata", type: "Network", events: "1.8M / day", enabled: true },
  { name: "Microsoft Sentinel", type: "SIEM", events: "—", enabled: false },
  { name: "Splunk", type: "SIEM", events: "—", enabled: false },
  { name: "Elastic SIEM", type: "SIEM", events: "1.1M / day", enabled: true },
  { name: "Firewall Logs", type: "Network", events: "5.2M / day", enabled: true },
  { name: "DNS Logs", type: "Network", events: "4.0M / day", enabled: true },
  { name: "Proxy Logs", type: "Network", events: "3.3M / day", enabled: true },
];

const TYPE_COLOR: Record<string, string> = {
  Endpoint: "text-primary",
  EDR: "text-violet-400",
  Cloud: "text-amber-400",
  Network: "text-emerald-400",
  SIEM: "text-sky-400",
};

export default function DataSourcesPage() {
  return (
    <div className="space-y-5">
      <PageHeader
        title="Data Sources"
        description="Connected telemetry feeds across endpoint, cloud, network, and SIEM"
        actions={<Button size="sm"><Plus className="size-4" /> Add Connector</Button>}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {SOURCES.map((s, i) => (
          <motion.div key={s.name} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
            <Card glass className="h-full">
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div className="flex size-9 items-center justify-center rounded-lg bg-muted/60">
                    <Database className={`size-4 ${TYPE_COLOR[s.type]}`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.type} · {s.events}</p>
                  </div>
                </div>
                {s.enabled ? (
                  <Badge variant="success" className="gap-1"><CheckCircle2 className="size-3" /> Active</Badge>
                ) : (
                  <Badge variant="secondary" className="gap-1"><CircleSlash className="size-3" /> Off</Badge>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
