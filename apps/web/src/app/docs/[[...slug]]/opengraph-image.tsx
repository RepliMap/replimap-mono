import { ImageResponse } from 'next/og'
import { source } from '@/lib/source'

export const runtime = 'edge'
export const alt = 'RepliMap Documentation'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

interface PageData {
  title?: string
  description?: string
}

export default async function Image({ params }: { params: Promise<{ slug?: string[] }> }) {
  const resolvedParams = await params
  const page = source.getPage(resolvedParams.slug)
  const data = page?.data as PageData | undefined
  const title = data?.title || 'Documentation'
  const description = data?.description || 'AWS Infrastructure Intelligence'

  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          justifyContent: 'center',
          backgroundColor: '#030712',
          backgroundImage: 'linear-gradient(to bottom right, #030712, #0a1628)',
          padding: '60px 80px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '40px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              backgroundColor: '#10b981',
              borderRadius: '8px',
              marginRight: '16px',
            }}
          />
          <span style={{ fontSize: '28px', fontWeight: 600, color: '#94a3b8' }}>
            RepliMap Docs
          </span>
        </div>
        <div
          style={{
            fontSize: '64px',
            fontWeight: 700,
            color: '#f1f5f9',
            lineHeight: 1.2,
            marginBottom: '20px',
            maxWidth: '900px',
          }}
        >
          {title}
        </div>
        <div style={{ fontSize: '28px', color: '#94a3b8', maxWidth: '800px', lineHeight: 1.4 }}>
          {description}
        </div>
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '6px',
            background: 'linear-gradient(to right, #10b981, #06b6d4)',
          }}
        />
      </div>
    ),
    { ...size }
  )
}
