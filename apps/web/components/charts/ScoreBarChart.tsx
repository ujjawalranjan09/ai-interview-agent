"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface ScoreBarChartProps {
  data: { label: string; score: number; type: string }[];
}

const getColor = (score: number) => {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
};

export function ScoreBarChart({ data }: ScoreBarChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Bar dataKey="score" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => <Cell key={i} fill={getColor(entry.score)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
