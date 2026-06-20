"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Eye, Send, Loader2 } from "lucide-react";

const TEMPLATES = [
  "interview_invitation",
  "interview_reminder",
  "interview_completed",
  "report_ready",
  "coaching_ready",
  "welcome",
  "password_reset",
];

export default function EmailTemplatesPage() {
  const [selected, setSelected] = useState(TEMPLATES[0]);
  const [preview, setPreview] = useState<{ subject: string; html: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const loadPreview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/dev/email-preview/${selected}`);
      if (!res.ok) throw new Error("Failed to load");
      const data = await res.json();
      setPreview(data);
    } catch {
      toast.error("Failed to load email preview");
    }
    setLoading(false);
  };

  const sendTest = async () => {
    toast.success("Test email sent (simulated)");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Email Templates</h1>
        <p className="text-muted-foreground">Preview and test email templates</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Template</CardTitle>
          <CardDescription>Choose a template to preview</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TEMPLATES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
            <Button onClick={loadPreview} disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Eye className="mr-2 h-4 w-4" />}
              Preview
            </Button>
            <Button variant="outline" onClick={sendTest}>
              <Send className="mr-2 h-4 w-4" />
              Send Test
            </Button>
          </div>
        </CardContent>
      </Card>

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>{preview.subject}</CardTitle>
          </CardHeader>
          <CardContent>
            <iframe
              srcDoc={preview.html}
              className="w-full border rounded-md"
              style={{ height: "500px" }}
              title="Email preview"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
