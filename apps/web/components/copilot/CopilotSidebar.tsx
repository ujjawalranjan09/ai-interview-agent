"use client";

import { SuggestionCard } from "./SuggestionCard";

interface Suggestion {
  id: string;
  type: string;
  icon: string;
  color: string;
  text: string;
  dismissed?: boolean;
}

interface CopilotSidebarProps {
  suggestions: Suggestion[];
  onDismiss: (id: string) => void;
}

export function CopilotSidebar({
  suggestions,
  onDismiss,
}: CopilotSidebarProps) {
  const visible = suggestions.filter((s) => !s.dismissed);

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-lg font-semibold mb-3">🤖 AI Suggestions</h2>
      <div className="flex-1 overflow-y-auto space-y-2">
        {visible.length === 0 ? (
          <p className="text-sm text-muted-foreground">No suggestions yet</p>
        ) : (
          visible.map((s) => (
            <SuggestionCard
              key={s.id}
              id={s.id}
              type={s.type}
              icon={s.icon}
              color={s.color}
              text={s.text}
              onDismiss={onDismiss}
            />
          ))
        )}
      </div>
    </div>
  );
}
