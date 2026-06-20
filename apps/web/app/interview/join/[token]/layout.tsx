import { Providers } from "@/components/providers";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

export default function JoinLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      <header className="p-4 border-b bg-white">
        <h1 className="text-lg font-bold text-center">🎯 AI Interview Agent</h1>
      </header>
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <Providers>
            <ErrorBoundary>{children}</ErrorBoundary>
          </Providers>
        </div>
      </main>
    </div>
  );
}
