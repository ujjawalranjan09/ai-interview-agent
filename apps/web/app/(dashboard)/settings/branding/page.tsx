"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Save, Loader2, Palette, Globe, Type } from "lucide-react";
import { useBranding, useUpdateBranding } from "@/hooks/useBranding";

export default function BrandingPage() {
  const { data: branding, isLoading } = useBranding();
  const updateBranding = useUpdateBranding();
  const [form, setForm] = useState<Record<string, string>>({});
  const [initialized, setInitialized] = useState(false);

  if (branding && !initialized) {
    setForm({
      logo_url: branding.logo_url || "",
      favicon_url: branding.favicon_url || "",
      primary_color: branding.primary_color || "#3b82f6",
      secondary_color: branding.secondary_color || "#8b5cf6",
      accent_color: branding.accent_color || "#10b981",
      font_family: branding.font_family || "",
      custom_domain: branding.custom_domain || "",
      portal_heading: branding.portal_heading || "",
    });
    setInitialized(true);
  }

  const handleSubmit = async () => {
    try {
      await updateBranding.mutateAsync(form);
      toast.success("Branding updated");
    } catch {
      toast.error("Failed to update branding");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">White-Label Branding</h1>
        <p className="text-muted-foreground">Customize the appearance of your organization's portal</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Theme Colors</CardTitle>
          <CardDescription>Customize the color scheme</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="primary_color">Primary Color</Label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      id="primary_color"
                      value={form.primary_color || "#3b82f6"}
                      onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                      className="h-10 w-10 rounded border cursor-pointer"
                    />
                    <Input
                      value={form.primary_color || ""}
                      onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                      placeholder="#3b82f6"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secondary_color">Secondary Color</Label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      id="secondary_color"
                      value={form.secondary_color || "#8b5cf6"}
                      onChange={(e) => setForm({ ...form, secondary_color: e.target.value })}
                      className="h-10 w-10 rounded border cursor-pointer"
                    />
                    <Input
                      value={form.secondary_color || ""}
                      onChange={(e) => setForm({ ...form, secondary_color: e.target.value })}
                      placeholder="#8b5cf6"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="accent_color">Accent Color</Label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      id="accent_color"
                      value={form.accent_color || "#10b981"}
                      onChange={(e) => setForm({ ...form, accent_color: e.target.value })}
                      className="h-10 w-10 rounded border cursor-pointer"
                    />
                    <Input
                      value={form.accent_color || ""}
                      onChange={(e) => setForm({ ...form, accent_color: e.target.value })}
                      placeholder="#10b981"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="font_family">Font Family</Label>
                <div className="flex items-center gap-2">
                  <Type className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="font_family"
                    value={form.font_family || ""}
                    onChange={(e) => setForm({ ...form, font_family: e.target.value })}
                    placeholder="Inter, system-ui, sans-serif"
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logo & Branding Assets</CardTitle>
          <CardDescription>Configure URLs for your brand assets</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="logo_url">Logo URL</Label>
            <Input
              id="logo_url"
              value={form.logo_url || ""}
              onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
              placeholder="https://example.com/logo.png"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="favicon_url">Favicon URL</Label>
            <Input
              id="favicon_url"
              value={form.favicon_url || ""}
              onChange={(e) => setForm({ ...form, favicon_url: e.target.value })}
              placeholder="https://example.com/favicon.ico"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="portal_heading">Portal Heading</Label>
            <Input
              id="portal_heading"
              value={form.portal_heading || ""}
              onChange={(e) => setForm({ ...form, portal_heading: e.target.value })}
              placeholder="Welcome to our Interview Portal"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Custom Domain</CardTitle>
          <CardDescription>Configure a custom domain for your portal</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <Input
              value={form.custom_domain || ""}
              onChange={(e) => setForm({ ...form, custom_domain: e.target.value })}
              placeholder="interview.example.com"
            />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSubmit} disabled={updateBranding.isPending} className="w-full">
        {updateBranding.isPending ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Save className="mr-2 h-4 w-4" />
        )}
        Save Branding Settings
      </Button>
    </div>
  );
}
