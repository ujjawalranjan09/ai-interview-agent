"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CriterionScore {
  criterion_id: string;
  criterion_name: string;
  score: number;
  weight: number;
  weighted_score: number;
  feedback: string;
}

interface RubricScoresProps {
  rubric_total: number;
  rubric_feedback: string;
  criteria_scores: CriterionScore[];
  rubric_name?: string;
}

export function RubricScores({
  rubric_total,
  rubric_feedback,
  criteria_scores,
  rubric_name,
}: RubricScoresProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">
          {rubric_name || "Rubric Evaluation"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center">
          <div className={`text-4xl font-bold ${getScoreColor(rubric_total)}`}>
            {Math.round(rubric_total)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">Rubric Score</div>
        </div>

        <div className="space-y-3">
          {criteria_scores.map((criterion) => (
            <div key={criterion.criterion_id} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{criterion.criterion_name}</span>
                <span className={`text-sm font-semibold ${getScoreColor(criterion.score)}`}>
                  {Math.round(criterion.score)}
                </span>
              </div>
              <div className="relative h-2 w-full bg-muted rounded-full overflow-hidden">
                <div
                  className={`absolute h-full ${getProgressColor(criterion.score)} rounded-full transition-all`}
                  style={{ width: `${Math.min(100, criterion.score)}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">{criterion.feedback}</p>
            </div>
          ))}
        </div>

        {rubric_feedback && (
          <div className="pt-2 border-t">
            <p className="text-sm text-muted-foreground">{rubric_feedback}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
