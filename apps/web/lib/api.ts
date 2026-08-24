// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { ApiError, MastermindApi, type ApiComponents } from '@mastermind/api-client';
// Imports the dependency used by this module.
import { useCallback, useMemo } from 'react';
// Imports the dependency used by this module.
import { useSession } from '@/components/session-provider';

// Exports this declaration for use by other modules.
export const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8000';

// Declares the Schemas data shape or implementation.
type Schemas = ApiComponents['schemas'];
// Exports this declaration for use by other modules.
export type GameConfig = Schemas['GameConfigSchema'];
// Exports this declaration for use by other modules.
export type Attempt = Schemas['AttemptSchema'];
// Exports this declaration for use by other modules.
export type ScoreBreakdown = Schemas['ScoreBreakdownSchema'];
// Exports this declaration for use by other modules.
export type GameStatus = 'created' | 'active' | 'won' | 'lost' | 'abandoned' | 'expired';
// Exports this declaration for use by other modules.
export type Game = Omit<Schemas['GameResponse'], 'status'> & { status: GameStatus };
// Exports this declaration for use by other modules.
export type DailyDefinition = Schemas['DailyDefinitionResponse'];
// Exports this declaration for use by other modules.
export type Challenge = Schemas['ChallengeResponse'];
// Exports this declaration for use by other modules.
export type ChallengeResults = Schemas['ChallengeResultsResponse'];
// Exports this declaration for use by other modules.
export type Room = Schemas['RoomResponse'];
// Exports this declaration for use by other modules.
export type Leaderboard = Schemas['PaginatedLeaderboard'];
// Exports this declaration for use by other modules.
export type Profile = Schemas['ProfileResponse'];
// Exports this declaration for use by other modules.
export type Stats = Schemas['StatsResponse'];
// Exports this declaration for use by other modules.
export type GameHistory = Schemas['PaginatedGames'];

// Exports this declaration for use by other modules.
export { ApiError };

// Exports this declaration for use by other modules.
export function useApi() {
  // Executes this line as the next step in the surrounding logic.
  const { getAccessToken } = useSession();
  // Computes and stores client for subsequent operations.
  const client = useMemo(() => new MastermindApi(API_ORIGIN, getAccessToken), [getAccessToken]);
  // Returns this result to the caller and ends the current function.
  return useCallback(
    // Supplies this item to the surrounding call or collection.
    async <T>(path: string, options: RequestInit = {}) => client.request<T>(path, options),
    // Supplies this item to the surrounding call or collection.
    [client],
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
