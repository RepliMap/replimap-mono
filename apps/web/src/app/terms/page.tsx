import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "RepliMap Terms of Service",
}

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-background pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-foreground mb-8">Terms of Service</h1>
        <p className="text-muted-foreground mb-4">Last updated: January 2026</p>

        <div className="prose prose-invert prose-emerald max-w-none space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              By using RepliMap, you agree to these Terms of Service. If you do not agree, please do
              not use our software or services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">2. Description of Service</h2>
            <p className="text-muted-foreground leading-relaxed">
              RepliMap is a command-line tool that helps you reverse-engineer AWS infrastructure into
              Terraform code, detect configuration drift, and generate IAM policies. The software
              runs locally on your machine and does not transmit infrastructure data to our servers.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">3. License</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              Subject to your compliance with these Terms, we grant you a limited, non-exclusive,
              non-transferable license to use RepliMap according to your subscription tier:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>
                <strong className="text-foreground">Free:</strong> Limited features for evaluation
                purposes.
              </li>
              <li>
                <strong className="text-foreground">Solo/Pro/Team:</strong> Full features according
                to the plan purchased.
              </li>
              <li>
                <strong className="text-foreground">Lifetime:</strong> Perpetual license for the
                purchased tier, including future updates.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">4. Restrictions</h2>
            <p className="text-muted-foreground leading-relaxed">You may not:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2 mt-2">
              <li>Reverse engineer, decompile, or disassemble the software</li>
              <li>Share, resell, or redistribute your license</li>
              <li>Use the software to violate any laws or regulations</li>
              <li>Remove any proprietary notices from the software</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">5. Disclaimer</h2>
            <p className="text-muted-foreground leading-relaxed">
              RepliMap is provided &quot;as is&quot; without warranty of any kind. We do not
              guarantee that the generated Terraform code or IAM policies will be error-free or
              suitable for production use without review. You are responsible for reviewing and
              testing all outputs before deployment.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. Limitation of Liability</h2>
            <p className="text-muted-foreground leading-relaxed">
              To the maximum extent permitted by law, RepliMap and its creators shall not be liable
              for any indirect, incidental, special, consequential, or punitive damages arising from
              your use of the software.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">7. Refund Policy</h2>
            <p className="text-muted-foreground leading-relaxed">
              Monthly and annual subscriptions may be canceled at any time. Refunds for Lifetime
              licenses are available within 14 days of purchase if you have not activated the
              license.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Changes to Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may update these Terms from time to time. Continued use of RepliMap after changes
              constitutes acceptance of the new Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">9. Contact</h2>
            <p className="text-muted-foreground leading-relaxed">
              For questions about these Terms, contact us at{" "}
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
