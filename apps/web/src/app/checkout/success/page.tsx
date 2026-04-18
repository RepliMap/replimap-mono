"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Check,
  Copy,
  ArrowRight,
  Terminal,
  Download,
  Key,
  Scan,
  Loader2,
  AlertCircle,
  RefreshCw,
} from "lucide-react"
import { getCheckoutLicense, type CheckoutLicenseResponse } from "@/lib/api"

const STEPS = [
  {
    icon: Download,
    title: "Install the CLI",
    command: "pip install replimap",
    description: "Works on macOS, Linux, and Windows (WSL).",
  },
  {
    icon: Key,
    title: "Activate your license",
    // {{LICENSE_KEY}} is substituted at render time with the real key
    command: "replimap auth login",
    description:
      "Opens your browser to authenticate. Or paste your license key directly when prompted.",
  },
  {
    icon: Scan,
    title: "Scan your AWS infrastructure",
    command: "replimap scan --profile your-profile --region us-east-1",
    description:
      "Discovers resources, maps dependencies, and builds your infrastructure graph.",
  },
]

// Poll schedule — cumulative wait to license-ready.
// 0s  →  request now (catches already-processed webhooks)
// +1s, +2s, +4s, +8s, +8s  →  up to ~23s total window
const BACKOFF_MS = [0, 1000, 2000, 4000, 8000, 8000]

type PollState =
  | { kind: "no-session" }
  | { kind: "pending" }
  | { kind: "ready"; license: CheckoutLicenseResponse }
  | { kind: "timeout" }

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session_id")
  const [state, setState] = useState<PollState>(
    sessionId ? { kind: "pending" } : { kind: "no-session" }
  )
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedCommand, setCopiedCommand] = useState<number | null>(null)

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false

    const poll = async () => {
      for (const delay of BACKOFF_MS) {
        if (cancelled) return
        if (delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, delay))
          if (cancelled) return
        }
        try {
          const license = await getCheckoutLicense(sessionId)
          if (!cancelled) {
            setState({ kind: "ready", license })
          }
          return
        } catch {
          // Keep polling — ApiError 404 means the webhook is still in flight
        }
      }
      if (!cancelled) setState({ kind: "timeout" })
    }

    poll()

    return () => {
      cancelled = true
    }
  }, [sessionId])

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const handleCopyCommand = (command: string, index: number) => {
    navigator.clipboard.writeText(command)
    setCopiedCommand(index)
    setTimeout(() => setCopiedCommand(null), 2000)
  }

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Success Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-6">
            <Check className="w-8 h-8 text-emerald-400" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            Payment successful!
          </h1>
          <p className="text-muted-foreground">
            Thank you for subscribing to RepliMap. A receipt has been sent to
            your email.
          </p>
        </div>

        {/* License Key Block — state-dependent */}
        {state.kind === "pending" && (
          <div className="rounded-2xl border border-border bg-card/50 p-6 mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
              <span className="text-sm font-medium text-foreground">
                Creating your license…
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              This usually takes a few seconds. Keep this page open.
            </p>
          </div>
        )}

        {state.kind === "ready" && (
          <div className="rounded-2xl border border-emerald-500/50 bg-emerald-500/5 p-6 mb-8">
            <div className="flex items-center gap-2 mb-3">
              <Key className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-medium text-foreground">
                Your license key
              </h2>
              <Badge
                variant="outline"
                className="ml-auto border-emerald-500/50 text-emerald-400 uppercase text-[10px]"
              >
                {state.license.plan}
              </Badge>
            </div>
            <div className="flex items-center gap-2 bg-slate-900 rounded-lg px-4 py-3">
              <code className="text-sm text-emerald-400 flex-1 overflow-x-auto font-mono tracking-wider">
                {state.license.license_key}
              </code>
              <button
                onClick={() => handleCopyKey(state.license.license_key)}
                className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
                aria-label="Copy license key"
              >
                {copiedKey ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              Save this somewhere safe. You can always retrieve it from your{" "}
              <Link
                href="/dashboard"
                className="text-emerald-400 hover:underline"
              >
                dashboard
              </Link>
              .
            </p>
          </div>
        )}

        {state.kind === "timeout" && (
          <div className="rounded-2xl border border-yellow-500/50 bg-yellow-500/5 p-6 mb-8">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-yellow-400" />
              <h2 className="text-sm font-medium text-foreground">
                License is taking longer than expected
              </h2>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Your payment was received but the license is still being created.
              Check your email in a minute, or refresh this page.
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => window.location.reload()}
              className="gap-2"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </Button>
          </div>
        )}

        {state.kind === "no-session" && (
          <div className="rounded-2xl border border-border bg-card/50 p-6 mb-8">
            <p className="text-sm text-muted-foreground">
              No checkout session found. Please visit your{" "}
              <Link
                href="/dashboard"
                className="text-emerald-400 hover:underline"
              >
                dashboard
              </Link>{" "}
              to find your license key.
            </p>
          </div>
        )}

        {/* Next Steps (always shown) */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Get started in 3 steps
          </h2>

          <div className="space-y-6">
            {STEPS.map((step, index) => {
              const Icon = step.icon
              return (
                <div
                  key={index}
                  className="rounded-xl border border-border bg-card/50 p-5"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold">
                      {index + 1}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className="w-4 h-4 text-emerald-400" />
                        <h3 className="font-medium text-foreground">
                          {step.title}
                        </h3>
                      </div>

                      <div className="flex items-center gap-2 bg-slate-900 rounded-lg px-4 py-3 mb-2">
                        <Terminal className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <code className="text-sm text-emerald-400 flex-1 overflow-x-auto">
                          {step.command}
                        </code>
                        <button
                          onClick={() =>
                            handleCopyCommand(step.command, index)
                          }
                          className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
                          aria-label="Copy command"
                        >
                          {copiedCommand === index ? (
                            <Check className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      <p className="text-sm text-muted-foreground">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Button
            asChild
            className="flex-1 h-12 bg-emerald-500 hover:bg-emerald-600 text-white"
          >
            <Link href="/dashboard">
              Go to Dashboard
              <ArrowRight className="ml-2 w-4 h-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" className="flex-1 h-12">
            <Link href="/docs">Read the Docs</Link>
          </Button>
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-muted-foreground mt-8">
          Need help? Check the{" "}
          <Link href="/docs" className="text-emerald-400 hover:underline">
            documentation
          </Link>{" "}
          or email{" "}
          <a
            href="mailto:support@replimap.com"
            className="text-emerald-400 hover:underline"
          >
            support@replimap.com
          </a>
        </p>
      </div>
    </div>
  )
}
