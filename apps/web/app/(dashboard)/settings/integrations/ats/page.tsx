"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Link2, Link2Off, Loader2, RefreshCw, Upload } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const PROVIDERS = [
  { value: "greenhouse", label: "Greenhouse", desc: "Harvest API" },
  { value: "lever", label: "Lever", desc: "Lever API" },
];

export default function ATSPage() {
  const qc = useQueryClient();
  const [provider, setProvider] = useState("greenhouse");
  const [apiKey, setApiKey] = useState("");
  const [interviewId, setInterviewId] = useState("");

  const { data: integrations, isLoading } = useQuery({
    queryKey: ["integrations", "ats"],
    queryFn: () => apiFetch("/api/v1/integrations/ats"),
  });

  const connectMutation = useMutation({
    mutationFn: (data: any) => apiFetch("/api/v1/integrations/ats", { method: "POST", json: data }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["integrations"] }); toast.success("ATS connected"); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/ats/${id}`, { method: "DELETE" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["integrations"] }); toast.success("Integration removed"); },
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/ats/${id}/sync`, { method: "POST" }),
    onSuccess: (data: any) => toast.success(`Synced: ${data.candidates_pulled} candidates pulled`),
  });

  const pushMutation = useMutation({
    mutationFn: ({ integrationId, interviewId }: { integrationId: string; interviewId: string }) =>
      apiFetch(`/api/v1/integrations/ats/${integrationId}/push/${interviewId}`, { method: "POST" }),
    onSuccess: () => toast.success("Interview pushed to ATS"),
  });

  const handleConnect = () => {
    if (!apiKey) return;
    connectMutation.mutate({ provider, config: { api_key: apiKey } });
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">ATS Integration</h1><p className="text-muted-foreground">Connect your Applicant Tracking System</p></div>
      <Card>
        <CardHeader><CardTitle>Connect ATS</CardTitle><CardDescription>Select your ATS provider and enter API credentials</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2"><Label>Provider</Label>
            <select value={provider} onChange={e => setProvider(e.target.value)} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
              {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label} — {p.desc}</option>)}
            </select>
          </div>
          <div className="space-y-2"><Label>API Key</Label><Input type="password" placeholder="Enter your API key" value={apiKey} onChange={e => setApiKey(e.target.value)} /></div>
          <Button onClick={handleConnect} disabled={connectMutation.isPending}><Link2 className="mr-2 h-4 w-4" /> Connect</Button>
        </CardContent>
      </Card>

      {isLoading ? <div className="flex justify-center py-4"><Loader2 className="h-5 w-5 animate-spin" /></div> : integrations?.length > 0 && integrations.map((i: any) => (
        <Card key={i.id}>
          <CardHeader><CardTitle>{i.provider} Integration</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between"><span className="text-sm">Status</span><span className={`text-sm font-medium ${i.is_active ? "text-green-500" : "text-red-500"}`}>{i.is_active ? "Active" : "Inactive"}</span></div>
            <div className="flex items-center justify-between"><span className="text-sm">Direction</span><span className="text-sm">{i.sync_direction}</span></div>
            {i.last_sync_at && <div className="flex items-center justify-between"><span className="text-sm">Last Sync</span><span className="text-sm">{new Date(i.last_sync_at).toLocaleString()}</span></div>}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => syncMutation.mutate(i.id)} disabled={syncMutation.isPending}><RefreshCw className="mr-1 h-3 w-3" /> Sync Now</Button>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(i.id)}><Link2Off className="mr-1 h-3 w-3" /> Remove</Button>
            </div>
            <div className="pt-2 border-t"><Label>Push Interview Result</Label>
              <div className="flex gap-2 mt-1"><Input placeholder="Interview ID" value={interviewId} onChange={e => setInterviewId(e.target.value)} /><Button variant="outline" size="sm" onClick={() => pushMutation.mutate({ integrationId: i.id, interviewId })} disabled={pushMutation.isPending || !interviewId}><Upload className="mr-1 h-3 w-3" /> Push</Button></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
