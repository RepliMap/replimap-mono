import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    question: "Is my AWS data sent to your servers?",
    answer:
      "No. RepliMap runs 100% locally on your machine. Your AWS credentials and infrastructure data never leave your environment. We only contact our license server for subscription validation—no infrastructure data is transmitted.",
  },
  {
    question: "Can I use RepliMap in air-gapped environments?",
    answer:
      "Scanning and all reports run fully offline once your license is activated: Pro includes a 7-day offline grace period and Team 14 days between license checks, and every generated report (including the interactive dependency graph) is a self-contained file that loads nothing from the internet. Fully offline activation for permanently air-gapped environments is part of the Sovereign plan.",
  },
  {
    question: "What AWS services are supported?",
    answer:
      "RepliMap scans 30+ AWS resource types across VPC, EC2, RDS, ElastiCache, Lambda, S3, IAM, ELB/ALB, Auto Scaling, SQS, SNS, CloudWatch and more — the core of a typical production account. New types are added based on what real scans encounter.",
  },
  {
    question: "How does the Lifetime deal work?",
    answer:
      "Pay once, use forever. Lifetime licenses include all features of the selected tier (Pro or Team) and all future updates. No recurring charges. Limited availability at Early Bird pricing.",
  },
  {
    question: "Can I upgrade or downgrade my plan?",
    answer:
      "Yes. Upgrades take effect immediately with prorated billing. Downgrades take effect at the end of your current billing cycle. Lifetime license holders can upgrade to a higher lifetime tier by paying the difference.",
  },
  {
    question: "How many AWS accounts can I scan?",
    answer:
      "Community covers 1 AWS account. Pro and above are uncapped under fair use — RepliMap is built for contractors and consultancies who rotate through client accounts, so we don't meter the thing your job depends on.",
  },
  {
    question: "Does RepliMap do drift detection?",
    answer:
      "Honestly: attribute-level drift comparison is experimental and not something we charge for today. What we ship and stand behind is IaC Coverage — telling you exactly which resources exist in no Terraform state at all, which is the question terraform plan structurally cannot answer.",
  },
]

export function FAQ() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-3xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-foreground">Frequently Asked Questions</h2>
        </div>

        <Accordion type="single" collapsible className="w-full">
          {faqs.map((faq, index) => (
            <AccordionItem key={index} value={`item-${index}`} className="border-b border-border">
              <AccordionTrigger className="text-left text-foreground font-medium py-4 hover:text-emerald-400 hover:no-underline">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground pb-4">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
