import { Card } from "@/components/ui/card"
import { Clock, Shield, GitCompare, FileCode, Zap, Building2 } from "lucide-react"

const useCases = [
  {
    icon: Clock,
    title: "Brownfield Takeover",
    metric: "Weeks → a day",
    description:
      "Walk into an unfamiliar AWS account and walk out with a full inventory, a dependency map, and import-ready Terraform.",
  },
  {
    icon: Shield,
    title: "Security Hardening",
    metric: "Zero manual IAM",
    description:
      "Auto-generate least-privilege IAM policies based on actual resource dependencies and usage patterns.",
  },
  {
    icon: GitCompare,
    title: "Audit Evidence",
    metric: "Evidence, not screenshots",
    description:
      "Run a SOC 2-mapped audit against live AWS and export the findings as an evidence package your auditor can actually use.",
  },
]

const targetAudience = [
  { icon: Zap, label: "DevOps Contractors" },
  { icon: Building2, label: "Cloud Consultancies" },
  { icon: Shield, label: "SOC 2-bound Startups" },
  { icon: FileCode, label: "Platform Engineers" },
]

export function UseCases() {
  return (
    <section className="py-24 bg-background">
      <div className="max-w-6xl mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Built for the people who inherit AWS accounts
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Most AWS environments weren&apos;t born in Terraform. RepliMap is for whoever has to
            clean that up — and prove it&apos;s done.
          </p>
        </div>

        {/* Use Case Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {useCases.map((useCase, index) => (
            <Card
              key={index}
              className="p-6 bg-card border-border hover:border-emerald-500/50 transition-colors"
            >
              {/* Metric Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full mb-4">
                <useCase.icon className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400 font-medium text-sm">{useCase.metric}</span>
              </div>

              {/* Title */}
              <h3 className="text-xl font-semibold text-foreground mb-2">{useCase.title}</h3>

              {/* Description */}
              <p className="text-muted-foreground text-sm leading-relaxed">{useCase.description}</p>
            </Card>
          ))}
        </div>

        {/* Target Audience */}
        <div className="flex flex-wrap items-center justify-center gap-4">
          <span className="text-muted-foreground text-sm">Built for:</span>
          {targetAudience.map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 border border-border rounded-full text-sm text-muted-foreground"
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
