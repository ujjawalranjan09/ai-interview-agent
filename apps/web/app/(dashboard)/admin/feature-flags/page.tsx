"use client";
import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Loader2, Flag } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  enabled_for_roles: string;
}

export default function FeatureFlagsPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState("");
  const [newName, setNewName] = useState("");
  const [open, setOpen] = useState(false);

  const loadFlags = async () => {
    try {
      const data = await apiFetch<FeatureFlag[]>("/api/v1/feature-flags/");
      setFlags(data);
    } catch {
      toast.error("Failed to load feature flags");
    }
    setLoading(false);
  };

  useEffect(() => {
    loadFlags();
  }, []);

  const toggleFlag = async (key: string, enabled: boolean) => {
    try {
      await apiFetch(`/api/v1/feature-flags/${key}`, {
        method: "PATCH",
        json: { enabled },
      });
      setFlags(prev => prev.map(f => f.key === key ? { ...f, enabled } : f));
      toast.success(`${key} ${enabled ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update flag");
    }
  };

  const createFlag = async () => {
    if (!newKey || !newName) return;
    try {
      await apiFetch("/api/v1/feature-flags/", {
        method: "POST",
        json: { key: newKey, name: newName },
      });
      setOpen(false);
      setNewKey("");
      setNewName("");
      loadFlags();
      toast.success("Flag created");
    } catch {
      toast.error("Failed to create flag");
    }
  };

  if (loading) return <div className="flex items-center justify-center p-8"><Loader2 className="h-6 w-6 animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Feature Flags</h1>
          <p className="text-muted-foreground">Manage feature rollout and A/B testing</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> New Flag
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Feature Flag</DialogTitle>
              <DialogDescription>Add a new feature flag to control feature rollout</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="key">Flag Key</Label>
                <Input id="key" value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="new-feature" />
              </div>
              <div>
                <Label htmlFor="name">Display Name</Label>
                <Input id="name" value={newName} onChange={e => setNewName(e.target.value)} placeholder="New Feature" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={createFlag}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <Card>
        <CardContent className="p-0">
          {flags.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center">
              <Flag className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No feature flags yet</p>
            </div>
          ) : (
            <div className="divide-y">
              {flags.map(flag => (
                <div key={flag.id} className="flex items-center justify-between p-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{flag.name}</span>
                      <Badge variant="outline" className="font-mono text-xs">{flag.key}</Badge>
                    </div>
                    {flag.description && <p className="mt-1 text-sm text-muted-foreground">{flag.description}</p>}
                  </div>
                  <Switch checked={flag.enabled} onCheckedChange={v => toggleFlag(flag.key, v)} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
