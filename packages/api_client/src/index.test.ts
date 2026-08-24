// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import { ApiError, MastermindApi } from './index.js';

// Calls describe with the supplied values.
describe('MastermindApi', () => {
  // Calls afterEach with the supplied values.
  afterEach(() => vi.restoreAllMocks());

  // Calls it with the supplied values.
  it('returns undefined for successful no-content responses', async () => {
    // Calls vi.spyOn with the supplied values.
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
    // Computes and stores client for subsequent operations.
    const client = new MastermindApi('https://api.example.test', async () => 'token');

    // Waits for this asynchronous operation to complete.
    await expect(
      // Supplies this item to the surrounding call or collection.
      client.request<undefined>('/v1/challenges/id', { method: 'DELETE' }),
      // Executes this line as the next step in the surrounding logic.
    ).resolves.toBeUndefined();
    // Calls expect with the supplied values.
    expect(fetch).toHaveBeenCalledWith(
      // Supplies this item to the surrounding call or collection.
      'https://api.example.test/v1/challenges/id',
      // Calls expect.objectContaining with the supplied values.
      expect.objectContaining({
        // Defines the cache field in the surrounding object or type.
        cache: 'no-store',
        // Defines the headers field in the surrounding object or type.
        headers: expect.any(Headers),
        // Defines the method field in the surrounding object or type.
        method: 'DELETE',
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('normalizes non-JSON API failures without leaking response content', async () => {
    // Calls vi.spyOn with the supplied values.
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      // Begins the nested block or object completed below.
      new Response('gateway failure', {
        // Defines the status field in the surrounding object or type.
        status: 502,
        // Defines the headers field in the surrounding object or type.
        headers: { 'x-request-id': 'request-1' },
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores client for subsequent operations.
    const client = new MastermindApi('https://api.example.test', async () => null);

    // Waits for this asynchronous operation to complete.
    await expect(client.request('/v1/daily')).rejects.toEqual(
      // Begins the nested block or object completed below.
      new ApiError(502, {
        // Defines the code field in the surrounding object or type.
        code: 'UNEXPECTED_ERROR',
        // Defines the message field in the surrounding object or type.
        message: 'The request could not be completed.',
        // Defines the requestId field in the surrounding object or type.
        requestId: 'request-1',
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
