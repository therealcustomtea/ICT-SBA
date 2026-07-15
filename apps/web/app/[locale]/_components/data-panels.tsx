'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import { AsyncState } from '@/components/feature-page';
import { useSession } from '@/components/session-provider';
import { Link } from '@/i18n/navigation';
import { type GameHistory, type Leaderboard, type Profile, type Stats, useApi } from '@/lib/api';

export function LeaderboardPanel({
  initialPeriod = 'weekly',
}: {
  initialPeriod?: 'daily' | 'weekly' | 'all-time';
}) {
  const locale = useLocale();
  const t = useTranslations('Leaderboards');
  const tp = useTranslations('Play');
  const tc = useTranslations('Common');
  const api = useApi();
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'all-time'>(initialPeriod);
  const [difficulty, setDifficulty] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Leaderboard | null>(null);
  const [state, setState] = useState<'loading' | 'error' | 'empty' | 'ready'>('loading');

  useEffect(() => {
    let active = true;
    const endpoint =
      period === 'daily'
        ? `/v1/daily/leaderboard?page=${page}&page_size=25`
        : `/v1/leaderboards?period=${period}&page=${page}&page_size=25${difficulty ? `&difficulty=${difficulty}` : ''}`;
    api<Leaderboard>(endpoint)
      .then((value) => {
        if (active) {
          setData(value);
          setState(value.items.length ? 'ready' : 'empty');
        }
      })
      .catch(() => {
        if (active) setState('error');
      });
    return () => {
      active = false;
    };
  }, [api, difficulty, page, period]);

  return (
    <div className="data-view">
      <div className="filter-bar">
        <label>
          {t('period')}
          <select
            name="period"
            autoComplete="off"
            value={period}
            onChange={(event) => {
              setState('loading');
              setPeriod(event.target.value as typeof period);
              setPage(1);
            }}
          >
            <option value="daily">{t('daily')}</option>
            <option value="weekly">{t('weekly')}</option>
            <option value="all-time">{t('allTime')}</option>
          </select>
        </label>
        <label>
          {t('difficulty')}
          <select
            name="difficulty"
            autoComplete="off"
            value={difficulty}
            disabled={period === 'daily'}
            onChange={(event) => {
              setState('loading');
              setDifficulty(event.target.value);
              setPage(1);
            }}
          >
            <option value="">{t('allDifficulties')}</option>
            {(['easy', 'normal', 'hard', 'expert'] as const).map((value) => (
              <option value={value} key={value}>
                {tp(value)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <AsyncState
        state={state}
        loadingLabel={tc('loading')}
        errorLabel={tc('loadError')}
        emptyLabel={t('empty')}
      >
        {data ? (
          <>
            <div className="table-scroll">
              <table>
                <caption className="sr-only">{t('title')}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t('rank')}</th>
                    <th scope="col">{t('player')}</th>
                    <th scope="col">{t('score')}</th>
                    <th scope="col">{t('attempts')}</th>
                    <th scope="col">{t('time')}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={`${item.rank}-${item.displayName}`}
                      className={item.isCurrentUser ? 'current-user' : undefined}
                    >
                      <td>{item.rank}</td>
                      <th scope="row">
                        {item.displayName === 'Anonymous breaker' || !item.displayName
                          ? tc('anonymous')
                          : item.displayName}
                      </th>
                      <td>{new Intl.NumberFormat(locale).format(item.score)}</td>
                      <td>{item.attemptsUsed}</td>
                      <td>{formatDuration(item.elapsedSeconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.currentUserRank ? (
              <p className="current-rank">
                {t('yourRank')}: {data.currentUserRank}
              </p>
            ) : null}
            <nav className="pagination" aria-label={tc('page', { page: data.page })}>
              <button
                className="button secondary"
                type="button"
                disabled={page <= 1}
                onClick={() => {
                  setState('loading');
                  setPage((value) => Math.max(1, value - 1));
                }}
              >
                {tc('previous')}
              </button>
              <span>{tc('page', { page: data.page })}</span>
              <button
                className="button secondary"
                type="button"
                disabled={page * data.pageSize >= data.total}
                onClick={() => {
                  setState('loading');
                  setPage((value) => value + 1);
                }}
              >
                {tc('next')}
              </button>
            </nav>
          </>
        ) : null}
      </AsyncState>
    </div>
  );
}

export function ProfilePanel({ statsOnly = false }: { statsOnly?: boolean }) {
  const locale = useLocale();
  const t = useTranslations('Profile');
  const tp = useTranslations('Play');
  const tg = useTranslations('Game');
  const ta = useTranslations('Achievements');
  const tc = useTranslations('Common');
  const api = useApi();
  const { isGuest } = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<GameHistory | null>(null);
  const [name, setName] = useState('');
  const [publicLeaderboards, setPublicLeaderboards] = useState(false);
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [error, setError] = useState<string | null>(null);
  const outcomeStats = stats as (Stats & { gamesLost?: number; gamesAbandoned?: number }) | null;
  const logicWeekProgress = stats?.achievementProgress?.logic_week;

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Profile>('/v1/me/profile'),
      api<Stats>('/v1/me/stats'),
      api<GameHistory>('/v1/me/games?page=1&page_size=8'),
    ])
      .then(([nextProfile, nextStats, nextHistory]) => {
        if (active) {
          setProfile(nextProfile);
          setStats(nextStats);
          setHistory(nextHistory);
          setName(nextProfile.displayName ?? '');
          setPublicLeaderboards(nextProfile.publicLeaderboards);
          setState('ready');
        }
      })
      .catch(() => {
        if (active) setState('error');
      });
    return () => {
      active = false;
    };
  }, [api]);

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaveState('saving');
    setError(null);
    try {
      const next = await api<Profile>('/v1/me/profile', {
        method: 'PATCH',
        body: JSON.stringify({ displayName: name || null, publicLeaderboards }),
      });
      setProfile(next);
      setSaveState('saved');
    } catch {
      setError(t('saveError'));
      setSaveState('idle');
    }
  };

  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={tc('loadError')}
      emptyLabel={tc('empty')}
    >
      {profile && stats && history ? (
        <div className="profile-layout">
          {!statsOnly ? (
            <form className="panel profile-form" onSubmit={(event) => void save(event)}>
              <h2>{t('title')}</h2>
              {isGuest ? (
                <div className="notice">
                  <p>{t('guestNotice')}</p>
                  <Link className="button secondary" href="/auth">
                    {t('upgrade')}
                  </Link>
                </div>
              ) : null}
              <label>
                {t('displayName')}
                <input
                  name="display-name"
                  autoComplete="nickname"
                  spellCheck={false}
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  minLength={2}
                  maxLength={32}
                  disabled={isGuest}
                  aria-describedby="display-name-hint"
                />
              </label>
              <small id="display-name-hint">{t('displayNameHint')}</small>
              <label className="check-row">
                <input
                  type="checkbox"
                  name="public-leaderboards"
                  checked={publicLeaderboards}
                  disabled={isGuest}
                  onChange={(event) => setPublicLeaderboards(event.target.checked)}
                />
                <span>{t('publicVisibility')}</span>
              </label>
              {error ? (
                <p className="inline-error" role="alert">
                  {error}
                </p>
              ) : null}
              <button className="button primary" disabled={saveState === 'saving' || isGuest}>
                {saveState === 'saving'
                  ? tc('saving')
                  : saveState === 'saved'
                    ? tc('saved')
                    : tc('save')}
              </button>
            </form>
          ) : null}
          <section className="stats-section" aria-labelledby="stats-heading">
            <h2 id="stats-heading">{t('stats')}</h2>
            <dl className="stats-list">
              <Stat label={t('gamesPlayed')} value={stats.gamesPlayed} />
              <Stat label={t('gamesWon')} value={stats.gamesWon} />
              <Stat label={t('gamesLost')} value={outcomeStats?.gamesLost ?? 0} />
              <Stat label={t('gamesAbandoned')} value={outcomeStats?.gamesAbandoned ?? 0} />
              <Stat label={t('winRate')} value={`${stats.winRate}%`} />
              <Stat
                label={t('averageAttempts')}
                value={stats.averageAttemptsOnWins ?? tc('unavailable')}
              />
              <Stat label={t('dailyStreak')} value={stats.dailyStreak} />
              <Stat
                label={t('fastestSolve')}
                value={
                  stats.fastestEligibleSolve === null
                    ? tc('unavailable')
                    : formatDuration(stats.fastestEligibleSolve)
                }
              />
              <Stat label={t('blackPegs')} value={stats.totalBlackPegs} />
              <Stat label={t('whitePegs')} value={stats.totalWhitePegs} />
              <Stat label={t('favouriteMode')} value={modeLabel(stats.favouriteMode, tg, tc)} />
            </dl>
            {!statsOnly ? (
              <Link className="text-link" href="/profile/stats">
                {t('viewAllStats')} →
              </Link>
            ) : null}
          </section>
          <section className="panel">
            <h2>{t('bestScores')}</h2>
            {Object.keys(stats.bestScoreByDifficulty).length ? (
              <dl className="score-list">
                {Object.entries(stats.bestScoreByDifficulty).map(([key, value]) => (
                  <div key={key}>
                    <dt>{difficultyLabel(key, tp)}</dt>
                    <dd>{new Intl.NumberFormat(locale).format(value)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p>{t('historyEmpty')}</p>
            )}
          </section>
          <section className="panel" aria-labelledby="daily-history-heading">
            <h2 id="daily-history-heading">{t('dailyHistory')}</h2>
            <p className="quiet-note">{t('dailyHistoryIntro')}</p>
            {stats.dailyCompletionHistory.length ? (
              <ol className="daily-history-list">
                {stats.dailyCompletionHistory.map((day) => (
                  <li key={day}>
                    <time dateTime={day}>{formatDailyChallengeDate(day, locale)}</time>
                  </li>
                ))}
              </ol>
            ) : (
              <p>{t('dailyHistoryEmpty')}</p>
            )}
          </section>
          <section className="panel" aria-labelledby="achievement-progress-heading">
            <h2 id="achievement-progress-heading">{t('achievementProgress')}</h2>
            <p className="quiet-note">{t('achievementProgressIntro')}</p>
            {logicWeekProgress ? (
              <div className="achievement-progress-row">
                <div>
                  <h3>{ta('logicWeek')}</h3>
                  <strong>
                    {ta('progress', {
                      current: logicWeekProgress.current,
                      target: logicWeekProgress.target,
                    })}
                  </strong>
                </div>
                <progress
                  aria-label={ta('progressLabel', {
                    achievement: ta('logicWeek'),
                    current: logicWeekProgress.current,
                    target: logicWeekProgress.target,
                  })}
                  max={logicWeekProgress.target}
                  value={logicWeekProgress.current}
                />
                <p>{ta('logicWeekBody')}</p>
              </div>
            ) : null}
            <Link className="text-link" href="/achievements">
              {t('viewAchievements')} →
            </Link>
          </section>
          <section className="recent-games">
            <h2>{t('recentGames')}</h2>
            {history.items.length ? (
              <ul className="history-list">
                {history.items.map((game) => (
                  <li key={game.id}>
                    <Link href={`/play/${game.id}/result`}>
                      <span>{difficultyLabel(game.difficulty, tp)}</span>
                      <span className={`status ${game.status}`}>{tg(`status.${game.status}`)}</span>
                      <strong>
                        {game.score === null
                          ? '—'
                          : new Intl.NumberFormat(locale).format(game.score)}
                      </strong>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p>{t('historyEmpty')}</p>
            )}
          </section>
        </div>
      ) : null}
    </AsyncState>
  );
}

const achievementDefinitions = [
  ['first_break', 'firstBreak'],
  ['one_shot', 'oneShot'],
  ['no_waste', 'noWaste'],
  ['daily_debut', 'dailyDebut'],
  ['logic_week', 'logicWeek'],
  ['hard_mode', 'hardMode'],
  ['expert_breaker', 'expertBreaker'],
  ['challenger', 'challenger'],
  ['duelist', 'duelist'],
  ['comeback', 'comeback'],
] as const;

export function AchievementsPanel() {
  const t = useTranslations('Achievements');
  const tc = useTranslations('Common');
  const api = useApi();
  const [stats, setStats] = useState<Stats | null>(null);
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  useEffect(() => {
    let active = true;
    api<Stats>('/v1/me/stats')
      .then((value) => {
        if (active) {
          setStats(value);
          setState('ready');
        }
      })
      .catch(() => {
        if (active) setState('error');
      });
    return () => {
      active = false;
    };
  }, [api]);
  const earned = useMemo(() => new Set(stats?.achievements ?? []), [stats]);
  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={tc('loadError')}
      emptyLabel={t('empty')}
    >
      {stats ? (
        <ul className="achievement-list">
          {achievementDefinitions.map(([id, key]) => {
            const progress = stats.achievementProgress?.[id];
            return (
              <li key={id} className={earned.has(id) ? 'earned' : 'locked'}>
                <span className="achievement-mark" aria-hidden="true">
                  {earned.has(id) ? '●' : '○'}
                </span>
                <div>
                  <h2>{t(key)}</h2>
                  <p>{t(`${key}Body`)}</p>
                  <small>{earned.has(id) ? t('earnedStatus') : t('locked')}</small>
                  {progress ? (
                    <div className="achievement-progress-row">
                      <span>
                        {t('progress', {
                          current: progress.current,
                          target: progress.target,
                        })}
                      </span>
                      <progress
                        aria-label={t('progressLabel', {
                          achievement: t(key),
                          current: progress.current,
                          target: progress.target,
                        })}
                        max={progress.target}
                        value={progress.current}
                      />
                    </div>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}
    </AsyncState>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
function formatDuration(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}
function formatDailyChallengeDate(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: 'UTC' }).format(
    new Date(`${value}T00:00:00Z`),
  );
}
function difficultyLabel(
  value: string | null | undefined,
  t: ReturnType<typeof useTranslations>,
  fallback = '—',
) {
  return value && ['easy', 'normal', 'hard', 'expert', 'custom'].includes(value)
    ? t(value)
    : fallback;
}
function modeLabel(
  value: string | null,
  tg: ReturnType<typeof useTranslations>,
  tc: ReturnType<typeof useTranslations>,
) {
  return value &&
    ['solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel'].includes(value)
    ? tg(`modes.${value}`)
    : tc('unavailable');
}
