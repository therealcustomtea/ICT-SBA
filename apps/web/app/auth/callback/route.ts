import type { EmailOtpType } from '@supabase/supabase-js';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse, type NextRequest } from 'next/server';

const allowedNext = /^\/(?:en|zh-Hant)(?:\/[A-Za-z0-9_\-/]*)?$/;

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const tokenHash = url.searchParams.get('token_hash');
  const type = url.searchParams.get('type') as EmailOtpType | null;
  const requestedNext = url.searchParams.get('next') ?? '/en/profile';
  const next = allowedNext.test(requestedNext) ? requestedNext : '/en/profile';
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !publishableKey)
    return NextResponse.redirect(new URL('/en/auth?error=configuration', request.url));

  const cookieStore = await cookies();
  const supabase = createServerClient(supabaseUrl, publishableKey, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: (values) =>
        values.forEach(({ name, value, options }) => cookieStore.set(name, value, options)),
    },
  });

  const result = code
    ? await supabase.auth.exchangeCodeForSession(code)
    : tokenHash && type
      ? await supabase.auth.verifyOtp({ token_hash: tokenHash, type })
      : { error: new Error('Missing authentication callback token.') };

  if (result.error) {
    const locale = next.startsWith('/zh-Hant') ? 'zh-Hant' : 'en';
    return NextResponse.redirect(new URL(`/${locale}/auth?error=invalid_callback`, request.url));
  }
  return NextResponse.redirect(new URL(next, request.url));
}
