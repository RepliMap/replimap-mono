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
        <p className="text-muted-foreground mb-4">Last updated: January 2026</p>

        <div className="prose prose-invert prose-emerald max-w-none space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Overview</h2>
            <p className="text-muted-foreground leading-relaxed">
              RepliMap is designed with privacy at its core. Our CLI tool runs 100% locally on your
              machine. Your AWS credentials, infrastructure data, and generated outputs never leave
              your environment.
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
                <strong className="text-foreground">License Validation:</strong> Machine ID hash
                (anonymized) for license activation. No infrastructure data is transmitted.
              </li>
              <li>
                <strong className="text-foreground">Usage Analytics:</strong> Anonymized usage
                statistics (scan counts, feature usage) to improve our product.
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
              RepliMap operates entirely on your local machine. The only network communication is
              with our license server to validate your subscription status. This communication is
              encrypted using TLS 1.3 and contains only your license key and anonymized machine
              identifier.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Air-Gapped Environments</h2>
            <p className="text-muted-foreground leading-relaxed">
              For air-gapped or restricted network environments, Solo and Pro plans support offline
              license activation. Contact support for assistance with offline deployments.
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
