import { cn } from "@/lib/utils";

export function Kbd({ className, ...props }: React.ComponentProps<"kbd">) {
  return (
    <kbd
      className={cn(
        "inline-flex items-center rounded border bg-muted px-2 py-1 font-mono text-xs",
        className
      )}
      {...props}
    />
  );
}
