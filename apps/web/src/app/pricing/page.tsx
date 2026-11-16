import type { Metadata } from "next"
import { Header } from "@/components/header"
import { Pricing } from "@/components/pricing"
import { FAQ } from "@/components/faq"
import { Footer } from "@/components/footer"

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "RepliMap plans: a free Community tier, Pro, Team and Sovereign. Monthly and annual billing.",
  alternates: { canonical: "https://www.replimap.com/pricing" },
}

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background">
      <Header />
      <h1 className="sr-only">RepliMap Pricing</h1>
      <Pricing />
      <FAQ />
      <Footer />
    </main>
  )
}
