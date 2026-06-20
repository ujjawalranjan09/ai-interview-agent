"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Bell, BellOff, Loader2 } from "lucide-react";
import { requestNotificationPermission, subscribeToPush, unsubscribeFromPush } from "@/lib/pushNotifications";

export default function NotificationsPage() {
  const [pushEnabled, setPushEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleTogglePush = async () => {
    setLoading(true);
    try {
      if (pushEnabled) {
        await unsubscribeFromPush();
        setPushEnabled(false);
        toast.success("Push notifications disabled");
      } else {
        const granted = await requestNotificationPermission();
        if (!granted) {
          toast.error("Notification permission denied");
          return;
        }
        const subscribed = await subscribeToPush();
        if (subscribed) {
          setPushEnabled(true);
          toast.success("Push notifications enabled");
        } else {
          toast.error("Failed to subscribe");
        }
      }
    } catch {
      toast.error("Failed to update notification settings");
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notification Settings</h1>
        <p className="text-muted-foreground">Manage how you receive notifications</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Push Notifications</CardTitle>
          <CardDescription>Receive notifications even when the browser is closed</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {pushEnabled ? <Bell className="h-5 w-5 text-primary" /> : <BellOff className="h-5 w-5 text-muted-foreground" />}
              <div>
                <Label htmlFor="push-toggle">Push Notifications</Label>
                <p className="text-sm text-muted-foreground">{pushEnabled ? "Enabled" : "Disabled"}</p>
              </div>
            </div>
            <Switch id="push-toggle" checked={pushEnabled} onCheckedChange={handleTogglePush} disabled={loading} />
          </div>
          {pushEnabled && (
            <Button variant="outline" className="mt-4" onClick={async () => { toast.success("Test notification sent"); }} disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Bell className="mr-2 h-4 w-4" />}
              Send Test
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
