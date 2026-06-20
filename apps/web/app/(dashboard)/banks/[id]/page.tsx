"use client";

import { useParams } from "next/navigation";
import { useBank, useBankQuestions, useAddBankQuestion, useImportFromInterview, useGenerateInterviewFromBank } from "@/hooks/useBanks";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

export default function BankDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: bank, isLoading: bankLoading } = useBank(id);
  const { data: questionsData, isLoading: questionsLoading } = useBankQuestions(id);
  const addQuestion = useAddBankQuestion(id);
  const importFromInterview = useImportFromInterview(id);
  const generateInterview = useGenerateInterviewFromBank(id);

  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [interviewId, setInterviewId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [generateCount, setGenerateCount] = useState(10);
  const [newQuestion, setNewQuestion] = useState({
    question_text: "",
    question_type: "technical",
    difficulty: "medium",
    reference_answer: "",
  });

  const handleAddQuestion = async () => {
    if (!newQuestion.question_text) return;
    await addQuestion.mutateAsync(newQuestion);
    setShowAdd(false);
    setNewQuestion({ question_text: "", question_type: "technical", difficulty: "medium", reference_answer: "" });
  };

  const handleImport = async () => {
    if (!interviewId) return;
    await importFromInterview.mutateAsync(interviewId);
    setShowImport(false);
    setInterviewId("");
  };

  const handleGenerate = async () => {
    if (!candidateId) return;
    const result = await generateInterview.mutateAsync({ candidate_id: candidateId, count: generateCount });
    alert(`Interview created: ${result.interview_id}`);
    setShowGenerate(false);
    setCandidateId("");
  };

  if (bankLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  if (!bank) {
    return <div className="text-center py-12 text-muted-foreground">Bank not found</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{bank.name}</h1>
          <p className="text-muted-foreground">{bank.category} • {bank.question_count} questions</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowAdd(true)}>Add Question</Button>
          <Button variant="outline" onClick={() => setShowImport(true)}>Import from Interview</Button>
          <Button variant="outline" onClick={() => setShowGenerate(true)}>Generate Interview</Button>
        </div>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>Add Question</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Question Text</label>
              <textarea
                value={newQuestion.question_text}
                onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Type</label>
                <select
                  value={newQuestion.question_type}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_type: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="technical">Technical</option>
                  <option value="behavioral">Behavioral</option>
                  <option value="conceptual">Conceptual</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Difficulty</label>
                <select
                  value={newQuestion.difficulty}
                  onChange={(e) => setNewQuestion({ ...newQuestion, difficulty: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Reference Answer (optional)</label>
              <textarea
                value={newQuestion.reference_answer}
                onChange={(e) => setNewQuestion({ ...newQuestion, reference_answer: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                rows={2}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleAddQuestion} disabled={addQuestion.isPending}>
                {addQuestion.isPending ? "Adding..." : "Add"}
              </Button>
              <Button variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {showImport && (
        <Card>
          <CardHeader>
            <CardTitle>Import from Interview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Interview ID</label>
              <input
                type="text"
                value={interviewId}
                onChange={(e) => setInterviewId(e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Enter interview ID"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleImport} disabled={importFromInterview.isPending}>
                {importFromInterview.isPending ? "Importing..." : "Import"}
              </Button>
              <Button variant="outline" onClick={() => setShowImport(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {showGenerate && (
        <Card>
          <CardHeader>
            <CardTitle>Generate Interview from Bank</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Candidate ID</label>
              <input
                type="text"
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Enter candidate ID"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Number of Questions</label>
              <input
                type="number"
                value={generateCount}
                onChange={(e) => setGenerateCount(parseInt(e.target.value) || 10)}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                min={1}
                max={50}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleGenerate} disabled={generateInterview.isPending}>
                {generateInterview.isPending ? "Generating..." : "Generate"}
              </Button>
              <Button variant="outline" onClick={() => setShowGenerate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {questionsLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading questions...</div>
      ) : !questionsData?.items?.length ? (
        <div className="text-center py-12 text-muted-foreground">No questions in this bank yet</div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-muted-foreground">
                  <th className="p-3">Question</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Difficulty</th>
                  <th className="p-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {questionsData.items.map((q) => (
                  <tr key={q.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-3 max-w-md truncate">{q.question_text}</td>
                    <td className="p-3">{q.question_type}</td>
                    <td className="p-3">{q.difficulty}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {new Date(q.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
