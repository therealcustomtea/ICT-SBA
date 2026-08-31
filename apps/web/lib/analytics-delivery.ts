// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { loadPreferences } from './preferences';

// Declares the Mode data shape or implementation.
type Mode = 'solo' | 'daily' | 'practice' | 'pass_and_play' | 'friend_challenge' | 'duel';
// Declares the Difficulty data shape or implementation.
type Difficulty = 'easy' | 'normal' | 'hard' | 'expert' | 'custom';
// Declares the Result data shape or implementation.
type Result = 'won' | 'lost' | 'abandoned' | 'expired' | 'tie';

// Exports this declaration for use by other modules.
export type AnalyticsEventMap = {
  // Defines the game_started field in the surrounding object or type.
  game_started: { mode: Mode; difficulty: Difficulty };
  // Defines the game_completed field in the surrounding object or type.
  game_completed: {
    // Defines the mode field in the surrounding object or type.
    mode: Mode;
    // Defines the result field in the surrounding object or type.
    result: Exclude<Result, 'tie'>;
    // Defines the attemptsUsed field in the surrounding object or type.
    attemptsUsed: number;
    // Defines the ranked field in the surrounding object or type.
    ranked: boolean;
    // Defines the scoreBand field in the surrounding object or type.
    scoreBand: 'zero' | '1-999' | '1000-1499' | '1500+';
    // Closes the expression, call, or declaration started above.
  };
  // Defines the game_abandoned field in the surrounding object or type.
  game_abandoned: { mode: Mode; attemptsUsed: number };
  // Defines the difficulty_selected field in the surrounding object or type.
  difficulty_selected: { difficulty: Difficulty };
  // Defines the daily_completed field in the surrounding object or type.
  daily_completed: {
    // Defines the dailyChallengeId field in the surrounding object or type.
    dailyChallengeId: string;
    // Defines the result field in the surrounding object or type.
    result: Exclude<Result, 'tie'>;
    // Defines the attemptsUsed field in the surrounding object or type.
    attemptsUsed: number;
    // Closes the expression, call, or declaration started above.
  };
  // Defines the friend_challenge_created field in the surrounding object or type.
  friend_challenge_created: { official: boolean; expiryBand: '30_days' };
  // Defines the room_joined field in the surrounding object or type.
  room_joined: {
    // Defines the roomState field in the surrounding object or type.
    roomState: 'waiting' | 'active' | 'completed' | 'expired' | 'terminated';
    // Defines the reconnect field in the surrounding object or type.
    reconnect: boolean;
    // Closes the expression, call, or declaration started above.
  };
  // Defines the duel_completed field in the surrounding object or type.
  duel_completed: { result: Result; attemptsUsed: number; tie: boolean };
  // Defines the validation_error field in the surrounding object or type.
  validation_error: {
    // Defines the validationCategory field in the surrounding object or type.
    validationCategory: 'game_config' | 'guess' | 'challenge' | 'room' | 'profile' | 'auth';
    // Closes the expression, call, or declaration started above.
  };
  // Defines the reconnect field in the surrounding object or type.
  reconnect: { surface: 'game' | 'room' | 'daily' | 'challenge' | 'account'; recovered: boolean };
  // Defines the account_upgraded field in the surrounding object or type.
  account_upgraded: { previousAnonymous: true };
  // Closes the expression, call, or declaration started above.
};

// Declares the Locale data shape or implementation.
type Locale = 'en' | 'zh-Hant';
// Computes and stores API_ORIGIN for subsequent operations.
const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8000';

// Exports this declaration for use by other modules.
export async function deliverProductEvent<K extends keyof AnalyticsEventMap>(
  // Defines the token field in the surrounding object or type.
  token: string | null,
  // Defines the locale field in the surrounding object or type.
  locale: Locale,
  // Defines the eventName field in the surrounding object or type.
  eventName: K,
  // Defines the fields field in the surrounding object or type.
  fields: AnalyticsEventMap[K],
  // Begins the nested block or object completed below.
) {
  // Checks this condition before running the nested branch.
  if (!token || !loadPreferences().analytics) return;
  // Starts an operation whose expected failures are handled below.
  try {
    // Waits for this asynchronous operation to complete.
    await fetch(`${API_ORIGIN}/v1/analytics/events`, {
      // Defines the method field in the surrounding object or type.
      method: 'POST',
      // Defines the cache field in the surrounding object or type.
      cache: 'no-store',
      // Defines the keepalive field in the surrounding object or type.
      keepalive: true,
      // Defines the headers field in the surrounding object or type.
      headers: {
        // Defines the Accept field in the surrounding object or type.
        Accept: 'application/json',
        // Defines the Authorization field in the surrounding object or type.
        Authorization: `Bearer ${token}`,
        // Supplies this item to the surrounding call or collection.
        'Content-Type': 'application/json',
        // Closes the expression, call, or declaration started above.
      },
      // Defines the body field in the surrounding object or type.
      body: JSON.stringify({
        // Defines the clientEventId field in the surrounding object or type.
        clientEventId: crypto.randomUUID(),
        // Supplies this item to the surrounding call or collection.
        eventName,
        // Defines the consent field in the surrounding object or type.
        consent: true,
        // Defines the consentVersion field in the surrounding object or type.
        consentVersion: 'privacy-v1',
        // Supplies this item to the surrounding call or collection.
        locale,
        // Supplies this item to the surrounding call or collection.
        ...fields,
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    });
    // Handles a failure from the protected operation.
  } catch {
    // Analytics never blocks or changes the product flow.
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function gameDifficulty(value: string | null): Difficulty {
  // Returns this result to the caller and ends the current function.
  return value === 'easy' || value === 'normal' || value === 'hard' || value === 'expert'
    ? // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      value
    : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      'custom';
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function gameMode(value: string): Mode {
  // Returns this result to the caller and ends the current function.
  return value === 'daily' ||
    // Provides the value value to the surrounding call or element.
    value === 'practice' ||
    // Provides the value value to the surrounding call or element.
    value === 'pass_and_play' ||
    // Provides the value value to the surrounding call or element.
    value === 'friend_challenge' ||
    // Provides the value value to the surrounding call or element.
    value === 'duel'
    ? // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      value
    : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      'solo';
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function scoreBand(score: number | null): AnalyticsEventMap['game_completed']['scoreBand'] {
  // Checks this condition before running the nested branch.
  if (!score || score <= 0) return 'zero';
  // Checks this condition before running the nested branch.
  if (score < 1000) return '1-999';
  // Checks this condition before running the nested branch.
  if (score < 1500) return '1000-1499';
  // Returns this result to the caller and ends the current function.
  return '1500+';
  // Closes the expression, call, or declaration started above.
}
