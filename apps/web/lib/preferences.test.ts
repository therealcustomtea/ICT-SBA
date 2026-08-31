// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import {
  // Supplies this item to the surrounding call or collection.
  applyPreferences,
  // Supplies this item to the surrounding call or collection.
  defaultPreferences,
  // Supplies this item to the surrounding call or collection.
  loadPreferences,
  // Supplies this item to the surrounding call or collection.
  playGameSound,
  // Supplies this item to the surrounding call or collection.
  savePreferences,
  // Executes this line as the next step in the surrounding logic.
} from './preferences';

// Calls describe with the supplied values.
describe('preferences', () => {
  // Calls afterEach with the supplied values.
  afterEach(() => {
    // Calls localStorage.clear with the supplied values.
    localStorage.clear();
    // Calls document.documentElement.removeAttribute with the supplied values.
    document.documentElement.removeAttribute('data-theme');
    // Calls document.documentElement.removeAttribute with the supplied values.
    document.documentElement.removeAttribute('data-peg-style');
    // Calls document.documentElement.removeAttribute with the supplied values.
    document.documentElement.removeAttribute('data-reduce-motion');
    // Calls vi.restoreAllMocks with the supplied values.
    vi.restoreAllMocks();
    // Calls vi.unstubAllGlobals with the supplied values.
    vi.unstubAllGlobals();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('validates stored values and removes malformed JSON', () => {
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem('cipherboard:preferences', '{broken');
    // Calls expect with the supplied values.
    expect(loadPreferences()).toEqual(defaultPreferences);
    // Calls expect with the supplied values.
    expect(localStorage.getItem('cipherboard:preferences')).toBeNull();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('falls back field-by-field for absent or invalid stored values', () => {
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(
      // Supplies this item to the surrounding call or collection.
      'cipherboard:preferences',
      // Calls JSON.stringify with the supplied values.
      JSON.stringify({
        // Defines the theme field in the surrounding object or type.
        theme: 'neon',
        // Defines the pegStyle field in the surrounding object or type.
        pegStyle: 'glass',
        // Defines the reducedMotion field in the surrounding object or type.
        reducedMotion: 'yes',
        // Defines the sound field in the surrounding object or type.
        sound: 1,
        // Defines the analytics field in the surrounding object or type.
        analytics: null,
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(loadPreferences()).toEqual(defaultPreferences);
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem('cipherboard:preferences', JSON.stringify('not-an-object'));
    // Calls expect with the supplied values.
    expect(loadPreferences()).toEqual(defaultPreferences);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('applies saved visual and accessibility preferences to the document', () => {
    // Computes and stores preferences for subsequent operations.
    const preferences = {
      // Supplies this item to the surrounding call or collection.
      ...defaultPreferences,
      // Defines the theme field in the surrounding object or type.
      theme: 'dark' as const,
      // Defines the pegStyle field in the surrounding object or type.
      pegStyle: 'highContrast' as const,
      // Defines the reducedMotion field in the surrounding object or type.
      reducedMotion: true,
      // Closes the expression, call, or declaration started above.
    };
    // Calls savePreferences with the supplied values.
    savePreferences(preferences);

    // Calls expect with the supplied values.
    expect(loadPreferences()).toEqual(preferences);
    // Calls expect with the supplied values.
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    // Calls expect with the supplied values.
    expect(document.documentElement).toHaveAttribute('data-peg-style', 'highContrast');
    // Calls expect with the supplied values.
    expect(document.documentElement).toHaveAttribute('data-reduce-motion', 'true');
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('resolves system appearance and removes an explicit appearance override', () => {
    // Computes and stores matchMedia for subsequent operations.
    const matchMedia = vi.fn().mockReturnValue({ matches: true });
    // Calls vi.stubGlobal with the supplied values.
    vi.stubGlobal('matchMedia', matchMedia);
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem('cipherboard:appearance', 'light');
    // Calls applyPreferences with the supplied values.
    applyPreferences(defaultPreferences);
    // Calls expect with the supplied values.
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    // Calls expect with the supplied values.
    expect(localStorage.getItem('cipherboard:appearance')).toBeNull();
    // Calls matchMedia.mockReturnValue with the supplied values.
    matchMedia.mockReturnValue({ matches: false });
    // Calls applyPreferences with the supplied values.
    applyPreferences(defaultPreferences);
    // Calls expect with the supplied values.
    expect(document.documentElement).toHaveAttribute('data-theme', 'light');
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('plays the selected optional sound cue without retaining an audio context', async () => {
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(
      // Supplies this item to the surrounding call or collection.
      'cipherboard:preferences',
      // Calls JSON.stringify with the supplied values.
      JSON.stringify({ ...defaultPreferences, sound: true }),
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores close for subsequent operations.
    const close = vi.fn().mockResolvedValue(undefined);
    // Computes and stores resume for subsequent operations.
    const resume = vi.fn().mockResolvedValue(undefined);
    // Computes and stores oscillator for subsequent operations.
    const oscillator = {
      // Defines the type field in the surrounding object or type.
      type: 'sine',
      // Defines the frequency field in the surrounding object or type.
      frequency: { value: 0 },
      // Defines the connect field in the surrounding object or type.
      connect: vi.fn(),
      // Defines the start field in the surrounding object or type.
      start: vi.fn(),
      // Defines the stop field in the surrounding object or type.
      stop: vi.fn(),
      // Defines the addEventListener field in the surrounding object or type.
      addEventListener: vi.fn((_name: string, callback: () => void) => callback()),
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores gain for subsequent operations.
    const gain = {
      // Defines the gain field in the surrounding object or type.
      gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
      // Defines the connect field in the surrounding object or type.
      connect: vi.fn(),
      // Closes the expression, call, or declaration started above.
    };
    // Declares the MockAudioContext data shape or implementation.
    class MockAudioContext {
      // Provides the state value to the surrounding call or element.
      state = 'suspended';
      // Provides the currentTime value to the surrounding call or element.
      currentTime = 0;
      // Provides the destination value to the surrounding call or element.
      destination = {};
      // Provides the close value to the surrounding call or element.
      close = close;
      // Provides the resume value to the surrounding call or element.
      resume = resume;
      // Provides the createOscillator value to the surrounding call or element.
      createOscillator = () => oscillator;
      // Provides the createGain value to the surrounding call or element.
      createGain = () => gain;
      // Closes the expression, call, or declaration started above.
    }
    // Calls vi.stubGlobal with the supplied values.
    vi.stubGlobal('AudioContext', MockAudioContext);

    // Waits for this asynchronous operation to complete.
    await playGameSound('success');
    // Calls expect with the supplied values.
    expect(oscillator.frequency.value).toBe(660);
    // Waits for this asynchronous operation to complete.
    await playGameSound('failure');
    // Calls expect with the supplied values.
    expect(oscillator.frequency.value).toBe(220);
    // Waits for this asynchronous operation to complete.
    await playGameSound('feedback');
    // Calls expect with the supplied values.
    expect(oscillator.frequency.value).toBe(440);
    // Calls expect with the supplied values.
    expect(resume).toHaveBeenCalledTimes(3);
    // Calls expect with the supplied values.
    expect(close).toHaveBeenCalledTimes(3);
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
