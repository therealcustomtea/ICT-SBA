import { readFile } from 'node:fs/promises';
import { expect, test, type APIRequestContext } from '@playwright/test';
import { apiOrigin, captureSession } from './helpers';

const inbucketOrigin = process.env.PLAYWRIGHT_INBUCKET_URL;
const deletionEnabled = process.env.PLAYWRIGHT_ACCOUNT_DELETION_ENABLED === '1';

function stringValues(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(stringValues);
  if (value && typeof value === 'object')
    return Object.values(value as Record<string, unknown>).flatMap(stringValues);
  return [];
}

function identifiers(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(identifiers);
  if (!value || typeof value !== 'object') return [];
  const object = value as Record<string, unknown>;
  return [
    ...(typeof object.id === 'string' ? [object.id] : []),
    ...(typeof object.ID === 'string' ? [object.ID] : []),
    ...Object.values(object).flatMap(identifiers),
  ];
}

function authLinkFrom(values: string[]): string | null {
  for (const source of values) {
    const decoded = source
      .replaceAll('&amp;', '&')
      .replaceAll('&#x3D;', '=')
      .replaceAll('&#61;', '=')
      .replaceAll('=3D', '=')
      .replace(/=\r?\n/g, '');
    for (const candidate of decoded.match(/https?:\/\/[^\s"'<>]+/g) ?? []) {
      if (candidate.includes('/auth/v1/verify') && candidate.includes('token=')) return candidate;
    }
  }
  return null;
}

async function requestJson(request: APIRequestContext, url: string): Promise<unknown | null> {
  try {
    const response = await request.get(url);
    if (!response.ok()) return null;
    return response.json();
  } catch {
    return null;
  }
}

async function waitForAuthLink(request: APIRequestContext, email: string): Promise<string> {
  const mailbox = email.split('@')[0]!;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const lists = (
      await Promise.all([
        requestJson(request, `${inbucketOrigin}/api/v1/mailbox/${encodeURIComponent(mailbox)}`),
        requestJson(request, `${inbucketOrigin}/api/v1/messages`),
      ])
    ).filter((value): value is unknown => value !== null);
    const matchingLists = lists.filter((value) =>
      stringValues(value).some((entry) => entry.includes(email) || entry.includes(mailbox)),
    );
    const values = matchingLists.flatMap(stringValues);
    const ids = [...new Set(matchingLists.flatMap(identifiers))];
    const details = await Promise.all(
      ids.flatMap((id) => [
        requestJson(
          request,
          `${inbucketOrigin}/api/v1/mailbox/${encodeURIComponent(mailbox)}/${encodeURIComponent(id)}`,
        ),
        requestJson(request, `${inbucketOrigin}/api/v1/message/${encodeURIComponent(id)}`),
        requestJson(request, `${inbucketOrigin}/api/v1/messages/${encodeURIComponent(id)}`),
      ]),
    );
    values.push(
      ...details.filter((value): value is unknown => value !== null).flatMap(stringValues),
    );
    const link = authLinkFrom(values);
    if (link) return link;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No local Supabase confirmation email arrived for ${email}.`);
}

test('guest upgrades in place, exports data, and permanently deletes the account', async ({
  isMobile,
  page,
}) => {
  test.skip(Boolean(isMobile), 'The account lifecycle runs once in the desktop project.');
  test.skip(!inbucketOrigin, 'PLAYWRIGHT_INBUCKET_URL is required for the local Auth email flow.');
  test.setTimeout(75_000);

  const original = await captureSession(page);
  expect(original.profile.isAnonymous).toBe(true);
  const email = `cipherboard-e2e-${Date.now()}@example.test`;
  await page.goto('/en/auth');
  await expect(page.getByRole('link', { name: 'Continue as guest', exact: true })).toHaveAttribute(
    'aria-disabled',
    'false',
  );
  await page.getByLabel('Email address').fill(email);
  const emailRequest = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.origin === new URL(process.env.NEXT_PUBLIC_SUPABASE_URL!).origin &&
      ['/auth/v1/user', '/auth/v1/otp'].includes(url.pathname)
    );
  });
  await page.getByRole('button', { name: 'Email me a sign-in link', exact: true }).click();
  expect((await emailRequest).ok()).toBe(true);
  await expect(page.getByRole('status')).toContainText('Check your email');

  const authLink = await waitForAuthLink(page.request, email);
  const pendingConfirmation = await captureSession(page);
  expect(pendingConfirmation.profile.id).toBe(original.profile.id);
  expect(pendingConfirmation.profile.isAnonymous).toBe(true);
  await page.goto(authLink);
  await expect(page).toHaveURL(/\/en\/profile$/);
  const upgraded = await captureSession(page);
  expect(upgraded.profile.id).toBe(original.profile.id);
  expect(upgraded.profile.isAnonymous).toBe(false);

  await page.goto('/en/account');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download data export', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('cipherboard-data.zip');
  const path = await download.path();
  expect(path).not.toBeNull();
  const archive = await readFile(path!);
  expect(archive.byteLength).toBeGreaterThan(40);
  expect(archive.subarray(0, 2).toString('ascii')).toBe('PK');
  expect(archive.toString('utf8')).not.toContain(upgraded.token);

  test.skip(
    !deletionEnabled,
    'PLAYWRIGHT_ACCOUNT_DELETION_ENABLED is required with an API-side service credential.',
  );
  await page.getByLabel('Type DELETE to confirm').fill('DELETE');
  const deletionResponse = page.waitForResponse(
    (response) =>
      response.url() === `${apiOrigin}/v1/me` && response.request().method() === 'DELETE',
  );
  await page.getByRole('button', { name: 'Permanently delete account', exact: true }).click();
  const deleted = await deletionResponse;
  expect(deleted.ok()).toBe(true);
  expect(await deleted.json()).toEqual({ deleted: true });
  await expect(page).toHaveURL(/\/en$/);

  const nextGuest = await captureSession(page);
  expect(nextGuest.profile.isAnonymous).toBe(true);
  expect(nextGuest.profile.id).not.toBe(original.profile.id);
});
