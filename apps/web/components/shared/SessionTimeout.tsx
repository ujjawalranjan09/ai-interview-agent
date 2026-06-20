"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

const TIMEOUT_MS = 30 * 60 * 1000;
const WARNING_MS = 60 * 1000;

export function SessionTimeout() {
  const [showWarning, setShowWarning] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warningRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();

  const resetTimers = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningRef.current) clearTimeout(warningRef.current);

    warningRef.current = setTimeout(() => setShowWarning(true), TIMEOUT_MS - WARNING_MS);
    timeoutRef.current = setTimeout(async () => {
      try {
        await apiFetch("/api/v1/auth/logout", { method: "POST" });
      } catch {}
      router.push("/login");
    }, TIMEOUT_MS);
  }, [router]);

  useEffect(() => {
    const events = ["mousedown", "keydown", "scroll", "touchstart"];
    const handler = () => resetTimers();
    events.forEach(e => document.addEventListener(e, handler));
    resetTimers();
    return () => {
      events.forEach(e => document.removeEventListener(e, handler));
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningRef.current) clearTimeout(warningRef.current);
    };
  }, [resetTimers]);

  const extendSession = () => {
    setShowWarning(false);
    resetTimers();
  };

  return (
    <Dialog open={showWarning} onOpenChange={setShowWarning}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Session Expiring</DialogTitle>
          <DialogDescription>
            Your session will expire in 1 minute due to inactivity.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => router.push("/login")}>Logout</Button>
          <Button onClick={extendSession}>Stay Logged In</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
