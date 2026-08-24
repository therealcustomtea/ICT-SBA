// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { Check, CircleX, Eraser, Flag, RotateCcw, Share2, Wifi, WifiOff } from 'lucide-react';
// Imports the dependency used by this module.
import { useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { ApiError, type Game, type Leaderboard, type Stats, useApi } from '@/lib/api';
// Imports the dependency used by this module.
import { gameDifficulty, gameMode, scoreBand } from '@/lib/analytics-delivery';
// Imports the dependency used by this module.
import { playGameSound } from '@/lib/preferences';
// Imports the dependency used by this module.
import { useProductAnalytics } from '@/lib/use-product-analytics';

// Computes and stores colorSymbols for subsequent operations.
const colorSymbols: Record<string, string> = {
  // Defines the R field in the surrounding object or type.
  R: '●',
  // Defines the B field in the surrounding object or type.
  B: '◆',
  // Defines the G field in the surrounding object or type.
  G: '▲',
  // Defines the Y field in the surrounding object or type.
  Y: '■',
  // Defines the W field in the surrounding object or type.
  W: '○',
  // Defines the K field in the surrounding object or type.
  K: '✚',
  // Defines the O field in the surrounding object or type.
  O: '⬟',
  // Defines the P field in the surrounding object or type.
  P: '✦',
  // Defines the C field in the surrounding object or type.
  C: '⬢',
  // Defines the M field in the surrounding object or type.
  M: '♥',
  // Closes the expression, call, or declaration started above.
};

// Declares the GameBoardProps data shape or implementation.
type GameBoardProps = {
  // Defines the title field in the surrounding object or type.
  title: string;
  // Executes this line as the next step in the surrounding logic.
  intro?: string;
  // Executes this line as the next step in the surrounding logic.
  startEndpoint?: string;
  // Executes this line as the next step in the surrounding logic.
  startBody?: Record<string, unknown>;
  // Executes this line as the next step in the surrounding logic.
  replayBody?: Record<string, unknown>;
  // Executes this line as the next step in the surrounding logic.
  replayLabel?: string;
  // Executes this line as the next step in the surrounding logic.
  dailyChallengeId?: string;
  // Executes this line as the next step in the surrounding logic.
  initialGameId?: string;
  // Closes the expression, call, or declaration started above.
};

// Declares the ResultDetails data shape or implementation.
type ResultDetails = { personalBest: boolean; rank: number | null; newAchievements: string[] };
// Declares the PendingAttempt data shape or implementation.
type PendingAttempt = {
  // Defines the gameId field in the surrounding object or type.
  gameId: string;
  // Defines the guess field in the surrounding object or type.
  guess: string[];
  // Defines the idempotencyKey field in the surrounding object or type.
  idempotencyKey: string;
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: number;
  // Closes the expression, call, or declaration started above.
};
// Computes and stores achievementTranslationKeys for subsequent operations.
const achievementTranslationKeys: Record<string, string> = {
  // Defines the first_break field in the surrounding object or type.
  first_break: 'firstBreak',
  // Defines the one_shot field in the surrounding object or type.
  one_shot: 'oneShot',
  // Defines the no_waste field in the surrounding object or type.
  no_waste: 'noWaste',
  // Defines the daily_debut field in the surrounding object or type.
  daily_debut: 'dailyDebut',
  // Defines the logic_week field in the surrounding object or type.
  logic_week: 'logicWeek',
  // Defines the hard_mode field in the surrounding object or type.
  hard_mode: 'hardMode',
  // Defines the expert_breaker field in the surrounding object or type.
  expert_breaker: 'expertBreaker',
  // Defines the challenger field in the surrounding object or type.
  challenger: 'challenger',
  // Defines the duelist field in the surrounding object or type.
  duelist: 'duelist',
  // Defines the comeback field in the surrounding object or type.
  comeback: 'comeback',
  // Closes the expression, call, or declaration started above.
};
// Computes and stores rowStorageKey for subsequent operations.
const rowStorageKey = (gameId: string) => `cipherboard:row:${gameId}`;
// Computes and stores pendingAttemptStorageKey for subsequent operations.
const pendingAttemptStorageKey = (gameId: string) => `cipherboard:pending-attempt:${gameId}`;
// Computes and stores dailyGameStorageKey for subsequent operations.
const dailyGameStorageKey = (dailyChallengeId: string) =>
  // Executes this line as the next step in the surrounding logic.
  `cipherboard:daily:${dailyChallengeId}:active-game`;

// Defines the loadPendingAttempt function and its callable behavior.
function loadPendingAttempt(gameId: string): PendingAttempt | null {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores pending for subsequent operations.
    const pending = JSON.parse(
      // Calls localStorage.getItem with the supplied values.
      localStorage.getItem(pendingAttemptStorageKey(gameId)) ?? 'null',
      // Executes this line as the next step in the surrounding logic.
    ) as Partial<PendingAttempt> | null;
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      !pending ||
      // Executes this line as the next step in the surrounding logic.
      pending.gameId !== gameId ||
      // Executes this line as the next step in the surrounding logic.
      !Array.isArray(pending.guess) ||
      // Executes this line as the next step in the surrounding logic.
      typeof pending.idempotencyKey !== 'string' ||
      // Executes this line as the next step in the surrounding logic.
      typeof pending.attemptsUsed !== 'number'
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return null;
    // Returns this result to the caller and ends the current function.
    return pending as PendingAttempt;
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return null;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function GameBoard({
  // Supplies this item to the surrounding call or collection.
  title,
  // Supplies this item to the surrounding call or collection.
  intro,
  // Provides the startEndpoint value to the surrounding call or element.
  startEndpoint = '/v1/games',
  // Provides the startBody value to the surrounding call or element.
  startBody = { mode: 'solo', difficulty: 'normal' },
  // Supplies this item to the surrounding call or collection.
  replayBody,
  // Supplies this item to the surrounding call or collection.
  replayLabel,
  // Supplies this item to the surrounding call or collection.
  dailyChallengeId,
  // Supplies this item to the surrounding call or collection.
  initialGameId,
  // Begins the nested block or object completed below.
}: GameBoardProps) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Game');
  // Computes and stores tr for subsequent operations.
  const tr = useTranslations('Result');
  // Computes and stores ta for subsequent operations.
  const ta = useTranslations('Achievements');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores analytics for subsequent operations.
  const analytics = useProductAnalytics();
  // Executes this line as the next step in the surrounding logic.
  const [game, setGame] = useState<Game | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [row, setRow] = useState<string[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [selectedSlot, setSelectedSlot] = useState(0);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'idle' | 'loading' | 'ready' | 'submitting' | 'error'>(
    // Supplies this item to the surrounding call or collection.
    initialGameId || dailyChallengeId ? 'loading' : 'idle',
    // Closes the expression, call, or declaration started above.
  );
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [online, setOnline] = useState(true);
  // Executes this line as the next step in the surrounding logic.
  const [syncing, setSyncing] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [syncRequired, setSyncRequired] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [announcement, setAnnouncement] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [elapsed, setElapsed] = useState(0);
  // Executes this line as the next step in the surrounding logic.
  const [resultDetails, setResultDetails] = useState<ResultDetails | null>(null);
  // Computes and stores slotRefs for subsequent operations.
  const slotRefs = useRef<Array<HTMLButtonElement | null>>([]);
  // Computes and stores resultRef for subsequent operations.
  const resultRef = useRef<HTMLDivElement | null>(null);
  // Computes and stores achievementBaselineRef for subsequent operations.
  const achievementBaselineRef = useRef<Set<string> | null>(null);
  // Computes and stores achievementBaselineLoadingRef for subsequent operations.
  const achievementBaselineLoadingRef = useRef(false);
  // Computes and stores gameRef for subsequent operations.
  const gameRef = useRef<Game | null>(null);
  // Computes and stores rowRef for subsequent operations.
  const rowRef = useRef<string[]>([]);

  // Computes and stores hydrateGame for subsequent operations.
  const hydrateGame = useCallback(
    // Begins the nested block or object completed below.
    (nextGame: Game) => {
      // Calls setResultDetails with the supplied values.
      setResultDetails(null);
      // Executes this line as the next step in the surrounding logic.
      gameRef.current = nextGame;
      // Calls setGame with the supplied values.
      setGame(nextGame);
      // Checks this condition before running the nested branch.
      if (dailyChallengeId) {
        // Computes and stores storageKey for subsequent operations.
        const storageKey = dailyGameStorageKey(dailyChallengeId);
        // Checks this condition before running the nested branch.
        if (nextGame.mode === 'daily' && nextGame.status === 'active')
          // Calls localStorage.setItem with the supplied values.
          localStorage.setItem(storageKey, nextGame.id);
        // Executes this line as the next step in the surrounding logic.
        else localStorage.removeItem(storageKey);
        // Closes the expression, call, or declaration started above.
      }
      // Checks this condition before running the nested branch.
      if (
        // Executes this line as the next step in the surrounding logic.
        nextGame.status === 'active' &&
        // Executes this line as the next step in the surrounding logic.
        achievementBaselineRef.current === null &&
        // Executes this line as the next step in the surrounding logic.
        !achievementBaselineLoadingRef.current
        // Begins the nested block or object completed below.
      ) {
        // Executes this line as the next step in the surrounding logic.
        achievementBaselineLoadingRef.current = true;
        // Executes this line as the next step in the surrounding logic.
        void api<Stats>('/v1/me/stats')
          // Begins the nested block or object completed below.
          .then((stats) => {
            // Executes this line as the next step in the surrounding logic.
            achievementBaselineRef.current = new Set(stats.achievements ?? []);
            // Closes the expression, call, or declaration started above.
          })
          // Executes this line as the next step in the surrounding logic.
          .catch(() => undefined)
          // Begins the nested block or object completed below.
          .finally(() => {
            // Executes this line as the next step in the surrounding logic.
            achievementBaselineLoadingRef.current = false;
            // Closes the expression, call, or declaration started above.
          });
        // Closes the expression, call, or declaration started above.
      }
      // Calls setRow with the supplied values.
      setRow((current) => {
        // Computes and stores storageKey for subsequent operations.
        const storageKey = rowStorageKey(nextGame.id);
        // Checks this condition before running the nested branch.
        if (current.length > 0) return current;
        // Starts an operation whose expected failures are handled below.
        try {
          // Computes and stores stored for subsequent operations.
          const stored = JSON.parse(localStorage.getItem(storageKey) ?? '[]') as string[];
          // Returns this result to the caller and ends the current function.
          return (
            stored
              // Executes this line as the next step in the surrounding logic.
              .filter((color) => nextGame.config.colours.includes(color))
              // Executes this line as the next step in the surrounding logic.
              .slice(0, nextGame.config.codeLength)
          );
          // Handles a failure from the protected operation.
        } catch {
          // Returns this result to the caller and ends the current function.
          return [];
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      });
      // Calls setState with the supplied values.
      setState('ready');
      // Closes the expression, call, or declaration started above.
    },
    // Supplies this item to the surrounding call or collection.
    [api, dailyChallengeId],
    // Closes the expression, call, or declaration started above.
  );

  // Computes and stores resyncGame for subsequent operations.
  const resyncGame = useCallback(async () => {
    // Computes and stores currentGame for subsequent operations.
    const currentGame = gameRef.current;
    // Checks this condition before running the nested branch.
    if (!currentGame || currentGame.status !== 'active' || !navigator.onLine) return;
    // Calls setSyncRequired with the supplied values.
    setSyncRequired(true);
    // Calls setSyncing with the supplied values.
    setSyncing(true);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores nextGame for subsequent operations.
      const nextGame = await api<Game>(`/v1/games/${encodeURIComponent(currentGame.id)}`);
      // Computes and stores pending for subsequent operations.
      const pending = loadPendingAttempt(currentGame.id);
      // Checks this condition before running the nested branch.
      if (pending && nextGame.attemptsUsed > pending.attemptsUsed) {
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(pendingAttemptStorageKey(currentGame.id));
        // Checks this condition before running the nested branch.
        if (JSON.stringify(rowRef.current) === JSON.stringify(pending.guess)) {
          // Executes this line as the next step in the surrounding logic.
          rowRef.current = [];
          // Calls setRow with the supplied values.
          setRow([]);
          // Calls localStorage.removeItem with the supplied values.
          localStorage.removeItem(rowStorageKey(currentGame.id));
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      }
      // Calls hydrateGame with the supplied values.
      hydrateGame(nextGame);
      // Calls setError with the supplied values.
      setError(null);
      // Calls setSyncRequired with the supplied values.
      setSyncRequired(false);
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('restoreError'));
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setSyncing with the supplied values.
      setSyncing(false);
      // Closes the expression, call, or declaration started above.
    }
    // Executes this line as the next step in the surrounding logic.
  }, [api, hydrateGame, t]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores handleOnline for subsequent operations.
    const handleOnline = () => {
      // Calls setOnline with the supplied values.
      setOnline(true);
      // Executes this line as the next step in the surrounding logic.
      void resyncGame();
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores handleOffline for subsequent operations.
    const handleOffline = () => {
      // Calls setOnline with the supplied values.
      setOnline(false);
      // Calls setSyncRequired with the supplied values.
      setSyncRequired(true);
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores handleFocus for subsequent operations.
    const handleFocus = () => void resyncGame();
    // Computes and stores handleVisibility for subsequent operations.
    const handleVisibility = () => {
      // Checks this condition before running the nested branch.
      if (document.visibilityState === 'visible') void resyncGame();
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores frame for subsequent operations.
    const frame = requestAnimationFrame(() => setOnline(navigator.onLine));
    // Calls addEventListener with the supplied values.
    addEventListener('online', handleOnline);
    // Calls addEventListener with the supplied values.
    addEventListener('offline', handleOffline);
    // Calls addEventListener with the supplied values.
    addEventListener('focus', handleFocus);
    // Calls document.addEventListener with the supplied values.
    document.addEventListener('visibilitychange', handleVisibility);
    // Returns this result to the caller and ends the current function.
    return () => {
      // Calls removeEventListener with the supplied values.
      removeEventListener('online', handleOnline);
      // Calls removeEventListener with the supplied values.
      removeEventListener('offline', handleOffline);
      // Calls removeEventListener with the supplied values.
      removeEventListener('focus', handleFocus);
      // Calls document.removeEventListener with the supplied values.
      document.removeEventListener('visibilitychange', handleVisibility);
      // Calls cancelAnimationFrame with the supplied values.
      cancelAnimationFrame(frame);
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [resyncGame]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!initialGameId) return;
    // Executes this line as the next step in the surrounding logic.
    api<Game>(`/v1/games/${encodeURIComponent(initialGameId)}`)
      // Executes this line as the next step in the surrounding logic.
      .then(hydrateGame)
      // Begins the nested block or object completed below.
      .catch(() => {
        // Calls setError with the supplied values.
        setError(t('genericError'));
        // Calls setState with the supplied values.
        setState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Executes this line as the next step in the surrounding logic.
  }, [api, hydrateGame, initialGameId, t]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (initialGameId || !dailyChallengeId) return;
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores restoreStoredDailyGame for subsequent operations.
    const restoreStoredDailyGame = async () => {
      // Waits for this asynchronous operation to complete.
      await Promise.resolve();
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Computes and stores storageKey for subsequent operations.
      const storageKey = dailyGameStorageKey(dailyChallengeId);
      // Computes and stores storedGameId for subsequent operations.
      const storedGameId = localStorage.getItem(storageKey);
      // Checks this condition before running the nested branch.
      if (!storedGameId || !/^[A-Za-z0-9_-]{8,128}$/.test(storedGameId)) {
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(storageKey);
        // Calls setState with the supplied values.
        setState('idle');
        // Returns this result to the caller and ends the current function.
        return;
        // Closes the expression, call, or declaration started above.
      }

      // Calls setState with the supplied values.
      setState('loading');
      // Starts an operation whose expected failures are handled below.
      try {
        // Computes and stores restoredGame for subsequent operations.
        const restoredGame = await api<Game>(`/v1/games/${encodeURIComponent(storedGameId)}`);
        // Checks this condition before running the nested branch.
        if (!active) return;
        // Checks this condition before running the nested branch.
        if (restoredGame.mode !== 'daily' || restoredGame.status !== 'active') {
          // Calls localStorage.removeItem with the supplied values.
          localStorage.removeItem(storageKey);
          // Calls setError with the supplied values.
          setError(null);
          // Calls setState with the supplied values.
          setState('idle');
          // Returns this result to the caller and ends the current function.
          return;
          // Closes the expression, call, or declaration started above.
        }
        // Calls hydrateGame with the supplied values.
        hydrateGame(restoredGame);
        // Handles a failure from the protected operation.
      } catch {
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(storageKey);
        // Checks this condition before running the nested branch.
        if (!active) return;
        // Executes this line as the next step in the surrounding logic.
        gameRef.current = null;
        // Calls setGame with the supplied values.
        setGame(null);
        // Calls setError with the supplied values.
        setError(null);
        // Calls setState with the supplied values.
        setState('idle');
        // Closes the expression, call, or declaration started above.
      }
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
    void restoreStoredDailyGame();
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, dailyChallengeId, hydrateGame, initialGameId]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!game || game.status !== 'active') return;
    // Computes and stores update for subsequent operations.
    const update = () =>
      // Calls setElapsed with the supplied values.
      setElapsed(Math.max(0, Math.floor((Date.now() - Date.parse(game.startedAt)) / 1000)));
    // Calls update with the supplied values.
    update();
    // Computes and stores timer for subsequent operations.
    const timer = setInterval(update, 1000);
    // Returns this result to the caller and ends the current function.
    return () => clearInterval(timer);
    // Executes this line as the next step in the surrounding logic.
  }, [game]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!game) return;
    // Executes this line as the next step in the surrounding logic.
    rowRef.current = row;
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(rowStorageKey(game.id), JSON.stringify(row));
    // Executes this line as the next step in the surrounding logic.
  }, [game, row]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!game || !['won', 'lost', 'abandoned', 'expired'].includes(game.status)) return;
    // Computes and stores frame for subsequent operations.
    const frame = requestAnimationFrame(() => resultRef.current?.focus());
    // Returns this result to the caller and ends the current function.
    return () => cancelAnimationFrame(frame);
    // Executes this line as the next step in the surrounding logic.
  }, [game]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!game || !['won', 'lost'].includes(game.status)) return;
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores loadDetails for subsequent operations.
    const loadDetails = async () => {
      // Computes and stores leaderboardEndpoint for subsequent operations.
      const leaderboardEndpoint =
        // Executes this line as the next step in the surrounding logic.
        game.mode === 'daily'
          ? // Executes this line as the next step in the surrounding logic.
            '/v1/daily/leaderboard?page=1&page_size=1'
          : // Executes this line as the next step in the surrounding logic.
            game.ranked && game.difficulty
            ? // Executes this line as the next step in the surrounding logic.
              `/v1/leaderboards?period=all-time&difficulty=${encodeURIComponent(game.difficulty)}&page=1&page_size=1`
            : // Executes this line as the next step in the surrounding logic.
              null;
      // Executes this line as the next step in the surrounding logic.
      const [statsResult, leaderboardResult] = await Promise.allSettled([
        // Supplies this item to the surrounding call or collection.
        api<Stats>('/v1/me/stats'),
        // Supplies this item to the surrounding call or collection.
        leaderboardEndpoint ? api<Leaderboard>(leaderboardEndpoint) : Promise.resolve(null),
        // Closes the expression, call, or declaration started above.
      ]);
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Computes and stores stats for subsequent operations.
      const stats = statsResult.status === 'fulfilled' ? statsResult.value : null;
      // Computes and stores leaderboard for subsequent operations.
      const leaderboard = leaderboardResult.status === 'fulfilled' ? leaderboardResult.value : null;
      // Computes and stores bestScores for subsequent operations.
      const bestScores = stats?.bestScoreByDifficulty ?? {};
      // Calls setResultDetails with the supplied values.
      setResultDetails({
        // Defines the personalBest field in the surrounding object or type.
        personalBest: Boolean(
          // Supplies this item to the surrounding call or collection.
          game.score !== null && game.difficulty && bestScores[game.difficulty] === game.score,
          // Closes the expression, call, or declaration started above.
        ),
        // Defines the rank field in the surrounding object or type.
        rank: leaderboard?.currentUserRank ?? null,
        // Defines the newAchievements field in the surrounding object or type.
        newAchievements:
          // Executes this line as the next step in the surrounding logic.
          achievementBaselineRef.current && stats
            ? // Executes this line as the next step in the surrounding logic.
              (stats.achievements ?? []).filter(
                // Supplies this item to the surrounding call or collection.
                (achievement) => !achievementBaselineRef.current?.has(achievement),
                // Closes the expression, call, or declaration started above.
              )
            : // Supplies this item to the surrounding call or collection.
              [],
        // Closes the expression, call, or declaration started above.
      });
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
    void loadDetails();
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, game]);

  // Computes and stores handleStart for subsequent operations.
  const handleStart = async () => {
    // Executes this line as the next step in the surrounding logic.
    achievementBaselineRef.current = null;
    // Executes this line as the next step in the surrounding logic.
    achievementBaselineLoadingRef.current = false;
    // Calls setState with the supplied values.
    setState('loading');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores nextGame for subsequent operations.
      const nextGame = await api<Game>(startEndpoint, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify(startBody),
        // Closes the expression, call, or declaration started above.
      });
      // Calls hydrateGame with the supplied values.
      hydrateGame(nextGame);
      // Calls analytics with the supplied values.
      analytics('game_started', {
        // Defines the mode field in the surrounding object or type.
        mode: gameMode(nextGame.mode),
        // Defines the difficulty field in the surrounding object or type.
        difficulty: gameDifficulty(nextGame.difficulty),
        // Closes the expression, call, or declaration started above.
      });
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('genericError'));
      // Calls setState with the supplied values.
      setState('error');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleColor for subsequent operations.
  const handleColor = (color: string) => {
    // Checks this condition before running the nested branch.
    if (!game) return;
    // Calls setRow with the supplied values.
    setRow((current) => {
      // Computes and stores next for subsequent operations.
      const next = [...current];
      // Executes this line as the next step in the surrounding logic.
      next[selectedSlot] = color;
      // Returns this result to the caller and ends the current function.
      return next.slice(0, game.config.codeLength);
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores nextSlot for subsequent operations.
    const nextSlot = Math.min(selectedSlot + 1, game.config.codeLength - 1);
    // Calls setSelectedSlot with the supplied values.
    setSelectedSlot(nextSlot);
    // Executes this line as the next step in the surrounding logic.
    slotRefs.current[nextSlot]?.focus();
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleClear for subsequent operations.
  const handleClear = () => {
    // Calls setRow with the supplied values.
    setRow([]);
    // Calls setSelectedSlot with the supplied values.
    setSelectedSlot(0);
    // Executes this line as the next step in the surrounding logic.
    slotRefs.current[0]?.focus();
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleSubmit for subsequent operations.
  const handleSubmit = async () => {
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      !game ||
      // Executes this line as the next step in the surrounding logic.
      !Array.from({ length: game.config.codeLength }, (_, index) => Boolean(row[index])).every(
        // Supplies this item to the surrounding call or collection.
        Boolean,
        // Executes this line as the next step in the surrounding logic.
      ) ||
      // Executes this line as the next step in the surrounding logic.
      !online ||
      // Executes this line as the next step in the surrounding logic.
      syncing ||
      // Executes this line as the next step in the surrounding logic.
      syncRequired
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return;
    // Computes and stores guess for subsequent operations.
    const guess = row.slice(0, game.config.codeLength);
    // Computes and stores existingPending for subsequent operations.
    const existingPending = loadPendingAttempt(game.id);
    // Computes and stores pending for subsequent operations.
    const pending =
      // Executes this line as the next step in the surrounding logic.
      existingPending &&
      // Executes this line as the next step in the surrounding logic.
      existingPending.attemptsUsed === game.attemptsUsed &&
      // Calls JSON.stringify with the supplied values.
      JSON.stringify(existingPending.guess) === JSON.stringify(guess)
        ? // Executes this line as the next step in the surrounding logic.
          existingPending
        : // Begins the nested block or object completed below.
          {
            // Defines the gameId field in the surrounding object or type.
            gameId: game.id,
            // Supplies this item to the surrounding call or collection.
            guess,
            // Defines the idempotencyKey field in the surrounding object or type.
            idempotencyKey: crypto.randomUUID(),
            // Defines the attemptsUsed field in the surrounding object or type.
            attemptsUsed: game.attemptsUsed,
            // Closes the expression, call, or declaration started above.
          };
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(pendingAttemptStorageKey(game.id), JSON.stringify(pending));
    // Calls setState with the supplied values.
    setState('submitting');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores nextGame for subsequent operations.
      const nextGame = await api<Game>(`/v1/games/${encodeURIComponent(game.id)}/attempts`, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ guess: pending.guess, idempotencyKey: pending.idempotencyKey }),
        // Closes the expression, call, or declaration started above.
      });
      // Computes and stores last for subsequent operations.
      const last = nextGame.attempts.at(-1);
      // Checks this condition before running the nested branch.
      if (last)
        // Calls setAnnouncement with the supplied values.
        setAnnouncement(
          // Calls t with the supplied values.
          t('attemptAnnouncement', {
            // Defines the number field in the surrounding object or type.
            number: last.number,
            // Defines the black field in the surrounding object or type.
            black: last.feedback.black,
            // Defines the white field in the surrounding object or type.
            white: last.feedback.white,
            // Defines the remaining field in the surrounding object or type.
            remaining: nextGame.attemptsRemaining,
            // Closes the expression, call, or declaration started above.
          }),
          // Closes the expression, call, or declaration started above.
        );
      // Calls localStorage.removeItem with the supplied values.
      localStorage.removeItem(rowStorageKey(game.id));
      // Calls localStorage.removeItem with the supplied values.
      localStorage.removeItem(pendingAttemptStorageKey(game.id));
      // Executes this line as the next step in the surrounding logic.
      rowRef.current = [];
      // Calls setRow with the supplied values.
      setRow([]);
      // Calls setSelectedSlot with the supplied values.
      setSelectedSlot(0);
      // Calls hydrateGame with the supplied values.
      hydrateGame(nextGame);
      // Checks this condition before running the nested branch.
      if (nextGame.status === 'won') {
        // Executes this line as the next step in the surrounding logic.
        void playGameSound('success');
        // Calls analytics with the supplied values.
        analytics('game_completed', {
          // Defines the mode field in the surrounding object or type.
          mode: gameMode(nextGame.mode),
          // Defines the result field in the surrounding object or type.
          result: nextGame.status,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: nextGame.attemptsUsed,
          // Defines the ranked field in the surrounding object or type.
          ranked: nextGame.ranked,
          // Defines the scoreBand field in the surrounding object or type.
          scoreBand: scoreBand(nextGame.score),
          // Closes the expression, call, or declaration started above.
        });
        // Checks this condition before running the nested branch.
        if (nextGame.mode === 'daily' && dailyChallengeId)
          // Calls analytics with the supplied values.
          analytics('daily_completed', {
            // Supplies this item to the surrounding call or collection.
            dailyChallengeId,
            // Defines the result field in the surrounding object or type.
            result: nextGame.status,
            // Defines the attemptsUsed field in the surrounding object or type.
            attemptsUsed: nextGame.attemptsUsed,
            // Closes the expression, call, or declaration started above.
          });
        // Checks this alternative after the earlier branch failed.
      } else if (nextGame.status === 'lost') {
        // Executes this line as the next step in the surrounding logic.
        void playGameSound('failure');
        // Calls analytics with the supplied values.
        analytics('game_completed', {
          // Defines the mode field in the surrounding object or type.
          mode: gameMode(nextGame.mode),
          // Defines the result field in the surrounding object or type.
          result: nextGame.status,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: nextGame.attemptsUsed,
          // Defines the ranked field in the surrounding object or type.
          ranked: nextGame.ranked,
          // Defines the scoreBand field in the surrounding object or type.
          scoreBand: scoreBand(nextGame.score),
          // Closes the expression, call, or declaration started above.
        });
        // Checks this condition before running the nested branch.
        if (nextGame.mode === 'daily' && dailyChallengeId)
          // Calls analytics with the supplied values.
          analytics('daily_completed', {
            // Supplies this item to the surrounding call or collection.
            dailyChallengeId,
            // Defines the result field in the surrounding object or type.
            result: nextGame.status,
            // Defines the attemptsUsed field in the surrounding object or type.
            attemptsUsed: nextGame.attemptsUsed,
            // Closes the expression, call, or declaration started above.
          });
        // Handles the remaining unmatched case.
      } else {
        // Executes this line as the next step in the surrounding logic.
        void playGameSound('feedback');
        // Closes the expression, call, or declaration started above.
      }
      // Calls requestAnimationFrame with the supplied values.
      requestAnimationFrame(() => slotRefs.current[0]?.focus());
      // Handles a failure from the protected operation.
    } catch (caught) {
      // Checks this condition before running the nested branch.
      if (
        // Executes this line as the next step in the surrounding logic.
        caught instanceof ApiError &&
        // Executes this line as the next step in the surrounding logic.
        caught.status === 422 &&
        // Executes this line as the next step in the surrounding logic.
        caught.body.code === 'DUPLICATES_NOT_ALLOWED'
        // Begins the nested block or object completed below.
      ) {
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(pendingAttemptStorageKey(game.id));
        // Calls setError with the supplied values.
        setError(t('duplicatesNotAllowed'));
        // Calls setState with the supplied values.
        setState('ready');
        // Calls analytics with the supplied values.
        analytics('validation_error', { validationCategory: 'guess' });
        // Returns this result to the caller and ends the current function.
        return;
        // Closes the expression, call, or declaration started above.
      }
      // Calls setError with the supplied values.
      setError(t('genericError'));
      // Calls setSyncRequired with the supplied values.
      setSyncRequired(true);
      // Calls setState with the supplied values.
      setState('ready');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleAbandon for subsequent operations.
  const handleAbandon = async () => {
    // Checks this condition before running the nested branch.
    if (!game || !confirm(t('confirmAbandon'))) return;
    // Calls setState with the supplied values.
    setState('submitting');
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores abandoned for subsequent operations.
      const abandoned = await api<Game>(`/v1/games/${encodeURIComponent(game.id)}/abandon`, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Closes the expression, call, or declaration started above.
      });
      // Calls hydrateGame with the supplied values.
      hydrateGame(abandoned);
      // Calls analytics with the supplied values.
      analytics('game_abandoned', {
        // Defines the mode field in the surrounding object or type.
        mode: gameMode(abandoned.mode),
        // Defines the attemptsUsed field in the surrounding object or type.
        attemptsUsed: abandoned.attemptsUsed,
        // Closes the expression, call, or declaration started above.
      });
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('genericError'));
      // Calls setState with the supplied values.
      setState('ready');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores shareText for subsequent operations.
  const shareText = useMemo(() => {
    // Checks this condition before running the nested branch.
    if (!game || !['won', 'lost'].includes(game.status)) return '';
    // Computes and stores header for subsequent operations.
    const header = `${t('shareTitle')}\n${game.status === 'won' ? t('shareSolved', { used: game.attemptsUsed, max: game.maxAttempts }) : t('shareNotSolved')}`;
    // Computes and stores rows for subsequent operations.
    const rows = game.attempts.map(
      // Supplies this item to the surrounding call or collection.
      (attempt) => `${'⬛'.repeat(attempt.feedback.black)}${'⬜'.repeat(attempt.feedback.white)}`,
      // Closes the expression, call, or declaration started above.
    );
    // Returns this result to the caller and ends the current function.
    return [
      // Supplies this item to the surrounding call or collection.
      header,
      // Supplies this item to the surrounding call or collection.
      ...rows,
      // Calls t with the supplied values.
      t('shareAccessible', { attempts: game.attemptsUsed, status: t(`status.${game.status}`) }),
      // Executes this line as the next step in the surrounding logic.
    ].join('\n');
    // Executes this line as the next step in the surrounding logic.
  }, [game, t]);

  // Computes and stores handleShare for subsequent operations.
  const handleShare = async () => {
    // Checks this condition before running the nested branch.
    if (!shareText) return;
    // Starts an operation whose expected failures are handled below.
    try {
      // Checks this condition before running the nested branch.
      if (navigator.share) await navigator.share({ text: shareText });
      // Executes this line as the next step in the surrounding logic.
      else await navigator.clipboard.writeText(shareText);
      // Calls setAnnouncement with the supplied values.
      setAnnouncement(t('copied'));
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(tr('shareError'));
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleReplay for subsequent operations.
  const handleReplay = async () => {
    // Calls setError with the supplied values.
    setError(null);
    // Checks this condition before running the nested branch.
    if (!replayBody) {
      // Executes this line as the next step in the surrounding logic.
      achievementBaselineRef.current = null;
      // Executes this line as the next step in the surrounding logic.
      achievementBaselineLoadingRef.current = false;
      // Checks this condition before running the nested branch.
      if (game) {
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(rowStorageKey(game.id));
        // Calls localStorage.removeItem with the supplied values.
        localStorage.removeItem(pendingAttemptStorageKey(game.id));
        // Closes the expression, call, or declaration started above.
      }
      // Executes this line as the next step in the surrounding logic.
      gameRef.current = null;
      // Calls setGame with the supplied values.
      setGame(null);
      // Calls setState with the supplied values.
      setState('idle');
      // Returns this result to the caller and ends the current function.
      return;
      // Closes the expression, call, or declaration started above.
    }
    // Calls setState with the supplied values.
    setState('loading');
    // Executes this line as the next step in the surrounding logic.
    achievementBaselineRef.current = null;
    // Executes this line as the next step in the surrounding logic.
    achievementBaselineLoadingRef.current = false;
    // Calls setRow with the supplied values.
    setRow([]);
    // Calls setSelectedSlot with the supplied values.
    setSelectedSlot(0);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores replay for subsequent operations.
      const replay = await api<Game>(startEndpoint, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify(replayBody),
        // Closes the expression, call, or declaration started above.
      });
      // Calls hydrateGame with the supplied values.
      hydrateGame(replay);
      // Calls analytics with the supplied values.
      analytics('game_started', {
        // Defines the mode field in the surrounding object or type.
        mode: gameMode(replay.mode),
        // Defines the difficulty field in the surrounding object or type.
        difficulty: gameDifficulty(replay.difficulty),
        // Closes the expression, call, or declaration started above.
      });
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('genericError'));
      // Calls setState with the supplied values.
      setState('ready');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores handleKeyboard for subsequent operations.
  const handleKeyboard = (event: React.KeyboardEvent) => {
    // Checks this condition before running the nested branch.
    if (!game) return;
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      event.key === 'Enter' &&
      // Executes this line as the next step in the surrounding logic.
      event.target instanceof HTMLElement &&
      // Calls event.target.matches with the supplied values.
      event.target.matches('button, a, input, select, textarea')
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return;
    // Computes and stores number for subsequent operations.
    const number = Number(event.key);
    // Checks this condition before running the nested branch.
    if (Number.isInteger(number) && number >= 1 && number <= game.config.colours.length) {
      // Calls event.preventDefault with the supplied values.
      event.preventDefault();
      // Calls handleColor with the supplied values.
      handleColor(game.config.colours[number - 1] as string);
      // Checks this alternative after the earlier branch failed.
    } else if (event.key === 'Backspace' || event.key === 'Delete') {
      // Calls event.preventDefault with the supplied values.
      event.preventDefault();
      // Calls setRow with the supplied values.
      setRow((current) => current.filter((_, index) => index !== selectedSlot));
      // Checks this alternative after the earlier branch failed.
    } else if (event.key === 'Enter') {
      // Calls event.preventDefault with the supplied values.
      event.preventDefault();
      // Executes this line as the next step in the surrounding logic.
      void handleSubmit();
      // Checks this alternative after the earlier branch failed.
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      // Calls event.preventDefault with the supplied values.
      event.preventDefault();
      // Computes and stores delta for subsequent operations.
      const delta = event.key === 'ArrowLeft' ? -1 : 1;
      // Computes and stores next for subsequent operations.
      const next = Math.max(0, Math.min(game.config.codeLength - 1, selectedSlot + delta));
      // Calls setSelectedSlot with the supplied values.
      setSelectedSlot(next);
      // Executes this line as the next step in the surrounding logic.
      slotRefs.current[next]?.focus();
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Checks this condition before running the nested branch.
  if (!game) {
    // Returns this result to the caller and ends the current function.
    return (
      // Renders the section interface element or component.
      <section className="game-intro panel">
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the h1 interface element or component. */}
          <h1>{title}</h1>
          {/* Executes this line as the next step in the surrounding logic. */}
          {intro ? <p>{intro}</p> : null}
          {/* Renders the p interface element or component. */}
          <p className="quiet-note">{t('serverAuthoritative')}</p>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the className value to the surrounding call or element. */
          className="button primary"
          /* Provides the type value to the surrounding call or element. */
          type="button"
          /* Provides the onClick value to the surrounding call or element. */
          onClick={() => void handleStart()}
          /* Provides the disabled value to the surrounding call or element. */
          disabled={state === 'loading'}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {state === 'loading' ? t('starting') : t('start')}
          {/* Closes the button interface element. */}
        </button>
        {/* Executes this line as the next step in the surrounding logic. */}
        {error ? (
          // Renders the p interface element or component.
          <p className="inline-error" role="alert">
            {/* Executes this line as the next step in the surrounding logic. */}
            {error}
            {/* Closes the p interface element. */}
          </p>
        ) : // Executes this line as the next step in the surrounding logic.
        null}
        {/* Closes the section interface element. */}
      </section>
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  }

  // Computes and stores terminal for subsequent operations.
  const terminal = ['won', 'lost', 'abandoned', 'expired'].includes(game.status);
  // Computes and stores rowComplete for subsequent operations.
  const rowComplete = Array.from(
    // Creates one entry for every position required by the active code.
    { length: game.config.codeLength },
    (_, index) =>
      // Calls Boolean with the supplied values.
      Boolean(row[index]),
    // Executes this line as the next step in the surrounding logic.
  ).every(Boolean);
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the section interface element or component.
    <section className="game-workspace" onKeyDown={handleKeyboard} aria-labelledby="game-heading">
      {/* Renders the header interface element or component. */}
      <header className="game-header">
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the p interface element or component. */}
          <p className="mode-label">{t(`modes.${game.mode}`)}</p>
          {/* Renders the h1 interface element or component. */}
          <h1 id="game-heading">{title}</h1>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the dl interface element or component. */}
        <dl className="game-facts">
          {/* Renders the div interface element or component. */}
          <div>
            {/* Renders the dt interface element or component. */}
            <dt>{t('remaining')}</dt>
            {/* Renders the dd interface element or component. */}
            <dd>{game.attemptsRemaining}</dd>
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the div interface element or component. */}
          <div>
            {/* Renders the dt interface element or component. */}
            <dt>{t('elapsed')}</dt>
            {/* Renders the dd interface element or component. */}
            <dd aria-label={t('elapsedAccessible', { seconds: elapsed })}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
              {/* Closes the dd interface element. */}
            </dd>
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the div interface element or component. */}
          <div>
            {/* Renders the dt interface element or component. */}
            <dt>{t('connection')}</dt>
            {/* Renders the dd interface element or component. */}
            <dd className={online ? 'online' : 'offline'}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {online ? <Wifi aria-hidden="true" /> : <WifiOff aria-hidden="true" />}{' '}
              {/* Executes this line as the next step in the surrounding logic. */}
              {online ? t('online') : t('offline')}
              {/* Closes the dd interface element. */}
            </dd>
            {/* Closes the div interface element. */}
          </div>
          {/* Closes the dl interface element. */}
        </dl>
        {/* Renders the span interface element or component. */}
        <span className="sr-only" role="status">
          {/* Executes this line as the next step in the surrounding logic. */}
          {online ? t('online') : t('offline')}
          {/* Closes the span interface element. */}
        </span>
        {/* Closes the header interface element. */}
      </header>
      {/* Renders the div interface element or component. */}
      <div className="board-layout">
        {/* Renders the div interface element or component. */}
        <div className="attempt-board" role="region" aria-label={t('board')}>
          {/* Executes this line as the next step in the surrounding logic. */}
          {game.attempts.length === 0 ? (
            // Renders the p interface element or component.
            <p className="board-empty">{t('firstGuess')}</p>
          ) : (
            // Executes this line as the next step in the surrounding logic.
            // Calls game.attempts.map with the supplied values.
            game.attempts.map((attempt) => <AttemptRow key={attempt.number} attempt={attempt} />)
            // Closes the expression, call, or declaration started above.
          )}
          {/* Executes this line as the next step in the surrounding logic. */}
          {!terminal ? (
            // Renders the div interface element or component.
            <div className="current-row" role="group" aria-label={t('currentGuess')}>
              {/* Renders the span interface element or component. */}
              <span className="attempt-number">{game.attemptsUsed + 1}</span>
              {/* Renders the div interface element or component. */}
              <div className="guess-pegs">
                {/* Begins the nested block or object completed below. */}
                {Array.from({ length: game.config.codeLength }, (_, index) => {
                  // Computes and stores color for subsequent operations.
                  const color = row[index];
                  // Returns this result to the caller and ends the current function.
                  return (
                    // Renders the button interface element or component.
                    <button
                      /* Provides the ref value to the surrounding call or element. */
                      ref={(element) => {
                        // Executes this line as the next step in the surrounding logic.
                        slotRefs.current[index] = element;
                        // Closes the expression, call, or declaration started above.
                      }}
                      /* Provides the key value to the surrounding call or element. */
                      key={index}
                      /* Provides the type value to the surrounding call or element. */
                      type="button"
                      /* Provides the className value to the surrounding call or element. */
                      className={`peg slot ${color ? `peg-${color}` : ''} ${selectedSlot === index ? 'selected' : ''}`}
                      /* Provides the onClick value to the surrounding call or element. */
                      onClick={() => setSelectedSlot(index)}
                      /* Begins the nested block or object completed below. */
                      aria-label={t('slot', {
                        // Defines the number field in the surrounding object or type.
                        number: index + 1,
                        // Defines the color field in the surrounding object or type.
                        color: color ? t(`colors.${color}`) : t('empty'),
                        // Closes the expression, call, or declaration started above.
                      })}
                      /* Executes this line as the next step in the surrounding logic. */
                      aria-pressed={selectedSlot === index}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {color ? colorSymbols[color] : index + 1}
                      {/* Closes the button interface element. */}
                    </button>
                    // Closes the expression, call, or declaration started above.
                  );
                  // Closes the expression, call, or declaration started above.
                })}
                {/* Closes the div interface element. */}
              </div>
              {/* Renders the span interface element or component. */}
              <span className="feedback-placeholder" aria-hidden="true">
                —{/* Closes the span interface element. */}
              </span>
              {/* Closes the div interface element. */}
            </div>
          ) : // Executes this line as the next step in the surrounding logic.
          null}
          {/* Closes the div interface element. */}
        </div>
        {/* Executes this line as the next step in the surrounding logic. */}
        {!terminal ? (
          // Renders the div interface element or component.
          <div className="peg-controls" role="group" aria-label={t('picker')}>
            {/* Renders the p interface element or component. */}
            <p>{t('pickColor', { slot: selectedSlot + 1 })}</p>
            {/* Renders the div interface element or component. */}
            <div className="palette">
              {/* Executes this line as the next step in the surrounding logic. */}
              {game.config.colours.map((color, index) => (
                // Renders the button interface element or component.
                <button
                  /* Provides the key value to the surrounding call or element. */
                  key={color}
                  /* Provides the type value to the surrounding call or element. */
                  type="button"
                  /* Provides the className value to the surrounding call or element. */
                  className={`peg peg-${color}`}
                  /* Provides the onClick value to the surrounding call or element. */
                  onClick={() => handleColor(color)}
                  /* Begins the nested block or object completed below. */
                  aria-label={t('chooseColor', {
                    // Defines the color field in the surrounding object or type.
                    color: t(`colors.${color}`),
                    // Defines the shortcut field in the surrounding object or type.
                    shortcut: index + 1,
                    // Closes the expression, call, or declaration started above.
                  })}
                  /* Closes the expression, call, or declaration started above. */
                >
                  {/* Renders the span interface element or component. */}
                  <span aria-hidden="true">{colorSymbols[color]}</span>
                  {/* Renders the small interface element or component. */}
                  <small>{index + 1}</small>
                  {/* Closes the button interface element. */}
                </button>
                // Closes the expression, call, or declaration started above.
              ))}
              {/* Closes the div interface element. */}
            </div>
            {/* Renders the div interface element or component. */}
            <div className="game-actions">
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the onClick value to the surrounding call or element. */
                onClick={handleClear}
                /* Provides the disabled value to the surrounding call or element. */
                disabled={row.length === 0}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Renders the Eraser interface element or component. */}
                <Eraser aria-hidden="true" />
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('clear')}
                {/* Closes the button interface element. */}
              </button>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button primary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => void handleSubmit()}
                /* Provides the disabled value to the surrounding call or element. */
                disabled={
                  // Executes this line as the next step in the surrounding logic.
                  !rowComplete || !online || syncing || syncRequired || state === 'submitting'
                  // Closes the expression, call, or declaration started above.
                }
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Renders the Check interface element or component. */}
                <Check aria-hidden="true" />
                {/* Executes this line as the next step in the surrounding logic. */}
                {state === 'submitting' ? t('checking') : syncing ? t('syncing') : t('submit')}
                {/* Closes the button interface element. */}
              </button>
              {/* Closes the div interface element. */}
            </div>
            {/* Executes this line as the next step in the surrounding logic. */}
            {!online ? (
              // Renders the p interface element or component.
              <p className="connection-warning" role="status">
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('offlinePreserved')}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {syncing ? (
              // Renders the p interface element or component.
              <p className="connection-warning" role="status">
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('syncingState')}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {online && syncRequired && !syncing ? (
              // Renders the button interface element or component.
              <button className="button secondary" type="button" onClick={() => void resyncGame()}>
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('retrySync')}
                {/* Closes the button interface element. */}
              </button>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {error ? (
              // Renders the p interface element or component.
              <p className="inline-error" role="alert">
                {/* Executes this line as the next step in the surrounding logic. */}
                {error}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the button interface element or component. */}
            <button
              /* Provides the className value to the surrounding call or element. */
              className="text-button danger"
              /* Provides the type value to the surrounding call or element. */
              type="button"
              /* Provides the onClick value to the surrounding call or element. */
              onClick={() => void handleAbandon()}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Renders the Flag interface element or component. */}
              <Flag aria-hidden="true" />
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('abandon')}
              {/* Closes the button interface element. */}
            </button>
            {/* Closes the div interface element. */}
          </div>
        ) : (
          // Executes this line as the next step in the surrounding logic.
          // Renders the div interface element or component.
          <div
            /* Provides the ref value to the surrounding call or element. */
            ref={resultRef}
            /* Provides the className value to the surrounding call or element. */
            className="result-panel"
            /* Provides the role value to the surrounding call or element. */
            role="region"
            /* Executes this line as the next step in the surrounding logic. */
            aria-labelledby="game-result-heading"
            /* Executes this line as the next step in the surrounding logic. */
            aria-live="polite"
            /* Provides the tabIndex value to the surrounding call or element. */
            tabIndex={-1}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Executes this line as the next step in the surrounding logic. */}
            {game.status === 'won' ? (
              // Renders the Check interface element or component.
              <Check className="result-icon" aria-hidden="true" />
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the CircleX interface element or component.
              <CircleX className="result-icon" aria-hidden="true" />
              // Closes the expression, call, or declaration started above.
            )}
            {/* Renders the h2 interface element or component. */}
            <h2 id="game-result-heading">{t(`result.${game.status}`)}</h2>
            {/* Renders the p interface element or component. */}
            <p>
              {/* Begins the nested block or object completed below. */}
              {t('resultSummary', {
                // Defines the attempts field in the surrounding object or type.
                attempts: game.attemptsUsed,
                // Defines the max field in the surrounding object or type.
                max: game.maxAttempts,
                // Defines the score field in the surrounding object or type.
                score: game.score ?? 0,
                // Closes the expression, call, or declaration started above.
              })}
              {/* Closes the p interface element. */}
            </p>
            {/* Renders the p interface element or component. */}
            <p className="status muted">{game.ranked ? t('rankedResult') : t('unrankedResult')}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {resultDetails?.personalBest ? (
              // Renders the p interface element or component.
              <p className="notice" role="status">
                {/* Executes this line as the next step in the surrounding logic. */}
                {tr('personalBest')}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {resultDetails?.rank ? (
              // Renders the p interface element or component.
              <p>
                {/* Executes this line as the next step in the surrounding logic. */}
                {tr('rank')}: {resultDetails.rank}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {resultDetails?.newAchievements.length ? (
              // Renders the section interface element or component.
              <section aria-labelledby="new-achievements-heading">
                {/* Renders the h3 interface element or component. */}
                <h3 id="new-achievements-heading">{tr('earned')}</h3>
                {/* Renders the ul interface element or component. */}
                <ul>
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {resultDetails.newAchievements.map((achievement) => (
                    // Renders the li interface element or component.
                    <li key={achievement}>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {ta(achievementTranslationKeys[achievement] ?? 'earnedStatus')}
                      {/* Closes the li interface element. */}
                    </li>
                    // Closes the expression, call, or declaration started above.
                  ))}
                  {/* Closes the ul interface element. */}
                </ul>
                {/* Closes the section interface element. */}
              </section>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {game.secret ? (
              // Renders the div interface element or component.
              <div>
                {/* Renders the p interface element or component. */}
                <p>{t('secret')}</p>
                {/* Renders the div interface element or component. */}
                <div className="guess-pegs">
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {game.secret.map((color, index) => (
                    // Renders the span interface element or component.
                    <span
                      /* Provides the key value to the surrounding call or element. */
                      key={`${color}-${index}`}
                      /* Provides the className value to the surrounding call or element. */
                      className={`peg peg-${color}`}
                      /* Provides the role value to the surrounding call or element. */
                      role="img"
                      /* Executes this line as the next step in the surrounding logic. */
                      aria-label={t(`colors.${color}`)}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {colorSymbols[color]}
                      {/* Closes the span interface element. */}
                    </span>
                    // Closes the expression, call, or declaration started above.
                  ))}
                  {/* Closes the div interface element. */}
                </div>
                {/* Closes the div interface element. */}
              </div>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {game.scoreBreakdown ? (
              // Renders the dl interface element or component.
              <dl className="score-breakdown">
                {/* Renders the div interface element or component. */}
                <div>
                  {/* Renders the dt interface element or component. */}
                  <dt>{t('attemptPoints')}</dt>
                  {/* Renders the dd interface element or component. */}
                  <dd>{game.scoreBreakdown.attempts}</dd>
                  {/* Closes the div interface element. */}
                </div>
                {/* Renders the div interface element or component. */}
                <div>
                  {/* Renders the dt interface element or component. */}
                  <dt>{t('difficultyPoints')}</dt>
                  {/* Renders the dd interface element or component. */}
                  <dd>{game.scoreBreakdown.difficulty}</dd>
                  {/* Closes the div interface element. */}
                </div>
                {/* Renders the div interface element or component. */}
                <div>
                  {/* Renders the dt interface element or component. */}
                  <dt>{t('total')}</dt>
                  {/* Renders the dd interface element or component. */}
                  <dd>{game.scoreBreakdown.total}</dd>
                  {/* Closes the div interface element. */}
                </div>
                {/* Closes the dl interface element. */}
              </dl>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the p interface element or component. */}
            <p className="quiet-note">{tr('shareSafe')}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {error ? (
              // Renders the p interface element or component.
              <p className="inline-error" role="alert">
                {/* Executes this line as the next step in the surrounding logic. */}
                {error}
                {/* Closes the p interface element. */}
              </p>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the div interface element or component. */}
            <div className="result-actions">
              {/* Renders the button interface element or component. */}
              <button className="button primary" type="button" onClick={() => void handleShare()}>
                {/* Renders the Share2 interface element or component. */}
                <Share2 aria-hidden="true" />
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('share')}
                {/* Closes the button interface element. */}
              </button>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the disabled value to the surrounding call or element. */
                disabled={state === 'loading'}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => void handleReplay()}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Renders the RotateCcw interface element or component. */}
                <RotateCcw aria-hidden="true" />
                {/* Executes this line as the next step in the surrounding logic. */}
                {state === 'loading' ? t('starting') : (replayLabel ?? t('playAgain'))}
                {/* Closes the button interface element. */}
              </button>
              {/* Renders the Link interface element or component. */}
              <Link className="button secondary" href="/">
                {/* Executes this line as the next step in the surrounding logic. */}
                {tr('home')}
                {/* Closes the Link interface element. */}
              </Link>
              {/* Closes the div interface element. */}
            </div>
            {/* Closes the div interface element. */}
          </div>
          // Closes the expression, call, or declaration started above.
        )}
        {/* Closes the div interface element. */}
      </div>
      {/* Renders the div interface element or component. */}
      <div className="sr-only" aria-live="polite">
        {/* Executes this line as the next step in the surrounding logic. */}
        {announcement}
        {/* Closes the div interface element. */}
      </div>
      {/* Closes the section interface element. */}
    </section>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the AttemptRow function and its callable behavior.
function AttemptRow({ attempt }: { attempt: Game['attempts'][number] }) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Game');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div
      /* Provides the className value to the surrounding call or element. */
      className="attempt-row"
      /* Provides the role value to the surrounding call or element. */
      role="group"
      /* Begins the nested block or object completed below. */
      aria-label={t('attemptRow', {
        // Defines the number field in the surrounding object or type.
        number: attempt.number,
        // Defines the black field in the surrounding object or type.
        black: attempt.feedback.black,
        // Defines the white field in the surrounding object or type.
        white: attempt.feedback.white,
        // Closes the expression, call, or declaration started above.
      })}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Renders the span interface element or component. */}
      <span className="attempt-number">{attempt.number}</span>
      {/* Renders the div interface element or component. */}
      <div className="guess-pegs">
        {/* Executes this line as the next step in the surrounding logic. */}
        {attempt.guess.map((color, index) => (
          // Renders the span interface element or component.
          <span
            /* Provides the key value to the surrounding call or element. */
            key={`${color}-${index}`}
            /* Provides the className value to the surrounding call or element. */
            className={`peg peg-${color}`}
            /* Provides the role value to the surrounding call or element. */
            role="img"
            /* Executes this line as the next step in the surrounding logic. */
            aria-label={t(`colors.${color}`)}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Executes this line as the next step in the surrounding logic. */}
            {colorSymbols[color]}
            {/* Closes the span interface element. */}
          </span>
          // Closes the expression, call, or declaration started above.
        ))}
        {/* Closes the div interface element. */}
      </div>
      {/* Renders the div interface element or component. */}
      <div className="feedback-pegs" aria-hidden="true">
        {/* Renders the span interface element or component. */}
        <span>
          {/* Renders the b interface element or component. */}
          <b>{attempt.feedback.black}</b>●{/* Closes the span interface element. */}
        </span>
        {/* Renders the span interface element or component. */}
        <span>
          {/* Renders the b interface element or component. */}
          <b>{attempt.feedback.white}</b>○{/* Closes the span interface element. */}
        </span>
        {/* Closes the div interface element. */}
      </div>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
