import fs from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

const raw = fs.readFileSync(path.join(process.cwd(), "public", "_headers"), "utf8")

function blockFor(route: string): string[] {
  const lines = raw.split("\n")
  const start = lines.findIndex((l) => l === route)
  expect(start, `${route} block exists`).toBeGreaterThanOrEqual(0)
  const out: string[] = []
  for (let i = start + 1; i < lines.length && /^\s+\S/.test(lines[i]); i++) out.push(lines[i].trim())
  return out
}

const csp = (block: string[]) =>
  block.find((l) => l.startsWith("Content-Security-Policy:"))!.replace("Content-Security-Policy: ", "")

describe("_headers: /demo exceptions", () => {
  const globalCsp = csp(blockFor("/*"))

  it("/demo restates the global CSP, differing only by 'self' in frame-src", () => {
    const demo = csp(blockFor("/demo"))
    expect(demo).toBe(globalCsp.replace("frame-src https://", "frame-src 'self' https://"))
    expect(demo).not.toBe(globalCsp)
  })

  it("/demo detaches the inherited CSP so headers are replaced, not merged", () => {
    expect(blockFor("/demo")).toContain("! Content-Security-Policy")
  })

  it("/demo/graph (graph.html) is frameable by same origin only and has no network access", () => {
    const b = blockFor("/demo/graph")
    expect(b).toContain("X-Frame-Options: SAMEORIGIN")
    const c = csp(b)
    expect(c).toContain("frame-ancestors 'self'")
    expect(c).toContain("connect-src 'none'")
    expect(c).toContain("default-src 'none'")
  })

  it("global policy still forbids framing", () => {
    expect(globalCsp).toContain("frame-ancestors 'none'")
    expect(blockFor("/*")).toContain("X-Frame-Options: DENY")
  })
})
