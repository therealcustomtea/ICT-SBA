// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import { deliverProductEvent, gameDifficulty, gameMode, scoreBand } from './analytics-delivery';
// Imports the dependency used by this module.
import { defaultPreferences } from './preferences';

// Calls describe with the supplied values.
describe('analytics delivery', () => {
  // Calls afterEach with the supplied values.
  afterEach(() => {
    // Calls localStorage.clear with the supplied values.
    localStorage.clear();
    // Calls vi.restoreAllMocks with the supplied values.
    vi.restoreAllMocks();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('does not send events without explicit analytics consent', async () => {
    // Computes and stores fetchMock for subsequent operations.
    const fetchMock = vi.spyOn(globalThis, 'fetch');
    // Waits for this asynchronous operation to complete.
    await deliverProductEvent('token', 'en', 'difficulty_selected', { difficulty: 'hard' });
    // Calls expect with the supplied values.
    expect(fetchMock).not.toHaveBeenCalled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('sends only the allowlisted, consent-versioned event body and fails silently', async () => {
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(
      // Supplies this item to the surrounding call or collection.
      'cipherboard:preferences',
      // Calls JSON.stringify with the supplied values.
      JSON.stringify({ ...defaultPreferences, analytics: true }),
      // Closes the expression, call, or declaration started above.
    );
    // Calls vi.spyOn with the supplied values.
    vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue(
      // Supplies this item to the surrounding call or collection.
      '00000000-0000-4000-8000-000000000001',
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores fetchMock for subsequent operations.
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'));

    // Waits for this asynchronous operation to complete.
    await expect(
      // Calls deliverProductEvent with the supplied values.
      deliverProductEvent('token', 'zh-Hant', 'account_upgraded', { previousAnonymous: true }),
      // Executes this line as the next step in the surrounding logic.
    ).resolves.toBeUndefined();
    // Executes this line as the next step in the surrounding logic.
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    // Calls expect with the supplied values.
    expect(JSON.parse(String(init.body))).toEqual({
      // Defines the clientEventId field in the surrounding object or type.
      clientEventId: '00000000-0000-4000-8000-000000000001',
      // Defines the eventName field in the surrounding object or type.
      eventName: 'account_upgraded',
      // Defines the consent field in the surrounding object or type.
      consent: true,
      // Defines the consentVersion field in the surrounding object or type.
      consentVersion: 'privacy-v1',
      // Defines the locale field in the surrounding object or type.
      locale: 'zh-Hant',
      // Defines the previousAnonymous field in the surrounding object or type.
      previousAnonymous: true,
      // Closes the expression, call, or declaration started above.
    });
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('normalizes bounded gameplay analytics fields', () => {
    // Calls expect with the supplied values.
    expect(gameMode('unexpected')).toBe('solo');
    // Calls expect with the supplied values.
    expect(gameDifficulty(null)).toBe('custom');
    // Calls expect with the supplied values.
    expect([scoreBand(0), scoreBand(999), scoreBand(1000), scoreBand(1500)]).toEqual([
      // Supplies this item to the surrounding call or collection.
      'zero',
      // Supplies this item to the surrounding call or collection.
      '1-999',
      // Supplies this item to the surrounding call or collection.
      '1000-1499',
      // Supplies this item to the surrounding call or collection.
      '1500+',
      // Closes the expression, call, or declaration started above.
    ]);
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
