import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  applyPreferences,
  defaultPreferences,
  loadPreferences,
  playGameSound,
  savePreferences,
} from './preferences';

describe('preferences', () => {
  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.removeAttribute('data-peg-style');
    document.documentElement.removeAttribute('data-reduce-motion');
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('validates stored values and removes malformed JSON', () => {
    localStorage.setItem('cipherboard:preferences', '{broken');
    expect(loadPreferences()).toEqual(defaultPreferences);
    expect(localStorage.getItem('cipherboard:preferences')).toBeNull();
  });

  it('falls back field-by-field for absent or invalid stored values', () => {
    localStorage.setItem(
      'cipherboard:preferences',
      JSON.stringify({
        theme: 'neon',
        pegStyle: 'glass',
        reducedMotion: 'yes',
        sound: 1,
        analytics: null,
      }),
    );
    expect(loadPreferences()).toEqual(defaultPreferences);
    localStorage.setItem('cipherboard:preferences', JSON.stringify('not-an-object'));
    expect(loadPreferences()).toEqual(defaultPreferences);
  });

  it('applies saved visual and accessibility preferences to the document', () => {
    const preferences = {
      ...defaultPreferences,
      theme: 'dark' as const,
      pegStyle: 'highContrast' as const,
      reducedMotion: true,
    };
    savePreferences(preferences);

    expect(loadPreferences()).toEqual(preferences);
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(document.documentElement).toHaveAttribute('data-peg-style', 'highContrast');
    expect(document.documentElement).toHaveAttribute('data-reduce-motion', 'true');
  });

  it('resolves system appearance and removes an explicit appearance override', () => {
    const matchMedia = vi.fn().mockReturnValue({ matches: true });
    vi.stubGlobal('matchMedia', matchMedia);
    localStorage.setItem('cipherboard:appearance', 'light');
    applyPreferences(defaultPreferences);
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(localStorage.getItem('cipherboard:appearance')).toBeNull();
    matchMedia.mockReturnValue({ matches: false });
    applyPreferences(defaultPreferences);
    expect(document.documentElement).toHaveAttribute('data-theme', 'light');
  });

  it('plays the selected optional sound cue without retaining an audio context', async () => {
    localStorage.setItem(
      'cipherboard:preferences',
      JSON.stringify({ ...defaultPreferences, sound: true }),
    );
    const close = vi.fn().mockResolvedValue(undefined);
    const resume = vi.fn().mockResolvedValue(undefined);
    const oscillator = {
      type: 'sine',
      frequency: { value: 0 },
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
      addEventListener: vi.fn((_name: string, callback: () => void) => callback()),
    };
    const gain = {
      gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
      connect: vi.fn(),
    };
    class MockAudioContext {
      state = 'suspended';
      currentTime = 0;
      destination = {};
      close = close;
      resume = resume;
      createOscillator = () => oscillator;
      createGain = () => gain;
    }
    vi.stubGlobal('AudioContext', MockAudioContext);

    await playGameSound('success');
    expect(oscillator.frequency.value).toBe(660);
    await playGameSound('failure');
    expect(oscillator.frequency.value).toBe(220);
    await playGameSound('feedback');
    expect(oscillator.frequency.value).toBe(440);
    expect(resume).toHaveBeenCalledTimes(3);
    expect(close).toHaveBeenCalledTimes(3);
  });
});
