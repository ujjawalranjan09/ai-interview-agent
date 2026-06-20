"use client";

interface InterviewProgressProps {
  current: number;
  total: number;
}

export function InterviewProgress({ current, total }: InterviewProgressProps) {
  const percentage = total > 0 ? (current / total) * 100 : 0;

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm text-muted-foreground mb-1">
        <span>Progress</span>
        <span>{current} of {total} questions</span>
      </div>
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
