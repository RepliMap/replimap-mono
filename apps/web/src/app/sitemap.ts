import { MetadataRoute } from 'next'
import { source } from '@/lib/source'

// Required for `output: 'export'` — Next 16 needs this explicit even though
// this route has no dynamic behavior to begin with.
export const dynamic = 'force-static'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://www.replimap.com'
  const now = new Date() // build time (static export)

  // Core pages
  const coreRoutes: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${baseUrl}/docs`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${baseUrl}/demo`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${baseUrl}/pricing`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${baseUrl}/security`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
  ]

  // Documentation pages
  // Generated from the fumadocs source; /docs itself is listed in core routes.
  const docRoutes: MetadataRoute.Sitemap = source
    .getPages()
    .filter((page) => page.url !== '/docs')
    .map((page) => ({
      url: `${baseUrl}${page.url}`,
      lastModified: now,
      changeFrequency: 'monthly' as const,
      priority: page.url === '/docs/quick-start' ? 0.9 : 0.7,
    }))

  // Legal pages
  const legalRoutes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}/privacy`,
      lastModified: new Date('2026-11-16'),
      changeFrequency: 'yearly',
      priority: 0.3,
    },
    {
      url: `${baseUrl}/terms`,
      lastModified: new Date('2026-01-01'),
      changeFrequency: 'yearly',
      priority: 0.3,
    },
  ]

  return [...coreRoutes, ...docRoutes, ...legalRoutes]
}
