import Link from "next/link"
import { Github, Twitter, MessageCircle, Terminal } from "lucide-react"

type FooterLink = { label: string; href: string; external?: boolean }

const footerLinks: Record<string, FooterLink[]> = {
  product: [
    { label: "Features", href: "#features" },
    { label: "Pricing", href: "#pricing" },
    { label: "Changelog", href: "https://github.com/RepliMap/replimap-community/blob/main/CHANGELOG.md", external: true },
  ],
  resources: [
    { label: "Documentation", href: "https://github.com/RepliMap/replimap-community#readme", external: true },
  ],
  company: [
    { label: "Support", href: "https://github.com/RepliMap/replimap-community/issues", external: true },
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
  ],
}

const socialLinks = [
  { icon: Github, href: "https://github.com/RepliMap/replimap-community", label: "GitHub" },
  { icon: Twitter, href: "https://twitter.com/replimap_io", label: "Twitter" },
  { icon: MessageCircle, href: "https://discord.gg/CXa7ZJmFM6", label: "Discord" },
]

export function Footer() {
  return (
    <footer className="py-12 bg-background border-t border-border">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <Terminal className="w-6 h-6 text-emerald-400" />
              <span className="font-bold text-foreground text-lg">RepliMap</span>
            </Link>
            <p className="text-muted-foreground text-sm mt-2">AWS Infrastructure Intelligence</p>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-foreground font-semibold text-sm mb-4">Product</h3>
            <ul className="space-y-2">
              {footerLinks.product.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    {...(link.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-foreground font-semibold text-sm mb-4">Resources</h3>
            <ul className="space-y-2">
              {footerLinks.resources.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    {...(link.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-foreground font-semibold text-sm mb-4">Company</h3>
            <ul className="space-y-2">
              {footerLinks.company.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    {...(link.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Social */}
          <div>
            <h3 className="text-foreground font-semibold text-sm mb-4">Connect</h3>
            <div className="flex items-center gap-4">
              {socialLinks.map((social, index) => {
                const Icon = social.icon
                return (
                  <Link
                    key={index}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={social.label}
                  >
                    <Icon className="w-5 h-5" />
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-muted-foreground text-sm">© 2025-{new Date().getFullYear()} RepliMap. All rights reserved.</p>
          <p className="text-muted-foreground text-sm">Made with ❤️ in New Zealand</p>
        </div>
      </div>
    </footer>
  )
}
