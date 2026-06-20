import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import withBundleAnalyzerFn from "@next/bundle-analyzer";

const withBundleAnalyzer = withBundleAnalyzerFn({
  enabled: process.env.ANALYZE === "true",
});
import withPWA from "next-pwa";

const withNextIntl = createNextIntlPlugin();

const pwaConfig = {
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/(.*)/,
      handler: "NetworkFirst" as const,
      options: {
        cacheName: "api-cache",
        expiration: { maxEntries: 100, maxAgeSeconds: 60 * 5 },
      },
    },
    {
      urlPattern: /\.(?:js|css|png|jpg|jpeg|svg|ico|woff2?)$/,
      handler: "CacheFirst" as const,
      options: {
        cacheName: "static-assets",
        expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
      },
    },
  ],
};

const nextConfig: NextConfig = {
  output: "standalone",
  basePath: "/dashboard",
  turbopack: {
    root: process.cwd(),
  },
  compress: true,
  rewrites: async () => [
    {
      source: "/api/:path*",
      destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
    },
  ],
};

export default withPWA(pwaConfig)(withBundleAnalyzer(withNextIntl(nextConfig)));