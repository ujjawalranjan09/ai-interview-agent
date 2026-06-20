"use client";

import { useAuth } from "@/hooks/useAuth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LanguageSwitcher } from "@/components/shared/LanguageSwitcher";
import { ThemeToggle } from "@/components/shared/ThemeToggle";

export function TopBar() {
  const { user, logout } = useAuth();
  const initials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "??";

  return (
    <header className="h-14 border-b flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <LanguageSwitcher />
      <DropdownMenu>
        <DropdownMenuTrigger aria-label="Open user menu" className="relative flex h-8 w-8 items-center justify-center rounded-full hover:bg-accent">
          <Avatar className="h-8 w-8">
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem className="font-medium">{user?.full_name}</DropdownMenuItem>
          <DropdownMenuItem>{user?.email}</DropdownMenuItem>
          <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      </div>
    </header>
  );
}
