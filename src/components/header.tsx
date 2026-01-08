"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Github, Menu, Terminal, Star } from "lucide-react"

export function Header() {
  // Controlled state for mobile sheet - ensures it closes on navigation
  const [open, setOpen] = useState(false)

  const handleLinkClick = () => {
    setOpen(false)
  }

  const navLinks = [
    { href: "#features", label: "Features" },
    { href: "#pricing", label: "Pricing" },
    { href: "/docs", label: "Docs" },
    { href: "/changelog", label: "Changelog" },
  ]

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
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
            href="https://github.com/replimap/replimap"
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

          {/* Primary CTA - Links to pricing instead of non-existent sign-up */}
          <Button asChild size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white">
            <Link href="#pricing">Get Started</Link>
          </Button>

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
                    href="https://github.com/replimap/replimap"
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={handleLinkClick}
                    className="flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm"
                  >
                    <Github className="w-4 h-4" />
                    View on GitHub
                  </Link>
                  <Button
                    asChild
                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                    onClick={handleLinkClick}
                  >
                    <Link href="#pricing">Get Started</Link>
                  </Button>
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
