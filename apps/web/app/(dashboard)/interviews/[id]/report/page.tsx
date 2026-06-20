"use client";

import { useParams } from "next/navigation";
import { useReport } from "@/hooks/useReport";

interface ReportData {
  pdf_url: string | null;
}

export default function ReportPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: report } = useReport(id) as { data: ReportData | undefined };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">PDF Report</h1>
      {report?.pdf_url ? (
        <a href={report.pdf_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
          Download PDF Report
        </a>
      ) : (
        <p className="text-muted-foreground">No PDF report available. Generate one from the Results page.</p>
      )}
    </div>
  );
}
