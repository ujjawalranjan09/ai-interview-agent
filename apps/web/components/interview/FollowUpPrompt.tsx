"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface FollowUpPromptProps {
  questionText: string;
  onAnswer: () => void;
  onSkip: () => void;
}

export function FollowUpPrompt({ questionText, onAnswer, onSkip }: FollowUpPromptProps) {
  return (
    <Card className="border-2 border-dashed border-primary/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-primary">Follow-up Question</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-lg">{questionText}</p>
        <div className="flex gap-2">
          <Button onClick={onAnswer} size="sm">Answer</Button>
          <Button onClick={onSkip} variant="outline" size="sm">Skip</Button>
        </div>
      </CardContent>
    </Card>
  );
}
