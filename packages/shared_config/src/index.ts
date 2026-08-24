// Exports this declaration for use by other modules.
export const productConfig = {
  // Defines the name field in the surrounding object or type.
  name: process.env.NEXT_PUBLIC_PRODUCT_NAME ?? 'Cipherboard',
  // Defines the minimumAge field in the surrounding object or type.
  minimumAge: 13,
  // Defines the apiOrigin field in the surrounding object or type.
  apiOrigin: process.env.NEXT_PUBLIC_API_ORIGIN ?? '',
  // Defines the productOrigin field in the surrounding object or type.
  productOrigin: process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? '',
  // Defines the supabaseUrl field in the surrounding object or type.
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  // Defines the supabasePublishableKey field in the surrounding object or type.
  supabasePublishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? '',
  // Defines the supportEmail field in the surrounding object or type.
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@example.invalid',
  // Defines the legalEntity field in the surrounding object or type.
  legalEntity: process.env.NEXT_PUBLIC_LEGAL_ENTITY ?? '',
  // Defines the jurisdiction field in the surrounding object or type.
  jurisdiction: process.env.NEXT_PUBLIC_JURISDICTION ?? '',
  // Defines the policyDate field in the surrounding object or type.
  policyDate: process.env.NEXT_PUBLIC_POLICY_DATE ?? '',
  // Executes this line as the next step in the surrounding logic.
} as const;

// Defines the isExactHttpsOrigin function and its callable behavior.
function isExactHttpsOrigin(value: string): boolean {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores parsed for subsequent operations.
    const parsed = new URL(value);
    // Returns this result to the caller and ends the current function.
    return (
      // Executes this line as the next step in the surrounding logic.
      parsed.protocol === 'https:' &&
      // Executes this line as the next step in the surrounding logic.
      !parsed.username &&
      // Executes this line as the next step in the surrounding logic.
      !parsed.password &&
      // Executes this line as the next step in the surrounding logic.
      parsed.pathname === '/' &&
      // Executes this line as the next step in the surrounding logic.
      !parsed.search &&
      // Executes this line as the next step in the surrounding logic.
      !parsed.hash &&
      // Executes this line as the next step in the surrounding logic.
      (value === parsed.origin || value === `${parsed.origin}/`)
      // Closes the expression, call, or declaration started above.
    );
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return false;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Defines the isPublicSupabaseKey function and its callable behavior.
function isPublicSupabaseKey(value: string): boolean {
  // Checks this condition before running the nested branch.
  if (value.startsWith('sb_secret_') || value.startsWith('sb_service_')) return false;
  // Checks this condition before running the nested branch.
  if (value.startsWith('sb_publishable_')) return value.length >= 24 && !/\s/.test(value);
  // Computes and stores segments for subsequent operations.
  const segments = value.split('.');
  // Checks this condition before running the nested branch.
  if (segments.length !== 3) return false;
  // Computes and stores encodedPayload for subsequent operations.
  const encodedPayload = segments[1];
  // Checks this condition before running the nested branch.
  if (!encodedPayload) return false;
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores payload for subsequent operations.
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8')) as {
      // Executes this line as the next step in the surrounding logic.
      role?: unknown;
      // Closes the expression, call, or declaration started above.
    };
    // Returns this result to the caller and ends the current function.
    return payload.role === 'anon' || payload.role === 'authenticated';
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return false;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Defines the isIsoDate function and its callable behavior.
function isIsoDate(value: string): boolean {
  // Checks this condition before running the nested branch.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  // Computes and stores parsed for subsequent operations.
  const parsed = new Date(`${value}T00:00:00Z`);
  // Returns this result to the caller and ends the current function.
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function assertLaunchConfiguration(): void {
  // Checks this condition before running the nested branch.
  if (process.env.NODE_ENV !== 'production') return;
  // Computes and stores missing for subsequent operations.
  const missing = Object.entries({
    // Defines the NEXT_PUBLIC_API_ORIGIN field in the surrounding object or type.
    NEXT_PUBLIC_API_ORIGIN: productConfig.apiOrigin,
    // Defines the NEXT_PUBLIC_PRODUCT_ORIGIN field in the surrounding object or type.
    NEXT_PUBLIC_PRODUCT_ORIGIN: productConfig.productOrigin,
    // Defines the NEXT_PUBLIC_SUPABASE_URL field in the surrounding object or type.
    NEXT_PUBLIC_SUPABASE_URL: productConfig.supabaseUrl,
    // Defines the NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY field in the surrounding object or type.
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: productConfig.supabasePublishableKey,
    // Defines the NEXT_PUBLIC_PRODUCT_NAME field in the surrounding object or type.
    NEXT_PUBLIC_PRODUCT_NAME: productConfig.name,
    // Defines the NEXT_PUBLIC_SUPPORT_EMAIL field in the surrounding object or type.
    NEXT_PUBLIC_SUPPORT_EMAIL: productConfig.supportEmail.toLowerCase().endsWith('.invalid')
      ? // Executes this line as the next step in the surrounding logic.
        ''
      : // Supplies this item to the surrounding call or collection.
        productConfig.supportEmail,
    // Defines the NEXT_PUBLIC_LEGAL_ENTITY field in the surrounding object or type.
    NEXT_PUBLIC_LEGAL_ENTITY: productConfig.legalEntity,
    // Defines the NEXT_PUBLIC_JURISDICTION field in the surrounding object or type.
    NEXT_PUBLIC_JURISDICTION: productConfig.jurisdiction,
    // Defines the NEXT_PUBLIC_POLICY_DATE field in the surrounding object or type.
    NEXT_PUBLIC_POLICY_DATE: productConfig.policyDate,
    // Closes the expression, call, or declaration started above.
  })
    // Executes this line as the next step in the surrounding logic.
    .filter(([, value]) => !value)
    // Executes this line as the next step in the surrounding logic.
    .map(([key]) => key);
  // Checks this condition before running the nested branch.
  if (missing.length > 0) {
    // Throws this error to report an invalid or failed operation.
    throw new Error(`Missing launch configuration: ${missing.join(', ')}`);
    // Closes the expression, call, or declaration started above.
  }

  // Computes and stores invalid for subsequent operations.
  const invalid = [
    // Executes this line as the next step in the surrounding logic.
    ...// Executes this line as the next step in the surrounding logic.
    (
      [
        // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_API_ORIGIN', productConfig.apiOrigin],
        // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_PRODUCT_ORIGIN', productConfig.productOrigin],
        // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_SUPABASE_URL', productConfig.supabaseUrl],
        // Executes this line as the next step in the surrounding logic.
      ] as const
    )
      // Closes the expression, call, or declaration started above.
      // Executes this line as the next step in the surrounding logic.
      .filter(([, value]) => !isExactHttpsOrigin(value))
      // Supplies this item to the surrounding call or collection.
      .map(([key]) => key),
    // Executes this line as the next step in the surrounding logic.
    ...(isPublicSupabaseKey(productConfig.supabasePublishableKey)
      ? // Executes this line as the next step in the surrounding logic.
        []
      : // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY']),
    // Supplies this item to the surrounding call or collection.
    ...(/^\S+@\S+\.\S+$/.test(productConfig.supportEmail) ? [] : ['NEXT_PUBLIC_SUPPORT_EMAIL']),
    // Supplies this item to the surrounding call or collection.
    ...(productConfig.name === productConfig.name.trim() ? [] : ['NEXT_PUBLIC_PRODUCT_NAME']),
    // Executes this line as the next step in the surrounding logic.
    ...(productConfig.legalEntity === productConfig.legalEntity.trim()
      ? // Executes this line as the next step in the surrounding logic.
        []
      : // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_LEGAL_ENTITY']),
    // Executes this line as the next step in the surrounding logic.
    ...(productConfig.jurisdiction === productConfig.jurisdiction.trim()
      ? // Executes this line as the next step in the surrounding logic.
        []
      : // Supplies this item to the surrounding call or collection.
        ['NEXT_PUBLIC_JURISDICTION']),
    // Supplies this item to the surrounding call or collection.
    ...(isIsoDate(productConfig.policyDate) ? [] : ['NEXT_PUBLIC_POLICY_DATE']),
    // Closes the expression, call, or declaration started above.
  ];
  // Checks this condition before running the nested branch.
  if (invalid.length > 0) {
    // Throws this error to report an invalid or failed operation.
    throw new Error(`Invalid launch configuration: ${invalid.join(', ')}`);
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}
