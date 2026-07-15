import { afterEach, describe, expect, it, vi } from 'vitest';

const launchKeys = [
  'NEXT_PUBLIC_API_ORIGIN',
  'NEXT_PUBLIC_PRODUCT_ORIGIN',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY',
  'NEXT_PUBLIC_PRODUCT_NAME',
  'NEXT_PUBLIC_SUPPORT_EMAIL',
  'NEXT_PUBLIC_LEGAL_ENTITY',
  'NEXT_PUBLIC_JURISDICTION',
  'NEXT_PUBLIC_POLICY_DATE',
] as const;

const validLaunchConfiguration = {
  NEXT_PUBLIC_API_ORIGIN: 'https://api.example.com',
  NEXT_PUBLIC_PRODUCT_ORIGIN: 'https://play.example.com',
  NEXT_PUBLIC_SUPABASE_URL: 'https://project.supabase.co',
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_test_fixture_only',
  NEXT_PUBLIC_PRODUCT_NAME: 'Cipherboard',
  NEXT_PUBLIC_SUPPORT_EMAIL: 'support@example.com',
  NEXT_PUBLIC_LEGAL_ENTITY: 'Test Entity',
  NEXT_PUBLIC_JURISDICTION: 'Test Jurisdiction',
  NEXT_PUBLIC_POLICY_DATE: '2026-07-15',
} as const;

async function loadConfiguration(
  values: Partial<Record<(typeof launchKeys)[number], string>>,
  nodeEnvironment = 'production',
) {
  process.env.NODE_ENV = nodeEnvironment;
  for (const key of launchKeys) Reflect.deleteProperty(process.env, key);
  Object.assign(process.env, values);
  vi.resetModules();
  return import('./index.js');
}

afterEach(() => {
  for (const key of launchKeys) Reflect.deleteProperty(process.env, key);
  Reflect.deleteProperty(process.env, 'NODE_ENV');
  vi.resetModules();
});

describe('assertLaunchConfiguration', () => {
  it('accepts a complete browser-safe production configuration', async () => {
    const { assertLaunchConfiguration } = await loadConfiguration(validLaunchConfiguration);
    expect(() => assertLaunchConfiguration()).not.toThrow();
  });

  it('reports missing production values by name without exposing values', async () => {
    const { assertLaunchConfiguration } = await loadConfiguration({});
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_API_ORIGIN/);
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY/);
  });

  it('rejects non-origin URLs', async () => {
    const { assertLaunchConfiguration } = await loadConfiguration({
      ...validLaunchConfiguration,
      NEXT_PUBLIC_API_ORIGIN: 'http://api.example.com/v1',
    });
    expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_API_ORIGIN/);
  });

  it('rejects placeholder contacts and impossible policy dates', async () => {
    const placeholder = await loadConfiguration({
      ...validLaunchConfiguration,
      NEXT_PUBLIC_SUPPORT_EMAIL: 'support@example.invalid',
    });
    expect(() => placeholder.assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPPORT_EMAIL/);

    const impossibleDate = await loadConfiguration({
      ...validLaunchConfiguration,
      NEXT_PUBLIC_POLICY_DATE: '2026-02-30',
    });
    expect(() => impossibleDate.assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_POLICY_DATE/);
  });

  it('rejects modern and legacy privileged Supabase credentials', async () => {
    const privilegedPayload = Buffer.from(JSON.stringify({ role: 'service_role' })).toString(
      'base64url',
    );
    for (const key of ['sb_secret_test_fixture_only', `e30.${privilegedPayload}.signature`]) {
      const { assertLaunchConfiguration } = await loadConfiguration({
        ...validLaunchConfiguration,
        NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: key,
      });
      expect(() => assertLaunchConfiguration()).toThrow(/NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY/);
    }
  });

  it('does not block local development defaults', async () => {
    const { assertLaunchConfiguration } = await loadConfiguration({}, 'development');
    expect(() => assertLaunchConfiguration()).not.toThrow();
  });
});
