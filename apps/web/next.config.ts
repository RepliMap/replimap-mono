import { createMDX } from 'fumadocs-mdx/next'
import type { NextConfig } from "next";

const withMDX = createMDX()

const nextConfig: NextConfig = {
  // Static export for Cloudflare Workers Static Assets — see the internal decision log
  // (2026-09-27) and CLAUDE.md landmine 9. `redirects()` is not supported
  // under `output: 'export'`; the /pricing -> /#pricing 301 now lives in
  // public/_redirects (Workers Static Assets format) instead.
  output: 'export',
};

export default withMDX(nextConfig);
