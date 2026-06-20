import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    title: "AI-Powered Questions",
    description: "Adaptive question generation based on candidate resume and skills.",
    icon: "🤖",
  },
  {
    title: "Multimodal Analysis",
    description: "Voice, facial emotion, and text analysis for comprehensive evaluation.",
    icon: "🎯",
  },
  {
    title: "Real-time Copilot",
    description: "AI suggestions for human interviewers during live sessions.",
    icon: "💡",
  },
  {
    title: "Coaching Plans",
    description: "Personalized improvement roadmaps with curated resources.",
    icon: "📚",
  },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b">
        <div className="container mx-auto px-6 h-14 flex items-center justify-between">
          <span className="font-bold text-lg">🎯 AI Interview Agent</span>
          <div className="flex gap-3">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="container mx-auto px-6 py-24 text-center">
          <h1 className="text-5xl font-bold tracking-tight mb-6">
            Smarter Interviews,<br />Better Hires
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            AI-powered interview platform with multimodal analysis, adaptive questions,
            and real-time coaching — helping you find the best candidates.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register">
              <Button size="lg">Start Free</Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Sign In
              </Button>
            </Link>
          </div>
        </section>

        <section className="container mx-auto px-6 pb-24">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <Card key={f.title}>
                <CardContent className="pt-6">
                  <div className="text-4xl mb-3">{f.icon}</div>
                  <h3 className="font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        AI Interview Agent &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
