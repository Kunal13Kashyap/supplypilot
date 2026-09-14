"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const tooltipStyle = {
  border: "1px solid hsl(var(--border))",
  borderRadius: "6px",
  background: "hsl(var(--card))",
  boxShadow: "var(--shadow-md)",
  fontSize: "12px",
};

export function DecisionChart({ data }: { data: Record<string, number> }) {
  const rows = Object.entries(data).map(([name, value]) => ({ name, value }));
  if (!rows.length) {
    return (
      <div className="grid h-64 place-items-center text-sm text-muted-foreground">
        Run an investigation to populate decisions.
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
        <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="2 4" />
        <XAxis
          dataKey="name"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
        />
        <YAxis
          allowDecimals={false}
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
        />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "hsl(var(--muted))" }} />
        <Bar dataKey="value" fill="hsl(var(--foreground))" radius={[3, 3, 0, 0]} maxBarSize={38} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function BudgetChart({ amount, spent }: { amount: number; spent: number }) {
  const used = Math.min(spent, amount);
  const data = [
    { name: "Committed", value: used },
    { name: "Available", value: Math.max(amount - used, 0) },
  ];
  return (
    <div className="relative h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            innerRadius={72}
            outerRadius={94}
            paddingAngle={2}
            stroke="none"
          >
            <Cell fill="hsl(var(--primary))" />
            <Cell fill="hsl(var(--muted))" />
          </Pie>
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value) => `$${Number(value).toLocaleString()}`}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="text-3xl font-semibold tracking-tight">
            {Math.round((used / (amount || 1)) * 100)}%
          </div>
          <div className="eyebrow mt-1">Utilized</div>
        </div>
      </div>
    </div>
  );
}
