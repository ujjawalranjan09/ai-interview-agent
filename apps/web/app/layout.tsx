import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import { InstallPrompt } from "@/components/shared/InstallPrompt";
import { getLocale } from "next-intl/server";
import { ThemeProvider } from "next-themes";
import * as Sentry from "@sentry/nextjs";
import "./globals.css";

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || "production",
    tracesSampleRate: 0.1,
  });
}

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AI Interview Agent",
    template: "%s | AI Interview Agent",
  },
  description: "AI-powered interview platform for technical hiring. Automate screening, conduct live coding interviews, and generate insightful reports.",
  keywords: ["interview", "ai", "hiring", "technical", "coding", "assessment"],
  authors: [{ name: "AI Interview Agent Team" }],
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "InterviewAI",
  },
  openGraph: {
    title: "AI Interview Agent",
    description: "AI-powered interview platform for technical hiring",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Interview Agent",
    description: "AI-powered interview platform for technical hiring",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
      </head>
      <body className="min-h-full flex flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <Providers>{children}</Providers>
        </ThemeProvider>
        <InstallPrompt />
      </body>
    </html>
  );
}
