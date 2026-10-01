import { DocsLayout } from 'fumadocs-ui/layouts/docs'
import { RootProvider } from 'fumadocs-ui/provider/next'
import type { ReactNode } from 'react'
import { baseOptions } from '@/app/layout.config'
import { source } from '@/lib/source'

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <RootProvider
      theme={{
        enabled: false, // Disable Fumadocs theme management, use root ThemeProvider
      }}
    >
      <DocsLayout
        tree={source.pageTree}
        {...baseOptions}
        themeSwitch={{ enabled: false }} // Hide theme switch button
      >
        {children}
      </DocsLayout>
    </RootProvider>
  )
}
