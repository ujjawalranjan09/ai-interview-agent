"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface ComparisonGroupedChartProps {
  data: { label: string; semantic: number; keyword: number; concept: number }[];
}

export function ComparisonGroupedChart({ data }: ComparisonGroupedChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Bar dataKey="semantic" fill="#3b82f6" name="Semantic" />
        <Bar dataKey="keyword" fill="#ef4444" name="Keywords" />
        <Bar dataKey="concept" fill="#10b981" name="Concepts" />
      </BarChart>
    </ResponsiveContainer>
  );
}
