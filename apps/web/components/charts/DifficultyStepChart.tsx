"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface DifficultyStepChartProps {
  data: { label: string; difficulty: number; score: number }[];
}

const DIFF_COLORS = { 1: "#10b981", 2: "#f59e0b", 3: "#f97316", 4: "#ef4444" };
const DIFF_NAMES = { 1: "Easy", 2: "Medium", 3: "Hard", 4: "Expert" };

export function DifficultyStepChart({ data }: DifficultyStepChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis domain={[0, 4]} ticks={[1, 2, 3, 4]} tickFormatter={(v) => DIFF_NAMES[v as keyof typeof DIFF_NAMES] || v} />
        <Tooltip formatter={(value) => [DIFF_NAMES[value as keyof typeof DIFF_NAMES] || String(value), "Difficulty"]} />
        <Bar dataKey="difficulty" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => <Cell key={i} fill={DIFF_COLORS[entry.difficulty as keyof typeof DIFF_COLORS] || "#94a3b8"} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
