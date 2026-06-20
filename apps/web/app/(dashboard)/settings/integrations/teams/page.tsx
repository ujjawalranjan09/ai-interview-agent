"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Link2, Link2Off, Loader2, Send, MessageSquare } from "lucide-react";
import { useTeamsIntegrations, useConnectTeams, useDeleteTeams, useTestTeams } from "@/hooks/useIntegrations";

const EVENTS = [
  { value: "interview.completed", label: "Interview Completed" },
  { value: "report.generated", label: "Report Generated" },
];

export default function TeamsPage() {
  const { data: integrations, isLoading } = useTeamsIntegrations();
  const connectTeams = useConnectTeams();
  const deleteTeams = useDeleteTeams();
  const testTeams = useTestTeams();
  const [webhookUrl, setWebhookUrl] = useState("");
  const [channelName, setChannelName] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([EVENTS[0].value]);

  const handleConnect = async () => {
    if (!webhookUrl || !channelName) return;
    try {
      await connectTeams.mutateAsync({ webhook_url: webhookUrl, channel_name: channelName, events: selectedEvents });
      toast.success("Teams connected");
      setWebhookUrl(""); setChannelName("");
    } catch { toast.error("Failed to connect"); }
  };

  const handleDelete = async (id: string) => {
    try { await deleteTeams.mutateAsync(id); toast.success("Integration removed"); }
    catch { toast.error("Failed to remove"); }
  };

  const handleTest = async (id: string) => {
    try { await testTeams.mutateAsync(id); toast.success("Test message sent"); }
    catch { toast.error("Failed to send test"); }
  };

  const toggleEvent = (value: string) => {
    setSelectedEvents(prev => prev.includes(value) ? prev.filter(e => e !== value) : [...prev, value]);
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">Microsoft Teams Integration</h1><p className="text-muted-foreground">Send interview notifications to Teams</p></div>
      <Card>
        <CardHeader><CardTitle>Connect Teams</CardTitle><CardDescription>Create an Incoming Webhook in Teams and paste the URL below</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2"><Label>Webhook URL</Label><Input placeholder="https://your-org.webhook.office.com/..." value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)} /></div>
          <div className="space-y-2"><Label>Channel Name</Label><Input placeholder="General" value={channelName} onChange={e => setChannelName(e.target.value)} /></div>
          <div className="space-y-2"><Label>Events to Notify</Label>{EVENTS.map(e => (
            <label key={e.value} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedEvents.includes(e.value)} onChange={() => toggleEvent(e.value)} />{e.label}</label>
          ))}</div>
          <Button onClick={handleConnect} disabled={connectTeams.isPending}><Link2 className="mr-2 h-4 w-4" /> Connect Teams</Button>
        </CardContent>
      </Card>
      {isLoading ? <div className="flex justify-center py-4"><Loader2 className="h-5 w-5 animate-spin" /></div> : integrations?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Connected Channels</CardTitle></CardHeader>
          <CardContent className="space-y-4">{integrations.map((i: any) => (
            <div key={i.id} className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-3"><MessageSquare className="h-5 w-5 text-muted-foreground" /><div><p className="text-sm font-medium">{i.channel_name}</p><p className="text-xs text-muted-foreground">{i.events?.length || 0} events</p></div></div>
              <div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => handleTest(i.id)} disabled={testTeams.isPending}><Send className="mr-1 h-3 w-3" /> Test</Button><Button variant="destructive" size="sm" onClick={() => handleDelete(i.id)}><Link2Off className="mr-1 h-3 w-3" /> Remove</Button></div>
            </div>
          ))}</CardContent>
        </Card>
      )}
    </div>
  );
}
