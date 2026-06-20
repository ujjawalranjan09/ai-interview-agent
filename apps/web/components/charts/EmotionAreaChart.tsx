"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface EmotionAreaChartProps {
  data: { time: number; confidence: number; emotion: string }[];
}

export function EmotionAreaChart({ data }: EmotionAreaChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No emotion data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" label={{ value: "Time (s)", position: "bottom" }} />
        <YAxis domain={[0, 100]} />
        <Tooltip formatter={(value) => [String(value), "Confidence"]} labelFormatter={(l) => `${l}s`} />
        <Area type="monotone" dataKey="confidence" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
