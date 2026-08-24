// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';

// Computes and stores launchKeys for subsequent operations.
const launchKeys = [
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_API_ORIGIN',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_PRODUCT_ORIGIN',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_SUPABASE_URL',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_PRODUCT_NAME',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_SUPPORT_EMAIL',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_LEGAL_ENTITY',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_JURISDICTION',
  // Supplies this item to the surrounding call or collection.
  'NEXT_PUBLIC_POLICY_DATE',
  // Executes this line as the next step in the surrounding logic.
] as const;

// Computes and stores validLaunchConfiguration for subsequent operations.
const validLaunchConfiguration = {
  // Defines the NEXT_PUBLIC_API_ORIGIN field in the surrounding object or type.
  NEXT_PUBLIC_API_ORIGIN: 'https://api.example.com',
  // Defines the NEXT_PUBLIC_PRODUCT_ORIGIN field in the surrounding object or type.
  NEXT_PUBLIC_PRODUCT_ORIGIN: 'https://play.example.com',
  // Defines the NEXT_PUBLIC_SUPABASE_URL field in the surrounding object or type.
  NEXT_PUBLIC_SUPABASE_URL: 'https://project.supabase.co',
  // Defines the NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY field in the surrounding object or type.
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_test_fixture_only',
  // Defines the NEXT_PUBLIC_PRODUCT_NAME field in the surrounding object or type.
  NEXT_PUBLIC_PRODUCT_NAME: 'Cipherboard',
  // Defines the NEXT_PUBLIC_SUPPORT_EMAIL field in the surrounding object or type.
  NEXT_PUBLIC_SUPPORT_EMAIL: 'support@example.com',
  // Defines the NEXT_PUBLIC_LEGAL_ENTITY field in the surrounding object or type.
  NEXT_PUBLIC_LEGAL_ENTITY: 'Test Entity',
  // Defines the NEXT_PUBLIC_JURISDICTION field in the surrounding object or type.
  NEXT_PUBLIC_JURISDICTION: 'Test Jurisdiction',
  // Defines the NEXT_PUBLIC_POLICY_DATE field in the surrounding object or type.
  NEXT_PUBLIC_POLICY_DATE: '2026-07-15',
  // Executes this line as the next step in the surrounding logic.
} as const;

// Defines the loadConfiguration function and its callable behavior.
async function loadConfiguration(
  // Defines the values field in the surrounding object or type.
  values: Partial<Record<(typeof launchKeys)[number], string>>,
  // Provides the nodeEnvironment value to the surrounding call or element.
  nodeEnvironment = 'production',
  // Begins the nested block or object completed below.
) {
  // Executes this line as the next step in the surrounding logic.
  process.env.NODE_ENV = nodeEnvironment;
  // Iterates through these values for the nested operation.
  for (const key of launchKeys) Reflect.deleteProperty(process.env, key);
  // Calls Object.assign with the supplied values.
  Object.assign(process.env, values);
  // Calls vi.resetModules with the supplied values.
  vi.resetModules();
  // Returns this result to the caller and ends the current function.
  return import('./index.js');
  // Closes the expression, call, or declaration started above.
}

// Calls afterEach with the supplied values.
afterEach(() => {
  // Iterates through these values for the nested operation.
  for (const key of launchKeys) Reflect.deleteProperty(process.env, key);
  // Calls Reflect.deleteProperty with the supplied values.
  Reflect.deleteProperty(process.env, 'NODE_ENV');
  // Calls vi.resetModules with the supplied values.
  vi.resetModules();
  // Closes the expression, call, or declaration started above.
});

// Calls describe with the supplied values.
describe('assertLaunchConfiguration', () => {
  // Calls it with the supplied values.
  it('accepts a complete browser-safe production configuration', async () => {
    // Executes this line as the next step in the surrounding logic.
    const { assertLaunchConfiguration } = await loadConfiguration(validLaunchConfiguration);
    // Calls expect with the supplied values.
    expect(() => assertLaunchConfiguration()).not.toThrow();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('reports missing production values by name without exposing values', async () => {
    // Executes this line as the next step in the surrounding logic.
    const { assertLaunchConfiguration } = await loadConfiguration({});
    // Calls expect with the supplied values.
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_API_ORIGIN/);
    // Calls expect with the supplied values.
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY/);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('rejects non-origin URLs', async () => {
    // Begins the nested block or object completed below.
    const { assertLaunchConfiguration } = await loadConfiguration({
      // Supplies this item to the surrounding call or collection.
      ...validLaunchConfiguration,
      // Defines the NEXT_PUBLIC_API_ORIGIN field in the surrounding object or type.
      NEXT_PUBLIC_API_ORIGIN: 'http://api.example.com/v1',
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_API_ORIGIN/);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('rejects placeholder contacts and impossible policy dates', async () => {
    // Computes and stores placeholder for subsequent operations.
    const placeholder = await loadConfiguration({
      // Supplies this item to the surrounding call or collection.
      ...validLaunchConfiguration,
      // Defines the NEXT_PUBLIC_SUPPORT_EMAIL field in the surrounding object or type.
      NEXT_PUBLIC_SUPPORT_EMAIL: 'support@example.invalid',
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(() => placeholder.assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPPORT_EMAIL/);

    // Computes and stores impossibleDate for subsequent operations.
    const impossibleDate = await loadConfiguration({
      // Supplies this item to the surrounding call or collection.
      ...validLaunchConfiguration,
      // Defines the NEXT_PUBLIC_POLICY_DATE field in the surrounding object or type.
      NEXT_PUBLIC_POLICY_DATE: '2026-02-30',
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(() => impossibleDate.assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_POLICY_DATE/);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('rejects modern and legacy privileged Supabase credentials', async () => {
    // Computes and stores privilegedPayload for subsequent operations.
    const privilegedPayload = Buffer.from(JSON.stringify({ role: 'service_role' })).toString(
      // Supplies this item to the surrounding call or collection.
      'base64url',
      // Closes the expression, call, or declaration started above.
    );
    // Iterates through these values for the nested operation.
    for (const key of ['sb_secret_test_fixture_only', `e30.${privilegedPayload}.signature`]) {
      // Begins the nested block or object completed below.
      const { assertLaunchConfiguration } = await loadConfiguration({
        // Supplies this item to the surrounding call or collection.
        ...validLaunchConfiguration,
        // Defines the NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY field in the surrounding object or type.
        NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: key,
        // Closes the expression, call, or declaration started above.
      });
      // Calls expect with the supplied values.
      expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY/);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('does not block local development defaults', async () => {
    // Executes this line as the next step in the surrounding logic.
    const { assertLaunchConfiguration } = await loadConfiguration({}, 'development');
    // Calls expect with the supplied values.
    expect(() => assertLaunchConfiguration()).not.toThrow();
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
