'use client';

export type Preferences = {
  theme: 'system' | 'light' | 'dark';
  pegStyle: 'symbols' | 'patterns' | 'highContrast';
  reducedMotion: boolean;
  sound: boolean;
  analytics: boolean;
};

export const PREFERENCES_KEY = 'cipherboard:preferences';
export const defaultPreferences: Preferences = {
  theme: 'system',
  pegStyle: 'patterns',
  reducedMotion: false,
  sound: false,
  analytics: false,
};

const themes = new Set<Preferences['theme']>(['system', 'light', 'dark']);
const pegStyles = new Set<Preferences['pegStyle']>(['symbols', 'patterns', 'highContrast']);

export function loadPreferences(): Preferences {
  if (typeof window === 'undefined') return defaultPreferences;
  try {
    const value = JSON.parse(
      localStorage.getItem(PREFERENCES_KEY) ?? 'null',
    ) as Partial<Preferences> | null;
    if (!value || typeof value !== 'object') return defaultPreferences;
    return {
      theme: value.theme && themes.has(value.theme) ? value.theme : defaultPreferences.theme,
      pegStyle:
        value.pegStyle && pegStyles.has(value.pegStyle)
          ? value.pegStyle
          : defaultPreferences.pegStyle,
      reducedMotion:
        typeof value.reducedMotion === 'boolean'
          ? value.reducedMotion
          : defaultPreferences.reducedMotion,
      sound: typeof value.sound === 'boolean' ? value.sound : defaultPreferences.sound,
      analytics:
        typeof value.analytics === 'boolean' ? value.analytics : defaultPreferences.analytics,
    };
  } catch {
    localStorage.removeItem(PREFERENCES_KEY);
    return defaultPreferences;
  }
}

export function savePreferences(preferences: Preferences) {
  localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
  applyPreferences(preferences);
  window.dispatchEvent(new CustomEvent('cipherboard:preferences-changed', { detail: preferences }));
}

export function applyPreferences(preferences: Preferences) {
  const root = document.documentElement;
  const resolvedTheme =
    preferences.theme === 'system'
      ? matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : preferences.theme;
  root.dataset.theme = resolvedTheme;
  root.dataset.pegStyle = preferences.pegStyle;
  root.dataset.reduceMotion = String(preferences.reducedMotion);
  root.dataset.sound = String(preferences.sound);
  root.dataset.analytics = String(preferences.analytics);
  if (preferences.theme === 'system') localStorage.removeItem('cipherboard:appearance');
  else localStorage.setItem('cipherboard:appearance', preferences.theme);
}

export async function playGameSound(kind: 'feedback' | 'success' | 'failure') {
  if (!loadPreferences().sound || typeof AudioContext === 'undefined') return;
  const context = new AudioContext();
  try {
    if (context.state === 'suspended') await context.resume();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = kind === 'success' ? 660 : kind === 'failure' ? 220 : 440;
    gain.gain.setValueAtTime(0.0001, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.06, context.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.1);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.11);
    oscillator.addEventListener('ended', () => void context.close(), { once: true });
  } catch {
    await context.close().catch(() => undefined);
  }
}
