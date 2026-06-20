"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Link2, Link2Off, Loader2, Send, MessageSquare } from "lucide-react";
import { useSlackIntegrations, useConnectSlack, useDeleteSlack, useTestSlack } from "@/hooks/useIntegrations";

const EVENTS = [
  { value: "interview.completed", label: "Interview Completed" },
  { value: "report.generated", label: "Report Generated" },
  { value: "interview.scheduled", label: "Interview Scheduled" },
];

export default function SlackPage() {
  const { data: integrations, isLoading } = useSlackIntegrations();
  const connectSlack = useConnectSlack();
  const deleteSlack = useDeleteSlack();
  const testSlack = useTestSlack();
  const [webhookUrl, setWebhookUrl] = useState("");
  const [channelName, setChannelName] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([EVENTS[0].value]);

  const handleConnect = async () => {
    if (!webhookUrl || !channelName) return;
    try {
      await connectSlack.mutateAsync({ webhook_url: webhookUrl, channel_name: channelName, events: selectedEvents });
      toast.success("Slack connected");
      setWebhookUrl("");
      setChannelName("");
    } catch { toast.error("Failed to connect"); }
  };

  const handleDelete = async (id: string) => {
    try { await deleteSlack.mutateAsync(id); toast.success("Integration removed"); }
    catch { toast.error("Failed to remove"); }
  };

  const handleTest = async (id: string) => {
    try { await testSlack.mutateAsync(id); toast.success("Test message sent"); }
    catch { toast.error("Failed to send test"); }
  };

  const toggleEvent = (value: string) => {
    setSelectedEvents(prev => prev.includes(value) ? prev.filter(e => e !== value) : [...prev, value]);
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">Slack Integration</h1><p className="text-muted-foreground">Send interview notifications to Slack</p></div>

      <Card>
        <CardHeader><CardTitle>Connect Slack</CardTitle><CardDescription>Create an Incoming Webhook in Slack and paste the URL below</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2"><Label>Webhook URL</Label><Input placeholder="https://hooks.slack.com/services/..." value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)} /></div>
          <div className="space-y-2"><Label>Channel Name</Label><Input placeholder="#interviews" value={channelName} onChange={e => setChannelName(e.target.value)} /></div>
          <div className="space-y-2"><Label>Events to Notify</Label>{EVENTS.map(e => (
            <label key={e.value} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedEvents.includes(e.value)} onChange={() => toggleEvent(e.value)} />{e.label}</label>
          ))}</div>
          <Button onClick={handleConnect} disabled={connectSlack.isPending}><Link2 className="mr-2 h-4 w-4" /> Connect Slack</Button>
        </CardContent>
      </Card>

      {isLoading ? <div className="flex justify-center py-4"><Loader2 className="h-5 w-5 animate-spin" /></div> : integrations?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Connected Channels</CardTitle></CardHeader>
          <CardContent className="space-y-4">{integrations.map((i: any) => (
            <div key={i.id} className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-3"><MessageSquare className="h-5 w-5 text-muted-foreground" /><div><p className="text-sm font-medium">{i.channel_name}</p><p className="text-xs text-muted-foreground">{i.events?.length || 0} events</p></div></div>
              <div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => handleTest(i.id)} disabled={testSlack.isPending}><Send className="mr-1 h-3 w-3" /> Test</Button><Button variant="destructive" size="sm" onClick={() => handleDelete(i.id)}><Link2Off className="mr-1 h-3 w-3" /> Remove</Button></div>
            </div>
          ))}</CardContent>
        </Card>
      )}
    </div>
  );
}
