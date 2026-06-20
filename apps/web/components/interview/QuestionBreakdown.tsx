"use client";

import { useState } from "react";

interface QuestionBreakdownProps {
  questions: {
    question_text: string;
    question_type: string;
    difficulty: string;
    answer_score: number;
    semantic_score: number;
    keyword_score: number;
    concept_score: number;
    candidate_answer_text: string | null;
    order_index: number;
  }[];
}

export function QuestionBreakdown({ questions }: QuestionBreakdownProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="space-y-2">
      {questions.map((q, i) => (
        <div key={i} className="border rounded-lg">
          <button
            className="w-full text-left p-3 flex items-center justify-between hover:bg-muted/50"
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">Q{q.order_index + 1}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">{q.question_type}</span>
              <span className="text-sm text-muted-foreground truncate max-w-md">{q.question_text}</span>
            </div>
            <span className={`text-sm font-bold ${q.answer_score >= 80 ? "text-green-600" : q.answer_score >= 60 ? "text-yellow-600" : "text-red-600"}`}>
              {Math.round(q.answer_score)}
            </span>
          </button>
          {expanded === i && (
            <div className="p-3 border-t bg-muted/30 space-y-2 text-sm">
              <p><strong>Answer:</strong> {q.candidate_answer_text || "No answer"}</p>
              <div className="flex gap-4">
                <span>Semantic: {Math.round(q.semantic_score)}</span>
                <span>Keywords: {Math.round(q.keyword_score)}</span>
                <span>Concepts: {Math.round(q.concept_score)}</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
