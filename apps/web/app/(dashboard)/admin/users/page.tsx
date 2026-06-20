"use client";

import { useState } from "react";
import { useAdminUsers, useUpdateUser } from "@/hooks/useAdmin";
import { UserTable } from "@/components/admin/UserTable";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function AdminUsersPage() {
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminUsers({ role: roleFilter, page });
  const updateUser = useUpdateUser();

  const handleUpdateRole = async (userId: string, role: string) => {
    try {
      await updateUser.mutateAsync({ userId, role });
      toast.success("Role updated");
    } catch {
      toast.error("Failed to update role");
    }
  };

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    if (!isActive && !window.confirm("Deactivate this user?")) return;
    try {
      await updateUser.mutateAsync({ userId, is_active: isActive });
      toast.success(isActive ? "User activated" : "User deactivated");
    } catch {
      toast.error("Failed to update user");
    }
  };

  const filters = ["All", "Admin", "Interviewer", "Candidate"];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">User Management</h1>

      <div className="flex gap-2">
        {filters.map((f) => (
          <Button
            key={f}
            variant={roleFilter === (f === "All" ? undefined : f.toLowerCase()) ? "default" : "outline"}
            size="sm"
            onClick={() =>
              setRoleFilter(f === "All" ? undefined : f.toLowerCase())
            }
          >
            {f}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : (
        <>
          <UserTable
            users={data?.items || []}
            onUpdateRole={handleUpdateRole}
            onToggleActive={handleToggleActive}
          />
          {data && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {data.page} of {Math.ceil(data.total / data.per_page)}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * data.per_page >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
