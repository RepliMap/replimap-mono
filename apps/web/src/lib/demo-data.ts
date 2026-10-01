import fs from "node:fs"
import path from "node:path"

/**
 * Build-time loader for the /demo page. Everything here runs in a server
 * component during `next build`; nothing is fetched by the browser.
 * Source of truth: public/demo/ (synthetic "Acme Shop" account, produced by
 * the real scan + codify pipeline).
 */

const DEMO_DIR = path.join(process.cwd(), "public", "demo")
const TF_DIR = path.join(DEMO_DIR, "terraform")

export const DEFAULT_FILE = "alb.tf"
export const IMPORTS_FILE = "imports.tf"

export interface DemoFile {
  name: string
  content: string
  lineCount: number
}

export interface DemoReference {
  file: string
  /** 1-based line number in the generated file. */
  line: number
  label: string
  /** The exact source line, trimmed. */
  code: string
}

export interface DemoSummary {
  region: string
  replimapVersion: string
  terraformVersion: string
  scanned: number
  graphNodes: number
  graphEdges: number
  imports: number
  importTypes: number
  graphOnlyResources: number
  graphOnlyTypes: number
  cfnSkipped: number
  defaultSkipped: number
  fileCount: number
}

export function loadDemoSummary(): DemoSummary {
  const s = JSON.parse(fs.readFileSync(path.join(DEMO_DIR, "summary.json"), "utf8"))
  return {
    region: s.region,
    replimapVersion: s.replimap_version,
    terraformVersion: s.terraform_validate.terraform_version,
    scanned: s.scan.resources,
    graphNodes: s.graph.nodes,
    graphEdges: s.graph.edges,
    imports: s.codify.imports,
    importTypes: s.codify.import_resource_types,
    graphOnlyResources: s.codify.graph_only_removed,
    graphOnlyTypes: Object.keys(s.codify.graph_only_by_type).length,
    cfnSkipped: s.codify.cfn_managed_skipped,
    defaultSkipped: s.codify.default_or_service_owned_skipped,
    fileCount: s.codify.files.filter((f: string) => f.endsWith(".tf")).length,
  }
}

export function loadDemoFiles(): DemoFile[] {
  return fs
    .readdirSync(TF_DIR)
    .filter((f) => f.endsWith(".tf"))
    .sort()
    .map((name) => {
      const content = fs.readFileSync(path.join(TF_DIR, name), "utf8")
      return { name, content, lineCount: content.split("\n").length - (content.endsWith("\n") ? 1 : 0) }
    })
}

/** Cross-resource references to point at. Located by pattern, never by hardcoded line numbers. */
const REFERENCE_PATTERNS: { file: string; pattern: RegExp; label: string }[] = [
  {
    file: "alb.tf",
    pattern: /^\s*certificate_arn\s*=\s*aws_acm_certificate\./,
    label: "The HTTPS listener references its ACM certificate",
  },
  {
    file: "dns.tf",
    pattern: /^\s*zone_id\s*=\s*aws_lb\./,
    label: "A Route53 alias record references the load balancer",
  },
  {
    file: "cdn.tf",
    pattern: /^\s*domain_name\s*=\s*aws_lb\./,
    label: "The CloudFront origin points at the same load balancer",
  },
]

export function findReferences(files: DemoFile[]): DemoReference[] {
  return REFERENCE_PATTERNS.map(({ file, pattern, label }) => {
    const f = files.find((x) => x.name === file)
    const lines = f?.content.split("\n") ?? []
    const idx = lines.findIndex((l) => pattern.test(l))
    if (idx === -1) {
      throw new Error(`demo: expected reference not found in ${file} (${pattern})`)
    }
    return { file, line: idx + 1, label, code: lines[idx].trim() }
  })
}
