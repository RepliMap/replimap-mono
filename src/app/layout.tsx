import type { Metadata } from "next";
import localFont from "next/font/local";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
  display: "swap",
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
  display: "swap",
  fallback: ["ui-monospace", "monospace"],
});

// SEO Metadata
export const metadata: Metadata = {
  title: {
    default: "RepliMap - AWS Infrastructure Intelligence",
    template: "%s | RepliMap",
  },
  description:
    "Reverse-engineer your AWS infrastructure into Terraform, detect drift, and generate least-privilege IAM policies. Open-source CLI tool.",
  keywords: [
    "AWS",
    "Terraform",
    "Infrastructure as Code",
    "IAM",
    "drift detection",
    "cloud security",
    "DevOps",
    "SRE",
    "infrastructure audit",
  ],
  authors: [{ name: "RepliMap" }],
  creator: "RepliMap",
  // Icons from v0 (enhanced)
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-icon.png",
  },
  openGraph: {
    title: "RepliMap - AWS Infrastructure Intelligence",
    description: "Reverse-engineer your AWS infrastructure into Terraform",
    url: "https://replimap.com",
    siteName: "RepliMap",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "RepliMap - AWS Infrastructure Intelligence",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "RepliMap - AWS Infrastructure Intelligence",
    description: "Reverse-engineer your AWS infrastructure into Terraform",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

// JSON-LD Structured Data for SEO
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "RepliMap",
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Linux, macOS, Windows",
  description:
    "AWS Infrastructure Intelligence Engine - Reverse-engineer infrastructure into Terraform, detect drift, generate IAM policies",
  offers: [
    { "@type": "Offer", price: "0", priceCurrency: "USD", name: "Free" },
    { "@type": "Offer", price: "49", priceCurrency: "USD", name: "Solo" },
    { "@type": "Offer", price: "99", priceCurrency: "USD", name: "Pro" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        {/* JSON-LD for SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          forcedTheme="dark"
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
