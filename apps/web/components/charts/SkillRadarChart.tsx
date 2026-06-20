"use client";

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts";

interface SkillRadarChartProps {
  data: { dimension: string; value: number }[];
}

export function SkillRadarChart({ data }: SkillRadarChartProps) {
  if (!data.length) return <div className="text-center py-8 text-muted-foreground">No data</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="dimension" />
        <PolarRadiusAxis angle={30} domain={[0, 100]} />
        <Radar name="Score" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
