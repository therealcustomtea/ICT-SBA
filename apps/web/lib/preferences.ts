// Selects the runtime or strict execution mode for this module.
'use client';

// Exports this declaration for use by other modules.
export type Preferences = {
  // Defines the theme field in the surrounding object or type.
  theme: 'system' | 'light' | 'dark';
  // Defines the pegStyle field in the surrounding object or type.
  pegStyle: 'symbols' | 'patterns' | 'highContrast';
  // Defines the reducedMotion field in the surrounding object or type.
  reducedMotion: boolean;
  // Defines the sound field in the surrounding object or type.
  sound: boolean;
  // Defines the analytics field in the surrounding object or type.
  analytics: boolean;
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export const PREFERENCES_KEY = 'cipherboard:preferences';
// Exports this declaration for use by other modules.
export const defaultPreferences: Preferences = {
  // Defines the theme field in the surrounding object or type.
  theme: 'system',
  // Defines the pegStyle field in the surrounding object or type.
  pegStyle: 'patterns',
  // Defines the reducedMotion field in the surrounding object or type.
  reducedMotion: false,
  // Defines the sound field in the surrounding object or type.
  sound: false,
  // Defines the analytics field in the surrounding object or type.
  analytics: false,
  // Closes the expression, call, or declaration started above.
};

// Computes and stores themes for subsequent operations.
const themes = new Set<Preferences['theme']>(['system', 'light', 'dark']);
// Computes and stores pegStyles for subsequent operations.
const pegStyles = new Set<Preferences['pegStyle']>(['symbols', 'patterns', 'highContrast']);

// Exports this declaration for use by other modules.
export function loadPreferences(): Preferences {
  // Checks this condition before running the nested branch.
  if (typeof window === 'undefined') return defaultPreferences;
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores value for subsequent operations.
    const value = JSON.parse(
      // Calls localStorage.getItem with the supplied values.
      localStorage.getItem(PREFERENCES_KEY) ?? 'null',
      // Executes this line as the next step in the surrounding logic.
    ) as Partial<Preferences> | null;
    // Checks this condition before running the nested branch.
    if (!value || typeof value !== 'object') return defaultPreferences;
    // Returns this result to the caller and ends the current function.
    return {
      // Defines the theme field in the surrounding object or type.
      theme: value.theme && themes.has(value.theme) ? value.theme : defaultPreferences.theme,
      // Defines the pegStyle field in the surrounding object or type.
      pegStyle:
        // Executes this line as the next step in the surrounding logic.
        value.pegStyle && pegStyles.has(value.pegStyle)
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            value.pegStyle
          : // Continues the surrounding operation with this required value or expression.
            // Supplies this item to the surrounding call or collection.
            defaultPreferences.pegStyle,
      // Defines the reducedMotion field in the surrounding object or type.
      reducedMotion:
        // Executes this line as the next step in the surrounding logic.
        typeof value.reducedMotion === 'boolean'
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            value.reducedMotion
          : // Continues the surrounding operation with this required value or expression.
            // Supplies this item to the surrounding call or collection.
            defaultPreferences.reducedMotion,
      // Defines the sound field in the surrounding object or type.
      sound: typeof value.sound === 'boolean' ? value.sound : defaultPreferences.sound,
      // Defines the analytics field in the surrounding object or type.
      analytics:
        // Supplies this item to the surrounding call or collection.
        typeof value.analytics === 'boolean' ? value.analytics : defaultPreferences.analytics,
      // Closes the expression, call, or declaration started above.
    };
    // Handles a failure from the protected operation.
  } catch {
    // Calls localStorage.removeItem with the supplied values.
    localStorage.removeItem(PREFERENCES_KEY);
    // Returns this result to the caller and ends the current function.
    return defaultPreferences;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function savePreferences(preferences: Preferences) {
  // Calls localStorage.setItem with the supplied values.
  localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
  // Calls applyPreferences with the supplied values.
  applyPreferences(preferences);
  // Calls window.dispatchEvent with the supplied values.
  window.dispatchEvent(new CustomEvent('cipherboard:preferences-changed', { detail: preferences }));
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function applyPreferences(preferences: Preferences) {
  // Computes and stores root for subsequent operations.
  const root = document.documentElement;
  // Computes and stores resolvedTheme for subsequent operations.
  const resolvedTheme =
    // Executes this line as the next step in the surrounding logic.
    preferences.theme === 'system'
      ? // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        matchMedia('(prefers-color-scheme: dark)').matches
        ? // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          'dark'
        : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          'light'
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        preferences.theme;
  // Executes this line as the next step in the surrounding logic.
  root.dataset.theme = resolvedTheme;
  // Executes this line as the next step in the surrounding logic.
  root.dataset.pegStyle = preferences.pegStyle;
  // Executes this line as the next step in the surrounding logic.
  root.dataset.reduceMotion = String(preferences.reducedMotion);
  // Executes this line as the next step in the surrounding logic.
  root.dataset.sound = String(preferences.sound);
  // Executes this line as the next step in the surrounding logic.
  root.dataset.analytics = String(preferences.analytics);
  // Checks this condition before running the nested branch.
  if (preferences.theme === 'system') localStorage.removeItem('cipherboard:appearance');
  // Executes this line as the next step in the surrounding logic.
  else localStorage.setItem('cipherboard:appearance', preferences.theme);
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function playGameSound(kind: 'feedback' | 'success' | 'failure') {
  // Checks this condition before running the nested branch.
  if (!loadPreferences().sound || typeof AudioContext === 'undefined') return;
  // Computes and stores context for subsequent operations.
  const context = new AudioContext();
  // Starts an operation whose expected failures are handled below.
  try {
    // Checks this condition before running the nested branch.
    if (context.state === 'suspended') await context.resume();
    // Computes and stores oscillator for subsequent operations.
    const oscillator = context.createOscillator();
    // Computes and stores gain for subsequent operations.
    const gain = context.createGain();
    // Executes this line as the next step in the surrounding logic.
    oscillator.type = 'sine';
    // Executes this line as the next step in the surrounding logic.
    oscillator.frequency.value = kind === 'success' ? 660 : kind === 'failure' ? 220 : 440;
    // Calls gain.gain.setValueAtTime with the supplied values.
    gain.gain.setValueAtTime(0.0001, context.currentTime);
    // Calls gain.gain.exponentialRampToValueAtTime with the supplied values.
    gain.gain.exponentialRampToValueAtTime(0.06, context.currentTime + 0.01);
    // Calls gain.gain.exponentialRampToValueAtTime with the supplied values.
    gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.1);
    // Calls oscillator.connect with the supplied values.
    oscillator.connect(gain);
    // Calls gain.connect with the supplied values.
    gain.connect(context.destination);
    // Calls oscillator.start with the supplied values.
    oscillator.start();
    // Calls oscillator.stop with the supplied values.
    oscillator.stop(context.currentTime + 0.11);
    // Calls oscillator.addEventListener with the supplied values.
    oscillator.addEventListener('ended', () => void context.close(), { once: true });
    // Handles a failure from the protected operation.
  } catch {
    // Waits for this asynchronous operation to complete.
    await context.close().catch(() => undefined);
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}
