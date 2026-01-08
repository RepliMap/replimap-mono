import { Card } from "@/components/ui/card"
import { Clock, Shield, GitCompare, FileCode, Zap, Building2 } from "lucide-react"

const useCases = [
  {
    icon: Clock,
    title: "Audit Time Reduction",
    metric: "2 weeks → 2 hours",
    description:
      "Generate complete infrastructure documentation for compliance audits. Export to PDF with one command.",
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
    title: "Drift Prevention",
    metric: "Catch issues early",
    description:
      "Detect configuration drift between your Terraform state and live AWS infrastructure before incidents happen.",
  },
]

const targetAudience = [
  { icon: Building2, label: "FinTech & Banking" },
  { icon: Shield, label: "SOC2 Compliant Teams" },
  { icon: FileCode, label: "Platform Engineers" },
  { icon: Zap, label: "DevOps Teams" },
]

export function UseCases() {
  return (
    <section className="py-24 bg-background">
      <div className="max-w-6xl mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Built for infrastructure teams
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            RepliMap helps teams reduce manual work, improve security posture, and maintain infrastructure consistency.
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
