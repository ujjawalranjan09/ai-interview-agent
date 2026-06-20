"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X, Download } from "lucide-react";

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem("install-prompt-dismissed");
    if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) return;

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShow(true);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === "accepted") {
      setShow(false);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShow(false);
    localStorage.setItem("install-prompt-dismissed", String(Date.now()));
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-sm rounded-lg border bg-card p-4 shadow-lg" role="alert">
      <div className="flex items-start gap-3">
        <Download className="mt-1 h-5 w-5 text-primary" />
        <div className="flex-1">
          <p className="text-sm font-medium">Install AI Interview Agent</p>
          <p className="text-xs text-muted-foreground">Get quick access and offline support</p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleDismiss} aria-label="Dismiss install prompt">
          <X className="h-4 w-4" />
        </Button>
      </div>
      <Button className="mt-3 w-full" onClick={handleInstall}>
        <Download className="mr-2 h-4 w-4" /> Install
      </Button>
    </div>
  );
}
