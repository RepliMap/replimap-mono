import type { Metadata } from "next";
import localFont from "next/font/local";
import { ClerkProviderWrapper } from "@/components/clerk-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { generateSiteSchema } from "@/lib/schema";
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
  metadataBase: new URL('https://replimap.com'),

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
    "AWS to Terraform",
    "reverse engineer AWS",
    "Terraform import",
  ],
  authors: [{ name: "RepliMap" }],
  creator: "RepliMap",
  publisher: "RepliMap",

  // CRITICAL FIX: './' instead of '/'
  // './' = relative to current path, each page gets correct canonical
  // '/' = absolute path, all pages point to homepage (fatal SEO error!)
  alternates: {
    canonical: './',
  },

  icons: {
    icon: [{ url: "/favicon.ico" }],
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
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },

  category: 'Technology',
  applicationName: 'RepliMap',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = generateSiteSchema();

  return (
    <ClerkProviderWrapper>
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
    </ClerkProviderWrapper>
  );
}
