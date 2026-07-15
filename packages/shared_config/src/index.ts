export const productConfig = {
  name: process.env.NEXT_PUBLIC_PRODUCT_NAME ?? 'Cipherboard',
  minimumAge: 13,
  apiOrigin: process.env.NEXT_PUBLIC_API_ORIGIN ?? '',
  productOrigin: process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? '',
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  supabasePublishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? '',
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@example.invalid',
  legalEntity: process.env.NEXT_PUBLIC_LEGAL_ENTITY ?? '',
  jurisdiction: process.env.NEXT_PUBLIC_JURISDICTION ?? '',
  policyDate: process.env.NEXT_PUBLIC_POLICY_DATE ?? '',
} as const;

function isExactHttpsOrigin(value: string): boolean {
  try {
    const parsed = new URL(value);
    return (
      parsed.protocol === 'https:' &&
      !parsed.username &&
      !parsed.password &&
      parsed.pathname === '/' &&
      !parsed.search &&
      !parsed.hash &&
      (value === parsed.origin || value === `${parsed.origin}/`)
    );
  } catch {
    return false;
  }
}

function isPublicSupabaseKey(value: string): boolean {
  if (value.startsWith('sb_secret_') || value.startsWith('sb_service_')) return false;
  if (value.startsWith('sb_publishable_')) return value.length >= 24 && !/\s/.test(value);
  const segments = value.split('.');
  if (segments.length !== 3) return false;
  const encodedPayload = segments[1];
  if (!encodedPayload) return false;
  try {
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8')) as {
      role?: unknown;
    };
    return payload.role === 'anon' || payload.role === 'authenticated';
  } catch {
    return false;
  }
}

function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
}

export function assertLaunchConfiguration(): void {
  if (process.env.NODE_ENV !== 'production') return;
  const missing = Object.entries({
    NEXT_PUBLIC_API_ORIGIN: productConfig.apiOrigin,
    NEXT_PUBLIC_PRODUCT_ORIGIN: productConfig.productOrigin,
    NEXT_PUBLIC_SUPABASE_URL: productConfig.supabaseUrl,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: productConfig.supabasePublishableKey,
    NEXT_PUBLIC_PRODUCT_NAME: productConfig.name,
    NEXT_PUBLIC_SUPPORT_EMAIL: productConfig.supportEmail.toLowerCase().endsWith('.invalid')
      ? ''
      : productConfig.supportEmail,
    NEXT_PUBLIC_LEGAL_ENTITY: productConfig.legalEntity,
    NEXT_PUBLIC_JURISDICTION: productConfig.jurisdiction,
    NEXT_PUBLIC_POLICY_DATE: productConfig.policyDate,
  })
    .filter(([, value]) => !value)
    .map(([key]) => key);
  if (missing.length > 0) {
    throw new Error(`Missing launch configuration: ${missing.join(', ')}`);
  }

  const invalid = [
    ...(
      [
        ['NEXT_PUBLIC_API_ORIGIN', productConfig.apiOrigin],
        ['NEXT_PUBLIC_PRODUCT_ORIGIN', productConfig.productOrigin],
        ['NEXT_PUBLIC_SUPABASE_URL', productConfig.supabaseUrl],
      ] as const
    )
      .filter(([, value]) => !isExactHttpsOrigin(value))
      .map(([key]) => key),
    ...(isPublicSupabaseKey(productConfig.supabasePublishableKey)
      ? []
      : ['NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY']),
    ...(/^\S+@\S+\.\S+$/.test(productConfig.supportEmail) ? [] : ['NEXT_PUBLIC_SUPPORT_EMAIL']),
    ...(productConfig.name === productConfig.name.trim() ? [] : ['NEXT_PUBLIC_PRODUCT_NAME']),
    ...(productConfig.legalEntity === productConfig.legalEntity.trim()
      ? []
      : ['NEXT_PUBLIC_LEGAL_ENTITY']),
    ...(productConfig.jurisdiction === productConfig.jurisdiction.trim()
      ? []
      : ['NEXT_PUBLIC_JURISDICTION']),
    ...(isIsoDate(productConfig.policyDate) ? [] : ['NEXT_PUBLIC_POLICY_DATE']),
  ];
  if (invalid.length > 0) {
    throw new Error(`Invalid launch configuration: ${invalid.join(', ')}`);
  }
}
