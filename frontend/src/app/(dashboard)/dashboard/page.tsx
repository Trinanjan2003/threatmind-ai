"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { ShieldAlert, Siren, Activity, Clock, ArrowUpRight } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { StatCard } from "@/components/features/stat-card";
import { SeverityBadge } from "@/components/features/severity-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AreaTrend } from "@/components/charts/area-trend";
import { SeverityDonut } from "@/components/charts/severity-donut";
import { ThreatHeatmap } from "@/components/charts/threat-heatmap";
import { mockAlerts, mockHeatmap, mockOverview, mockTrends } from "@/lib/mock";
import Link from "next/link";

export default function DashboardPage() {
  const overview = React.useMemo(() => mockOverview(), []);
  const trends = React.useMemo(() => mockTrends(), []);
  const heatmap = React.useMemo(() => mockHeatmap(), []);
  const recent = React.useMemo(() => mockAlerts().slice(0, 6), []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security Operations Overview"
        description="Real-time posture across endpoints, identities, cloud, and network."
        actions={
          <>
            <Button variant="outline" size="sm">Last 7 days</Button>
            <Button size="sm" asChild>
              <Link href="/hunting">
                Launch Hunt <ArrowUpRight className="size-4" />
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Open Alerts" value={overview.open_alerts} icon={ShieldAlert} delta={12} accent="high" index={0} />
        <StatCard label="Active Incidents" value={4} icon={Siren} delta={-8} accent="critical" index={1} />
        <StatCard label="Mean Time to Investigate" value="6.4m" icon={Clock} delta={-43} accent="success" index={2} />
        <StatCard label="Events / sec ingested" value={4820} icon={Activity} delta={5} accent="primary" index={3} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card glass className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Alert & Resolution Trend</CardTitle>
              <CardDescription>Detections vs. analyst resolutions over 14 days</CardDescription>
            </div>
            <Badge variant="success">+18% auto-triaged</Badge>
          </CardHeader>
          <CardContent>
            <AreaTrend data={trends} />
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle>Severity Distribution</CardTitle>
            <CardDescription>Current open alert breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <SeverityDonut data={overview.alerts_by_severity} />
            <div className="mt-4 grid grid-cols-2 gap-2">
              {Object.entries(overview.alerts_by_severity).map(([sev, count]) => (
                <div key={sev} className="flex items-center justify-between rounded-md bg-muted/40 px-2.5 py-1.5">
                  <SeverityBadge severity={sev} />
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card glass className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Threat Heatmap</CardTitle>
            <CardDescription>Suspicious activity intensity by host and attack category</CardDescription>
          </CardHeader>
          <CardContent>
            <ThreatHeatmap data={heatmap} />
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Recent Alerts</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/alerts">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-1">
            {recent.map((a, i) => (
              <motion.div
                key={a.id}
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Link
                  href={`/alerts/${a.id}`}
                  className="flex items-start gap-3 rounded-lg p-2.5 transition-colors hover:bg-accent/50"
                >
                  <SeverityBadge severity={a.severity} className="mt-0.5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{a.title}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {a.host} · {a.confidence}% confidence
                    </p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
