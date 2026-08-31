'use client';

import { Check, CircleX, Eraser, Flag, RotateCcw, Share2, Wifi, WifiOff } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from '@/i18n/navigation';
import { ApiError, type Game, type Leaderboard, type Stats, useApi } from '@/lib/api';
import { gameDifficulty, gameMode, scoreBand } from '@/lib/analytics-delivery';
import { playGameSound } from '@/lib/preferences';
import { useProductAnalytics } from '@/lib/use-product-analytics';

const colorSymbols: Record<string, string> = {
  R: '●',
  B: '◆',
  G: '▲',
  Y: '■',
  W: '○',
  K: '✚',
  O: '⬟',
  P: '✦',
  C: '⬢',
  M: '♥',
};

type GameBoardProps = {
  title: string;
  intro?: string;
  startEndpoint?: string;
  startBody?: Record<string, unknown>;
  replayBody?: Record<string, unknown>;
  replayLabel?: string;
  dailyChallengeId?: string;
  initialGameId?: string;
};

type ResultDetails = { personalBest: boolean; rank: number | null; newAchievements: string[] };
type PendingAttempt = {
  gameId: string;
  guess: string[];
  idempotencyKey: string;
  attemptsUsed: number;
};
const achievementTranslationKeys: Record<string, string> = {
  first_break: 'firstBreak',
  one_shot: 'oneShot',
  no_waste: 'noWaste',
  daily_debut: 'dailyDebut',
  logic_week: 'logicWeek',
  hard_mode: 'hardMode',
  expert_breaker: 'expertBreaker',
  challenger: 'challenger',
  duelist: 'duelist',
  comeback: 'comeback',
};
const rowStorageKey = (gameId: string) => `cipherboard:row:${gameId}`;
const pendingAttemptStorageKey = (gameId: string) => `cipherboard:pending-attempt:${gameId}`;
const dailyGameStorageKey = (dailyChallengeId: string) =>
  `cipherboard:daily:${dailyChallengeId}:active-game`;

function loadPendingAttempt(gameId: string): PendingAttempt | null {
  try {
    const pending = JSON.parse(
      localStorage.getItem(pendingAttemptStorageKey(gameId)) ?? 'null',
    ) as Partial<PendingAttempt> | null;
    if (
      !pending ||
      pending.gameId !== gameId ||
      !Array.isArray(pending.guess) ||
      typeof pending.idempotencyKey !== 'string' ||
      typeof pending.attemptsUsed !== 'number'
    )
      return null;
    return pending as PendingAttempt;
  } catch {
    return null;
  }
}

export function GameBoard({
  title,
  intro,
  startEndpoint = '/v1/games',
  startBody = { mode: 'solo', difficulty: 'normal' },
  replayBody,
  replayLabel,
  dailyChallengeId,
  initialGameId,
}: GameBoardProps) {
  const t = useTranslations('Game');
  const tr = useTranslations('Result');
  const ta = useTranslations('Achievements');
  const api = useApi();
  const analytics = useProductAnalytics();
  const [game, setGame] = useState<Game | null>(null);
  const [row, setRow] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState(0);
  const [state, setState] = useState<'idle' | 'loading' | 'ready' | 'submitting' | 'error'>(
    initialGameId || dailyChallengeId ? 'loading' : 'idle',
  );
  const [error, setError] = useState<string | null>(null);
  const [online, setOnline] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncRequired, setSyncRequired] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const [resultDetails, setResultDetails] = useState<ResultDetails | null>(null);
  const slotRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const resultRef = useRef<HTMLDivElement | null>(null);
  const achievementBaselineRef = useRef<Set<string> | null>(null);
  const achievementBaselineLoadingRef = useRef(false);
  const gameRef = useRef<Game | null>(null);
  const rowRef = useRef<string[]>([]);

  const hydrateGame = useCallback(
    (nextGame: Game) => {
      setResultDetails(null);
      gameRef.current = nextGame;
      setGame(nextGame);
      if (dailyChallengeId) {
        const storageKey = dailyGameStorageKey(dailyChallengeId);
        if (nextGame.mode === 'daily' && nextGame.status === 'active')
          localStorage.setItem(storageKey, nextGame.id);
        else localStorage.removeItem(storageKey);
      }
      if (
        nextGame.status === 'active' &&
        achievementBaselineRef.current === null &&
        !achievementBaselineLoadingRef.current
      ) {
        achievementBaselineLoadingRef.current = true;
        void api<Stats>('/v1/me/stats')
          .then((stats) => {
            achievementBaselineRef.current = new Set(stats.achievements ?? []);
          })
          .catch(() => undefined)
          .finally(() => {
            achievementBaselineLoadingRef.current = false;
          });
      }
      setRow((current) => {
        const storageKey = rowStorageKey(nextGame.id);
        if (current.length > 0) return current;
        try {
          const stored = JSON.parse(localStorage.getItem(storageKey) ?? '[]') as string[];
          return stored
            .filter((color) => nextGame.config.colours.includes(color))
            .slice(0, nextGame.config.codeLength);
        } catch {
          return [];
        }
      });
      setState('ready');
    },
    [api, dailyChallengeId],
  );

  const resyncGame = useCallback(async () => {
    const currentGame = gameRef.current;
    if (!currentGame || currentGame.status !== 'active' || !navigator.onLine) return;
    setSyncRequired(true);
    setSyncing(true);
    try {
      const nextGame = await api<Game>(`/v1/games/${encodeURIComponent(currentGame.id)}`);
      const pending = loadPendingAttempt(currentGame.id);
      if (pending && nextGame.attemptsUsed > pending.attemptsUsed) {
        localStorage.removeItem(pendingAttemptStorageKey(currentGame.id));
        if (JSON.stringify(rowRef.current) === JSON.stringify(pending.guess)) {
          rowRef.current = [];
          setRow([]);
          localStorage.removeItem(rowStorageKey(currentGame.id));
        }
      }
      hydrateGame(nextGame);
      setError(null);
      setSyncRequired(false);
    } catch {
      setError(t('restoreError'));
    } finally {
      setSyncing(false);
    }
  }, [api, hydrateGame, t]);

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      void resyncGame();
    };
    const handleOffline = () => {
      setOnline(false);
      setSyncRequired(true);
    };
    const handleFocus = () => void resyncGame();
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') void resyncGame();
    };
    const frame = requestAnimationFrame(() => setOnline(navigator.onLine));
    addEventListener('online', handleOnline);
    addEventListener('offline', handleOffline);
    addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibility);
    return () => {
      removeEventListener('online', handleOnline);
      removeEventListener('offline', handleOffline);
      removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibility);
      cancelAnimationFrame(frame);
    };
  }, [resyncGame]);

  useEffect(() => {
    if (!initialGameId) return;
    api<Game>(`/v1/games/${encodeURIComponent(initialGameId)}`)
      .then(hydrateGame)
      .catch(() => {
        setError(t('genericError'));
        setState('error');
      });
  }, [api, hydrateGame, initialGameId, t]);

  useEffect(() => {
    if (initialGameId || !dailyChallengeId) return;
    let active = true;
    const restoreStoredDailyGame = async () => {
      await Promise.resolve();
      if (!active) return;
      const storageKey = dailyGameStorageKey(dailyChallengeId);
      const storedGameId = localStorage.getItem(storageKey);
      if (!storedGameId || !/^[A-Za-z0-9_-]{8,128}$/.test(storedGameId)) {
        localStorage.removeItem(storageKey);
        setState('idle');
        return;
      }

      setState('loading');
      try {
        const restoredGame = await api<Game>(`/v1/games/${encodeURIComponent(storedGameId)}`);
        if (!active) return;
        if (restoredGame.mode !== 'daily' || restoredGame.status !== 'active') {
          localStorage.removeItem(storageKey);
          setError(null);
          setState('idle');
          return;
        }
        hydrateGame(restoredGame);
      } catch {
        localStorage.removeItem(storageKey);
        if (!active) return;
        gameRef.current = null;
        setGame(null);
        setError(null);
        setState('idle');
      }
    };
    void restoreStoredDailyGame();
    return () => {
      active = false;
    };
  }, [api, dailyChallengeId, hydrateGame, initialGameId]);

  useEffect(() => {
    if (!game || game.status !== 'active') return;
    const update = () =>
      setElapsed(Math.max(0, Math.floor((Date.now() - Date.parse(game.startedAt)) / 1000)));
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [game]);

  useEffect(() => {
    if (!game) return;
    rowRef.current = row;
    localStorage.setItem(rowStorageKey(game.id), JSON.stringify(row));
  }, [game, row]);

  useEffect(() => {
    if (!game || !['won', 'lost', 'abandoned', 'expired'].includes(game.status)) return;
    const frame = requestAnimationFrame(() => resultRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [game]);

  useEffect(() => {
    if (!game || !['won', 'lost'].includes(game.status)) return;
    let active = true;
    const loadDetails = async () => {
      const leaderboardEndpoint =
        game.mode === 'daily'
          ? '/v1/daily/leaderboard?page=1&page_size=1'
          : game.ranked && game.difficulty
            ? `/v1/leaderboards?period=all-time&difficulty=${encodeURIComponent(game.difficulty)}&page=1&page_size=1`
            : null;
      const [statsResult, leaderboardResult] = await Promise.allSettled([
        api<Stats>('/v1/me/stats'),
        leaderboardEndpoint ? api<Leaderboard>(leaderboardEndpoint) : Promise.resolve(null),
      ]);
      if (!active) return;
      const stats = statsResult.status === 'fulfilled' ? statsResult.value : null;
      const leaderboard = leaderboardResult.status === 'fulfilled' ? leaderboardResult.value : null;
      const bestScores = stats?.bestScoreByDifficulty ?? {};
      setResultDetails({
        personalBest: Boolean(
          game.score !== null && game.difficulty && bestScores[game.difficulty] === game.score,
        ),
        rank: leaderboard?.currentUserRank ?? null,
        newAchievements:
          achievementBaselineRef.current && stats
            ? (stats.achievements ?? []).filter(
                (achievement) => !achievementBaselineRef.current?.has(achievement),
              )
            : [],
      });
    };
    void loadDetails();
    return () => {
      active = false;
    };
  }, [api, game]);

  const handleStart = async () => {
    achievementBaselineRef.current = null;
    achievementBaselineLoadingRef.current = false;
    setState('loading');
    setError(null);
    try {
      const nextGame = await api<Game>(startEndpoint, {
        method: 'POST',
        body: JSON.stringify(startBody),
      });
      hydrateGame(nextGame);
      analytics('game_started', {
        mode: gameMode(nextGame.mode),
        difficulty: gameDifficulty(nextGame.difficulty),
      });
    } catch {
      setError(t('genericError'));
      setState('error');
    }
  };

  const handleColor = (color: string) => {
    if (!game) return;
    setRow((current) => {
      const next = [...current];
      next[selectedSlot] = color;
      return next.slice(0, game.config.codeLength);
    });
    const nextSlot = Math.min(selectedSlot + 1, game.config.codeLength - 1);
    setSelectedSlot(nextSlot);
    slotRefs.current[nextSlot]?.focus();
  };

  const handleClear = () => {
    setRow([]);
    setSelectedSlot(0);
    slotRefs.current[0]?.focus();
  };

  const handleSubmit = async () => {
    if (
      !game ||
      !Array.from({ length: game.config.codeLength }, (_, index) => Boolean(row[index])).every(
        Boolean,
      ) ||
      !online ||
      syncing ||
      syncRequired
    )
      return;
    const guess = row.slice(0, game.config.codeLength);
    const existingPending = loadPendingAttempt(game.id);
    const pending =
      existingPending &&
      existingPending.attemptsUsed === game.attemptsUsed &&
      JSON.stringify(existingPending.guess) === JSON.stringify(guess)
        ? existingPending
        : {
            gameId: game.id,
            guess,
            idempotencyKey: crypto.randomUUID(),
            attemptsUsed: game.attemptsUsed,
          };
    localStorage.setItem(pendingAttemptStorageKey(game.id), JSON.stringify(pending));
    setState('submitting');
    setError(null);
    try {
      const nextGame = await api<Game>(`/v1/games/${encodeURIComponent(game.id)}/attempts`, {
        method: 'POST',
        body: JSON.stringify({ guess: pending.guess, idempotencyKey: pending.idempotencyKey }),
      });
      const last = nextGame.attempts.at(-1);
      if (last)
        setAnnouncement(
          t('attemptAnnouncement', {
            number: last.number,
            black: last.feedback.black,
            white: last.feedback.white,
            remaining: nextGame.attemptsRemaining,
          }),
        );
      localStorage.removeItem(rowStorageKey(game.id));
      localStorage.removeItem(pendingAttemptStorageKey(game.id));
      rowRef.current = [];
      setRow([]);
      setSelectedSlot(0);
      hydrateGame(nextGame);
      if (nextGame.status === 'won') {
        void playGameSound('success');
        analytics('game_completed', {
          mode: gameMode(nextGame.mode),
          result: nextGame.status,
          attemptsUsed: nextGame.attemptsUsed,
          ranked: nextGame.ranked,
          scoreBand: scoreBand(nextGame.score),
        });
        if (nextGame.mode === 'daily' && dailyChallengeId)
          analytics('daily_completed', {
            dailyChallengeId,
            result: nextGame.status,
            attemptsUsed: nextGame.attemptsUsed,
          });
      } else if (nextGame.status === 'lost') {
        void playGameSound('failure');
        analytics('game_completed', {
          mode: gameMode(nextGame.mode),
          result: nextGame.status,
          attemptsUsed: nextGame.attemptsUsed,
          ranked: nextGame.ranked,
          scoreBand: scoreBand(nextGame.score),
        });
        if (nextGame.mode === 'daily' && dailyChallengeId)
          analytics('daily_completed', {
            dailyChallengeId,
            result: nextGame.status,
            attemptsUsed: nextGame.attemptsUsed,
          });
      } else {
        void playGameSound('feedback');
      }
      requestAnimationFrame(() => slotRefs.current[0]?.focus());
    } catch (caught) {
      if (
        caught instanceof ApiError &&
        caught.status === 422 &&
        caught.body.code === 'DUPLICATES_NOT_ALLOWED'
      ) {
        localStorage.removeItem(pendingAttemptStorageKey(game.id));
        setError(t('duplicatesNotAllowed'));
        setState('ready');
        analytics('validation_error', { validationCategory: 'guess' });
        return;
      }
      setError(t('genericError'));
      setSyncRequired(true);
      setState('ready');
    }
  };

  const handleAbandon = async () => {
    if (!game || !confirm(t('confirmAbandon'))) return;
    setState('submitting');
    try {
      const abandoned = await api<Game>(`/v1/games/${encodeURIComponent(game.id)}/abandon`, {
        method: 'POST',
      });
      hydrateGame(abandoned);
      analytics('game_abandoned', {
        mode: gameMode(abandoned.mode),
        attemptsUsed: abandoned.attemptsUsed,
      });
    } catch {
      setError(t('genericError'));
      setState('ready');
    }
  };

  const shareText = useMemo(() => {
    if (!game || !['won', 'lost'].includes(game.status)) return '';
    const header = `${t('shareTitle')}\n${game.status === 'won' ? t('shareSolved', { used: game.attemptsUsed, max: game.maxAttempts }) : t('shareNotSolved')}`;
    const rows = game.attempts.map(
      (attempt) => `${'⬛'.repeat(attempt.feedback.black)}${'⬜'.repeat(attempt.feedback.white)}`,
    );
    return [
      header,
      ...rows,
      t('shareAccessible', { attempts: game.attemptsUsed, status: t(`status.${game.status}`) }),
    ].join('\n');
  }, [game, t]);

  const handleShare = async () => {
    if (!shareText) return;
    try {
      if (navigator.share) await navigator.share({ text: shareText });
      else await navigator.clipboard.writeText(shareText);
      setAnnouncement(t('copied'));
    } catch {
      setError(tr('shareError'));
    }
  };

  const handleReplay = async () => {
    setError(null);
    if (!replayBody) {
      achievementBaselineRef.current = null;
      achievementBaselineLoadingRef.current = false;
      if (game) {
        localStorage.removeItem(rowStorageKey(game.id));
        localStorage.removeItem(pendingAttemptStorageKey(game.id));
      }
      gameRef.current = null;
      setGame(null);
      setState('idle');
      return;
    }
    setState('loading');
    achievementBaselineRef.current = null;
    achievementBaselineLoadingRef.current = false;
    setRow([]);
    setSelectedSlot(0);
    try {
      const replay = await api<Game>(startEndpoint, {
        method: 'POST',
        body: JSON.stringify(replayBody),
      });
      hydrateGame(replay);
      analytics('game_started', {
        mode: gameMode(replay.mode),
        difficulty: gameDifficulty(replay.difficulty),
      });
    } catch {
      setError(t('genericError'));
      setState('ready');
    }
  };

  const handleKeyboard = (event: React.KeyboardEvent) => {
    if (!game) return;
    if (
      event.key === 'Enter' &&
      event.target instanceof HTMLElement &&
      event.target.matches('button, a, input, select, textarea')
    )
      return;
    const number = Number(event.key);
    if (Number.isInteger(number) && number >= 1 && number <= game.config.colours.length) {
      event.preventDefault();
      handleColor(game.config.colours[number - 1] as string);
    } else if (event.key === 'Backspace' || event.key === 'Delete') {
      event.preventDefault();
      setRow((current) => current.filter((_, index) => index !== selectedSlot));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      void handleSubmit();
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      const delta = event.key === 'ArrowLeft' ? -1 : 1;
      const next = Math.max(0, Math.min(game.config.codeLength - 1, selectedSlot + delta));
      setSelectedSlot(next);
      slotRefs.current[next]?.focus();
    }
  };

  if (!game) {
    return (
      <section className="game-intro panel">
        <div>
          <h1>{title}</h1>
          {intro ? <p>{intro}</p> : null}
          <p className="quiet-note">{t('serverAuthoritative')}</p>
        </div>
        <button
          className="button primary"
          type="button"
          onClick={() => void handleStart()}
          disabled={state === 'loading'}
        >
          {state === 'loading' ? t('starting') : t('start')}
        </button>
        {error ? (
          <p className="inline-error" role="alert">
            {error}
          </p>
        ) : null}
      </section>
    );
  }

  const terminal = ['won', 'lost', 'abandoned', 'expired'].includes(game.status);
  const rowComplete = Array.from({ length: game.config.codeLength }, (_, index) =>
    Boolean(row[index]),
  ).every(Boolean);
  return (
    <section className="game-workspace" onKeyDown={handleKeyboard} aria-labelledby="game-heading">
      <header className="game-header">
        <div>
          <p className="mode-label">{t(`modes.${game.mode}`)}</p>
          <h1 id="game-heading">{title}</h1>
        </div>
        <dl className="game-facts">
          <div>
            <dt>{t('remaining')}</dt>
            <dd>{game.attemptsRemaining}</dd>
          </div>
          <div>
            <dt>{t('elapsed')}</dt>
            <dd aria-label={t('elapsedAccessible', { seconds: elapsed })}>
              {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
            </dd>
          </div>
          <div>
            <dt>{t('connection')}</dt>
            <dd className={online ? 'online' : 'offline'}>
              {online ? <Wifi aria-hidden="true" /> : <WifiOff aria-hidden="true" />}{' '}
              {online ? t('online') : t('offline')}
            </dd>
          </div>
        </dl>
        <span className="sr-only" role="status">
          {online ? t('online') : t('offline')}
        </span>
      </header>
      <div className="board-layout">
        <div className="attempt-board" role="region" aria-label={t('board')}>
          {game.attempts.length === 0 ? (
            <p className="board-empty">{t('firstGuess')}</p>
          ) : (
            game.attempts.map((attempt) => <AttemptRow key={attempt.number} attempt={attempt} />)
          )}
          {!terminal ? (
            <div className="current-row" role="group" aria-label={t('currentGuess')}>
              <span className="attempt-number">{game.attemptsUsed + 1}</span>
              <div className="guess-pegs">
                {Array.from({ length: game.config.codeLength }, (_, index) => {
                  const color = row[index];
                  return (
                    <button
                      ref={(element) => {
                        slotRefs.current[index] = element;
                      }}
                      key={index}
                      type="button"
                      className={`peg slot ${color ? `filled peg-${color}` : 'empty'} ${selectedSlot === index ? 'selected' : ''}`}
                      onClick={() => setSelectedSlot(index)}
                      aria-label={t('slot', {
                        number: index + 1,
                        color: color ? t(`colors.${color}`) : t('empty'),
                      })}
                      aria-pressed={selectedSlot === index}
                    >
                      {color ? colorSymbols[color] : index + 1}
                    </button>
                  );
                })}
              </div>
              <span className="feedback-placeholder" aria-hidden="true">
                —
              </span>
            </div>
          ) : null}
        </div>
        {!terminal ? (
          <div className="peg-controls" role="group" aria-label={t('picker')}>
            <p>{t('pickColor', { slot: selectedSlot + 1 })}</p>
            <div className="palette">
              {game.config.colours.map((color, index) => (
                <button
                  key={color}
                  type="button"
                  className={`peg peg-${color}`}
                  onClick={() => handleColor(color)}
                  aria-label={t('chooseColor', {
                    color: t(`colors.${color}`),
                    shortcut: index + 1,
                  })}
                >
                  <span aria-hidden="true">{colorSymbols[color]}</span>
                  <small>{index + 1}</small>
                </button>
              ))}
            </div>
            <div className="game-actions">
              <button
                className="button secondary"
                type="button"
                onClick={handleClear}
                disabled={row.length === 0}
              >
                <Eraser aria-hidden="true" />
                {t('clear')}
              </button>
              <button
                className="button primary"
                type="button"
                onClick={() => void handleSubmit()}
                disabled={
                  !rowComplete || !online || syncing || syncRequired || state === 'submitting'
                }
              >
                <Check aria-hidden="true" />
                {state === 'submitting' ? t('checking') : syncing ? t('syncing') : t('submit')}
              </button>
            </div>
            {!online ? (
              <p className="connection-warning" role="status">
                {t('offlinePreserved')}
              </p>
            ) : null}
            {syncing ? (
              <p className="connection-warning" role="status">
                {t('syncingState')}
              </p>
            ) : null}
            {online && syncRequired && !syncing ? (
              <button className="button secondary" type="button" onClick={() => void resyncGame()}>
                {t('retrySync')}
              </button>
            ) : null}
            {error ? (
              <p className="inline-error" role="alert">
                {error}
              </p>
            ) : null}
            <button
              className="text-button danger"
              type="button"
              onClick={() => void handleAbandon()}
            >
              <Flag aria-hidden="true" />
              {t('abandon')}
            </button>
          </div>
        ) : (
          <div
            ref={resultRef}
            className="result-panel"
            role="region"
            aria-labelledby="game-result-heading"
            aria-live="polite"
            tabIndex={-1}
          >
            {game.status === 'won' ? (
              <Check className="result-icon" aria-hidden="true" />
            ) : (
              <CircleX className="result-icon" aria-hidden="true" />
            )}
            <h2 id="game-result-heading">{t(`result.${game.status}`)}</h2>
            <p>
              {t('resultSummary', {
                attempts: game.attemptsUsed,
                max: game.maxAttempts,
                score: game.score ?? 0,
              })}
            </p>
            <p className="status muted">{game.ranked ? t('rankedResult') : t('unrankedResult')}</p>
            {resultDetails?.personalBest ? (
              <p className="notice" role="status">
                {tr('personalBest')}
              </p>
            ) : null}
            {resultDetails?.rank ? (
              <p>
                {tr('rank')}: {resultDetails.rank}
              </p>
            ) : null}
            {resultDetails?.newAchievements.length ? (
              <section aria-labelledby="new-achievements-heading">
                <h3 id="new-achievements-heading">{tr('earned')}</h3>
                <ul>
                  {resultDetails.newAchievements.map((achievement) => (
                    <li key={achievement}>
                      {ta(achievementTranslationKeys[achievement] ?? 'earnedStatus')}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            {game.secret ? (
              <div>
                <p>{t('secret')}</p>
                <div className="guess-pegs">
                  {game.secret.map((color, index) => (
                    <span
                      key={`${color}-${index}`}
                      className={`peg peg-${color}`}
                      role="img"
                      aria-label={t(`colors.${color}`)}
                    >
                      {colorSymbols[color]}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {game.scoreBreakdown ? (
              <dl className="score-breakdown">
                <div>
                  <dt>{t('attemptPoints')}</dt>
                  <dd>{game.scoreBreakdown.attempts}</dd>
                </div>
                <div>
                  <dt>{t('difficultyPoints')}</dt>
                  <dd>{game.scoreBreakdown.difficulty}</dd>
                </div>
                <div>
                  <dt>{t('total')}</dt>
                  <dd>{game.scoreBreakdown.total}</dd>
                </div>
              </dl>
            ) : null}
            <p className="quiet-note">{tr('shareSafe')}</p>
            {error ? (
              <p className="inline-error" role="alert">
                {error}
              </p>
            ) : null}
            <div className="result-actions">
              <button className="button primary" type="button" onClick={() => void handleShare()}>
                <Share2 aria-hidden="true" />
                {t('share')}
              </button>
              <button
                className="button secondary"
                type="button"
                disabled={state === 'loading'}
                onClick={() => void handleReplay()}
              >
                <RotateCcw aria-hidden="true" />
                {state === 'loading' ? t('starting') : (replayLabel ?? t('playAgain'))}
              </button>
              <Link className="button secondary" href="/">
                {tr('home')}
              </Link>
            </div>
          </div>
        )}
      </div>
      <div className="sr-only" aria-live="polite">
        {announcement}
      </div>
    </section>
  );
}

function AttemptRow({ attempt }: { attempt: Game['attempts'][number] }) {
  const t = useTranslations('Game');
  return (
    <div
      className="attempt-row"
      role="group"
      aria-label={t('attemptRow', {
        number: attempt.number,
        black: attempt.feedback.black,
        white: attempt.feedback.white,
      })}
    >
      <span className="attempt-number">{attempt.number}</span>
      <div className="guess-pegs">
        {attempt.guess.map((color, index) => (
          <span
            key={`${color}-${index}`}
            className={`peg peg-${color}`}
            role="img"
            aria-label={t(`colors.${color}`)}
          >
            {colorSymbols[color]}
          </span>
        ))}
      </div>
      <div className="feedback-pegs" aria-hidden="true">
        <span>
          <b>{attempt.feedback.black}</b>●
        </span>
        <span>
          <b>{attempt.feedback.white}</b>○
        </span>
      </div>
    </div>
  );
}
