"use client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Calendar, Download } from "lucide-react";

export default function CalendarPage() {
  const connectGoogle = async () => {
    try {
      const res = await fetch("/api/v1/auth/google/calendar");
      const data = await res.json();
      if (data.auth_url) window.location.href = data.auth_url;
    } catch { toast.error("Failed to connect"); }
  };

  const connectOutlook = () => {
    toast.info("Outlook OAuth flow — configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env");
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">Calendar Integration</h1><p className="text-muted-foreground">Connect your calendar to auto-sync interview bookings</p></div>
      <Card>
        <CardHeader><CardTitle>Connected Calendars</CardTitle><CardDescription>Sync your availability and bookings</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex items-center gap-3"><Calendar className="h-5 w-5 text-blue-500" /><div><p className="font-medium">Google Calendar</p><p className="text-sm text-muted-foreground">Sync interviews to Google Calendar</p></div></div>
            <Button onClick={connectGoogle}>Connect</Button>
          </div>
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex items-center gap-3"><Calendar className="h-5 w-5 text-purple-500" /><div><p className="font-medium">Outlook Calendar</p><p className="text-sm text-muted-foreground">Sync interviews to Outlook Calendar</p></div></div>
            <Button onClick={connectOutlook}>Connect</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
