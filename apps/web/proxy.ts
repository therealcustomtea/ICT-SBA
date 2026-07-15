import createMiddleware from 'next-intl/middleware';
import { NextRequest, NextResponse } from 'next/server';
import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);
const privatePath =
  /^\/(?:en|zh-Hant)\/(?:account|achievements|admin|auth|challenges(?:\/|$)|profile(?:\/|$)|rooms(?:\/|$)|settings(?:\/|$)|play\/[^/]+(?:\/|$))/;

function origin(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

export default function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const isDevelopment = process.env.NODE_ENV === 'development';
  const apiOrigin = origin(process.env.NEXT_PUBLIC_API_ORIGIN);
  const supabaseOrigin = origin(process.env.NEXT_PUBLIC_SUPABASE_URL);
  const productOrigin = origin(process.env.NEXT_PUBLIC_PRODUCT_ORIGIN);
  const socketOrigin = apiOrigin?.replace(/^http/, 'ws') ?? null;
  const connectSources = ["'self'", apiOrigin, socketOrigin, supabaseOrigin]
    .filter(Boolean)
    .join(' ');
  const cspDirectives = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDevelopment ? " 'unsafe-eval'" : ''}`,
    `style-src 'self' ${isDevelopment ? "'unsafe-inline'" : `'nonce-${nonce}'`}`,
    "img-src 'self' blob: data:",
    "font-src 'self'",
    `connect-src ${connectSources}`,
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];
  if (!isDevelopment && productOrigin?.startsWith('https://'))
    cspDirectives.push('upgrade-insecure-requests');
  const csp = cspDirectives.join('; ');
  const requestHeaders = new Headers(request.headers);
  const locale = request.nextUrl.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
  requestHeaders.set('x-document-locale', locale);
  requestHeaders.set('x-nonce', nonce);
  requestHeaders.set('Content-Security-Policy', csp);
  const nextRequest = new NextRequest(request, { headers: requestHeaders });
  const response = request.nextUrl.pathname.startsWith('/auth/callback')
    ? NextResponse.next({ request: { headers: requestHeaders } })
    : intlMiddleware(nextRequest);
  response.headers.set('Content-Security-Policy', csp);
  if (privatePath.test(request.nextUrl.pathname))
    response.headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
  return response;
}

export const config = {
  matcher: [
    {
      source: '/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
};
