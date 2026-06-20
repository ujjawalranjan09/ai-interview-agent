"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface TypePieChartProps {
  data: { type: string; count: number; avg_score: number }[];
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export function TypePieChart({ data }: TypePieChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={100} label>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
