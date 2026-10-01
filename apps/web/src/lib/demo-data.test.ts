import { describe, expect, it } from "vitest"
import { DEFAULT_FILE, findReferences, loadDemoFiles, loadDemoSummary } from "./demo-data"

describe("demo data", () => {
  const files = loadDemoFiles()

  it("loads every .tf file including the default and imports files", () => {
    const names = files.map((f) => f.name)
    expect(names).toContain(DEFAULT_FILE)
    expect(names).toContain("imports.tf")
    expect(files.length).toBe(loadDemoSummary().fileCount)
  })

  it("locates each highlighted reference on a real line of the file", () => {
    for (const r of findReferences(files)) {
      const line = files.find((f) => f.name === r.file)!.content.split("\n")[r.line - 1]
      expect(line.trim()).toBe(r.code)
      expect(r.code).toMatch(/=\s*aws_[a-z0-9_]+\./)
    }
  })

  it("summary counts are internally consistent", () => {
    const s = loadDemoSummary()
    expect(s.scanned - s.cfnSkipped - s.defaultSkipped - s.graphOnlyResources).toBe(s.imports)
  })
})
