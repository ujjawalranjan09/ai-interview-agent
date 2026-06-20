"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";

const mainNavItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/dashboard/interviews", label: "Interviews", icon: "📝" },
  { href: "/dashboard/candidates", label: "Candidates", icon: "👤" },
  { href: "/dashboard/banks", label: "Question Banks", icon: "📚" },
  { href: "/dashboard/templates", label: "Templates", icon: "📋" },
  { href: "/dashboard/coding", label: "Coding Practice", icon: "💻" },
];

const roleNavItems = [
  { href: "/dashboard/copilot", label: "Copilot", icon: "🤖", roles: ["interviewer", "admin"] },
  { href: "/dashboard/analytics", label: "Analytics", icon: "📈", roles: ["interviewer", "admin"] },
];

const toolNavItems = [
  { href: "/dashboard/tools/jd", label: "JD Match", icon: "🔍", roles: ["interviewer", "admin"] },
];

const adminNavItems = [
  { href: "/dashboard/admin/users", label: "Users", icon: "👥", roles: ["admin"] },
  { href: "/dashboard/admin/system", label: "System", icon: "⚙️", roles: ["admin"] },
  { href: "/dashboard/admin/audit", label: "Audit Log", icon: "📋", roles: ["admin"] },
  { href: "/admin/monitoring", label: "Monitoring", icon: "📊", roles: ["admin"] },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const role = user?.role || "";

  return (
    <aside className="w-64 border-r bg-muted/30 flex flex-col">
      <div className="p-4">
        <Link href="/dashboard" className="text-lg font-bold">
          🎯 AI Interview Agent
        </Link>
      </div>
      <Separator />
      <nav className="flex-1 p-3 space-y-1" role="navigation" aria-label="Main navigation">
        {mainNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            tabIndex={0}
            aria-label={item.label}
            aria-current={pathname === item.href ? "page" : undefined}
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
        {roleNavItems.filter((i) => i.roles.includes(role)).length > 0 && (
          <>
            <Separator className="my-2" />
              {roleNavItems
                .filter((i) => i.roles.includes(role))
                .map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    tabIndex={0}
                    aria-label={item.label}
                    aria-current={pathname === item.href ? "page" : undefined}
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
          </>
        )}
        {toolNavItems.filter((i) => i.roles.includes(role)).length > 0 && (
          <>
            <Separator className="my-2" />
            <p className="px-3 text-xs font-medium text-muted-foreground uppercase">Tools</p>
            {toolNavItems
              .filter((i) => i.roles.includes(role))
              .map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  tabIndex={0}
                  aria-label={item.label}
                  aria-current={pathname === item.href ? "page" : undefined}
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
          </>
        )}
        {adminNavItems.filter((i) => i.roles.includes(role)).length > 0 && (
          <>
            <Separator className="my-2" />
            <p className="px-3 text-xs font-medium text-muted-foreground uppercase">Admin</p>
            {adminNavItems
              .filter((i) => i.roles.includes(role))
              .map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  tabIndex={0}
                  aria-label={item.label}
                  aria-current={pathname === item.href ? "page" : undefined}
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
          </>
        )}
      </nav>
      <div className="p-4 text-xs text-muted-foreground">
        v0.1.0
      </div>
    </aside>
  );
}
