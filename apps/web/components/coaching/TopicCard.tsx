"use client";

interface TopicCardProps {
  topic: string;
  currentLevel: string;
  targetLevel: string;
  resources: { title: string; type: string; url: string }[];
  exercises: string[];
  estimatedTime: string;
}

export function TopicCard({ topic, currentLevel, targetLevel, resources, exercises, estimatedTime }: TopicCardProps) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">{topic}</h4>
        <span className="text-xs text-muted-foreground">{estimatedTime}</span>
      </div>
      <div className="text-sm">
        <span className="text-muted-foreground">Level:</span> {currentLevel} → {targetLevel}
      </div>
      {resources.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-muted-foreground mb-1">Resources</h5>
          <ul className="space-y-1">
            {resources.map((r, i) => (
              <li key={i} className="text-sm">
                {r.url ? (
                  <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{r.title}</a>
                ) : (
                  <span>{r.title}</span>
                )}
                <span className="text-muted-foreground ml-1">({r.type})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {exercises.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-muted-foreground mb-1">Practice</h5>
          <ul className="space-y-1">
            {exercises.map((e, i) => <li key={i} className="text-sm">{e}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
