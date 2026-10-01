// Type declarations for fumadocs-mdx generated .source module
// This file provides types for the auto-generated .source folder

declare module '@/.source' {
  import type { PageData, MetaData } from 'fumadocs-core/source'
  import type { MDXContent } from 'mdx/types'
  import type { TableOfContents } from 'fumadocs-core/toc'
  import type { Root } from 'mdast'

  interface FileInfo {
    path: string
    fullPath: string
  }

  interface DocMethods {
    info: FileInfo
    getText(type?: 'raw' | 'processed'): Promise<string>
    getMDAST(): Promise<Root>
  }

  interface DocEntry extends DocMethods, PageData {
    title: string
    description?: string
    body: MDXContent
    toc: TableOfContents
    full?: boolean
  }

  interface MetaMethods {
    info: FileInfo
  }

  interface MetaEntry extends MetaMethods, MetaData {
    title?: string
    pages?: string[]
    icon?: string
  }

  export const docs: DocEntry[]
  export const meta: MetaEntry[]
}
