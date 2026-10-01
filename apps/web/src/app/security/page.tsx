import type { Metadata } from "next"
import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"

export const metadata: Metadata = {
  title: "What RepliMap talks to",
  description:
    "Every network destination the RepliMap CLI can contact, what it sends, when, and how to verify it yourself: AWS read-only APIs, one license call, nothing else.",
}

const VERIFIED_VERSION = "0.6.1"
const VERIFIED_DATE = "2026-10-01"

const linkClass =
  "text-emerald-400 underline underline-offset-4 hover:text-emerald-300 rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="font-mono text-[0.85em] text-foreground bg-muted/60 border border-border rounded px-1.5 py-0.5 break-words">
      {children}
    </code>
  )
}

function CodeBlock({ children, label }: { children: string; label: string }) {
  return (
    <pre
      aria-label={label}
      tabIndex={0}
      className="bg-card border border-border rounded-lg p-4 overflow-x-auto text-sm font-mono text-foreground leading-relaxed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
    >
      {children}
    </pre>
  )
}

function Table({
  caption,
  head,
  rows,
}: {
  caption: string
  head: string[]
  rows: React.ReactNode[][]
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm text-left">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-muted/50 text-foreground">
          <tr>
            {head.map((h) => (
              <th key={h} scope="col" className="px-4 py-3 font-semibold whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border text-muted-foreground">
          {rows.map((row, i) => (
            <tr key={i} className="align-top">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 min-w-[9rem]">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const H2 = "text-2xl font-semibold text-foreground mb-4 scroll-mt-24"
const P = "text-muted-foreground leading-relaxed"
const UL = "list-disc pl-5 text-muted-foreground space-y-2 leading-relaxed"

export default function SecurityPage() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-background pt-24 pb-16">
        <div className="max-w-4xl mx-auto px-4 space-y-12">
          <header>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
              What RepliMap talks to
            </h1>
            <p className="text-xl text-muted-foreground leading-relaxed mb-4">
              RepliMap is a local CLI. This page lists every network destination the shipped
              package can contact, what it sends, when, and how to check that yourself instead of
              trusting us.
            </p>
            <p className="text-sm text-muted-foreground">
              Verified against the RepliMap {VERIFIED_VERSION} package on {VERIFIED_DATE}. If
              something here does not match what you observe,{" "}
              <a
                className={linkClass}
                href="https://github.com/RepliMap/replimap-community/issues"
                target="_blank"
                rel="noopener noreferrer"
              >
                open an issue
              </a>
              .
            </p>
          </header>

          <section aria-labelledby="glance">
            <h2 id="glance" className={H2}>
              At a glance
            </h2>
            <Table
              caption="All network destinations of the RepliMap CLI"
              head={["Destination", "When", "What is sent"]}
              rows={[
                [
                  <>AWS service APIs (your credentials)</>,
                  <>Commands that scan or read your account</>,
                  <>Signed, read-only API requests to AWS</>,
                ],
                [
                  <>
                    <Code>api.replimap.com</Code>
                  </>,
                  <>
                    Only when you run <Code>replimap license activate</Code>
                  </>,
                  <>License key, a hashed machine id, CLI version</>,
                ],
                [
                  <>Anything else</>,
                  <>Never</>,
                  <>Nothing. No update checks, telemetry or crash reports.</>,
                ],
              ]}
            />
            <p className={`${P} mt-4`}>
              Scan results, dependency graphs, generated Terraform and reports are written to your
              local disk and are never uploaded. Without a license key the CLI runs on the
              community tier and makes no license call at all.
            </p>
          </section>

          <section aria-labelledby="aws">
            <h2 id="aws" className={H2}>
              1. AWS read-only APIs
            </h2>
            <ul className={UL}>
              <li>
                AWS calls go through boto3 with the profile and region you pass. They are
                metadata reads (<Code>Describe*</Code>, <Code>List*</Code>, <Code>Get*</Code>).
                The package contains no AWS create, put, delete or modify calls.
              </li>
              <li>
                <Code>sts:GetCallerIdentity</Code> identifies the account. <Code>sts:GetSessionToken</Code>{" "}
                is called only if your profile requires MFA (<Code>core/security/session_manager.py</Code>).
              </li>
              <li>
                <Code>s3:GetObject</Code> on the single Terraform state object you name, only for{" "}
                <Code>drift</Code> or <Code>audit</Code> with <Code>--state-bucket</Code> and{" "}
                <Code>--state-key</Code> (<Code>drift/state_parser.py</Code>). A local{" "}
                <Code>--state</Code> file avoids it.
              </li>
              <li>
                <Code>replimap doctor</Code> opens a TCP connection to{" "}
                <Code>sts.amazonaws.com:443</Code> to test reachability and sends nothing
                (<Code>cli/commands/doctor.py</Code>).
              </li>
              <li>
                Credential resolution for your profile is done by the AWS SDK, not by RepliMap.
                Depending on how your profile is set up, the SDK may contact AWS SSO or STS
                endpoints, or the link-local instance metadata address when running on EC2 or ECS.
              </li>
            </ul>
            <p className={`${P} mt-4`}>
              The minimal IAM policy is in the{" "}
              <Link className={linkClass} href="/docs/iam-policy">
                IAM policy documentation
              </Link>{" "}
              (also{" "}
              <a
                className={linkClass}
                href="https://github.com/RepliMap/replimap-community/blob/main/IAM_POLICY.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                IAM_POLICY.md on GitHub
              </a>
              ).
            </p>

            <h3 className="text-lg font-semibold text-foreground mt-8 mb-3">
              Never called
            </h3>
            <p className={`${P} mb-4`}>
              The package contains no call to any of the following, so do not grant them:
            </p>
            <Table
              caption="AWS actions RepliMap never calls"
              head={["Action", "Why it matters"]}
              rows={[
                [
                  <Code key="a">secretsmanager:GetSecretValue</Code>,
                  <>Returns secret values. RepliMap lists secret names and metadata only.</>,
                ],
                [
                  <>
                    <Code>ssm:GetParameter</Code>, <Code>GetParameters</Code>,{" "}
                    <Code>GetParametersByPath</Code>
                  </>,
                  <>Return parameter values, including plain String ones. Only names are listed.</>,
                ],
                [
                  <>
                    <Code>kms:Decrypt</Code>
                  </>,
                  <>RepliMap reads key metadata and policies, never key material or ciphertext.</>,
                ],
                [
                  <Code key="d">lambda:GetFunction</Code>,
                  <>Returns a presigned URL to download function code. Code is never read.</>,
                ],
                [
                  <>
                    DynamoDB data plane: <Code>Scan</Code>, <Code>Query</Code>, <Code>GetItem</Code>,{" "}
                    <Code>BatchGetItem</Code>, <Code>ExportTableToPointInTime</Code>
                  </>,
                  <>
                    Table items are never read. Only table definitions, tags, PITR and TTL
                    settings are (<Code>scanners/dynamodb_scanner.py</Code>).
                  </>,
                ],
                [
                  <>
                    ECR image pulls: <Code>GetAuthorizationToken</Code>, <Code>BatchGetImage</Code>,{" "}
                    <Code>GetDownloadUrlForLayer</Code>
                  </>,
                  <>Image contents are unreachable. Only repository metadata is listed.</>,
                ],
              ]}
            />
            <p className={`${P} mt-4`}>
              Check it yourself with the commands in{" "}
              <a className={linkClass} href="#verify">
                How to verify
              </a>
              .
            </p>
          </section>

          <section aria-labelledby="license">
            <h2 id="license" className={H2}>
              2. License validation
            </h2>
            <Table
              caption="License validation request"
              head={["Question", "Answer"]}
              rows={[
                [
                  <>Endpoint</>,
                  <>
                    <Code>POST https://api.replimap.com/v1/license/validate</Code>. The URL is a
                    constant in <Code>licensing/manager.py</Code>; setting{" "}
                    <Code>REPLIMAP_LICENSE_API</Code> overrides it, for example to route the call
                    through an internal proxy.
                  </>,
                ],
                [
                  <>When</>,
                  <>
                    Only when you run <Code>replimap license activate &lt;key&gt;</Code>. No other
                    command makes this call, and neither does the air-gapped path below: <Code>scan</Code>, <Code>codify</Code>,{" "}
                    <Code>audit</Code>, <Code>drift</Code> and <Code>license status</Code> read the
                    local cache and verify it offline.
                  </>,
                ],
                [
                  <>Fields sent</>,
                  <>
                    JSON body with exactly three fields: <Code>license_key</Code>,{" "}
                    <Code>machine_id</Code>, <Code>cli_version</Code>. The server also sees the
                    standard connection metadata of any HTTPS request, such as your source IP
                    address.
                  </>,
                ],
                [
                  <>
                    What <Code>machine_id</Code> is
                  </>,
                  <>
                    The first 32 hex characters of a SHA-256 over the OS name, CPU architecture and
                    the operating system machine id (<Code>/etc/machine-id</Code> on Linux,{" "}
                    <Code>IOPlatformUUID</Code> on macOS, <Code>MachineGuid</Code> on Windows). If
                    none is readable, a random UUID stored in <Code>~/.replimap/.device_id</Code>{" "}
                    is used instead. Hostname and MAC address are not part of it, except in the rare case
                    where that file cannot be written and a value derived from the hostname is
                    used. The hash is not
                    salted, so treat it as a stable pseudonymous identifier for the machine, not
                    as anonymous data.
                  </>,
                ],
                [
                  <>Second call, rarely</>,
                  <>
                    <Code>POST /v1/license/deactivate</Code> with <Code>license_key</Code> and the
                    previous <Code>machine_id</Code>. It happens during activation, and only when
                    the local cache holds the same key bound to a different machine id (for
                    example after the id changed), to free the old machine slot. It is best-effort
                    and never blocks activation.
                  </>,
                ],
                [
                  <>What comes back</>,
                  <>
                    An Ed25519-signed license that the CLI verifies locally against a public key
                    embedded in the package, then caches in <Code>~/.replimap/license.json</Code>.
                    The cached file is re-verified locally on every load, with no network I/O.
                  </>,
                ],
                [
                  <>Offline behaviour</>,
                  <>
                    The signed license expires at the end of the current billing period plus a
                    plan-dependent offline grace: 7 days on Pro, 14 days on Team, 30 days on
                    Sovereign. The CLI never re-contacts the server on its own. After expiry the
                    license is rejected locally and the CLI falls back to the community tier until
                    you activate again.
                  </>,
                ],
                [
                  <>Air-gapped activation (Sovereign, from CLI 0.6.1)</>,
                  <>
                    Zero network calls on the isolated host. You run{" "}
                    <Code>replimap license machine-id</Code> on that host, we issue a signed
                    license file for that machine on request, and you import it with{" "}
                    <Code>replimap license activate --file &lt;path&gt;</Code>. The CLI verifies
                    the Ed25519 signature locally, and refuses a file that is bound to a different
                    machine or that is not issued for a Sovereign license. The file expires on
                    the date set when it is issued.
                  </>,
                ],
              ]}
            />
            <p className={`${P} mt-4`}>
              What the license service stores about these requests is described in the{" "}
              <Link className={linkClass} href="/privacy">
                privacy policy
              </Link>
              .
            </p>
          </section>

          <section aria-labelledby="else">
            <h2 id="else" className={H2}>
              3. Everything else
            </h2>
            <Table
              caption="Other possible network activity and its status"
              head={["Topic", "Status"]}
              rows={[
                [
                  <>Update checks</>,
                  <>
                    None. The only HTTP client calls in the package are the two license calls above;
                    nothing contacts PyPI or a version endpoint.
                  </>,
                ],
                [
                  <>Telemetry, analytics, crash reports</>,
                  <>
                    None. There is no analytics or crash-reporting SDK in the dependencies. Error
                    diagnostics are written to <Code>~/.replimap/logs/errors/</Code> and usage
                    counters to <Code>~/.replimap/usage_history.json</Code>, both local files.
                  </>,
                ],
                [
                  <>Fonts, CDNs and scripts in generated HTML reports</>,
                  <>
                    None. The dependency graph and audit reports inline their JavaScript and CSS
                    (D3, Chart.js and a precompiled Tailwind stylesheet are bundled in the
                    package). Opening a report loads nothing from the internet. They contain plain
                    links such as replimap.com and checkov.io that are followed only if you click
                    them.
                  </>,
                ],
                [
                  <>
                    <Code>replimap upgrade</Code>
                  </>,
                  <>
                    Opens the pricing or checkout page in your own browser. The CLI process sends
                    nothing.
                  </>,
                ],
                [
                  <>MCP server</>,
                  <>
                    Uses stdio transport. It does not open a network listener
                    (<Code>mcp_server.py</Code>).
                  </>,
                ],
                [
                  <>Optional external programs</>,
                  <>
                    <Code>audit</Code> runs the separate <Code>checkov</Code> program if you have it
                    installed, and <Code>codify</Code> runs <Code>terraform fmt</Code> if{" "}
                    <Code>terraform</Code> is on your PATH. They are separate programs; RepliMap does
                    not control their network behaviour, so include them in your own checks.
                  </>,
                ],
              ]}
            />
          </section>

          <section aria-labelledby="verify">
            <h2 id="verify" className={H2}>
              How to verify it yourself
            </h2>

            <h3 className="text-lg font-semibold text-foreground mb-3">
              Inspect the package
            </h3>
            <p className={`${P} mb-3`}>
              List every import of a network library in the shipped code:
            </p>
            <CodeBlock label="Shell commands to list network imports in the RepliMap package">{`pip download replimap --no-deps -d rm-wheel
unzip -q rm-wheel/*.whl -d rm-src
grep -rnE "^\\s*(import|from) (httpx|requests|urllib\\.request|urllib3|aiohttp|http\\.client|socket|webbrowser)\\b" \\
  rm-src/replimap --include='*.py'`}</CodeBlock>
            <p className={`${P} mt-3 mb-6`}>
              Expected hits: <Code>licensing/manager.py</Code> (<Code>httpx</Code>, the license
              calls), <Code>cli/commands/doctor.py</Code> (<Code>socket</Code>, the STS probe),{" "}
              <Code>cli/commands/upgrade.py</Code> and <Code>core/browser.py</Code> (
              <Code>webbrowser</Code>, which opens your browser). boto3 is the AWS path and is not
              matched here. To confirm the never-called list, search the same tree for{" "}
              <Code>get_secret_value</Code>, <Code>get_parameter</Code>, <Code>.decrypt(</Code>,{" "}
              <Code>get_function(</Code>, <Code>get_item(</Code>, <Code>batch_get_image</Code> and{" "}
              <Code>get_authorization_token</Code>. None are present.
            </p>

            <h3 className="text-lg font-semibold text-foreground mb-3">
              Watch it run
            </h3>
            <ul className={UL}>
              <li>
                <strong className="text-foreground">Proxy.</strong> Both the license call and boto3
                honour <Code>HTTPS_PROXY</Code>. Point it at any logging proxy (squid, mitmproxy)
                and read the destination hostnames:{" "}
                <Code>HTTPS_PROXY=http://127.0.0.1:3128 replimap scan --profile prod --region us-east-1</Code>
                . Expect only <Code>*.amazonaws.com</Code> hosts. A <Code>CONNECT</Code> log is
                enough; you do not need to decrypt anything.
              </li>
              <li>
                <strong className="text-foreground">strace.</strong>{" "}
                <Code>strace -f -e trace=connect -o rm.trace replimap scan --profile prod</Code>{" "}
                lists every outbound connection by address. Resolve the addresses and compare
                them with the AWS endpoints for your region.
              </li>
              <li>
                <strong className="text-foreground">Firewall.</strong> Run with default-deny egress
                and allow only AWS endpoints (and, for the one-time activation,{" "}
                <Code>api.replimap.com</Code>). If the scan completes, nothing else was needed.
              </li>
              <li>
                <strong className="text-foreground">License call only.</strong> Run{" "}
                <Code>replimap license activate</Code> behind the proxy and you will see a single
                request to <Code>api.replimap.com</Code> (plus the rare deactivate call described
                above). Run <Code>replimap license status</Code>{" "}
                afterwards and you will see none.
              </li>
            </ul>
          </section>
        </div>
      </main>
      <Footer />
    </>
  )
}
