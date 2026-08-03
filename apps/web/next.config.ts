import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel handles tracing; avoid monorepo tracingRoot which breaks cloud builds.
};

export default nextConfig;
