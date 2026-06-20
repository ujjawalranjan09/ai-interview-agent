"use client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Download, Trash2, RefreshCw } from "lucide-react";
import { useConsents, useUpdateConsent, useDataExport, useDeleteData } from "@/hooks/useGDPR";

const consentLabels: Record<string, string> = {
  marketing: "Marketing Communications",
  analytics: "Analytics & Tracking",
  data_processing: "Data Processing",
  video_recording: "Video Recording & Analysis",
};

export default function GDPRPage() {
  const { data: consents, isLoading } = useConsents();
  const updateConsent = useUpdateConsent();
  const dataExport = useDataExport();
  const deleteData = useDeleteData();

  const handleConsentToggle = async (consentType: string, currentGranted: boolean) => {
    try {
      await updateConsent.mutateAsync({ consent_type: consentType, granted: !currentGranted });
      toast.success("Consent updated");
    } catch {
      toast.error("Failed to update consent");
    }
  };

  const handleExport = async () => {
    try {
      await dataExport.mutateAsync();
      toast.success("Data export requested. You will be notified when ready.");
    } catch {
      toast.error("Failed to request export");
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure? This will permanently delete all your data.")) return;
    try {
      await deleteData.mutateAsync();
      toast.success("Data deletion requested");
    } catch {
      toast.error("Failed to delete data");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Privacy & GDPR</h1>
        <p className="text-muted-foreground">Manage your consent preferences and data</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Consent Preferences</CardTitle>
          <CardDescription>Manage what data you allow us to process</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex justify-center py-4">
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            Object.entries(consentLabels).map(([key, label]) => {
              const consent = consents?.find((c) => c.consent_type === key);
              return (
                <div key={key} className="flex items-center justify-between">
                  <Label htmlFor={`consent-${key}`} className="flex-1">{label}</Label>
                  <Switch
                    id={`consent-${key}`}
                    checked={consent?.granted ?? false}
                    onCheckedChange={() => handleConsentToggle(key, consent?.granted ?? false)}
                  />
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data Management</CardTitle>
          <CardDescription>Export or delete your personal data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Export My Data</p>
              <p className="text-sm text-muted-foreground">Download all your data in a portable format</p>
            </div>
            <Button variant="outline" onClick={handleExport} disabled={dataExport.isPending}>
              {dataExport.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              Export
            </Button>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-destructive">Delete All Data</p>
              <p className="text-sm text-muted-foreground">Permanently remove all your personal data</p>
            </div>
            <Button variant="destructive" onClick={handleDelete} disabled={deleteData.isPending}>
              {deleteData.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="mr-2 h-4 w-4" />
              )}
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
