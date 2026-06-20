"use client";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface UserTableProps {
  users: User[];
  onUpdateRole: (userId: string, role: string) => void;
  onToggleActive: (userId: string, isActive: boolean) => void;
}

export function UserTable({
  users,
  onUpdateRole,
  onToggleActive,
}: UserTableProps) {
  if (!users.length) {
    return <p className="text-sm text-muted-foreground">No users found</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="p-3">Name</th>
            <th className="p-3">Email</th>
            <th className="p-3">Role</th>
            <th className="p-3">Status</th>
            <th className="p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b last:border-0 hover:bg-muted/50">
              <td className="p-3 font-medium">{u.full_name}</td>
              <td className="p-3 text-muted-foreground">{u.email}</td>
              <td className="p-3">
                <select
                  className="rounded border p-1 text-xs"
                  value={u.role}
                  onChange={(e) => onUpdateRole(u.id, e.target.value)}
                >
                  <option value="admin">admin</option>
                  <option value="interviewer">interviewer</option>
                  <option value="candidate">candidate</option>
                </select>
              </td>
              <td className="p-3">
                <button
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    u.is_active ? "bg-green-500" : "bg-red-500"
                  }`}
                  onClick={() => onToggleActive(u.id, !u.is_active)}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      u.is_active ? "translate-x-4" : "translate-x-1"
                    }`}
                  />
                </button>
              </td>
              <td className="p-3 text-muted-foreground">—</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
