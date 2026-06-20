"use client";
import { useEffect, useRef, useCallback } from "react";

export function useFocusTrap(active: boolean) {
  const ref = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!active || !ref.current) return;
    const focusable = ref.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.key === "Escape") {
      const closeBtn = ref.current.querySelector('[aria-label="Close"]') as HTMLElement;
      closeBtn?.click();
      return;
    }

    if (e.key === "Tab") {
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
  }, [active]);

  useEffect(() => {
    if (!active) return;
    document.addEventListener("keydown", handleKeyDown);
    ref.current?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )?.focus();
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [active, handleKeyDown]);

  return ref;
}
