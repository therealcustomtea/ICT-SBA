import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, MastermindApi } from './index.js';

describe('MastermindApi', () => {
  afterEach(() => vi.restoreAllMocks());

  it('returns undefined for successful no-content responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
    const client = new MastermindApi('https://api.example.test', async () => 'token');

    await expect(
      client.request<undefined>('/v1/challenges/id', { method: 'DELETE' }),
    ).resolves.toBeUndefined();
    expect(fetch).toHaveBeenCalledWith(
      'https://api.example.test/v1/challenges/id',
      expect.objectContaining({
        cache: 'no-store',
        headers: expect.any(Headers),
        method: 'DELETE',
      }),
    );
  });

  it('normalizes non-JSON API failures without leaking response content', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('gateway failure', {
        status: 502,
        headers: { 'x-request-id': 'request-1' },
      }),
    );
    const client = new MastermindApi('https://api.example.test', async () => null);

    await expect(client.request('/v1/daily')).rejects.toEqual(
      new ApiError(502, {
        code: 'UNEXPECTED_ERROR',
        message: 'The request could not be completed.',
        requestId: 'request-1',
      }),
    );
  });
});
