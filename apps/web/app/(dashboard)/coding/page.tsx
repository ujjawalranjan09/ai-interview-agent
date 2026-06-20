"use client";

import { useState } from "react";
import { useCodingQuestions, useCodingQuestion, useSubmitCode } from "@/hooks/useCoding";
import { CodeEditor } from "@/components/coding/CodeEditor";
import { TestResults } from "@/components/coding/TestResults";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CodingPage() {
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const { data: questionsData, isLoading: questionsLoading } = useCodingQuestions();
  const { data: selectedQuestion, isLoading: questionLoading } = useCodingQuestion(
    selectedQuestionId || ""
  );
  const submitCode = useSubmitCode();

  const handleSubmit = async (code: string) => {
    if (!selectedQuestionId) return;
    await submitCode.mutateAsync({
      questionId: selectedQuestionId,
      code,
      language: "python",
    });
  };

  const handleRun = (code: string) => {
    console.log("Running code:", code);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Coding Practice</h1>

      {!selectedQuestionId ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {questionsLoading ? (
            <div className="text-center py-12 text-muted-foreground col-span-full">
              Loading questions...
            </div>
          ) : !questionsData?.items?.length ? (
            <div className="text-center py-12 text-muted-foreground col-span-full">
              No coding questions available yet.
            </div>
          ) : (
            questionsData.items.map((question) => (
              <Card
                key={question.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedQuestionId(question.id)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">{question.title}</CardTitle>
                  <div className="flex gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        question.difficulty === "easy"
                          ? "bg-green-100 text-green-700"
                          : question.difficulty === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {question.difficulty}
                    </span>
                    <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                      {question.category}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {question.description}
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <Button variant="ghost" onClick={() => setSelectedQuestionId(null)}>
            ← Back to Questions
          </Button>

          {questionLoading ? (
            <div className="text-center py-12 text-muted-foreground">Loading question...</div>
          ) : selectedQuestion ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>{selectedQuestion.title}</CardTitle>
                    <div className="flex gap-2">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          selectedQuestion.difficulty === "easy"
                            ? "bg-green-100 text-green-700"
                            : selectedQuestion.difficulty === "medium"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {selectedQuestion.difficulty}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                        {selectedQuestion.category}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-2">Description</h3>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {selectedQuestion.description}
                      </p>
                    </div>
                    {selectedQuestion.constraints && (
                      <div>
                        <h3 className="text-sm font-medium mb-2">Constraints</h3>
                        <p className="text-sm text-muted-foreground">
                          {selectedQuestion.constraints}
                        </p>
                      </div>
                    )}
                    {selectedQuestion.examples && selectedQuestion.examples.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium mb-2">Examples</h3>
                        {selectedQuestion.examples.map((example, i) => (
                          <div key={i} className="bg-muted p-3 rounded-md mb-2">
                            <div className="text-xs">
                              <span className="font-medium">Input:</span>{" "}
                              <code>{example.input}</code>
                            </div>
                            <div className="text-xs">
                              <span className="font-medium">Output:</span>{" "}
                              <code>{example.output}</code>
                            </div>
                            {example.explanation && (
                              <div className="text-xs mt-1 text-muted-foreground">
                                {example.explanation}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <CodeEditor
                  initialCode={selectedQuestion.starter_code || ""}
                  language={selectedQuestion.language}
                  onSubmit={handleSubmit}
                  onRun={handleRun}
                  isSubmitting={submitCode.isPending}
                />

                {submitCode.data && (
                  <TestResults
                    results={submitCode.data.test_results}
                    score={submitCode.data.score}
                    passed={submitCode.data.passed}
                    executionTime={submitCode.data.execution_time}
                  />
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">Question not found</div>
          )}
        </div>
      )}
    </div>
  );
}
