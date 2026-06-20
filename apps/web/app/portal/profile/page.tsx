"use client";

import { useState } from "react";
import { useCandidateProfile, useUpdateCandidateProfile } from "@/hooks/usePortal";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function PortalProfilePage() {
  const { data: profile, isLoading } = useCandidateProfile();
  const updateProfile = useUpdateCandidateProfile();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
  });
  const [initialized, setInitialized] = useState(false);

  // Initialize form data when profile loads
  if (profile && !initialized) {
    setFormData({
      name: profile.name || "",
      email: profile.email || "",
      phone: profile.phone || "",
    });
    setInitialized(true);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProfile.mutateAsync(formData);
  };

  if (isLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Edit Profile</h1>

      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
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
                placeholder="Your name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="your.email@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="+1 (555) 000-0000"
              />
            </div>
            <Button type="submit" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {profile?.skills && profile.skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill, i) => (
                <span key={i} className="text-sm px-3 py-1 bg-muted rounded-full">
                  {skill}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
