"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const stats = [
  { title: "Total Interviews", value: "0", icon: "📝" },
  { title: "Candidates", value: "0", icon: "👤" },
  { title: "Avg Score", value: "—", icon: "📊" },
  { title: "Active Sessions", value: "0", icon: "🔴" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <span className="text-2xl">{stat.icon}</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Interviews</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No interviews yet. Create your first interview to get started.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
