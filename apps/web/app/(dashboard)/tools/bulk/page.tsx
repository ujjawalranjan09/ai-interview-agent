"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Upload, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { useBulkImportCandidates, useBulkDelete, useBulkStatus } from "@/hooks/useBulk";

export default function BulkPage() {
  const [candidatesJson, setCandidatesJson] = useState("");
  const [idsInput, setIdsInput] = useState("");
  const [entityType, setEntityType] = useState("candidates");
  const bulkImport = useBulkImportCandidates();
  const bulkDelete = useBulkDelete();
  const bulkStatus = useBulkStatus();

  const handleImport = async () => {
    try {
      const candidates = JSON.parse(candidatesJson);
      const result = await bulkImport.mutateAsync(candidates);
      toast.success(`Imported ${result.created} candidates`);
      if (result.errors?.length) {
        toast.error(`${result.errors.length} errors occurred`);
      }
    } catch {
      toast.error("Invalid JSON or import failed");
    }
  };

  const handleDelete = async () => {
    const ids = idsInput.split("\n").map((s) => s.trim()).filter(Boolean);
    if (!ids.length) return;
    try {
      const result = await bulkDelete.mutateAsync({ entity_type: entityType, ids });
      toast.success(`Deleted ${result.deleted} items`);
    } catch {
      toast.error("Delete failed");
    }
  };

  const handleStatus = async () => {
    const ids = idsInput.split("\n").map((s) => s.trim()).filter(Boolean);
    if (!ids.length) return;
    try {
      const result = await bulkStatus.mutateAsync({ entity_type: entityType, ids });
      toast.success(`Checked ${result.length} items`);
    } catch {
      toast.error("Status check failed");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bulk Operations</h1>
        <p className="text-muted-foreground">Import, update, and delete entities in bulk</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Import Candidates</CardTitle>
          <CardDescription>Paste a JSON array of candidates to import</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder='[{"name": "John Doe", "email": "john@example.com", "skills": ["Python", "React"]}]'
            value={candidatesJson}
            onChange={(e) => setCandidatesJson(e.target.value)}
            rows={6}
          />
          <Button onClick={handleImport} disabled={bulkImport.isPending || !candidatesJson}>
            {bulkImport.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            Import Candidates
          </Button>
          {bulkImport.data && (
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span>{bulkImport.data.created} candidates imported</span>
              {bulkImport.data.errors?.length > 0 && (
                <span className="text-destructive">
                  <XCircle className="ml-2 inline h-4 w-4" />
                  {bulkImport.data.errors.length} errors
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bulk Delete / Status Check</CardTitle>
          <CardDescription>Enter one ID per line</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="candidates">Candidates</option>
              <option value="interviews">Interviews</option>
            </select>
          </div>
          <Textarea
            placeholder="uuid-1&#10;uuid-2&#10;uuid-3"
            value={idsInput}
            onChange={(e) => setIdsInput(e.target.value)}
            rows={4}
          />
          <div className="flex gap-2">
            <Button variant="destructive" onClick={handleDelete} disabled={bulkDelete.isPending || !idsInput}>
              {bulkDelete.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Delete Selected
            </Button>
            <Button variant="outline" onClick={handleStatus} disabled={bulkStatus.isPending || !idsInput}>
              {bulkStatus.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Check Status
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
