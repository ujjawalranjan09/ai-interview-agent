"use client";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, Calendar, Briefcase, ExternalLink } from "lucide-react";

const integrations = [
  { name: "Slack", description: "Send interview notifications to Slack channels", icon: MessageSquare, href: "/settings/integrations/slack", color: "text-green-500" },
  { name: "Microsoft Teams", description: "Send interview notifications to Teams channels", icon: MessageSquare, href: "/settings/integrations/teams", color: "text-purple-500" },
  { name: "Calendar", description: "Sync interviews with Google Calendar or Outlook", icon: Calendar, href: "/settings/integrations/calendar", color: "text-blue-500" },
  { name: "ATS (Greenhouse/Lever)", description: "Push interview results to your ATS", icon: Briefcase, href: "/settings/integrations/ats", color: "text-orange-500" },
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">Integrations</h1><p className="text-muted-foreground">Connect your tools to automate workflows</p></div>
      <div className="grid gap-4 md:grid-cols-2">
        {integrations.map((integration) => (
          <Link key={integration.name} href={integration.href}>
            <Card className="hover:bg-accent transition-colors cursor-pointer">
              <CardHeader className="flex flex-row items-center gap-4">
                <integration.icon className={`h-8 w-8 ${integration.color}`} />
                <div><CardTitle className="text-lg">{integration.name}</CardTitle><CardDescription>{integration.description}</CardDescription></div>
              </CardHeader>
              <CardContent className="flex items-center text-sm text-muted-foreground"><ExternalLink className="mr-1 h-3 w-3" /> Configure</CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
