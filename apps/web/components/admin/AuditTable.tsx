"use client";

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

interface AuditTableProps {
  items: AuditEntry[];
}

export function AuditTable({ items }: AuditTableProps) {
  if (!items.length) {
    return <p className="text-sm text-muted-foreground">No audit entries</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="p-2">Action</th>
            <th className="p-2">User</th>
            <th className="p-2">Type</th>
            <th className="p-2">Resource</th>
            <th className="p-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id} className="border-b last:border-0 hover:bg-muted/50">
              <td className="p-2 font-medium">{e.action}</td>
              <td className="p-2 text-muted-foreground">{e.user_id?.slice(0, 8) || "—"}</td>
              <td className="p-2">{e.resource_type}</td>
              <td className="p-2 text-muted-foreground">{e.resource_id?.slice(0, 8) || "—"}</td>
              <td className="p-2 text-muted-foreground">
                {new Date(e.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
