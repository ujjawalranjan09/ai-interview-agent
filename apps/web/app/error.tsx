"use client";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 text-center max-w-md">
        <AlertTriangle className="h-16 w-16 text-destructive" />
        <h1 className="text-4xl font-bold">500</h1>
        <h2 className="text-xl font-semibold">Something went wrong</h2>
        <p className="text-muted-foreground">
          An unexpected error occurred. Our team has been notified.
        </p>
        <p className="text-xs text-muted-foreground">
          Error ID: {error.digest || "unknown"}
        </p>
        <div className="flex gap-3 mt-4">
          <Button variant="outline" onClick={() => reset()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
          <Link href="/dashboard">
            <Button>
              <Home className="mr-2 h-4 w-4" /> Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
