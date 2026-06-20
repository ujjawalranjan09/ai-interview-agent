"use client";

import { useState } from "react";
import { useAuditLogs } from "@/hooks/useAudit";
import { AuditTable } from "@/components/admin/AuditTable";
import { Button } from "@/components/ui/button";

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAuditLogs({ page });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Audit Log</h1>
      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : (
        <>
          <AuditTable items={data?.items || []} />
          {data && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {data.page} of {Math.ceil(data.total / data.per_page)}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                <Button variant="outline" size="sm" disabled={page * data.per_page >= data.total} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
