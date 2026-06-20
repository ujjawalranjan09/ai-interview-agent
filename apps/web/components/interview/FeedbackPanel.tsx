"use client";

interface FeedbackPanelProps {
  feedback: {
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
    overall_assessment: string;
  };
}

export function FeedbackPanel({ feedback }: FeedbackPanelProps) {
  return (
    <div className="space-y-6">
      <Section title="Strengths" items={feedback.strengths} color="text-green-600" />
      <Section title="Areas for Improvement" items={feedback.weaknesses} color="text-red-600" />
      <Section title="Suggestions" items={feedback.suggestions} color="text-blue-600" />
      {feedback.overall_assessment && (
        <div>
          <h4 className="font-semibold mb-2">Overall Assessment</h4>
          <p className="text-muted-foreground italic">{feedback.overall_assessment}</p>
        </div>
      )}
    </div>
  );
}

function Section({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <h4 className={`font-semibold mb-2 ${color}`}>{title}</h4>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm flex items-start gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-current shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
