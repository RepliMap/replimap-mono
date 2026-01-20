import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://replimap.com'
  const now = new Date()

  // Core marketing pages
  const coreRoutes = ['', '/docs']

  // Documentation pages (matches content/docs/*.mdx)
  const docRoutes = [
    '/docs/quick-start',
    '/docs/installation',
    '/docs/cli-reference',
    '/docs/iam-policy',
    '/docs/security',
    '/docs/changelog',
    '/docs/contributing',
  ]

  // Legal pages (privacy/page.tsx and terms/page.tsx exist)
  const legalRoutes = ['/privacy', '/terms']

  return [
    ...coreRoutes.map((route) => ({
      url: `${baseUrl}${route}`,
      lastModified: now,
      changeFrequency: 'weekly' as const,
      priority: route === '' ? 1.0 : 0.9,
    })),
    ...docRoutes.map((route) => ({
      url: `${baseUrl}${route}`,
      lastModified: now,
      changeFrequency: 'monthly' as const,
      priority: route.includes('quick-start') ? 0.9 : 0.7,
    })),
    ...legalRoutes.map((route) => ({
      url: `${baseUrl}${route}`,
      lastModified: new Date('2026-01-01'),
      changeFrequency: 'yearly' as const,
      priority: 0.3,
    })),
  ]
}
