import { afterEach, describe, expect, it, vi } from 'vitest';
import { deliverProductEvent, gameDifficulty, gameMode, scoreBand } from './analytics-delivery';
import { defaultPreferences } from './preferences';

describe('analytics delivery', () => {
  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('does not send events without explicit analytics consent', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch');
    await deliverProductEvent('token', 'en', 'difficulty_selected', { difficulty: 'hard' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sends only the allowlisted, consent-versioned event body and fails silently', async () => {
    localStorage.setItem(
      'cipherboard:preferences',
      JSON.stringify({ ...defaultPreferences, analytics: true }),
    );
    vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue(
      '00000000-0000-4000-8000-000000000001',
    );
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'));

    await expect(
      deliverProductEvent('token', 'zh-Hant', 'account_upgraded', { previousAnonymous: true }),
    ).resolves.toBeUndefined();
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      clientEventId: '00000000-0000-4000-8000-000000000001',
      eventName: 'account_upgraded',
      consent: true,
      consentVersion: 'privacy-v1',
      locale: 'zh-Hant',
      previousAnonymous: true,
    });
  });

  it('normalizes bounded gameplay analytics fields', () => {
    expect(gameMode('unexpected')).toBe('solo');
    expect(gameDifficulty(null)).toBe('custom');
    expect([scoreBand(0), scoreBand(999), scoreBand(1000), scoreBand(1500)]).toEqual([
      'zero',
      '1-999',
      '1000-1499',
      '1500+',
    ]);
  });
});
