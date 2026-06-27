"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { ScrollText } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const LOGS = [
  { actor: "priya@corp.com", action: "alert.close", resource: "al-0012", status: "success", time: "14:02:11" },
  { actor: "marcus@corp.com", action: "datasource.update", resource: "gcp_audit", status: "success", time: "13:51:40" },
  { actor: "admin@corp.com", action: "user.create", resource: "sam@corp.com", status: "success", time: "13:30:02" },
  { actor: "sam@corp.com", action: "auth.login", resource: "session", status: "success", time: "13:12:55" },
  { actor: "unknown", action: "auth.login", resource: "session", status: "failure", time: "13:09:18" },
  { actor: "priya@corp.com", action: "hunt.launch", resource: "hunt-0042", status: "success", time: "12:58:30" },
  { actor: "marcus@corp.com", action: "detection.deploy", resource: "det-0007", status: "success", time: "12:40:11" },
];

export default function AuditPage() {
  return (
    <div className="space-y-5">
      <PageHeader title="Audit Log" description="Immutable, append-only record of security-relevant actions" />
      <Card glass className="overflow-hidden">
        <div className="hidden grid-cols-[90px_200px_1fr_140px_90px] gap-3 border-b border-border/60 bg-muted/30 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
          <span>Time</span><span>Actor</span><span>Action</span><span>Resource</span><span>Status</span>
        </div>
        <div className="divide-y divide-border/50 font-mono text-xs">
          {LOGS.map((l, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.04 }}
              className="grid grid-cols-1 items-center gap-2 px-4 py-2.5 md:grid-cols-[90px_200px_1fr_140px_90px]"
            >
              <span className="text-muted-foreground">{l.time}</span>
              <span className="truncate">{l.actor}</span>
              <span className="flex items-center gap-1.5"><ScrollText className="size-3 text-muted-foreground" /> {l.action}</span>
              <span className="truncate text-muted-foreground">{l.resource}</span>
              <Badge variant={l.status === "success" ? "success" : "destructive"} className="w-fit">{l.status}</Badge>
            </motion.div>
          ))}
        </div>
      </Card>
    </div>
  );
}
