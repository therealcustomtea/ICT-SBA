// Imports the dependency used by this module.
import { readFile } from 'node:fs/promises';
// Imports the dependency used by this module.
import { expect, test, type APIRequestContext } from '@playwright/test';
// Imports the dependency used by this module.
import { apiOrigin, captureSession } from './helpers';

// Computes and stores inbucketOrigin for subsequent operations.
const mailpitOrigin = process.env.PLAYWRIGHT_MAILPIT_URL;
// Computes and stores deletionEnabled for subsequent operations.
const deletionEnabled = process.env.PLAYWRIGHT_ACCOUNT_DELETION_ENABLED === '1';

// Defines the stringValues function and its callable behavior.
function stringValues(value: unknown): string[] {
  // Checks this condition before running the nested branch.
  if (typeof value === 'string') return [value];
  // Checks this condition before running the nested branch.
  if (Array.isArray(value)) return value.flatMap(stringValues);
  // Checks this condition before running the nested branch.
  if (value && typeof value === 'object')
    // Returns this result to the caller and ends the current function.
    return Object.values(value as Record<string, unknown>).flatMap(stringValues);
  // Returns this result to the caller and ends the current function.
  return [];
  // Closes the expression, call, or declaration started above.
}

// Defines the identifiers function and its callable behavior.
function identifiers(value: unknown): string[] {
  // Checks this condition before running the nested branch.
  if (Array.isArray(value)) return value.flatMap(identifiers);
  // Checks this condition before running the nested branch.
  if (!value || typeof value !== 'object') return [];
  // Computes and stores object for subsequent operations.
  const object = value as Record<string, unknown>;
  // Returns this result to the caller and ends the current function.
  return [
    // Supplies this item to the surrounding call or collection.
    ...(typeof object.id === 'string' ? [object.id] : []),
    // Supplies this item to the surrounding call or collection.
    ...(typeof object.ID === 'string' ? [object.ID] : []),
    // Supplies this item to the surrounding call or collection.
    ...Object.values(object).flatMap(identifiers),
    // Closes the expression, call, or declaration started above.
  ];
  // Closes the expression, call, or declaration started above.
}

// Defines the authLinkFrom function and its callable behavior.
function authLinkFrom(values: string[]): string | null {
  // Iterates through these values for the nested operation.
  for (const source of values) {
    // Computes and stores decoded for subsequent operations.
    const decoded = source.replace(
      // Matches HTML and quoted-printable encodings used inside captured email links.
      /&amp;|&#x3D;|&#61;|=3D|=\r?\n/g,
      // Continues the surrounding operation with this required value or expression.
      (value) =>
        // Provides the value value to the surrounding call or element.
        value === '&amp;' ? '&' : value.startsWith('=\r') || value.startsWith('=\n') ? '' : '=',
      // Closes the expression, call, or declaration started above.
    );
    // Iterates through these values for the nested operation.
    for (const candidate of decoded.match(/https?:\/\/[^\s"'<>]+/g) ?? []) {
      // Checks this condition before running the nested branch.
      if (candidate.includes('/v1/auth/email/verify') && candidate.includes('token='))
        // Returns the computed result and ends the current callable.
        return candidate;
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return null;
  // Closes the expression, call, or declaration started above.
}

// Defines the requestJson function and its callable behavior.
async function requestJson(request: APIRequestContext, url: string): Promise<unknown | null> {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores response for subsequent operations.
    const response = await request.get(url);
    // Checks this condition before running the nested branch.
    if (!response.ok()) return null;
    // Returns this result to the caller and ends the current function.
    return response.json();
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return null;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Defines the waitForAuthLink function and its callable behavior.
async function waitForAuthLink(request: APIRequestContext, email: string): Promise<string> {
  // Computes and stores mailbox for subsequent operations.
  // Iterates through these values for the nested operation.
  for (let attempt = 0; attempt < 40; attempt += 1) {
    // Computes and stores lists for subsequent operations.
    const lists = // Waits for this asynchronous operation to complete.
      // Runs this required asynchronous effect without leaving it implicit.
      (
        await /* Waits for all mailbox requests before filtering their results. */ Promise.all([
          // Continues the surrounding operation with this required value or expression.
          requestJson(request, `${mailpitOrigin}/api/v1/messages`),
          // Closes the expression, call, or declaration started above.
        ])
      ) // Completes the collected mailbox results before the filter chain runs.
        // Executes this line as the next step in the surrounding logic.
        .filter((value): value is unknown => value !== null);
    // Computes and stores matchingLists for subsequent operations.
    const matchingLists = lists.filter(
      // Continues the surrounding operation with this required value or expression.
      (value) =>
        // Calls stringValues with the supplied values.
        stringValues(value).some((entry) => entry.includes(email)),
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores values for subsequent operations.
    const values = matchingLists.flatMap(stringValues);
    // Computes and stores ids for subsequent operations.
    const ids = [...new Set(matchingLists.flatMap(identifiers))];
    // Computes and stores details for subsequent operations.
    const details = await Promise.all(
      // Calls ids.flatMap with the supplied values.
      ids.flatMap((id) => [
        // Calls requestJson with the supplied values.
        requestJson(request, `${mailpitOrigin}/api/v1/message/${encodeURIComponent(id)}`),
        // Closes the expression, call, or declaration started above.
      ]),
      // Closes the expression, call, or declaration started above.
    );
    // Calls values.push with the supplied values.
    values.push(
      // Supplies this item to the surrounding call or collection.
      ...details.filter((value): value is unknown => value !== null).flatMap(stringValues),
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores link for subsequent operations.
    const link = authLinkFrom(values);
    // Checks this condition before running the nested branch.
    if (link) return link;
    // Waits for this asynchronous operation to complete.
    await new Promise((resolve) => setTimeout(resolve, 500));
    // Closes the expression, call, or declaration started above.
  }
  // Throws this error to report an invalid or failed operation.
  throw new Error(`No local sign-in email arrived for ${email}.`);
  // Closes the expression, call, or declaration started above.
}

// Calls test with the supplied values.
test('guest upgrades in place, exports data, and permanently deletes the account', async ({
  // Supplies this item to the surrounding call or collection.
  isMobile,
  // Supplies this item to the surrounding call or collection.
  page,
  // Begins the nested block or object completed below.
}) => {
  // Calls test.skip with the supplied values.
  test.skip(Boolean(isMobile), 'The account lifecycle runs once in the desktop project.');
  // Calls test.skip with the supplied values.
  test.skip(!mailpitOrigin, 'PLAYWRIGHT_MAILPIT_URL is required for the local Auth email flow.');
  // Calls test.setTimeout with the supplied values.
  test.setTimeout(75_000);

  // Computes and stores original for subsequent operations.
  const original = await captureSession(page);
  // Calls expect with the supplied values.
  expect(original.profile.isAnonymous).toBe(true);
  // Computes and stores email for subsequent operations.
  const email = `cipherboard-e2e-${Date.now()}@example.test`;
  // Waits for this asynchronous operation to complete.
  await page.goto('/en/auth');
  // Waits for this asynchronous operation to complete.
  await expect(page.getByRole('link', { name: 'Continue as guest', exact: true })).toHaveAttribute(
    // Supplies this item to the surrounding call or collection.
    'aria-disabled',
    // Supplies this item to the surrounding call or collection.
    'false',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.getByLabel('Email address').fill(email);
  // Computes and stores emailRequest for subsequent operations.
  const emailRequest = page.waitForResponse((response) => {
    // Computes and stores url for subsequent operations.
    const url = new URL(response.url());
    // Returns this result to the caller and ends the current function.
    return (
      // Executes this line as the next step in the surrounding logic.
      url.origin === new URL(apiOrigin).origin && url.pathname === '/v1/auth/email'
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });
  // Waits for this asynchronous operation to complete.
  await page.getByRole('button', { name: 'Email me a sign-in link', exact: true }).click();
  // Calls expect with the supplied values.
  expect((await emailRequest).ok()).toBe(true);
  // Waits for this asynchronous operation to complete.
  await expect(page.getByRole('status')).toContainText('Check your email');

  // Computes and stores authLink for subsequent operations.
  const authLink = await waitForAuthLink(page.request, email);
  // Computes and stores pendingConfirmation for subsequent operations.
  const pendingConfirmation = await captureSession(page);
  // Calls expect with the supplied values.
  expect(pendingConfirmation.profile.id).toBe(original.profile.id);
  // Calls expect with the supplied values.
  expect(pendingConfirmation.profile.isAnonymous).toBe(true);
  // Waits for this asynchronous operation to complete.
  await page.goto(authLink);
  // Waits for this asynchronous operation to complete.
  await expect(page).toHaveURL(/\/en\/profile$/);
  // Computes and stores upgraded for subsequent operations.
  const upgraded = await captureSession(page);
  // Calls expect with the supplied values.
  expect(upgraded.profile.id).toBe(original.profile.id);
  // Calls expect with the supplied values.
  expect(upgraded.profile.isAnonymous).toBe(false);

  // Waits for this asynchronous operation to complete.
  await page.goto('/en/account');
  // Computes and stores downloadPromise for subsequent operations.
  const downloadPromise = page.waitForEvent('download');
  // Waits for this asynchronous operation to complete.
  await page.getByRole('button', { name: 'Download data export', exact: true }).click();
  // Computes and stores download for subsequent operations.
  const download = await downloadPromise;
  // Calls expect with the supplied values.
  expect(download.suggestedFilename()).toBe('cipherboard-data.zip');
  // Computes and stores path for subsequent operations.
  const path = await download.path();
  // Calls expect with the supplied values.
  expect(path).not.toBeNull();
  // Computes and stores archive for subsequent operations.
  const archive = await readFile(path!);
  // Calls expect with the supplied values.
  expect(archive.byteLength).toBeGreaterThan(40);
  // Calls expect with the supplied values.
  expect(archive.subarray(0, 2).toString('ascii')).toBe('PK');
  // Calls expect with the supplied values.
  expect(archive.toString('utf8')).not.toContain(upgraded.token);

  // Calls test.skip with the supplied values.
  test.skip(
    // Supplies this item to the surrounding call or collection.
    !deletionEnabled,
    // Supplies this item to the surrounding call or collection.
    'PLAYWRIGHT_ACCOUNT_DELETION_ENABLED is required with an API-side service credential.',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.getByLabel('Type DELETE to confirm').fill('DELETE');
  // Computes and stores deletionResponse for subsequent operations.
  const deletionResponse = page.waitForResponse(
    // Executes this line as the next step in the surrounding logic.
    (response) =>
      // Calls response.url with the supplied values.
      response.url() === `${apiOrigin}/v1/me` && response.request().method() === 'DELETE',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.getByRole('button', { name: 'Permanently delete account', exact: true }).click();
  // Computes and stores deleted for subsequent operations.
  const deleted = await deletionResponse;
  // Calls expect with the supplied values.
  expect(deleted.ok()).toBe(true);
  // Calls expect with the supplied values.
  expect(await deleted.json()).toEqual({ deleted: true });
  // Waits for this asynchronous operation to complete.
  await expect(page).toHaveURL(/\/en$/);

  // Computes and stores nextGuest for subsequent operations.
  const nextGuest = await captureSession(page);
  // Calls expect with the supplied values.
  expect(nextGuest.profile.isAnonymous).toBe(true);
  // Calls expect with the supplied values.
  expect(nextGuest.profile.id).not.toBe(original.profile.id);
  // Closes the expression, call, or declaration started above.
});
