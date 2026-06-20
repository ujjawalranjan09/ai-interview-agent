"use client";

import { useParams } from "next/navigation";
import { useCoachingPlan, useGenerateCoaching } from "@/hooks/useReport";
import { CoachingOverview } from "@/components/coaching/CoachingOverview";
import { StudyTimeline } from "@/components/coaching/StudyTimeline";
import { TopicCard } from "@/components/coaching/TopicCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TopicPlan {
  topic: string;
  current_level: string;
  target_level: string;
  resources: { title: string; type: string; url: string }[];
  practice_exercises: string[];
  estimated_time: string;
}

interface CoachingPlan {
  strong_topics: string[];
  weak_topics: string[];
  one_week_plan: string;
  one_month_plan: string;
  three_month_plan: string;
  topic_plans: TopicPlan[];
  coaching_advice: string;
}

export default function CoachingPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: plan, isLoading } = useCoachingPlan(id) as { data: CoachingPlan | undefined; isLoading: boolean };
  const generateCoaching = useGenerateCoaching();

  if (isLoading) return <div className="text-center py-12 text-muted-foreground">Loading...</div>;

  if (!plan) {
    return (
      <div className="text-center py-12 space-y-4">
        <p className="text-muted-foreground">No coaching plan generated yet.</p>
        <Button onClick={() => generateCoaching.mutateAsync({ interviewId: id }).catch(() => {})} disabled={generateCoaching.isPending}>
          {generateCoaching.isPending ? "Generating..." : "Generate Coaching Plan"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Coaching Plan</h1>
        <Button variant="outline" size="sm" onClick={() => generateCoaching.mutateAsync({ interviewId: id, force: true }).catch(() => {})}>
          Regenerate
        </Button>
      </div>

      <CoachingOverview strongTopics={plan.strong_topics || []} weakTopics={plan.weak_topics || []} />

      <Card>
        <CardHeader><CardTitle>Study Timeline</CardTitle></CardHeader>
        <CardContent>
          <StudyTimeline
            oneWeek={plan.one_week_plan || ""}
            oneMonth={plan.one_month_plan || ""}
            threeMonth={plan.three_month_plan || ""}
          />
        </CardContent>
      </Card>

      {plan.topic_plans?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Topic Plans</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {plan.topic_plans.map((t, i) => (
              <TopicCard key={i} topic={t.topic} currentLevel={t.current_level} targetLevel={t.target_level}
                resources={t.resources || []} exercises={t.practice_exercises || []} estimatedTime={t.estimated_time} />
            ))}
          </CardContent>
        </Card>
      )}

      {plan.coaching_advice && (
        <Card>
          <CardHeader><CardTitle>Coaching Advice</CardTitle></CardHeader>
          <CardContent><p className="whitespace-pre-wrap">{plan.coaching_advice}</p></CardContent>
        </Card>
      )}
    </div>
  );
}
