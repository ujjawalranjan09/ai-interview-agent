"use client";

import Link from "next/link";
import { useBanks, useCreateBank, useDeleteBank } from "@/hooks/useBanks";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

export default function BanksPage() {
  const { data, isLoading } = useBanks();
  const createBank = useCreateBank();
  const deleteBank = useDeleteBank();
  const [showCreate, setShowCreate] = useState(false);
  const [newBank, setNewBank] = useState({ name: "", description: "", category: "technical" });

  const handleCreate = async () => {
    if (!newBank.name) return;
    await createBank.mutateAsync(newBank);
    setShowCreate(false);
    setNewBank({ name: "", description: "", category: "technical" });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Question Banks</h1>
        <Button onClick={() => setShowCreate(true)}>New Bank</Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create Question Bank</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                type="text"
                value={newBank.name}
                onChange={(e) => setNewBank({ ...newBank, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="e.g., Backend Technical Questions"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <input
                type="text"
                value={newBank.description}
                onChange={(e) => setNewBank({ ...newBank, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Category</label>
              <select
                value={newBank.category}
                onChange={(e) => setNewBank({ ...newBank, category: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
              >
                <option value="technical">Technical</option>
                <option value="behavioral">Behavioral</option>
                <option value="conceptual">Conceptual</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createBank.isPending}>
                {createBank.isPending ? "Creating..." : "Create"}
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : !data?.items?.length ? (
        <EmptyState
          title="No question banks yet"
          description="Create a question bank to organize and reuse your questions."
          actionLabel="New Bank"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((bank) => (
            <Card key={bank.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{bank.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{bank.category}</p>
              </CardHeader>
              <CardContent>
                {bank.description && (
                  <p className="text-sm text-muted-foreground mb-2">{bank.description}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{bank.question_count} questions</span>
                  <div className="flex gap-2">
                    <Link href={`/dashboard/banks/${bank.id}`}>
                      <Button variant="ghost" size="sm">View</Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => deleteBank.mutate(bank.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
