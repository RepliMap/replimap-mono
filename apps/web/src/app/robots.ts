import { MetadataRoute } from 'next'

// Required for `output: 'export'` — Next 16 needs this explicit even though
// this route has no dynamic behavior to begin with.
export const dynamic = 'force-static'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = 'https://www.replimap.com'

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/', '/_next/'],
      },
      // Explicitly welcome AI crawlers
      {
        userAgent: 'GPTBot',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/'],
      },
      {
        userAgent: 'PerplexityBot',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/'],
      },
      {
        userAgent: 'ClaudeBot',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/'],
      },
      {
        userAgent: 'Google-Extended',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/'],
      },
      {
        userAgent: 'Amazonbot',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/sign-in/', '/sign-up/'],
      },
      // Block low-value crawlers
      { userAgent: 'CCBot', disallow: '/' },
      { userAgent: 'AhrefsBot', disallow: '/' },
      { userAgent: 'SemrushBot', disallow: '/' },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  }
}
