"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { AudioRecorder } from "./AudioRecorder";

interface AnswerInputProps {
  onSubmit: (answer: string) => void;
  onAudioUpload?: (blob: Blob) => void;
  isLoading?: boolean;
  isUploading?: boolean;
}

export function AnswerInput({ onSubmit, onAudioUpload, isLoading, isUploading }: AnswerInputProps) {
  const [answer, setAnswer] = useState("");
  const [mode, setMode] = useState<"text" | "voice">("text");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) {
      onSubmit(answer.trim());
      setAnswer("");
    }
  };

  const handleAudioUpload = (blob: Blob) => {
    if (onAudioUpload) {
      onAudioUpload(blob);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2 border-b pb-2">
        <button
          type="button"
          onClick={() => setMode("text")}
          className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
            mode === "text" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Text
        </button>
        <button
          type="button"
          onClick={() => setMode("voice")}
          className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
            mode === "voice" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Voice
        </button>
      </div>

      {mode === "text" ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Textarea
            placeholder="Type your answer here..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={4}
            className="resize-none"
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={!answer.trim() || isLoading}>
              {isLoading ? "Submitting..." : "Submit Answer"}
            </Button>
          </div>
        </form>
      ) : (
        <div className="py-4">
          <AudioRecorder onUpload={handleAudioUpload} isUploading={isUploading} />
          {isUploading && (
            <p className="text-sm text-muted-foreground text-center mt-4">
              Transcribing and evaluating your answer...
            </p>
          )}
        </div>
      )}
    </div>
  );
}
