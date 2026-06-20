"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CodeEditorProps {
  initialCode?: string;
  language?: string;
  onSubmit?: (code: string) => void;
  onRun?: (code: string) => void;
  isSubmitting?: boolean;
  isRunning?: boolean;
  readOnly?: boolean;
}

export function CodeEditor({
  initialCode = "",
  language = "python",
  onSubmit,
  onRun,
  isSubmitting = false,
  isRunning = false,
  readOnly = false,
}: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.max(300, textareaRef.current.scrollHeight)}px`;
    }
  }, [code]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.currentTarget as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const newCode = code.substring(0, start) + "    " + code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      }, 0);
    }
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Code Editor</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{language}</span>
            {onRun && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRun(code)}
                disabled={isRunning || readOnly}
              >
                {isRunning ? "Running..." : "Run"}
              </Button>
            )}
            {onSubmit && (
              <Button
                size="sm"
                onClick={() => onSubmit(code)}
                disabled={isSubmitting || readOnly}
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative">
          <div className="absolute left-0 top-0 w-12 bg-muted/50 text-right pr-2 pt-2 text-xs text-muted-foreground select-none">
            {code.split("\n").map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={handleKeyDown}
            readOnly={readOnly}
            className="w-full min-h-[300px] p-2 pl-14 bg-muted/30 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Write your code here..."
            spellCheck={false}
          />
        </div>
      </CardContent>
    </Card>
  );
}
