// Imports the dependency used by this module.
import type { EmailOtpType } from '@supabase/supabase-js';
// Imports the dependency used by this module.
import { createServerClient } from '@supabase/ssr';
// Imports the dependency used by this module.
import { cookies } from 'next/headers';
// Imports the dependency used by this module.
import { NextResponse, type NextRequest } from 'next/server';

// Computes and stores allowedNext for subsequent operations.
const allowedNext = /^\/(?:en|zh-Hant)(?:\/[A-Za-z0-9_\-/]*)?$/;

// Exports this declaration for use by other modules.
export async function GET(request: NextRequest) {
  // Computes and stores url for subsequent operations.
  const url = new URL(request.url);
  // Computes and stores code for subsequent operations.
  const code = url.searchParams.get('code');
  // Computes and stores tokenHash for subsequent operations.
  const tokenHash = url.searchParams.get('token_hash');
  // Computes and stores type for subsequent operations.
  const type = url.searchParams.get('type') as EmailOtpType | null;
  // Computes and stores requestedNext for subsequent operations.
  const requestedNext = url.searchParams.get('next') ?? '/en/profile';
  // Computes and stores next for subsequent operations.
  const next = allowedNext.test(requestedNext) ? requestedNext : '/en/profile';
  // Computes and stores supabaseUrl for subsequent operations.
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  // Computes and stores publishableKey for subsequent operations.
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  // Checks this condition before running the nested branch.
  if (!supabaseUrl || !publishableKey)
    // Returns this result to the caller and ends the current function.
    return NextResponse.redirect(new URL('/en/auth?error=configuration', request.url));

  // Computes and stores cookieStore for subsequent operations.
  const cookieStore = await cookies();
  // Computes and stores supabase for subsequent operations.
  const supabase = createServerClient(supabaseUrl, publishableKey, {
    // Defines the cookies field in the surrounding object or type.
    cookies: {
      // Defines the getAll field in the surrounding object or type.
      getAll: () => cookieStore.getAll(),
      // Defines the setAll field in the surrounding object or type.
      setAll: (values) =>
        // Calls values.forEach with the supplied values.
        values.forEach(({ name, value, options }) => cookieStore.set(name, value, options)),
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  });

  // Computes and stores result for subsequent operations.
  const result = code
    ? // Executes this line as the next step in the surrounding logic.
      await supabase.auth.exchangeCodeForSession(code)
    : // Executes this line as the next step in the surrounding logic.
      tokenHash && type
      ? // Executes this line as the next step in the surrounding logic.
        await supabase.auth.verifyOtp({ token_hash: tokenHash, type })
      : // Executes this line as the next step in the surrounding logic.
        { error: new Error('Missing authentication callback token.') };

  // Checks this condition before running the nested branch.
  if (result.error) {
    // Computes and stores locale for subsequent operations.
    const locale = next.startsWith('/zh-Hant') ? 'zh-Hant' : 'en';
    // Returns this result to the caller and ends the current function.
    return NextResponse.redirect(new URL(`/${locale}/auth?error=invalid_callback`, request.url));
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return NextResponse.redirect(new URL(next, request.url));
  // Closes the expression, call, or declaration started above.
}
