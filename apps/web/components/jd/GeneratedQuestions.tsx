"use client";

interface Question {
  question_text: string;
  question_type: string;
  difficulty: string;
  target_skill: string;
}

interface GeneratedQuestionsProps {
  questions: Question[];
}

export function GeneratedQuestions({ questions }: GeneratedQuestionsProps) {
  if (!questions.length) {
    return <p className="text-sm text-muted-foreground">No questions generated</p>;
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-3">
      {questions.map((q, i) => (
        <div key={i} className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="rounded bg-primary/10 px-2 py-0.5 font-medium text-primary">
              {q.question_type}
            </span>
            <span className="rounded bg-muted px-2 py-0.5 text-muted-foreground">
              {q.difficulty}
            </span>
            <span className="rounded bg-muted px-2 py-0.5 text-muted-foreground">
              {q.target_skill}
            </span>
          </div>
          <p className="text-sm">{q.question_text}</p>
          <button
            onClick={() => copyToClipboard(q.question_text)}
            className="text-xs text-primary hover:underline"
          >
            Copy
          </button>
        </div>
      ))}
    </div>
  );
}
