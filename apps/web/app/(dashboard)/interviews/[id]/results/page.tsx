"use client";

import { useParams } from "next/navigation";
import { useReport, useGenerateReport } from "@/hooks/useReport";
import { ScoreOverview } from "@/components/interview/ScoreOverview";
import { QuestionBreakdown } from "@/components/interview/QuestionBreakdown";
import { FeedbackPanel } from "@/components/interview/FeedbackPanel";
import { ScoreBarChart, ScoreLineChart, EmotionAreaChart, SkillRadarChart, TypePieChart, DifficultyStepChart, ComparisonGroupedChart } from "@/components/charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

const CHART_TABS = [
  { key: "bar", label: "Scores" },
  { key: "line", label: "Progression" },
  { key: "emotion", label: "Emotion" },
  { key: "radar", label: "Skills" },
  { key: "pie", label: "Types" },
  { key: "difficulty", label: "Difficulty" },
  { key: "grouped", label: "Components" },
] as const;

interface ReportData {
  metrics: { average_score: number; overall_grade: string } | null;
  feedback: { strengths: string[]; weaknesses: string[]; suggestions: string[]; overall_assessment: string } | null;
  chart_data: Record<string, unknown[]> | null;
  pdf_url: string | null;
}

export default function ResultsPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: report, isLoading } = useReport(id) as { data: ReportData | undefined; isLoading: boolean };
  const generateReport = useGenerateReport();
  const [chartTab, setChartTab] = useState<string>("bar");

  if (isLoading) return <div className="text-center py-12 text-muted-foreground">Loading...</div>;

  if (!report) {
    return (
      <div className="text-center py-12 space-y-4">
        <p className="text-muted-foreground">No report generated yet.</p>
        <Button onClick={() => generateReport.mutateAsync(id).catch(() => {})} disabled={generateReport.isPending}>
          {generateReport.isPending ? "Generating..." : "Generate Report"}
        </Button>
      </div>
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const charts: any = report.chart_data || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Interview Results</h1>
        {report.pdf_url && (
          <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm">Download PDF</Button>
          </a>
        )}
      </div>

      <ScoreOverview score={report.metrics?.average_score || 0} grade={report.metrics?.overall_grade || "N/A"} />

      <Card>
        <CardHeader><CardTitle>Charts</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-1 border-b mb-4 overflow-x-auto">
            {CHART_TABS.map((t) => (
              <button key={t.key} onClick={() => setChartTab(t.key)}
                className={`pb-2 px-3 text-xs font-medium border-b-2 whitespace-nowrap ${chartTab === t.key ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="h-[300px]">
            {chartTab === "bar" && <ScoreBarChart data={charts.score_bar || []} />}
            {chartTab === "line" && <ScoreLineChart data={charts.score_line || []} />}
            {chartTab === "emotion" && <EmotionAreaChart data={charts.emotion_area || []} />}
            {chartTab === "radar" && <SkillRadarChart data={charts.skill_radar || []} />}
            {chartTab === "pie" && <TypePieChart data={charts.type_pie || []} />}
            {chartTab === "difficulty" && <DifficultyStepChart data={charts.difficulty_step || []} />}
            {chartTab === "grouped" && <ComparisonGroupedChart data={charts.comparison_grouped || []} />}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Question Breakdown</CardTitle></CardHeader>
        <CardContent>
          <QuestionBreakdown questions={(charts.score_bar || []).map((q: Record<string, unknown>, i: number) => ({
            question_text: String(q.label || ""),
            question_type: String(q.type || ""),
            difficulty: String(q.difficulty || ""),
            answer_score: Number(q.score || 0),
            semantic_score: Number(q.semantic || 0),
            keyword_score: Number(q.keyword || 0),
            concept_score: Number(q.concept || 0),
            candidate_answer_text: typeof q.answer === "string" ? q.answer : null,
            order_index: i,
          }))} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Feedback</CardTitle></CardHeader>
        <CardContent>
          <FeedbackPanel feedback={report.feedback || { strengths: [], weaknesses: [], suggestions: [], overall_assessment: "" }} />
        </CardContent>
      </Card>
    </div>
  );
}
