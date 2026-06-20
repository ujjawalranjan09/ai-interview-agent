"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bell, Webhook, Shield, Building2, Palette, Puzzle, ArrowRight } from "lucide-react";

const settingsItems = [
  { title: "Notifications", description: "Push notification preferences", href: "/settings/notifications", icon: Bell },
  { title: "Webhooks", description: "Manage webhook endpoints", href: "/settings/webhooks", icon: Webhook },
  { title: "GDPR & Privacy", description: "Data retention and privacy settings", href: "/settings/gdpr", icon: Shield },
  { title: "Organization", description: "Organization profile and settings", href: "/settings/organization", icon: Building2 },
  { title: "Branding", description: "Customize your organization branding", href: "/settings/branding", icon: Palette },
  { title: "Integrations", description: "Connect third-party services", href: "/settings/integrations", icon: Puzzle },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage your account and application settings</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {settingsItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href}>
              <Card className="h-full transition-colors hover:bg-muted/50 cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </div>
                  <CardDescription>{item.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex justify-end">
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
