"use client";

import { useState } from "react";
import {
  useWebhooks,
  useCreateWebhook,
  useDeleteWebhook,
  useTestWebhook,
} from "@/hooks/useWebhooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const AVAILABLE_EVENTS = [
  "interview.created",
  "interview.started",
  "interview.completed",
  "interview.closed",
  "question.answered",
  "candidate.created",
];

export default function WebhooksPage() {
  const { data, isLoading } = useWebhooks();
  const createWebhook = useCreateWebhook();
  const deleteWebhook = useDeleteWebhook();
  const testWebhook = useTestWebhook();

  const [showCreate, setShowCreate] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
    secret: "",
  });

  const handleCreate = async () => {
    if (!newWebhook.name || !newWebhook.url) return;
    await createWebhook.mutateAsync({
      name: newWebhook.name,
      url: newWebhook.url,
      events: newWebhook.events,
      secret: newWebhook.secret || undefined,
    });
    setShowCreate(false);
    setNewWebhook({ name: "", url: "", events: [], secret: "" });
  };

  const handleTest = async (id: string) => {
    const result = await testWebhook.mutateAsync(id);
    alert(result.success ? "Test webhook delivered successfully!" : `Test failed: ${result.error}`);
  };

  const toggleEvent = (event: string) => {
    setNewWebhook((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <Button onClick={() => setShowCreate(true)}>New Webhook</Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create Webhook</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                type="text"
                value={newWebhook.name}
                onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="e.g., My Webhook"
              />
            </div>
            <div>
              <label className="text-sm font-medium">URL</label>
              <input
                type="url"
                value={newWebhook.url}
                onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="https://example.com/webhook"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Secret (optional)</label>
              <input
                type="text"
                value={newWebhook.secret}
                onChange={(e) => setNewWebhook({ ...newWebhook, secret: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Signing secret"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Events</label>
              <div className="flex flex-wrap gap-2 mt-1">
                {AVAILABLE_EVENTS.map((event) => (
                  <button
                    key={event}
                    onClick={() => toggleEvent(event)}
                    className={`text-xs px-2 py-1 rounded ${
                      newWebhook.events.includes(event)
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {event}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createWebhook.isPending}>
                {createWebhook.isPending ? "Creating..." : "Create"}
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : !data?.items?.length ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No webhooks configured yet. Create a webhook to receive event notifications.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data.items.map((webhook) => (
            <Card key={webhook.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{webhook.name}</h3>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          webhook.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {webhook.is_active ? "Active" : "Inactive"}
                      </span>
                      {webhook.failure_count > 0 && (
                        <span className="text-xs text-red-600">
                          {webhook.failure_count} failures
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{webhook.url}</p>
                    <div className="flex gap-1 mt-2">
                      {webhook.events.map((event) => (
                        <span key={event} className="text-xs px-1 bg-muted rounded">
                          {event}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTest(webhook.id)}
                      disabled={testWebhook.isPending}
                    >
                      Test
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => deleteWebhook.mutate(webhook.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
