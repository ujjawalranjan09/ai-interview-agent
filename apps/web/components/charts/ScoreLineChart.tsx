"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface ScoreLineChartProps {
  data: { label: string; score: number; rolling_avg: number }[];
}

export function ScoreLineChart({ data }: ScoreLineChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
        <Line type="monotone" dataKey="rolling_avg" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
