"use client";

import * as React from "react";
import { Filter, Download, Search } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { AlertTable } from "@/components/features/alert-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SEVERITY_ORDER } from "@/lib/utils";
import { mockAlerts } from "@/lib/mock";

export default function AlertsPage() {
  const all = React.useMemo(() => mockAlerts(), []);
  const [query, setQuery] = React.useState("");
  const [severity, setSeverity] = React.useState<string>("all");

  const filtered = all.filter((a) => {
    const matchesQuery =
      !query ||
      a.title.toLowerCase().includes(query.toLowerCase()) ||
      (a.host ?? "").toLowerCase().includes(query.toLowerCase());
    const matchesSeverity = severity === "all" || a.severity === severity;
    return matchesQuery && matchesSeverity;
  });

  return (
    <div className="space-y-5">
      <PageHeader
        title="Alerts"
        description={`${filtered.length} detections matching current filters`}
        actions={
          <>
            <Button variant="outline" size="sm"><Filter className="size-4" /> Filters</Button>
            <Button variant="outline" size="sm"><Download className="size-4" /> Export</Button>
          </>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by title or host…"
            className="pl-9"
          />
        </div>
        <Tabs value={severity} onValueChange={setSeverity}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            {SEVERITY_ORDER.map((s) => (
              <TabsTrigger key={s} value={s} className="capitalize">{s}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <AlertTable alerts={filtered} />
    </div>
  );
}
