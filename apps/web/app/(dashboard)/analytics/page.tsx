"use client";

import { useState } from "react";
import {
  useAnalyticsOverview,
  useAnalyticsTrends,
  useCandidateHistory,
} from "@/hooks/useAnalytics";
import { MetricCard } from "@/components/analytics/MetricCard";
import { SkillsBarChart } from "@/components/analytics/SkillsBarChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
} from "recharts";

export default function AnalyticsPage() {
  const { data: overview, isLoading: ovLoading } = useAnalyticsOverview();
  const { data: trends, isLoading: trLoading } = useAnalyticsTrends();
  const [candidateId, setCandidateId] = useState("");
  const { data: history } = useCandidateHistory(candidateId);

  if (ovLoading || trLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard value={overview?.total_interviews || 0} label="Total Interviews" icon="📝" />
        <MetricCard value={overview?.completed_interviews || 0} label="Completed" icon="✅" />
        <MetricCard value={overview?.average_score || 0} label="Avg Score" icon="📊" decimals={1} />
        <MetricCard value={overview?.total_candidates || 0} label="Candidates" icon="👤" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Score Trends</CardTitle>
        </CardHeader>
        <CardContent>
          {trends?.weekly_scores?.length ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends.weekly_scores}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week_start" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="average_score"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground">No trend data</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Skills</CardTitle>
        </CardHeader>
        <CardContent>
          <SkillsBarChart data={trends?.skill_distribution || []} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Candidate History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            className="w-full rounded-md border p-2"
            placeholder="Enter Candidate ID..."
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
          />
          {history?.items?.length ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="p-2">Interview</th>
                  <th className="p-2">Date</th>
                  <th className="p-2">Score</th>
                  <th className="p-2">Status</th>
                  <th className="p-2">Questions</th>
                </tr>
              </thead>
              <tbody>
                {history.items.map((item) => (
                  <tr key={item.interview_id} className="border-b last:border-0">
                    <td className="p-2">{item.interview_id.slice(0, 8)}...</td>
                    <td className="p-2">{new Date(item.date).toLocaleDateString()}</td>
                    <td className="p-2">{Math.round(item.score)}</td>
                    <td className="p-2">{item.status}</td>
                    <td className="p-2">{item.question_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : candidateId ? (
            <p className="text-sm text-muted-foreground">No history found</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
