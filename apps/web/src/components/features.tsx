import { FileCode, Shield, GitCompare, Zap, Network, Lock } from "lucide-react"

const features = [
  {
    icon: FileCode,
    title: "Terraform Generation",
    description:
      "Turn an existing AWS account into clean Terraform plus a full import scaffold — an adoption starting point that validates on day one.",
  },
  {
    icon: GitCompare,
    title: "IaC Coverage",
    description:
      "See exactly which resources live in no Terraform state at all — the ClickOps inventory that terraform plan structurally can't show you.",
  },
  {
    icon: Shield,
    title: "IAM Generation",
    description: "Generate least-privilege IAM policies based on actual resource dependencies.",
  },
  {
    icon: Network,
    title: "Dependency Mapping",
    description:
      "Visualize resource relationships and blast radius in an interactive graph — one self-contained HTML file you can open air-gapped or hand to a client.",
  },
  {
    icon: Zap,
    title: "Resilient Scanning",
    description:
      "Parallel scanners cover 1,500+ resource accounts in minutes, with per-item retries so a transient AWS error never silently drops a resource.",
  },
  {
    icon: Lock,
    title: "Security First",
    description:
      "Runs 100% locally. Credentials and infrastructure data never leave your machine — even generated reports load nothing from the internet.",
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 bg-muted/30">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Everything you need to take over a brownfield AWS account
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            From the first scan to import-ready Terraform and audit evidence — the takeover
            workflow, end to end.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="p-6 rounded-xl bg-card/50 border border-border hover:border-emerald-500/50 transition-colors duration-300"
              >
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
