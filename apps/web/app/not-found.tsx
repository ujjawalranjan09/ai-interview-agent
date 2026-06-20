"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft, FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 text-center max-w-md">
        <FileQuestion className="h-16 w-16 text-muted-foreground" />
        <h1 className="text-4xl font-bold">404</h1>
        <h2 className="text-xl font-semibold">Page Not Found</h2>
        <p className="text-muted-foreground">
          The page you are looking for does not exist or has been moved.
        </p>
        <div className="flex gap-3 mt-4">
          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Go Back
          </Button>
          <Link href="/">
            <Button>
              <Home className="mr-2 h-4 w-4" /> Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
