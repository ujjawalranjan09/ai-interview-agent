"use client";

interface MatchResultsProps {
  matchPercentage: number;
  matchedRequired: string[];
  missingRequired: string[];
  matchedPreferred: string[];
  missingPreferred: string[];
}

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-block rounded-full px-3 py-1 text-xs font-medium mr-1 mb-1"
      style={{ backgroundColor: `${color}20`, color }}
    >
      {label}
    </span>
  );
}

export function MatchResults({
  matchPercentage,
  matchedRequired,
  missingRequired,
  matchedPreferred,
  missingPreferred,
}: MatchResultsProps) {
  const color = matchPercentage >= 80 ? "#22c55e" : matchPercentage >= 60 ? "#eab308" : "#ef4444";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <svg width="80" height="80" viewBox="0 0 36 36">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={`${matchPercentage}, 100`}
          />
          <text x="18" y="20.5" textAnchor="middle" fontSize="6" fill={color} fontWeight="bold">
            {matchPercentage}%
          </text>
        </svg>
        <div>
          <p className="text-lg font-bold" style={{ color }}>
            {matchPercentage >= 80 ? "Strong Match" : matchPercentage >= 60 ? "Moderate Match" : "Weak Match"}
          </p>
          <p className="text-sm text-muted-foreground">Match Percentage</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm font-medium mb-2">Required Skills Met</p>
          <div>
            {matchedRequired.length ? matchedRequired.map((s) => <Chip key={s} label={s} color="#22c55e" />) : <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium mb-2">Required Skills Missing</p>
          <div>
            {missingRequired.length ? missingRequired.map((s) => <Chip key={s} label={s} color="#ef4444" />) : <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium mb-2">Preferred Skills Met</p>
          <div>
            {matchedPreferred.length ? matchedPreferred.map((s) => <Chip key={s} label={s} color="#22c55e" />) : <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium mb-2">Preferred Skills Missing</p>
          <div>
            {missingPreferred.length ? missingPreferred.map((s) => <Chip key={s} label={s} color="#f97316" />) : <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
