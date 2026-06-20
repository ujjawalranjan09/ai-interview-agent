"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface QuestionCardProps {
  question: {
    question_text: string;
    question_type: string;
    difficulty: string;
    order_index: number;
  };
  totalQuestions: number;
}

const typeColors: Record<string, string> = {
  resume: "bg-blue-100 text-blue-800",
  technical: "bg-purple-100 text-purple-800",
  behavioral: "bg-green-100 text-green-800",
  coding: "bg-orange-100 text-orange-800",
};

const difficultyColors: Record<string, string> = {
  easy: "text-green-600",
  medium: "text-yellow-600",
  hard: "text-orange-600",
  expert: "text-red-600",
};

export function QuestionCard({ question, totalQuestions }: QuestionCardProps) {
  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${typeColors[question.question_type] || "bg-gray-100"}`}>
              {question.question_type}
            </span>
            <span className={`text-xs font-medium capitalize ${difficultyColors[question.difficulty] || ""}`}>
              {question.difficulty}
            </span>
          </div>
          <span className="text-sm text-muted-foreground">
            Q{question.order_index + 1} of {totalQuestions}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-lg leading-relaxed">{question.question_text}</p>
      </CardContent>
    </Card>
  );
}
