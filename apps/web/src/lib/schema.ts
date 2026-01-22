import { PLANS, type PlanName } from './pricing'

/**
 * Generate JSON-LD structured data for SEO
 * Single Source of Truth: prices from PLANS config
 */
export function generateSiteSchema() {
  const displayPlans: PlanName[] = ['community', 'pro', 'team']

  const offers = displayPlans.map((planKey) => {
    const plan = PLANS[planKey]
    return {
      '@type': 'Offer',
      name: plan.name,
      price: String(plan.price.monthly),
      priceCurrency: 'USD',
      description: plan.tagline,
    }
  })

  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'SoftwareApplication',
        '@id': 'https://replimap.com/#software',
        name: 'RepliMap',
        applicationCategory: 'DeveloperApplication',
        applicationSubCategory: 'Infrastructure as Code Tool',
        operatingSystem: 'Linux, macOS, Windows',
        description:
          'AWS Infrastructure Intelligence Engine - Reverse-engineer infrastructure into Terraform, detect drift, generate IAM policies',
        url: 'https://replimap.com',
        downloadUrl: 'https://replimap.com/docs/installation',
        softwareVersion: '1.0.0',
        releaseNotes: 'https://replimap.com/docs/changelog',
        screenshot: 'https://replimap.com/og-image.png',
        featureList: [
          'Reverse-engineer AWS to Terraform',
          'Infrastructure drift detection',
          'Least-privilege IAM policy generation',
          'Multi-region scanning',
          'Offline/air-gapped support',
        ],
        offers,
        author: { '@id': 'https://replimap.com/#organization' },
      },
      {
        '@type': 'Organization',
        '@id': 'https://replimap.com/#organization',
        name: 'RepliMap',
        url: 'https://replimap.com',
        logo: { '@type': 'ImageObject', url: 'https://replimap.com/og-image.png' },
        sameAs: ['https://github.com/RepliMap/replimap-community'],
        contactPoint: {
          '@type': 'ContactPoint',
          email: 'hello@replimap.com',
          contactType: 'customer support',
        },
      },
      {
        '@type': 'WebSite',
        '@id': 'https://replimap.com/#website',
        url: 'https://replimap.com',
        name: 'RepliMap',
        description: 'AWS Infrastructure Intelligence',
        publisher: { '@id': 'https://replimap.com/#organization' },
      },
    ],
  }
}
