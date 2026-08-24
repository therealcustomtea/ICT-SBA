// Imports the dependency used by this module.
import createMiddleware from 'next-intl/middleware';
// Imports the dependency used by this module.
import { NextRequest, NextResponse } from 'next/server';
// Imports the dependency used by this module.
import { routing } from './i18n/routing';

// Computes and stores intlMiddleware for subsequent operations.
const intlMiddleware = createMiddleware(routing);
// Computes and stores privatePath for subsequent operations.
const privatePath =
  // Executes this line as the next step in the surrounding logic.
  /^\/(?:en|zh-Hant)\/(?:account|achievements|admin|auth|challenges(?:\/|$)|profile(?:\/|$)|rooms(?:\/|$)|settings(?:\/|$)|play\/[^/]+(?:\/|$))/;

// Defines the origin function and its callable behavior.
function origin(value: string | undefined): string | null {
  // Checks this condition before running the nested branch.
  if (!value) return null;
  // Starts an operation whose expected failures are handled below.
  try {
    // Returns this result to the caller and ends the current function.
    return new URL(value).origin;
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return null;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration as the module default.
export default function proxy(request: NextRequest) {
  // Computes and stores nonce for subsequent operations.
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  // Computes and stores isDevelopment for subsequent operations.
  const isDevelopment = process.env.NODE_ENV === 'development';
  // Computes and stores apiOrigin for subsequent operations.
  const apiOrigin = origin(process.env.NEXT_PUBLIC_API_ORIGIN);
  // Computes and stores supabaseOrigin for subsequent operations.
  const supabaseOrigin = origin(process.env.NEXT_PUBLIC_SUPABASE_URL);
  // Computes and stores productOrigin for subsequent operations.
  const productOrigin = origin(process.env.NEXT_PUBLIC_PRODUCT_ORIGIN);
  // Computes and stores socketOrigin for subsequent operations.
  const socketOrigin = apiOrigin?.replace(/^http/, 'ws') ?? null;
  // Computes and stores connectSources for subsequent operations.
  const connectSources = ["'self'", apiOrigin, socketOrigin, supabaseOrigin]
    // Executes this line as the next step in the surrounding logic.
    .filter(Boolean)
    // Executes this line as the next step in the surrounding logic.
    .join(' ');
  // Computes and stores cspDirectives for subsequent operations.
  const cspDirectives = [
    // Supplies this item to the surrounding call or collection.
    "default-src 'self'",
    // Supplies this item to the surrounding call or collection.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDevelopment ? " 'unsafe-eval'" : ''}`,
    // Supplies this item to the surrounding call or collection.
    `style-src 'self' ${isDevelopment ? "'unsafe-inline'" : `'nonce-${nonce}'`}`,
    // Supplies this item to the surrounding call or collection.
    "img-src 'self' blob: data:",
    // Supplies this item to the surrounding call or collection.
    "font-src 'self'",
    // Supplies this item to the surrounding call or collection.
    `connect-src ${connectSources}`,
    // Supplies this item to the surrounding call or collection.
    "worker-src 'self' blob:",
    // Supplies this item to the surrounding call or collection.
    "manifest-src 'self'",
    // Supplies this item to the surrounding call or collection.
    "object-src 'none'",
    // Supplies this item to the surrounding call or collection.
    "base-uri 'self'",
    // Supplies this item to the surrounding call or collection.
    "form-action 'self'",
    // Supplies this item to the surrounding call or collection.
    "frame-ancestors 'none'",
    // Closes the expression, call, or declaration started above.
  ];
  // Checks this condition before running the nested branch.
  if (!isDevelopment && productOrigin?.startsWith('https://'))
    // Calls cspDirectives.push with the supplied values.
    cspDirectives.push('upgrade-insecure-requests');
  // Computes and stores csp for subsequent operations.
  const csp = cspDirectives.join('; ');
  // Computes and stores requestHeaders for subsequent operations.
  const requestHeaders = new Headers(request.headers);
  // Computes and stores locale for subsequent operations.
  const locale = request.nextUrl.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
  // Calls requestHeaders.set with the supplied values.
  requestHeaders.set('x-document-locale', locale);
  // Calls requestHeaders.set with the supplied values.
  requestHeaders.set('x-nonce', nonce);
  // Calls requestHeaders.set with the supplied values.
  requestHeaders.set('Content-Security-Policy', csp);
  // Computes and stores nextRequest for subsequent operations.
  const nextRequest = new NextRequest(request, { headers: requestHeaders });
  // Computes and stores response for subsequent operations.
  const response = request.nextUrl.pathname.startsWith('/auth/callback')
    ? // Executes this line as the next step in the surrounding logic.
      NextResponse.next({ request: { headers: requestHeaders } })
    : // Executes this line as the next step in the surrounding logic.
      intlMiddleware(nextRequest);
  // Calls response.headers.set with the supplied values.
  response.headers.set('Content-Security-Policy', csp);
  // Checks this condition before running the nested branch.
  if (privatePath.test(request.nextUrl.pathname))
    // Calls response.headers.set with the supplied values.
    response.headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
  // Returns this result to the caller and ends the current function.
  return response;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export const config = {
  // Defines the matcher field in the surrounding object or type.
  matcher: [
    // Begins the nested block or object completed below.
    {
      // Keep Next's internal HTTP and WebSocket routes out of locale handling.
      // Defines the source field in the surrounding object or type.
      source: '/((?!api|_next|favicon.ico|.*\\..*).*)',
      // Defines the missing field in the surrounding object or type.
      missing: [
        // Supplies this item to the surrounding call or collection.
        { type: 'header', key: 'next-router-prefetch' },
        // Supplies this item to the surrounding call or collection.
        { type: 'header', key: 'purpose', value: 'prefetch' },
        // Closes the expression, call, or declaration started above.
      ],
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  ],
  // Closes the expression, call, or declaration started above.
};
