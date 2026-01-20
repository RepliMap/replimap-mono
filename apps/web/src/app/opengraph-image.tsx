import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'RepliMap - AWS Infrastructure Intelligence'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#030712',
          backgroundImage: 'linear-gradient(to bottom right, #030712, #0a1628)',
        }}
      >
        <div
          style={{
            width: '120px',
            height: '120px',
            backgroundColor: '#10b981',
            borderRadius: '24px',
            marginBottom: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span style={{ fontSize: '60px', color: 'white', fontWeight: 700 }}>R</span>
        </div>
        <div style={{ fontSize: '72px', fontWeight: 700, color: '#f1f5f9', marginBottom: '20px' }}>
          RepliMap
        </div>
        <div style={{ fontSize: '32px', color: '#10b981', marginBottom: '16px' }}>
          AWS Infrastructure Intelligence
        </div>
        <div
          style={{ fontSize: '24px', color: '#94a3b8', textAlign: 'center', maxWidth: '800px' }}
        >
          Reverse-engineer AWS into Terraform • Detect Drift • Generate IAM Policies
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
