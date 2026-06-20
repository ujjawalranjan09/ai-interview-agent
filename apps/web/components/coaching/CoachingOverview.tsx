"use client";

interface CoachingOverviewProps {
  strongTopics: string[];
  weakTopics: string[];
}

export function CoachingOverview({ strongTopics, weakTopics }: CoachingOverviewProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="p-4 rounded-lg bg-green-50 border border-green-200">
        <h4 className="font-semibold text-green-800 mb-2">Strong Areas</h4>
        <div className="flex flex-wrap gap-1">
          {strongTopics.map((t) => (
            <span key={t} className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">{t}</span>
          ))}
          {!strongTopics.length && <span className="text-sm text-green-700">None identified</span>}
        </div>
      </div>
      <div className="p-4 rounded-lg bg-red-50 border border-red-200">
        <h4 className="font-semibold text-red-800 mb-2">Areas to Improve</h4>
        <div className="flex flex-wrap gap-1">
          {weakTopics.map((t) => (
            <span key={t} className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-700">{t}</span>
          ))}
          {!weakTopics.length && <span className="text-sm text-red-700">None identified</span>}
        </div>
      </div>
    </div>
  );
}
