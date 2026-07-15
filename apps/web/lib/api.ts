'use client';

import { ApiError, MastermindApi, type ApiComponents } from '@mastermind/api-client';
import { useCallback, useMemo } from 'react';
import { useSession } from '@/components/session-provider';

export const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8000';

type Schemas = ApiComponents['schemas'];
export type GameConfig = Schemas['GameConfigSchema'];
export type Attempt = Schemas['AttemptSchema'];
export type ScoreBreakdown = Schemas['ScoreBreakdownSchema'];
export type GameStatus = 'created' | 'active' | 'won' | 'lost' | 'abandoned' | 'expired';
export type Game = Omit<Schemas['GameResponse'], 'status'> & { status: GameStatus };
export type DailyDefinition = Schemas['DailyDefinitionResponse'];
export type Challenge = Schemas['ChallengeResponse'];
export type ChallengeResults = Schemas['ChallengeResultsResponse'];
export type Room = Schemas['RoomResponse'];
export type Leaderboard = Schemas['PaginatedLeaderboard'];
export type Profile = Schemas['ProfileResponse'];
export type Stats = Schemas['StatsResponse'];
export type GameHistory = Schemas['PaginatedGames'];

export { ApiError };

export function useApi() {
  const { getAccessToken } = useSession();
  const client = useMemo(() => new MastermindApi(API_ORIGIN, getAccessToken), [getAccessToken]);
  return useCallback(
    async <T>(path: string, options: RequestInit = {}) => client.request<T>(path, options),
    [client],
  );
}
