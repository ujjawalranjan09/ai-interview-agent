"use client";

import { useState } from "react";
import { useOrganization, useUpdateOrganization } from "@/hooks/useOrg";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function OrganizationSettingsPage() {
  // For demo, use a hardcoded org ID
  const orgId = "demo-org-id";
  const { data: org, isLoading } = useOrganization(orgId);
  const updateOrganization = useUpdateOrganization();

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    website: "",
    industry: "",
    size: "",
  });
  const [initialized, setInitialized] = useState(false);

  if (org && !initialized) {
    setFormData({
      name: org.name || "",
      description: org.description || "",
      website: org.website || "",
      industry: org.industry || "",
      size: org.size || "",
    });
    setInitialized(true);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateOrganization.mutateAsync({ id: orgId, ...formData });
  };

  if (isLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Organization Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Organization Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Organization name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                rows={3}
                placeholder="About your organization"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Website</label>
              <input
                type="url"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="https://example.com"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Industry</label>
                <select
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="">Select industry</option>
                  <option value="technology">Technology</option>
                  <option value="finance">Finance</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="education">Education</option>
                  <option value="retail">Retail</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Company Size</label>
                <select
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="">Select size</option>
                  <option value="1-10">1-10 employees</option>
                  <option value="11-50">11-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-500">201-500 employees</option>
                  <option value="500+">500+ employees</option>
                </select>
              </div>
            </div>
            <Button type="submit" disabled={updateOrganization.isPending}>
              {updateOrganization.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {org && (
        <Card>
          <CardHeader>
            <CardTitle>Organization Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p><span className="font-medium">ID:</span> {org.id}</p>
            <p><span className="font-medium">Slug:</span> {org.slug}</p>
            <p><span className="font-medium">Members:</span> {org.member_count}</p>
            <p><span className="font-medium">Created:</span> {new Date(org.created_at).toLocaleDateString()}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
