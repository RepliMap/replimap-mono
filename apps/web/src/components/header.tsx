"use client"

import { useState } from "react"
import Link from "next/link"
import { SignInButton, SignedIn, SignedOut, UserButton } from "@/components/auth-components"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Github, Menu, Terminal, Star } from "lucide-react"

const TALLY_FORM_URL = "https://tally.so/r/2EaYae"

export function Header() {
  // Controlled state for mobile sheet - ensures it closes on navigation
  const [open, setOpen] = useState(false)

  const handleLinkClick = () => {
    setOpen(false)
  }

  const navLinks = [
    { href: "/#features", label: "Features" },
    { href: "/#pricing", label: "Pricing" },
    { href: "/docs", label: "Docs" },
    { href: "/docs/changelog", label: "Changelog" },
  ]

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/95 supports-[backdrop-filter]:bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <Terminal className="w-6 h-6 text-emerald-400" />
          <span className="font-bold text-foreground text-lg">RepliMap</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-muted-foreground hover:text-foreground text-sm transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Right Side Actions */}
        <div className="flex items-center gap-4">
          {/* GitHub Stars */}
          <Link
            href="https://github.com/RepliMap/replimap-community"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Github className="w-4 h-4" />
            <Star className="w-3 h-3" />
            <Badge variant="secondary" className="text-xs">
              523
            </Badge>
          </Link>

          {/* Auth Actions - Desktop */}
          <div className="hidden md:flex items-center gap-4">
            <SignedIn>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  Dashboard
                </Button>
              </Link>
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "w-8 h-8",
                    userButtonPopoverCard: "bg-[#030712] border border-slate-800",
                    userButtonPopoverActionButton: "text-slate-300 hover:text-white hover:bg-slate-800",
                    userButtonPopoverActionButtonText: "text-slate-300",
                    userButtonPopoverFooter: "hidden",
                  },
                }}
              />
            </SignedIn>

            <SignedOut>
              <SignInButton mode="modal">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  Sign In
                </Button>
              </SignInButton>
              <a
                href={`${TALLY_FORM_URL}?source=nav`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white">
                  Get Started
                </Button>
              </a>
            </SignedOut>
          </div>

          {/* Mobile Menu */}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden text-muted-foreground">
                <Menu className="h-6 w-6" />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="bg-background border-border">
              <nav className="flex flex-col gap-4 mt-8">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={handleLinkClick}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                ))}
                <div className="border-t border-border pt-4 mt-4 flex flex-col gap-3">
                  <Link
                    href="https://github.com/RepliMap/replimap-community"
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={handleLinkClick}
                    className="flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm"
                  >
                    <Github className="w-4 h-4" />
                    View on GitHub
                  </Link>

                  <SignedIn>
                    <Link
                      href="/dashboard"
                      onClick={handleLinkClick}
                      className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                    >
                      Dashboard
                    </Link>
                    <div className="flex items-center gap-2">
                      <UserButton
                        appearance={{
                          elements: {
                            avatarBox: "w-8 h-8",
                            userButtonPopoverCard: "bg-[#030712] border border-slate-800",
                            userButtonPopoverActionButton: "text-slate-300 hover:text-white hover:bg-slate-800",
                            userButtonPopoverActionButtonText: "text-slate-300",
                            userButtonPopoverFooter: "hidden",
                          },
                        }}
                      />
                      <span className="text-muted-foreground text-sm">Account</span>
                    </div>
                  </SignedIn>

                  <SignedOut>
                    <SignInButton mode="modal">
                      <Button
                        variant="ghost"
                        className="justify-start p-0 h-auto text-muted-foreground hover:text-foreground text-sm"
                        onClick={handleLinkClick}
                      >
                        Sign In
                      </Button>
                    </SignInButton>
                    <a
                      href={`${TALLY_FORM_URL}?source=nav_mobile`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={handleLinkClick}
                    >
                      <Button className="bg-emerald-500 hover:bg-emerald-600 text-white">
                        Get Started
                      </Button>
                    </a>
                  </SignedOut>
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
