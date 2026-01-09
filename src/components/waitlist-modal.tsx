/**
 * @deprecated This component is deprecated due to Tally Pro limitation.
 *
 * Tally forms show dark theme when accessed directly but force light theme
 * in iframe embeds (this is a Tally Pro paid feature).
 *
 * Use direct links instead:
 * <a href="https://tally.so/r/2EaYae?source=xxx" target="_blank" rel="noopener noreferrer">
 *   <Button>Get Started</Button>
 * </a>
 */
"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

const TALLY_FORM_ID = "2EaYae"
const BASE_TALLY_URL = `https://tally.so/r/${TALLY_FORM_ID}?transparentBackground=1&hideTitle=1`

interface WaitlistModalProps {
  children: React.ReactNode
  source?: string // Track where the user clicked (for analytics)
}

export function WaitlistModal({ children, source = "generic" }: WaitlistModalProps) {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Dynamic URL with source tracking
  const formUrl = `${BASE_TALLY_URL}&source=${encodeURIComponent(source)}`

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent
        className="sm:max-w-[550px] p-0 overflow-hidden bg-background border-border"
        showCloseButton={true}
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Join the Waitlist</DialogTitle>
        </DialogHeader>
        {/* Dark background prevents white flash while iframe loads */}
        <div className="w-full h-[750px] relative bg-background">
          {/* Loading spinner */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          <iframe
            src={formUrl}
            width="100%"
            height="100%"
            frameBorder="0"
            title="Join Waitlist"
            className="absolute inset-0 bg-transparent"
            onLoad={() => setIsLoading(false)}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
