import type { Metadata, Viewport } from 'next';
import { Fraunces, Manrope } from 'next/font/google';
import { connection } from 'next/server';
import { headers } from 'next/headers';
import { SessionProvider } from '@/components/session-provider';
import { RouteAnnouncerTarget } from '@/components/route-announcer-target';
import { assertLaunchConfiguration } from '@mastermind/shared-config';
import './globals.css';

const display = Fraunces({ subsets: ['latin'], variable: '--font-display', display: 'swap' });
const body = Manrope({ subsets: ['latin'], variable: '--font-body', display: 'swap' });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000'),
  title: { default: 'Cipherboard — Think in patterns', template: '%s — Cipherboard' },
  description:
    'An accessible, competitive Mastermind game for solo play, daily puzzles, and private challenges.',
  applicationName: 'Cipherboard',
  manifest: '/manifest.webmanifest',
  icons: { icon: '/icon.svg', apple: '/icon-192.png' },
  openGraph: {
    title: 'Cipherboard',
    description: 'Think in patterns. Break the code.',
    type: 'website',
    images: [
      {
        url: '/social-preview.png',
        width: 1200,
        height: 630,
        alt: 'Cipherboard code-breaking board',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Cipherboard',
    description: 'Think in patterns. Break the code.',
    images: ['/social-preview.png'],
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#9a641d' },
    { media: '(prefers-color-scheme: dark)', color: '#17130f' },
  ],
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  await connection();
  const requestHeaders = await headers();
  const locale = requestHeaders.get('x-document-locale') === 'zh-Hant' ? 'zh-Hant' : 'en';
  if (process.env.VALIDATE_LAUNCH_CONFIGURATION === 'true') assertLaunchConfiguration();
  return (
    <html lang={locale} data-scroll-behavior="smooth" suppressHydrationWarning>
      <body className={`${display.variable} ${body.variable}`}>
        <RouteAnnouncerTarget />
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
