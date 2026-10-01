import { MetadataRoute } from 'next'

// Required for `output: 'export'` — Next 16 needs this explicit even though
// this route has no dynamic behavior to begin with.
export const dynamic = 'force-static'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://www.replimap.com'
  const now = new Date()

  // Static list - more reliable than fs.readdirSync in Vercel monorepo
  // Update this when adding new docs (matches content/docs/*.mdx)
  const docSlugs = [
    'quick-start',
    'installation',
    'cli-reference',
    'iam-policy',
    'security',
    'changelog',
    'contributing',
  ]

  // Core pages
  const coreRoutes: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${baseUrl}/docs`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${baseUrl}/demo`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${baseUrl}/security`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
  ]

  // Documentation pages
  const docRoutes: MetadataRoute.Sitemap = docSlugs.map((slug) => ({
    url: `${baseUrl}/docs/${slug}`,
    lastModified: now,
    changeFrequency: 'monthly' as const,
    priority: slug === 'quick-start' ? 0.9 : 0.7,
  }))

  // Legal pages
  const legalRoutes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}/privacy`,
      lastModified: new Date('2026-01-01'),
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
