"use client";

import { useState } from "react";

interface StudyTimelineProps {
  oneWeek: string;
  oneMonth: string;
  threeMonth: string;
}

export function StudyTimeline({ oneWeek, oneMonth, threeMonth }: StudyTimelineProps) {
  const [tab, setTab] = useState<"1w" | "1m" | "3m">("1w");
  const plans = { "1w": oneWeek, "1m": oneMonth, "3m": threeMonth };
  const labels = { "1w": "1 Week", "1m": "1 Month", "3m": "3 Months" };

  return (
    <div>
      <div className="flex gap-2 border-b mb-4">
        {(["1w", "1m", "3m"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 px-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground"
            }`}
          >
            {labels[t]}
          </button>
        ))}
      </div>
      <div className="prose prose-sm max-w-none whitespace-pre-wrap">{plans[tab]}</div>
    </div>
  );
}
