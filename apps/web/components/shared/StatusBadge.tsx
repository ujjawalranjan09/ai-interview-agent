"use client";

import { cn } from "@/lib/utils";

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-gray-100 text-gray-800" },
  ready: { label: "Ready", className: "bg-blue-100 text-blue-800" },
  in_progress: { label: "In Progress", className: "bg-yellow-100 text-yellow-800" },
  paused: { label: "Paused", className: "bg-orange-100 text-orange-800" },
  completed: { label: "Completed", className: "bg-green-100 text-green-800" },
  cancelled: { label: "Cancelled", className: "bg-red-100 text-red-800" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || { label: status, className: "bg-gray-100 text-gray-800" };
  return (
    <span aria-label={config.label} className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", config.className)}>
      {config.label}
    </span>
  );
}
