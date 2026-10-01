import { Header } from "@/components/header"
import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { UseCases } from "@/components/use-cases"
import { Pricing } from "@/components/pricing"
import { FAQ } from "@/components/faq"
import { CallToAction } from "@/components/call-to-action"
import { Footer } from "@/components/footer"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <Header />
      <Hero />
      <Features />
      <UseCases />
      <Pricing />
      <FAQ />
      <CallToAction />
      <Footer />
    </main>
  )
}
