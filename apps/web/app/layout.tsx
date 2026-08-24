// Imports the dependency used by this module.
import type { Metadata, Viewport } from 'next';
// Imports the dependency used by this module.
import { Fraunces, Manrope } from 'next/font/google';
// Imports the dependency used by this module.
import { connection } from 'next/server';
// Imports the dependency used by this module.
import { headers } from 'next/headers';
// Imports the dependency used by this module.
import { SessionProvider } from '@/components/session-provider';
// Imports the dependency used by this module.
import { RouteAnnouncerTarget } from '@/components/route-announcer-target';
// Imports the dependency used by this module.
import { assertLaunchConfiguration } from '@mastermind/shared-config';
// Imports the dependency used by this module.
import './globals.css';

// Computes and stores display for subsequent operations.
const display = Fraunces({ subsets: ['latin'], variable: '--font-display', display: 'swap' });
// Computes and stores body for subsequent operations.
const body = Manrope({ subsets: ['latin'], variable: '--font-body', display: 'swap' });

// Exports this declaration for use by other modules.
export const metadata: Metadata = {
  // Defines the metadataBase field in the surrounding object or type.
  metadataBase: new URL(process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000'),
  // Defines the title field in the surrounding object or type.
  title: { default: 'Cipherboard — Think in patterns', template: '%s — Cipherboard' },
  // Defines the description field in the surrounding object or type.
  description:
    // Supplies this item to the surrounding call or collection.
    'An accessible, competitive Mastermind game for solo play, daily puzzles, and private challenges.',
  // Defines the applicationName field in the surrounding object or type.
  applicationName: 'Cipherboard',
  // Defines the manifest field in the surrounding object or type.
  manifest: '/manifest.webmanifest',
  // Defines the icons field in the surrounding object or type.
  icons: { icon: '/icon.svg', apple: '/icon-192.png' },
  // Defines the openGraph field in the surrounding object or type.
  openGraph: {
    // Defines the title field in the surrounding object or type.
    title: 'Cipherboard',
    // Defines the description field in the surrounding object or type.
    description: 'Think in patterns. Break the code.',
    // Defines the type field in the surrounding object or type.
    type: 'website',
    // Defines the images field in the surrounding object or type.
    images: [
      // Begins the nested block or object completed below.
      {
        // Defines the url field in the surrounding object or type.
        url: '/social-preview.png',
        // Defines the width field in the surrounding object or type.
        width: 1200,
        // Defines the height field in the surrounding object or type.
        height: 630,
        // Defines the alt field in the surrounding object or type.
        alt: 'Cipherboard code-breaking board',
        // Closes the expression, call, or declaration started above.
      },
      // Closes the expression, call, or declaration started above.
    ],
    // Closes the expression, call, or declaration started above.
  },
  // Defines the twitter field in the surrounding object or type.
  twitter: {
    // Defines the card field in the surrounding object or type.
    card: 'summary_large_image',
    // Defines the title field in the surrounding object or type.
    title: 'Cipherboard',
    // Defines the description field in the surrounding object or type.
    description: 'Think in patterns. Break the code.',
    // Defines the images field in the surrounding object or type.
    images: ['/social-preview.png'],
    // Closes the expression, call, or declaration started above.
  },
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export const viewport: Viewport = {
  // Defines the width field in the surrounding object or type.
  width: 'device-width',
  // Defines the initialScale field in the surrounding object or type.
  initialScale: 1,
  // Defines the themeColor field in the surrounding object or type.
  themeColor: [
    // Supplies this item to the surrounding call or collection.
    { media: '(prefers-color-scheme: light)', color: '#9a641d' },
    // Supplies this item to the surrounding call or collection.
    { media: '(prefers-color-scheme: dark)', color: '#17130f' },
    // Closes the expression, call, or declaration started above.
  ],
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration as the module default.
export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Waits for this asynchronous operation to complete.
  await connection();
  // Computes and stores requestHeaders for subsequent operations.
  const requestHeaders = await headers();
  // Computes and stores locale for subsequent operations.
  const locale = requestHeaders.get('x-document-locale') === 'zh-Hant' ? 'zh-Hant' : 'en';
  // Checks this condition before running the nested branch.
  if (process.env.VALIDATE_LAUNCH_CONFIGURATION === 'true') assertLaunchConfiguration();
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the html interface element or component.
    <html lang={locale} data-scroll-behavior="smooth" suppressHydrationWarning>
      {/* Renders the body interface element or component. */}
      <body className={`${display.variable} ${body.variable}`}>
        {/* Renders the RouteAnnouncerTarget interface element or component. */}
        <RouteAnnouncerTarget />
        {/* Renders the SessionProvider interface element or component. */}
        <SessionProvider>{children}</SessionProvider>
        {/* Closes the body interface element. */}
      </body>
      {/* Closes the html interface element. */}
    </html>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
