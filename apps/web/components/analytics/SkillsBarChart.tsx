"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface SkillsBarChartProps {
  data: { skill: string; count: number }[];
}

export function SkillsBarChart({ data }: SkillsBarChartProps) {
  if (!data.length) {
    return <p className="text-sm text-muted-foreground">No data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} layout="vertical" margin={{ left: 120 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" dataKey="count" />
        <YAxis type="category" dataKey="skill" width={120} />
        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
