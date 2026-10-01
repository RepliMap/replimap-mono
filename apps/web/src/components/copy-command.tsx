"use client"

import { useEffect, useRef, useState } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"

const RESET_MS = 2000

interface CopyCommandProps {
  command: string
  className?: string
}

/**
 * A shell command with a copy button. The button is a real <button>, so it is
 * keyboard-focusable and activates on Enter/Space; the "Copied" state is
 * announced through a polite live region.
 */
export function CopyCommand({ command, className }: CopyCommandProps) {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle")
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current)
    }
  }, [])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command)
      setStatus("copied")
    } catch {
      // Clipboard API missing (insecure context) or denied.
      setStatus("failed")
    }
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setStatus("idle"), RESET_MS)
  }

  return (
    <div
      className={cn(
        "inline-flex max-w-full items-center gap-3 rounded-lg border border-emerald-500/40 bg-card py-2 pl-4 pr-2 shadow-lg shadow-emerald-500/5",
        className
      )}
    >
      <span className="select-none font-mono text-emerald-400" aria-hidden="true">
        $
      </span>
      <code className="min-w-0 overflow-x-auto whitespace-nowrap font-mono text-base text-foreground sm:text-lg">
        {command}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={`Copy command: ${command}`}
        className="flex h-10 shrink-0 items-center gap-2 rounded-md bg-emerald-500 px-3 text-sm font-medium text-white transition-colors hover:bg-emerald-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        {status === "copied" ? (
          <Check className="h-4 w-4" aria-hidden="true" />
        ) : (
          <Copy className="h-4 w-4" aria-hidden="true" />
        )}
        <span>{status === "copied" ? "Copied" : status === "failed" ? "Press Ctrl+C" : "Copy"}</span>
      </button>
      <span role="status" aria-live="polite" className="sr-only">
        {status === "copied" ? "Command copied to clipboard" : status === "failed" ? "Copy failed. Select the command and copy it manually." : ""}
      </span>
    </div>
  )
}
