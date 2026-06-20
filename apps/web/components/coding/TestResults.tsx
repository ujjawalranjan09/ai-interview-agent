"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TestResult {
  test_case: number;
  passed: boolean;
  expected: unknown;
  actual: unknown;
  error?: string;
}

interface TestResultsProps {
  results: TestResult[];
  score: number;
  passed: boolean;
  executionTime: number;
}

export function TestResults({
  results,
  score,
  passed,
  executionTime,
}: TestResultsProps) {
  const passedCount = results.filter((r) => r.passed).length;
  const totalCount = results.length;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Test Results</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${passed ? "bg-green-500" : "bg-red-500"}`}
            />
            <span className="font-medium">
              {passed ? "All Tests Passed" : "Some Tests Failed"}
            </span>
          </div>
          <div className="text-sm text-muted-foreground">
            {passedCount}/{totalCount} passed
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Score: </span>
            <span
              className={`font-semibold ${
                score >= 80
                  ? "text-green-600"
                  : score >= 60
                  ? "text-yellow-600"
                  : "text-red-600"
              }`}
            >
              {Math.round(score)}%
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Time: </span>
            <span className="font-semibold">{executionTime.toFixed(2)}s</span>
          </div>
        </div>

        <div className="space-y-2">
          {results.map((result) => (
            <div
              key={result.test_case}
              className={`p-3 rounded-md border ${
                result.passed ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Test Case {result.test_case}</span>
                <span
                  className={`text-xs ${
                    result.passed ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {result.passed ? "PASSED" : "FAILED"}
                </span>
              </div>
              {!result.passed && (
                <div className="mt-2 text-xs space-y-1">
                  <div>
                    <span className="text-muted-foreground">Expected: </span>
                    <code className="bg-muted px-1 rounded">
                      {JSON.stringify(result.expected)}
                    </code>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Actual: </span>
                    <code className="bg-muted px-1 rounded">
                      {result.error || JSON.stringify(result.actual)}
                    </code>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
