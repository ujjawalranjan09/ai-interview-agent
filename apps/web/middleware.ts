import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js middleware: minimal pass-through.
 *
 * Note: The original next-intl middleware was rewriting /dashboard/* paths
 * to /dashboard/en/* which broke all routes that live under (dashboard) and
 * (auth) route groups. The app only uses the [locale] segment for a single
 * landing-page redirect, so i18n routing is disabled at the middleware level.
 */
export default function middleware(_req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
