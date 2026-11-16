import { PLANS, type PlanName } from './pricing'

/**
 * Generate JSON-LD structured data for SEO
 * Single Source of Truth: prices from PLANS config
 */
export function generateSiteSchema() {
  const displayPlans: PlanName[] = ['community', 'pro', 'team', 'sovereign']

  const offers = displayPlans.map((planKey) => {
    const plan = PLANS[planKey]
    return {
      '@type': 'Offer',
      name: plan.name,
      price: String(plan.price.monthly),
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      description: plan.tagline,
    }
  })

  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'SoftwareApplication',
        '@id': 'https://www.replimap.com/#software',
        name: 'RepliMap',
        applicationCategory: 'DeveloperApplication',
        applicationSubCategory: 'Infrastructure as Code Tool',
        operatingSystem: 'Linux, macOS, Windows',
        description:
          'AWS Infrastructure Intelligence Engine - scan brownfield AWS accounts, map dependencies, and generate Terraform with import blocks (free for one VPC; the whole account on Pro). 100% local.',
        url: 'https://www.replimap.com',
        downloadUrl: 'https://www.replimap.com/docs/installation',
        releaseNotes: 'https://www.replimap.com/docs/changelog',
        screenshot: 'https://www.replimap.com/og-image.png',
        featureList: [
          'Reverse-engineer AWS to Terraform',
          'IaC coverage — find resources in no Terraform state',
          'Least-privilege IAM policy generation',
          'Multi-region scanning',
          'Air-gapped activation by signed license file (Sovereign)',
        ],
        offers,
        author: { '@id': 'https://www.replimap.com/#organization' },
      },
      {
        '@type': 'Organization',
        '@id': 'https://www.replimap.com/#organization',
        name: 'RepliMap',
        url: 'https://www.replimap.com',
        logo: { '@type': 'ImageObject', url: 'https://www.replimap.com/og-image.png' },
        sameAs: ['https://github.com/RepliMap/replimap-community'],
        contactPoint: {
          '@type': 'ContactPoint',
          email: 'hello@replimap.com',
          contactType: 'customer support',
        },
      },
      {
        '@type': 'WebSite',
        '@id': 'https://www.replimap.com/#website',
        url: 'https://www.replimap.com',
        name: 'RepliMap',
        description: 'AWS Infrastructure Intelligence',
        publisher: { '@id': 'https://www.replimap.com/#organization' },
      },
    ],
  }
}
