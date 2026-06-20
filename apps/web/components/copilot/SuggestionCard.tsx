"use client";

interface SuggestionCardProps {
  id: string;
  type: string;
  icon: string;
  color: string;
  text: string;
  onDismiss: (id: string) => void;
}

export function SuggestionCard({
  id,
  type,
  icon,
  color,
  text,
  onDismiss,
}: SuggestionCardProps) {
  return (
    <div
      className="flex items-start gap-3 rounded-lg border p-3"
      style={{ backgroundColor: `${color}20` }}
    >
      <span className="text-2xl">{icon}</span>
      <div className="flex-1 min-w-0">
        <span
          className="inline-block rounded-full px-2 py-0.5 text-xs font-medium mb-1"
          style={{ backgroundColor: `${color}40`, color }}
        >
          {type}
        </span>
        <p className="text-sm">{text}</p>
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="text-muted-foreground hover:text-foreground shrink-0 ml-2"
      >
        ✕
      </button>
    </div>
  );
}
