"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Github, Terminal } from "lucide-react"

export function Hero() {
  // Typewriter animation state
  const command1 = "pip install replimap"
  const command2 = "replimap scan --profile prod --region us-east-1"
  const [text1, setText1] = useState("")
  const [text2, setText2] = useState("")
  const [showOutput, setShowOutput] = useState(false)
  const [cursorVisible, setCursorVisible] = useState(true)

  // Typewriter effect
  useEffect(() => {
    let i = 0
    const typingSpeed1 = 50 // ms per character for first command
    const typingSpeed2 = 30 // ms per character for second command
    const delayBetweenCommands = 500 // ms delay between commands
    const delayBeforeOutput = 300 // ms delay before showing output

    const timer1 = setInterval(() => {
      setText1(command1.slice(0, i + 1))
      i++
      if (i > command1.length) {
        clearInterval(timer1)
        // Start second command after delay
        setTimeout(() => {
          let j = 0
          const timer2 = setInterval(() => {
            setText2(command2.slice(0, j + 1))
            j++
            if (j > command2.length) {
              clearInterval(timer2)
              // Show output after delay
              setTimeout(() => {
                setShowOutput(true)
                setCursorVisible(false)
              }, delayBeforeOutput)
            }
          }, typingSpeed2)
        }, delayBetweenCommands)
      }
    }, typingSpeed1)

    return () => clearInterval(timer1)
  }, [])

  // Cursor blink effect
  useEffect(() => {
    if (!showOutput) {
      const cursorTimer = setInterval(() => {
        setCursorVisible((prev) => !prev)
      }, 530)
      return () => clearInterval(cursorTimer)
    }
  }, [showOutput])

  return (
    <section className="relative min-h-[90vh] flex items-center bg-background bg-dot-pattern">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 via-transparent to-cyan-500/10 pointer-events-none" />

      {/* Content container */}
      <div className="relative max-w-6xl mx-auto px-4 text-center py-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Badge */}
        <div className="mb-6 flex justify-center">
          <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 px-4 py-1.5">
            🚀 v1.0 Released — Now with IAM Generation
          </Badge>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
          <span className="text-foreground">AWS Infrastructure</span>
          <br />
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Intelligence Engine
          </span>
        </h1>

        {/* Subheadline */}
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed mb-8">
          Reverse-engineer your AWS infrastructure into Terraform. Detect drift. Generate least-privilege IAM policies.
          <span className="text-emerald-400 font-medium"> In seconds.</span>
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
          <Button asChild className="bg-emerald-500 hover:bg-emerald-600 text-white h-12 px-8">
            <Link href="/sign-up">
              Get Started Free
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-border text-muted-foreground hover:bg-muted h-12 px-8 bg-transparent"
          >
            <Link href="https://github.com/replimap/replimap" target="_blank" rel="noopener noreferrer">
              <Github className="mr-2 h-4 w-4" />
              View on GitHub
            </Link>
          </Button>
        </div>

        {/* Terminal Mockup */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-card rounded-xl border border-border shadow-2xl overflow-hidden">
            {/* Terminal header bar */}
            <div className="flex items-center gap-2 px-4 py-3 bg-muted/50 border-b border-border">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <div className="flex items-center gap-2 ml-2 text-muted-foreground text-sm">
                <Terminal className="w-4 h-4" />
                <span>terminal</span>
              </div>
            </div>

            {/* Terminal content with typewriter effect */}
            <div className="p-6 font-mono text-sm text-left space-y-2 min-h-[200px]">
              {/* First command */}
              <div className="flex items-center">
                <span className="text-emerald-400 select-none mr-2">$</span>
                <span className="text-foreground">{text1}</span>
                {text1.length < command1.length && cursorVisible && (
                  <span className="bg-muted-foreground w-2 h-4 inline-block ml-0.5" />
                )}
              </div>

              {/* Second command - appears after first is complete */}
              {text1.length === command1.length && (
                <div className="flex items-center">
                  <span className="text-emerald-400 select-none mr-2">$</span>
                  <span className="text-foreground">{text2}</span>
                  {text2.length < command2.length && !showOutput && cursorVisible && (
                    <span className="bg-muted-foreground w-2 h-4 inline-block ml-0.5" />
                  )}
                </div>
              )}

              {/* Output - appears after second command is complete */}
              {showOutput && (
                <div className="text-muted-foreground pl-4 border-l-2 border-border ml-2 space-y-1 pt-2 animate-in fade-in duration-500">
                  <div>
                    <span className="text-cyan-400">Scanning:</span> VPC, EC2, RDS, Lambda, S3...
                  </div>
                  <div>
                    <span className="text-emerald-400">✓</span> Found{" "}
                    <span className="text-foreground">1,847</span> resources
                  </div>
                  <div>
                    <span className="text-emerald-400">✓</span> Mapped{" "}
                    <span className="text-foreground">2,156</span> dependencies
                  </div>
                  <div>
                    <span className="text-emerald-400">✓</span> Generated Terraform in{" "}
                    <span className="text-cyan-400">./output/</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Social Proof */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 md:gap-8 text-muted-foreground text-sm">
          {/* Security Badge - Prominent placement */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
            <svg
              className="w-4 h-4 text-emerald-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <span className="text-emerald-400 font-medium">100% Local Execution</span>
          </div>

          <div className="hidden md:block w-px h-4 bg-border" />

          {/* Stats */}
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold text-lg">500+</span>
            <span>GitHub Stars</span>
          </div>
          <div className="hidden md:block w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold text-lg">50+</span>
            <span>Contributors</span>
          </div>
          <div className="hidden md:block w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold text-lg">10K+</span>
            <span>Scans Run</span>
          </div>
        </div>
      </div>
    </section>
  )
}
