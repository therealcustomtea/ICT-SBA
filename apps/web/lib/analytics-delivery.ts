'use client';

import { loadPreferences } from './preferences';

type Mode = 'solo' | 'daily' | 'practice' | 'pass_and_play' | 'friend_challenge' | 'duel';
type Difficulty = 'easy' | 'normal' | 'hard' | 'expert' | 'custom';
type Result = 'won' | 'lost' | 'abandoned' | 'expired' | 'tie';

export type AnalyticsEventMap = {
  game_started: { mode: Mode; difficulty: Difficulty };
  game_completed: {
    mode: Mode;
    result: Exclude<Result, 'tie'>;
    attemptsUsed: number;
    ranked: boolean;
    scoreBand: 'zero' | '1-999' | '1000-1499' | '1500+';
  };
  game_abandoned: { mode: Mode; attemptsUsed: number };
  difficulty_selected: { difficulty: Difficulty };
  daily_completed: {
    dailyChallengeId: string;
    result: Exclude<Result, 'tie'>;
    attemptsUsed: number;
  };
  friend_challenge_created: { official: boolean; expiryBand: '30_days' };
  room_joined: {
    roomState: 'waiting' | 'active' | 'completed' | 'expired' | 'terminated';
    reconnect: boolean;
  };
  duel_completed: { result: Result; attemptsUsed: number; tie: boolean };
  validation_error: {
    validationCategory: 'game_config' | 'guess' | 'challenge' | 'room' | 'profile' | 'auth';
  };
  reconnect: { surface: 'game' | 'room' | 'daily' | 'challenge' | 'account'; recovered: boolean };
  account_upgraded: { previousAnonymous: true };
};

type Locale = 'en' | 'zh-Hant';
const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8000';

export async function deliverProductEvent<K extends keyof AnalyticsEventMap>(
  token: string | null,
  locale: Locale,
  eventName: K,
  fields: AnalyticsEventMap[K],
) {
  if (!token || !loadPreferences().analytics) return;
  try {
    await fetch(`${API_ORIGIN}/v1/analytics/events`, {
      method: 'POST',
      cache: 'no-store',
      keepalive: true,
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        clientEventId: crypto.randomUUID(),
        eventName,
        consent: true,
        consentVersion: 'privacy-v1',
        locale,
        ...fields,
      }),
    });
  } catch {
    // Analytics never blocks or changes the product flow.
  }
}

export function gameDifficulty(value: string | null): Difficulty {
  return value === 'easy' || value === 'normal' || value === 'hard' || value === 'expert'
    ? value
    : 'custom';
}

export function gameMode(value: string): Mode {
  return value === 'daily' ||
    value === 'practice' ||
    value === 'pass_and_play' ||
    value === 'friend_challenge' ||
    value === 'duel'
    ? value
    : 'solo';
}

export function scoreBand(score: number | null): AnalyticsEventMap['game_completed']['scoreBand'] {
  if (!score || score <= 0) return 'zero';
  if (score < 1000) return '1-999';
  if (score < 1500) return '1000-1499';
  return '1500+';
}
