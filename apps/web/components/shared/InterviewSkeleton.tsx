import { Skeleton } from "@/components/shared/Skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function InterviewSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-32 mt-2" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardContent>
    </Card>
  );
}

export function InterviewListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4" aria-busy="true" role="status">
      <span className="sr-only">Loading interviews...</span>
      {Array.from({ length: count }).map((_, i) => (
        <InterviewSkeleton key={i} />
      ))}
    </div>
  );
}
