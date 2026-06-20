"use client";

import { useTemplates, useCreateTemplate, useDeleteTemplate } from "@/hooks/useTemplates";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

export default function TemplatesPage() {
  const { data, isLoading } = useTemplates();
  const createTemplate = useCreateTemplate();
  const deleteTemplate = useDeleteTemplate();
  const [showCreate, setShowCreate] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: "",
    description: "",
    question_count: 10,
    difficulty_level: 2,
    question_types: [] as string[],
    skills: [] as string[],
  });

  const handleCreate = async () => {
    if (!newTemplate.name) return;
    await createTemplate.mutateAsync(newTemplate);
    setShowCreate(false);
    setNewTemplate({ name: "", description: "", question_count: 10, difficulty_level: 2, question_types: [], skills: [] });
  };

  const getDifficultyLabel = (level: number) => {
    switch (level) {
      case 1: return "Easy";
      case 2: return "Medium";
      case 3: return "Hard";
      default: return "Medium";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Interview Templates</h1>
        <Button onClick={() => setShowCreate(true)}>New Template</Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create Interview Template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                type="text"
                value={newTemplate.name}
                onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="e.g., Backend Developer Interview"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <input
                type="text"
                value={newTemplate.description}
                onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Optional description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Question Count</label>
                <input
                  type="number"
                  value={newTemplate.question_count}
                  onChange={(e) => setNewTemplate({ ...newTemplate, question_count: parseInt(e.target.value) || 10 })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                  min={1}
                  max={50}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Difficulty</label>
                <select
                  value={newTemplate.difficulty_level}
                  onChange={(e) => setNewTemplate({ ...newTemplate, difficulty_level: parseInt(e.target.value) })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value={1}>Easy</option>
                  <option value={2}>Medium</option>
                  <option value={3}>Hard</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createTemplate.isPending}>
                {createTemplate.isPending ? "Creating..." : "Create"}
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
          title="No templates yet"
          description="Create an interview template to standardize your interview process."
          actionLabel="New Template"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((template) => (
            <Card key={template.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{template.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{getDifficultyLabel(template.difficulty_level)}</p>
              </CardHeader>
              <CardContent>
                {template.description && (
                  <p className="text-sm text-muted-foreground mb-2">{template.description}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{template.question_count} questions</span>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => deleteTemplate.mutate(template.id)}
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
