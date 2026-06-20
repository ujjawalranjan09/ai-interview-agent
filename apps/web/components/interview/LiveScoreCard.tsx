"use client";

import { Card, CardContent } from "@/components/ui/card";
import { RubricScores } from "./RubricScores";

interface CriterionScore {
  criterion_id: string;
  criterion_name: string;
  score: number;
  weight: number;
  weighted_score: number;
  feedback: string;
}

interface LiveScoreCardProps {
  evaluation: {
    total_score: number;
    semantic_score: number;
    keyword_score: number;
    concept_score: number;
    feedback?: string;
    rubric_total?: number;
    rubric_feedback?: string;
    criteria_scores?: CriterionScore[];
    rubric_scores?: { total: number; rubric_name?: string };
  };
}

export function LiveScoreCard({ evaluation }: LiveScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-center mb-4">
          <div className={`text-5xl font-bold ${getScoreColor(evaluation.total_score)}`}>
            {Math.round(evaluation.total_score)}
          </div>
          <div className="text-sm text-muted-foreground mt-1">Overall Score</div>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className={`text-lg font-semibold ${getScoreColor(evaluation.semantic_score)}`}>
              {Math.round(evaluation.semantic_score)}
            </div>
            <div className="text-xs text-muted-foreground">Semantic</div>
          </div>
          <div>
            <div className={`text-lg font-semibold ${getScoreColor(evaluation.keyword_score)}`}>
              {Math.round(evaluation.keyword_score)}
            </div>
            <div className="text-xs text-muted-foreground">Keywords</div>
          </div>
          <div>
            <div className={`text-lg font-semibold ${getScoreColor(evaluation.concept_score)}`}>
              {Math.round(evaluation.concept_score)}
            </div>
            <div className="text-xs text-muted-foreground">Concepts</div>
          </div>
        </div>
        {evaluation.feedback && (
          <p className="text-sm text-muted-foreground text-center mt-4">{evaluation.feedback}</p>
        )}
        
        {evaluation.criteria_scores && evaluation.criteria_scores.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <RubricScores
              rubric_total={evaluation.rubric_total || 0}
              rubric_feedback={evaluation.rubric_feedback || ""}
              criteria_scores={evaluation.criteria_scores}
              rubric_name={evaluation.rubric_scores?.rubric_name}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
