"use client";

import { useCandidateProfile, useCandidateInterviews } from "@/hooks/usePortal";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function PortalDashboardPage() {
  const { data: profile, isLoading: profileLoading } = useCandidateProfile();
  const { data: interviewsData, isLoading: interviewsLoading } = useCandidateInterviews();

  if (profileLoading || interviewsLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Candidate Portal</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p><span className="font-medium">Name:</span> {profile?.name || "Not set"}</p>
            <p><span className="font-medium">Email:</span> {profile?.email || "Not set"}</p>
            <p><span className="font-medium">Phone:</span> {profile?.phone || "Not set"}</p>
            {profile?.skills && profile.skills.length > 0 && (
              <div>
                <p className="font-medium">Skills:</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile.skills.map((skill, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-muted rounded">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <Link href="/portal/profile">
              <Button variant="outline" className="mt-2">Edit Profile</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p>
              <span className="font-medium">Total Interviews:</span>{" "}
              {profile?.stats.total_interviews || 0}
            </p>
            <p>
              <span className="font-medium">Completed:</span>{" "}
              {profile?.stats.completed_interviews || 0}
            </p>
            <p>
              <span className="font-medium">Average Score:</span>{" "}
              {profile?.stats.average_score || 0}%
            </p>
            <p>
              <span className="font-medium">Best Score:</span>{" "}
              {profile?.stats.best_score || 0}%
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Interviews</CardTitle>
        </CardHeader>
        <CardContent>
          {!interviewsData?.items?.length ? (
            <p className="text-muted-foreground">No interviews yet</p>
          ) : (
            <div className="space-y-3">
              {interviewsData.items.slice(0, 5).map((interview) => (
                <div
                  key={interview.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">Interview {interview.id.slice(0, 8)}...</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(interview.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className={`font-medium ${
                        (interview.total_score || 0) >= 70
                          ? "text-green-600"
                          : (interview.total_score || 0) >= 50
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}>
                        {interview.total_score ? `${Math.round(interview.total_score)}%` : "—"}
                      </p>
                      <p className="text-xs text-muted-foreground">{interview.status}</p>
                    </div>
                    <Link href={`/portal/interviews/${interview.id}`}>
                      <Button variant="ghost" size="sm">View</Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
