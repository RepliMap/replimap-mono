import { MetadataRoute } from 'next'
import fs from 'fs'
import path from 'path'

function getDocSlugs(): string[] {
  const docsDir = path.join(process.cwd(), 'content/docs')
  try {
    return fs
      .readdirSync(docsDir)
      .filter((file) => file.endsWith('.mdx'))
      .map((file) => file.replace('.mdx', ''))
      .filter((slug) => slug !== 'index')
  } catch {
    return []
  }
}

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://replimap.com'
  const now = new Date()

  // Core pages
  const coreRoutes: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${baseUrl}/docs`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
  ]

  // Dynamic documentation pages
  const docSlugs = getDocSlugs()
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
