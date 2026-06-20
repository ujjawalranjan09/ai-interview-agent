"use client";
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Keyboard } from "lucide-react";
import { useRouter } from "next/navigation";

interface Shortcut {
  key: string;
  label: string;
  action: () => void;
}

export function KeyboardShortcuts() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const shortcuts: Shortcut[] = [
    { key: "g d", label: "Go to Dashboard", action: () => router.push("/") },
    { key: "g i", label: "Go to Interviews", action: () => router.push("/interviews") },
    { key: "g s", label: "Go to Settings", action: () => router.push("/settings") },
    { key: "n", label: "Create new interview", action: () => router.push("/interviews/new") },
    { key: "/", label: "Focus search", action: () => document.querySelector<HTMLInputElement>('[aria-label="Search"]')?.focus() },
    { key: "?", label: "Show keyboard shortcuts", action: () => setOpen(true) },
  ];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      const key = e.key.toLowerCase();
      if (key === "?") {
        e.preventDefault();
        setOpen(true);
        return;
      }

      const shortcut = shortcuts.find(s => s.key === key);
      if (shortcut) {
        e.preventDefault();
        shortcut.action();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [shortcuts, router]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Keyboard shortcuts">
          <Keyboard className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>Navigate faster with keyboard shortcuts</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {shortcuts.map(shortcut => (
            <div key={shortcut.key} className="flex items-center justify-between">
              <span className="text-sm">{shortcut.label}</span>
              <kbd className="inline-flex items-center rounded border bg-muted px-2 py-1 font-mono text-xs">
                {shortcut.key === "?" ? "?" : shortcut.key.toUpperCase()}
              </kbd>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
