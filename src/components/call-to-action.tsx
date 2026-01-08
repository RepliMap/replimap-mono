"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, BookOpen, Copy, Check } from "lucide-react"
import { useState } from "react"

export function CallToAction() {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText("pip install replimap")
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section className="py-24 bg-gradient-to-b from-emerald-900/20 via-background to-background">
      <div className="max-w-3xl mx-auto px-4 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">
          Ready to take control of your AWS infrastructure?
        </h2>
        <p className="text-muted-foreground mt-4 mb-8">
          Start scanning in under 2 minutes. No credit card required.
        </p>

        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button asChild size="lg" className="bg-emerald-500 hover:bg-emerald-600 h-12 px-8">
            <Link href="#pricing">
              Get Started Free
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            size="lg"
            variant="outline"
            className="border-border h-12 px-8 bg-transparent"
          >
            <Link href="/docs">
              <BookOpen className="mr-2 h-4 w-4" />
              Read the Docs
            </Link>
          </Button>
        </div>

        <div className="mt-8 inline-flex items-center gap-3 bg-muted/50 border border-border rounded-lg px-4 py-2">
          <span className="font-mono text-sm text-muted-foreground">pip install replimap</span>
          <button
            onClick={handleCopy}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Copy install command"
          >
            {copied ? (
              <Check className="h-4 w-4 text-emerald-400" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </section>
  )
}
