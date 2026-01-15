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
      "Yes. Solo and Pro plans support offline license activation with machine ID binding. Enterprise customers get additional support for air-gapped deployments.",
  },
  {
    question: "What AWS services are supported?",
    answer:
      "RepliMap supports 50+ AWS services including VPC, EC2, RDS, Lambda, S3, IAM, ECS, EKS, DynamoDB, SQS, SNS, and more. We're constantly adding new services based on user feedback.",
  },
  {
    question: "How does the Lifetime deal work?",
    answer:
      "Pay once, use forever. Lifetime licenses include all features of the selected tier (Solo or Pro) and all future updates. No recurring charges. Limited to the first 50 customers at Early Bird pricing.",
  },
  {
    question: "Can I upgrade or downgrade my plan?",
    answer:
      "Yes. Upgrades take effect immediately with prorated billing. Downgrades take effect at the end of your current billing cycle. Lifetime license holders can upgrade to a higher lifetime tier by paying the difference.",
  },
  {
    question: "What if I need more than 10 AWS accounts?",
    answer:
      "Enterprise plans support unlimited AWS accounts. Contact our sales team for custom pricing based on your organization's needs.",
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
