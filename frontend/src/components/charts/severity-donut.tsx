"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS: Record<string, string> = {
  critical: "hsl(var(--sev-critical))",
  high: "hsl(var(--sev-high))",
  medium: "hsl(var(--sev-medium))",
  low: "hsl(var(--sev-low))",
  info: "hsl(var(--sev-info))",
};

export function SeverityDonut({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));
  const total = chartData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={62}
            outerRadius={92}
            paddingAngle={3}
            strokeWidth={0}
          >
            {chartData.map((d) => (
              <Cell key={d.name} fill={COLORS[d.name] ?? COLORS.info} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
              textTransform: "capitalize",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold">{total}</span>
        <span className="text-xs text-muted-foreground">Total alerts</span>
      </div>
    </div>
  );
}
