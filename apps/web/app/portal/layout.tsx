"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const portalNavItems = [
  { href: "/portal/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/portal/interviews", label: "My Interviews", icon: "📝" },
  { href: "/portal/profile", label: "Profile", icon: "👤" },
];

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4">
          <Link href="/portal/dashboard" className="text-lg font-bold">
            🎯 Candidate Portal
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {portalNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                pathname === item.href
                  ? "bg-accent text-accent-foreground font-medium"
                  : "text-muted-foreground"
              )}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="p-4">
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to Dashboard
          </Link>
        </div>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
