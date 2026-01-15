import { FileCode, Shield, GitCompare, Zap, Network, Lock } from "lucide-react"

const features = [
  {
    icon: FileCode,
    title: "Terraform Generation",
    description:
      "Reverse-engineer existing AWS resources into clean, production-ready Terraform code.",
  },
  {
    icon: GitCompare,
    title: "Drift Detection",
    description:
      "Detect configuration drift between your Terraform state and actual AWS infrastructure.",
  },
  {
    icon: Shield,
    title: "IAM Generation",
    description: "Generate least-privilege IAM policies based on actual resource dependencies.",
  },
  {
    icon: Network,
    title: "Dependency Mapping",
    description: "Visualize resource relationships and understand blast radius of changes.",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Scan thousands of resources in seconds with parallel processing.",
  },
  {
    icon: Lock,
    title: "Security First",
    description:
      "Runs 100% locally. Your credentials and infrastructure data never leave your machine.",
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 bg-muted/30">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Everything you need to manage AWS at scale
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            RepliMap provides a complete toolkit for infrastructure intelligence, from reverse
            engineering to security hardening.
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
