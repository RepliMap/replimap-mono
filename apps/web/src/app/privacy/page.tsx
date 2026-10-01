import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "RepliMap Privacy Policy - How we handle your data",
}

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-background pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-foreground mb-8">Privacy Policy</h1>
        <p className="text-muted-foreground mb-4">Last updated: 1 October 2026</p>

        <div className="prose prose-invert prose-emerald max-w-none space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Overview</h2>
            <p className="text-muted-foreground leading-relaxed">
              RepliMap is designed with privacy at its core. Our CLI tool runs locally on your
              machine. Your AWS credentials, infrastructure data, and generated outputs never leave
              your environment. The only call the CLI makes to our servers is license activation,
              described below. See{" "}
              <a href="/security" className="text-emerald-400 hover:text-emerald-300">
                What RepliMap talks to
              </a>{" "}
              for the complete list of network destinations.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">What We Collect</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We collect minimal data necessary to operate our service:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>
                <strong className="text-foreground">Account Information:</strong> Email address for
                license management and support communications.
              </li>
              <li>
                <strong className="text-foreground">License Activation:</strong> When you run{" "}
                <code>replimap license activate</code>, the CLI sends your license key, a machine
                identifier and the CLI version. The machine identifier is a truncated SHA-256 hash
                of your operating system, CPU architecture and the operating system&apos;s machine
                id. It does not include your MAC address, and it includes your hostname only in the rare case where the CLI cannot write its fallback id file. The hash is not salted, so it
                is a stable pseudonymous identifier for your machine, not anonymous data. The
                service also receives your IP address as part of the connection. No infrastructure
                data is transmitted.
              </li>
              <li>
                <strong className="text-foreground">Activation Records:</strong> For each
                activation request we store a log entry (license, machine identifier, CLI
                version, timestamp), and a machine record with first-seen and last-seen times that
                is used to enforce your plan&apos;s machine limit. The CLI does not send scan
                counts or feature usage.
              </li>
              <li>
                <strong className="text-foreground">Fields the Service Does Not Accept:</strong>{" "}
                The license service has no endpoints that accept AWS account IDs, region or VPC
                identifiers, snapshot, remediation or usage-event data, or device hostnames.
              </li>
              <li>
                <strong className="text-foreground">Payment Information:</strong> Processed securely
                by Stripe. We do not store credit card numbers.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">What We Do NOT Collect</h2>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>AWS credentials or access keys</li>
              <li>Infrastructure configuration data</li>
              <li>Generated Terraform code</li>
              <li>IAM policies or security configurations</li>
              <li>Any data from your AWS accounts</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Data Security</h2>
            <p className="text-muted-foreground leading-relaxed">
              RepliMap operates entirely on your local machine. Besides your own AWS API calls, the
              only network communication is with our license server, and only when you activate a
              license. This communication is
              encrypted using TLS and contains only your license key, a hashed machine
              identifier and the CLI version. Rate limiting counters keyed by IP address are kept
              for about two minutes. Operational logs may contain a truncated identifier (the
              prefix <code>RM-</code> plus at most four characters of a license key, or a shortened
              machine identifier) when abuse checks trigger.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Air-Gapped Environments</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              Online activation (all paid plans) needs one network call. The CLI then verifies the
              signed license locally and does not contact our servers again on its own. The signed
              license expires at the end of your current billing period plus an offline grace
              period (7 days on Pro, 14 days on Team, 30 days on Sovereign), after which you must
              activate again.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              Sovereign customers can instead activate with no network call on the isolated host,
              from CLI 0.6.1. You run <code>replimap license machine-id</code> on that host and send
              us the id. We issue a signed license file for that machine on request, and you import
              it with <code>replimap license activate --file &lt;path&gt;</code>. The file is bound
              to one machine and expires on the date set when we issue it. We record each file we
              issue (see Retention).
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Retention</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              A job runs automatically every day and deletes data on the schedule below. Nothing
              else is deleted automatically.
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>
                Records of devices you have removed are deleted 90 days after removal. Active devices
                are never removed automatically.
              </li>
              <li>Activation and validation logs are kept for 90 days.</li>
              <li>Device-change logs are kept for 90 days.</li>
              <li>
                The log of offline licenses we issue is kept as an audit record.
              </li>
              <li>Request-deduplication keys are kept for 7 days.</li>
              <li>Payment-event identifiers are kept for 30 days.</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-4">
              Contact us if you want other data deleted.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Contact</h2>
            <p className="text-muted-foreground leading-relaxed">
              For privacy-related questions, contact us at{" "}
              <a
                href="mailto:hello@replimap.com"
                className="text-emerald-400 hover:text-emerald-300"
              >
                hello@replimap.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </main>
  )
}
