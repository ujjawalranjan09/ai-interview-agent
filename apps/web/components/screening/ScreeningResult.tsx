"use client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ScreeningResultProps {
  result: {
    candidate_id: string;
    score: number;
    strengths: string[];
    gaps: string[];
    recommendation: string;
  };
}

export function ScreeningResult({ result }: ScreeningResultProps) {
  const scoreColor = result.score >= 70 ? "text-green-500" : result.score >= 40 ? "text-yellow-500" : "text-red-500";
  const badgeVariant = result.recommendation === "strong_fit" ? "default" as const : result.recommendation === "moderate_fit" ? "secondary" as const : "destructive" as const;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Match Score</CardTitle>
          <Badge variant={badgeVariant}>
            {result.recommendation === "strong_fit" ? "Strong Fit" : result.recommendation === "moderate_fit" ? "Moderate Fit" : "Weak Fit"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-center py-4">
          <div className={`text-5xl font-bold ${scoreColor}`}>{result.score}%</div>
        </div>
        {result.strengths.length > 0 && (
          <div>
            <p className="text-sm font-medium mb-2">Strengths</p>
            <div className="flex flex-wrap gap-1">
              {result.strengths.map((s, i) => (
                <span key={i} className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">{s}</span>
              ))}
            </div>
          </div>
        )}
        {result.gaps.length > 0 && (
          <div>
            <p className="text-sm font-medium mb-2">Gaps</p>
            <div className="flex flex-wrap gap-1">
              {result.gaps.map((g, i) => (
                <span key={i} className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">{g}</span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
