import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared'

export const baseOptions: BaseLayoutProps = {
  nav: {
    title: "RepliMap Docs",
    transparentMode: "top",
    url: "/",
  },
  links: [
    {
      text: 'Home',
      url: '/',
    },
    {
      text: 'Pricing',
      url: '/#pricing',
    },
    {
      text: 'GitHub',
      url: 'https://github.com/RepliMap/replimap-community',
      external: true,
    },
  ],
}
