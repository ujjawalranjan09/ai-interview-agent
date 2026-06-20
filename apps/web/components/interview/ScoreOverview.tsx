"use client";

interface ScoreOverviewProps {
  score: number;
  grade: string;
}

export function ScoreOverview({ score, grade }: ScoreOverviewProps) {
  const circumference = 2 * Math.PI * 70;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-4">
      <svg width="180" height="180" viewBox="0 0 180 180">
        <circle cx="90" cy="90" r="70" fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="90" cy="90" r="70" fill="none"
          stroke={score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444"}
          strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 90 90)" className="transition-all duration-1000"
        />
        <text x="90" y="85" textAnchor="middle" className="text-3xl font-bold" fill="currentColor">
          {Math.round(score)}
        </text>
        <text x="90" y="105" textAnchor="middle" className="text-sm" fill="#6b7280">
          out of 100
        </text>
      </svg>
      <span className="text-lg font-semibold px-3 py-1 rounded-full bg-primary/10 text-primary">
        Grade: {grade}
      </span>
    </div>
  );
}
