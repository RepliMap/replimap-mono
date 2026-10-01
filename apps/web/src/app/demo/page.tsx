import type { Metadata } from "next"
import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { CopyCommand } from "@/components/copy-command"
import { TerraformBrowser } from "@/components/demo/terraform-browser"
import {
  DEFAULT_FILE,
  IMPORTS_FILE,
  findReferences,
  loadDemoFiles,
  loadDemoSummary,
} from "@/lib/demo-data"

const TITLE = "Demo: a fictional AWS account, mapped and codified"
const DESCRIPTION =
  "No install needed. Explore the dependency graph and the import-ready Terraform RepliMap generated for a 100% synthetic AWS account, produced by the real scanners and the real codify pipeline."

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/demo" },
  openGraph: {
    title: `${TITLE} | RepliMap`,
    description: DESCRIPTION,
    url: "/demo",
    type: "website",
    images: [{ url: "/og-image.png" }],
  },
  twitter: {
    card: "summary_large_image",
    title: `${TITLE} | RepliMap`,
    description: DESCRIPTION,
    images: ["/og-image.png"],
  },
}

const GIF_WIDTH = 1180
const GIF_HEIGHT = 760

const linkClass =
  "text-emerald-400 underline underline-offset-4 hover:text-emerald-300 rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
const H2 = "text-2xl font-semibold text-foreground mb-4 scroll-mt-24"
const P = "text-muted-foreground leading-relaxed"

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="font-mono text-[0.85em] text-foreground bg-muted/60 border border-border rounded px-1.5 py-0.5 break-words">
      {children}
    </code>
  )
}

export default function DemoPage() {
  const s = loadDemoSummary()
  const files = loadDemoFiles()
  const references = findReferences(files)

  return (
    <>
      <Header />
      <main className="min-h-screen bg-background pt-24 pb-16">
        <div className="max-w-5xl mx-auto px-4 space-y-14">
          <header>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
              See it on a fictional account
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Everything below comes from &ldquo;Acme Shop&rdquo;, a fictional AWS account
              (123456789012, <Code>example.com</Code>) that contains no real infrastructure. The
              scanners and the <Code>codify</Code> pipeline are the real ones (RepliMap{" "}
              {s.replimapVersion}); nothing in the outputs is mocked. The scan found{" "}
              <strong className="text-foreground">{s.scanned} resources</strong>, which became a
              graph of <strong className="text-foreground">{s.graphNodes} nodes</strong> and{" "}
              <strong className="text-foreground">{s.graphEdges} edges</strong>.{" "}
              <strong className="text-foreground">{s.imports} imports</strong> across {s.importTypes}{" "}
              resource types were generated, and the Terraform passes{" "}
              <Code>terraform validate</Code> ({s.terraformVersion}). {s.graphOnlyResources}{" "}
              resources ({s.graphOnlyTypes} types) are graph-only and not generated,{" "}
              {s.cfnSkipped} were skipped because CloudFormation owns them, and{" "}
              {s.defaultSkipped} were skipped because they are AWS defaults or service-owned.
            </p>
          </header>

          <section aria-labelledby="graph">
            <h2 id="graph" className={H2}>
              The dependency graph
            </h2>
            <p className={`${P} mb-4`}>
              Interactive: drag, zoom and click nodes. It is a single self-contained HTML file with
              no external requests.{" "}
              <a className={linkClass} href="/demo/graph">
                Open full screen
              </a>
              .
            </p>
            <iframe
              src="/demo/graph"
              title="Interactive dependency graph of the synthetic Acme Shop AWS account"
              loading="lazy"
              className="block h-[26rem] md:h-[40rem] w-full rounded-lg border border-border bg-card"
            />
          </section>

          <section aria-labelledby="terraform">
            <h2 id="terraform" className={H2}>
              The generated Terraform
            </h2>
            <p className={`${P} mb-4`}>
              {s.fileCount} files, written to disk by <Code>replimap codify</Code>. Pick a file, or
              use the arrow keys in the list.{" "}
              <a className={linkClass} href="/demo/acme-shop-terraform.zip">
                Download all (.zip)
              </a>
              .
            </p>
            <TerraformBrowser
              files={files}
              references={references}
              defaultFile={DEFAULT_FILE}
              importsFile={IMPORTS_FILE}
            />
          </section>

          <section aria-labelledby="limits">
            <h2 id="limits" className={H2}>
              What you don&apos;t see
            </h2>
            <ul className="list-disc pl-5 text-muted-foreground space-y-2 leading-relaxed">
              <li>
                Lambda functions, ECS services and task definitions, API Gateway resources and SSM
                parameters appear in the graph but are not generated as Terraform.
              </li>
              <li>
                EC2 <Code>user_data</Code> is never stored, and secret values are never read.
              </li>
              <li>
                Resources owned by CloudFormation and AWS-default resources are skipped on purpose.
              </li>
            </ul>
            <p className={`${P} mt-4`}>
              More on what RepliMap reads and sends on the{" "}
              <Link className={linkClass} href="/security">
                What RepliMap talks to
              </Link>{" "}
              page.
            </p>
          </section>

          <section aria-labelledby="recording">
            <h2 id="recording" className={H2}>
              40 seconds in the terminal
            </h2>
            <p className={`${P} mb-4`}>
              The terminal output replays the synthetic account&apos;s numbers. The{" "}
              <Code>terraform plan</Code> line is illustrative.
            </p>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/demo/demo.gif"
              width={GIF_WIDTH}
              height={GIF_HEIGHT}
              loading="lazy"
              decoding="async"
              alt={`Looping 40-second terminal recording: replimap scan reads the Acme Shop account (${s.scanned} resources), replimap graph builds the dependency graph, replimap codify writes ${s.imports} import-ready Terraform resources, and a plan shows them being adopted with no changes.`}
              className="h-auto w-full rounded-lg border border-border bg-card"
            />
          </section>

          <section aria-labelledby="try" className="text-center">
            <h2 id="try" className={H2}>
              Run it on your own account
            </h2>
            <p className={`${P} mb-6`}>
              Read-only, local, and nothing is uploaded.
            </p>
            <div className="flex justify-center mb-4">
              <CopyCommand command="pip install replimap" />
            </div>
            <p className="text-sm text-muted-foreground">
              Then follow the{" "}
              <Link className={linkClass} href="/docs/quick-start">
                quick start
              </Link>{" "}
              or read the{" "}
              <Link className={linkClass} href="/docs">
                docs
              </Link>
              .
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </>
  )
}
