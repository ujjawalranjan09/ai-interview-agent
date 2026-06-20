"use client";
interface LiveRegionProps {
  children: React.ReactNode;
  assertive?: boolean;
}

export function LiveRegion({ children, assertive }: LiveRegionProps) {
  return (
    <div
      role="status"
      aria-live={assertive ? "assertive" : "polite"}
      aria-atomic="true"
      className="sr-only"
    >
      {children}
    </div>
  );
}
