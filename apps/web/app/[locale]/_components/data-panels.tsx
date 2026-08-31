// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useMemo, useState } from 'react';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { useSession } from '@/components/session-provider';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { type GameHistory, type Leaderboard, type Profile, type Stats, useApi } from '@/lib/api';

// Exports this declaration for use by other modules.
export function LeaderboardPanel({
  // Provides the initialPeriod value to the surrounding call or element.
  initialPeriod = 'weekly',
  // Begins the nested block or object completed below.
}: {
  // Executes this line as the next step in the surrounding logic.
  initialPeriod?: 'daily' | 'weekly' | 'all-time';
  // Begins the nested block or object completed below.
}) {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Leaderboards');
  // Computes and stores tp for subsequent operations.
  const tp = useTranslations('Play');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'all-time'>(initialPeriod);
  // Executes this line as the next step in the surrounding logic.
  const [difficulty, setDifficulty] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [page, setPage] = useState(1);
  // Executes this line as the next step in the surrounding logic.
  const [data, setData] = useState<Leaderboard | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'empty' | 'ready'>('loading');

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores endpoint for subsequent operations.
    const endpoint =
      // Provides the period value to the surrounding call or element.
      period === 'daily'
        ? // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          `/v1/daily/leaderboard?page=${page}&page_size=25`
        : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          `/v1/leaderboards?period=${period}&page=${page}&page_size=25${difficulty ? `&difficulty=${difficulty}` : ''}`;
    // Executes this line as the next step in the surrounding logic.
    api<Leaderboard>(endpoint)
      // Begins the nested block or object completed below.
      .then((value) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setData with the supplied values.
          setData(value);
          // Calls setState with the supplied values.
          setState(value.items.length ? 'ready' : 'empty');
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, difficulty, page, period]);

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="data-view">
      {/* Renders the div interface element or component. */}
      <div className="filter-bar">
        {/* Renders the label interface element or component. */}
        <label>
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('period')}
          {/* Renders the select interface element or component. */}
          <select
            /* Provides the name value to the surrounding call or element. */
            name="period"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the value value to the surrounding call or element. */
            value={period}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => {
              // Calls setState with the supplied values.
              setState('loading');
              // Calls setPeriod with the supplied values.
              setPeriod(event.target.value as typeof period);
              // Calls setPage with the supplied values.
              setPage(1);
              // Closes the expression, call, or declaration started above.
            }}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the option interface element or component. */}
            <option value="daily">{t('daily')}</option>
            {/* Renders the option interface element or component. */}
            <option value="weekly">{t('weekly')}</option>
            {/* Renders the option interface element or component. */}
            <option value="all-time">{t('allTime')}</option>
            {/* Closes the select interface element. */}
          </select>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the label interface element or component. */}
        <label>
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('difficulty')}
          {/* Renders the select interface element or component. */}
          <select
            /* Provides the name value to the surrounding call or element. */
            name="difficulty"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the value value to the surrounding call or element. */
            value={difficulty}
            /* Provides the disabled value to the surrounding call or element. */
            disabled={period === 'daily'}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => {
              // Calls setState with the supplied values.
              setState('loading');
              // Calls setDifficulty with the supplied values.
              setDifficulty(event.target.value);
              // Calls setPage with the supplied values.
              setPage(1);
              // Closes the expression, call, or declaration started above.
            }}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the option interface element or component. */}
            <option value="">{t('allDifficulties')}</option>
            {/* Executes this line as the next step in the surrounding logic. */}
            {(['easy', 'normal', 'hard', 'expert'] as const).map((value) => (
              // Renders the option interface element or component.
              <option value={value} key={value}>
                {/* Executes this line as the next step in the surrounding logic. */}
                {tp(value)}
                {/* Closes the option interface element. */}
              </option>
              // Closes the expression, call, or declaration started above.
            ))}
            {/* Closes the select interface element. */}
          </select>
          {/* Closes the label interface element. */}
        </label>
        {/* Closes the div interface element. */}
      </div>
      {/* Renders the AsyncState interface element or component. */}
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state={state}
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel={tc('loading')}
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel={tc('loadError')}
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel={t('empty')}
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Executes this line as the next step in the surrounding logic. */}
        {data ? (
          // Starts a JSX fragment that groups the following interface elements.
          <>
            {/* Renders the div interface element or component. */}
            <div className="table-scroll">
              {/* Renders the table interface element or component. */}
              <table>
                {/* Renders the caption interface element or component. */}
                <caption className="sr-only">{t('title')}</caption>
                {/* Renders the thead interface element or component. */}
                <thead>
                  {/* Renders the tr interface element or component. */}
                  <tr>
                    {/* Renders the th interface element or component. */}
                    <th scope="col">{t('rank')}</th>
                    {/* Renders the th interface element or component. */}
                    <th scope="col">{t('player')}</th>
                    {/* Renders the th interface element or component. */}
                    <th scope="col">{t('score')}</th>
                    {/* Renders the th interface element or component. */}
                    <th scope="col">{t('attempts')}</th>
                    {/* Renders the th interface element or component. */}
                    <th scope="col">{t('time')}</th>
                    {/* Closes the tr interface element. */}
                  </tr>
                  {/* Closes the thead interface element. */}
                </thead>
                {/* Renders the tbody interface element or component. */}
                <tbody>
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {data.items.map((item) => (
                    // Renders the tr interface element or component.
                    <tr
                      /* Provides the key value to the surrounding call or element. */
                      key={`${item.rank}-${item.displayName}`}
                      /* Provides the className value to the surrounding call or element. */
                      className={item.isCurrentUser ? 'current-user' : undefined}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Renders the td interface element or component. */}
                      <td>{item.rank}</td>
                      {/* Renders the th interface element or component. */}
                      <th scope="row">
                        {/* Executes this line as the next step in the surrounding logic. */}
                        {item.displayName === 'Anonymous breaker' || !item.displayName
                          ? // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            tc('anonymous')
                          : // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            item.displayName}
                        {/* Closes the th interface element. */}
                      </th>
                      {/* Renders the td interface element or component. */}
                      <td>{new Intl.NumberFormat(locale).format(item.score)}</td>
                      {/* Renders the td interface element or component. */}
                      <td>{item.attemptsUsed}</td>
                      {/* Renders the td interface element or component. */}
                      <td>{formatDuration(item.elapsedSeconds)}</td>
                      {/* Closes the tr interface element. */}
                    </tr>
                    // Closes the expression, call, or declaration started above.
                  ))}
                  {/* Closes the tbody interface element. */}
                </tbody>
                {/* Closes the table interface element. */}
              </table>
              {/* Closes the div interface element. */}
            </div>
            {/* Executes this line as the next step in the surrounding logic. */}
            {data.currentUserRank ? (
              // Renders the p interface element or component.
              <p className="current-rank">
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('yourRank')}: {data.currentUserRank}
                {/* Closes the p interface element. */}
              </p>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the nav interface element or component. */}
            <nav className="pagination" aria-label={tc('page', { page: data.page })}>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the disabled value to the surrounding call or element. */
                disabled={page <= 1}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => {
                  // Calls setState with the supplied values.
                  setState('loading');
                  // Calls setPage with the supplied values.
                  setPage((value) => Math.max(1, value - 1));
                  // Closes the expression, call, or declaration started above.
                }}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Executes this line as the next step in the surrounding logic. */}
                {tc('previous')}
                {/* Closes the button interface element. */}
              </button>
              {/* Renders the span interface element or component. */}
              <span>{tc('page', { page: data.page })}</span>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the disabled value to the surrounding call or element. */
                disabled={page * data.pageSize >= data.total}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => {
                  // Calls setState with the supplied values.
                  setState('loading');
                  // Calls setPage with the supplied values.
                  setPage((value) => value + 1);
                  // Closes the expression, call, or declaration started above.
                }}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Executes this line as the next step in the surrounding logic. */}
                {tc('next')}
                {/* Closes the button interface element. */}
              </button>
              {/* Closes the nav interface element. */}
            </nav>
            {/* Closes the JSX fragment started above. */}
          </>
        ) : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null}
        {/* Closes the AsyncState interface element. */}
      </AsyncState>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function ProfilePanel({ statsOnly = false }: { statsOnly?: boolean }) {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Profile');
  // Computes and stores tp for subsequent operations.
  const tp = useTranslations('Play');
  // Computes and stores tg for subsequent operations.
  const tg = useTranslations('Game');
  // Computes and stores ta for subsequent operations.
  const ta = useTranslations('Achievements');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const { isGuest } = useSession();
  // Executes this line as the next step in the surrounding logic.
  const [profile, setProfile] = useState<Profile | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [stats, setStats] = useState<Stats | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [history, setHistory] = useState<GameHistory | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [name, setName] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [publicLeaderboards, setPublicLeaderboards] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  // Executes this line as the next step in the surrounding logic.
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Computes and stores outcomeStats for subsequent operations.
  const outcomeStats = stats as (Stats & { gamesLost?: number; gamesAbandoned?: number }) | null;
  // Computes and stores logicWeekProgress for subsequent operations.
  const logicWeekProgress = stats?.achievementProgress?.logic_week;

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Calls Promise.all with the supplied values.
    Promise.all([
      // Supplies this item to the surrounding call or collection.
      api<Profile>('/v1/me/profile'),
      // Supplies this item to the surrounding call or collection.
      api<Stats>('/v1/me/stats'),
      // Supplies this item to the surrounding call or collection.
      api<GameHistory>('/v1/me/games?page=1&page_size=8'),
      // Closes the expression, call, or declaration started above.
    ])
      // Begins the nested block or object completed below.
      .then(([nextProfile, nextStats, nextHistory]) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setProfile with the supplied values.
          setProfile(nextProfile);
          // Calls setStats with the supplied values.
          setStats(nextStats);
          // Calls setHistory with the supplied values.
          setHistory(nextHistory);
          // Calls setName with the supplied values.
          setName(nextProfile.displayName ?? '');
          // Calls setPublicLeaderboards with the supplied values.
          setPublicLeaderboards(nextProfile.publicLeaderboards);
          // Calls setState with the supplied values.
          setState('ready');
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api]);

  // Computes and stores save for subsequent operations.
  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Calls setSaveState with the supplied values.
    setSaveState('saving');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores next for subsequent operations.
      const next = await api<Profile>('/v1/me/profile', {
        // Defines the method field in the surrounding object or type.
        method: 'PATCH',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ displayName: name || null, publicLeaderboards }),
        // Closes the expression, call, or declaration started above.
      });
      // Calls setProfile with the supplied values.
      setProfile(next);
      // Calls setSaveState with the supplied values.
      setSaveState('saved');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('saveError'));
      // Calls setSaveState with the supplied values.
      setSaveState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={tc('loadError')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={tc('empty')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {profile && stats && history ? (
        // Renders the div interface element or component.
        <div className="profile-layout">
          {/* Executes this line as the next step in the surrounding logic. */}
          {!statsOnly ? (
            // Renders the form interface element or component.
            <form className="panel profile-form" onSubmit={(event) => void save(event)}>
              {/* Renders the h2 interface element or component. */}
              <h2>{t('title')}</h2>
              {/* Executes this line as the next step in the surrounding logic. */}
              {isGuest ? (
                // Renders the div interface element or component.
                <div className="notice">
                  {/* Renders the p interface element or component. */}
                  <p>{t('guestNotice')}</p>
                  {/* Renders the Link interface element or component. */}
                  <Link className="button secondary" href="/auth">
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {t('upgrade')}
                    {/* Closes the Link interface element. */}
                  </Link>
                  {/* Closes the div interface element. */}
                </div>
              ) : // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              null}
              {/* Renders the label interface element or component. */}
              <label>
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('displayName')}
                {/* Renders the input interface element or component. */}
                <input
                  /* Provides the name value to the surrounding call or element. */
                  name="display-name"
                  /* Provides the autoComplete value to the surrounding call or element. */
                  autoComplete="nickname"
                  /* Provides the spellCheck value to the surrounding call or element. */
                  spellCheck={false}
                  /* Provides the value value to the surrounding call or element. */
                  value={name}
                  /* Provides the onChange value to the surrounding call or element. */
                  onChange={(event) => setName(event.target.value)}
                  /* Provides the minLength value to the surrounding call or element. */
                  minLength={2}
                  /* Provides the maxLength value to the surrounding call or element. */
                  maxLength={32}
                  /* Provides the disabled value to the surrounding call or element. */
                  disabled={isGuest}
                  /* Executes this line as the next step in the surrounding logic. */
                  aria-describedby="display-name-hint"
                  /* Executes this line as the next step in the surrounding logic. */
                />
                {/* Closes the label interface element. */}
              </label>
              {/* Renders the small interface element or component. */}
              <small id="display-name-hint">{t('displayNameHint')}</small>
              {/* Renders the label interface element or component. */}
              <label className="check-row">
                {/* Renders the input interface element or component. */}
                <input
                  /* Provides the type value to the surrounding call or element. */
                  type="checkbox"
                  /* Provides the name value to the surrounding call or element. */
                  name="public-leaderboards"
                  /* Provides the checked value to the surrounding call or element. */
                  checked={publicLeaderboards}
                  /* Provides the disabled value to the surrounding call or element. */
                  disabled={isGuest}
                  /* Provides the onChange value to the surrounding call or element. */
                  onChange={(event) => setPublicLeaderboards(event.target.checked)}
                  /* Executes this line as the next step in the surrounding logic. */
                />
                {/* Renders the span interface element or component. */}
                <span>{t('publicVisibility')}</span>
                {/* Closes the label interface element. */}
              </label>
              {/* Executes this line as the next step in the surrounding logic. */}
              {error ? (
                // Renders the p interface element or component.
                <p className="inline-error" role="alert">
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {error}
                  {/* Closes the p interface element. */}
                </p>
              ) : // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              null}
              {/* Renders the button interface element or component. */}
              <button className="button primary" disabled={saveState === 'saving' || isGuest}>
                {/* Executes this line as the next step in the surrounding logic. */}
                {saveState === 'saving'
                  ? // Continues the surrounding operation with this required value or expression.
                    // Executes this line as the next step in the surrounding logic.
                    tc('saving')
                  : // Continues the surrounding operation with this required value or expression.
                    // Executes this line as the next step in the surrounding logic.
                    saveState === 'saved'
                    ? // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      tc('saved')
                    : // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      tc('save')}
                {/* Closes the button interface element. */}
              </button>
              {/* Closes the form interface element. */}
            </form>
          ) : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          null}
          {/* Renders the section interface element or component. */}
          <section className="stats-section" aria-labelledby="stats-heading">
            {/* Renders the h2 interface element or component. */}
            <h2 id="stats-heading">{t('stats')}</h2>
            {/* Renders the dl interface element or component. */}
            <dl className="stats-list">
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('gamesPlayed')} value={stats.gamesPlayed} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('gamesWon')} value={stats.gamesWon} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('gamesLost')} value={outcomeStats?.gamesLost ?? 0} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('gamesAbandoned')} value={outcomeStats?.gamesAbandoned ?? 0} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('winRate')} value={`${stats.winRate}%`} />
              {/* Renders the Stat interface element or component. */}
              <Stat
                /* Provides the label value to the surrounding call or element. */
                label={t('averageAttempts')}
                /* Provides the value value to the surrounding call or element. */
                value={stats.averageAttemptsOnWins ?? tc('unavailable')}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('dailyStreak')} value={stats.dailyStreak} />
              {/* Renders the Stat interface element or component. */}
              <Stat
                /* Provides the label value to the surrounding call or element. */
                label={t('fastestSolve')}
                /* Provides the value value to the surrounding call or element. */
                value={
                  // Executes this line as the next step in the surrounding logic.
                  stats.fastestEligibleSolve === null
                    ? /* Continues the surrounding operation with this required value or expression. */
                      // Executes this line as the next step in the surrounding logic.
                      tc('unavailable')
                    : /* Continues the surrounding operation with this required value or expression. */
                      // Executes this line as the next step in the surrounding logic.
                      formatDuration(stats.fastestEligibleSolve)
                  // Closes the expression, call, or declaration started above.
                }
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('blackPegs')} value={stats.totalBlackPegs} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('whitePegs')} value={stats.totalWhitePegs} />
              {/* Renders the Stat interface element or component. */}
              <Stat label={t('favouriteMode')} value={modeLabel(stats.favouriteMode, tg, tc)} />
              {/* Closes the dl interface element. */}
            </dl>
            {/* Executes this line as the next step in the surrounding logic. */}
            {!statsOnly ? (
              // Renders the Link interface element or component.
              <Link className="text-link" href="/profile/stats">
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('viewAllStats')} →{/* Closes the Link interface element. */}
              </Link>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="panel">
            {/* Renders the h2 interface element or component. */}
            <h2>{t('bestScores')}</h2>
            {/* Executes this line as the next step in the surrounding logic. */}
            {Object.keys(stats.bestScoreByDifficulty).length ? (
              // Renders the dl interface element or component.
              <dl className="score-list">
                {/* Executes this line as the next step in the surrounding logic. */}
                {Object.entries(stats.bestScoreByDifficulty).map(([key, value]) => (
                  // Renders the div interface element or component.
                  <div key={key}>
                    {/* Renders the dt interface element or component. */}
                    <dt>{difficultyLabel(key, tp)}</dt>
                    {/* Renders the dd interface element or component. */}
                    <dd>{new Intl.NumberFormat(locale).format(value)}</dd>
                    {/* Closes the div interface element. */}
                  </div>
                  // Closes the expression, call, or declaration started above.
                ))}
                {/* Closes the dl interface element. */}
              </dl>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p>{t('historyEmpty')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="panel" aria-labelledby="daily-history-heading">
            {/* Renders the h2 interface element or component. */}
            <h2 id="daily-history-heading">{t('dailyHistory')}</h2>
            {/* Renders the p interface element or component. */}
            <p className="quiet-note">{t('dailyHistoryIntro')}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {stats.dailyCompletionHistory.length ? (
              // Renders the ol interface element or component.
              <ol className="daily-history-list">
                {/* Executes this line as the next step in the surrounding logic. */}
                {stats.dailyCompletionHistory.map((day) => (
                  // Renders the li interface element or component.
                  <li key={day}>
                    {/* Renders the time interface element or component. */}
                    <time dateTime={day}>{formatDailyChallengeDate(day, locale)}</time>
                    {/* Closes the li interface element. */}
                  </li>
                  // Closes the expression, call, or declaration started above.
                ))}
                {/* Closes the ol interface element. */}
              </ol>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p>{t('dailyHistoryEmpty')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="panel" aria-labelledby="achievement-progress-heading">
            {/* Renders the h2 interface element or component. */}
            <h2 id="achievement-progress-heading">{t('achievementProgress')}</h2>
            {/* Renders the p interface element or component. */}
            <p className="quiet-note">{t('achievementProgressIntro')}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {logicWeekProgress ? (
              // Renders the div interface element or component.
              <div className="achievement-progress-row">
                {/* Renders the div interface element or component. */}
                <div>
                  {/* Renders the h3 interface element or component. */}
                  <h3>{ta('logicWeek')}</h3>
                  {/* Renders the strong interface element or component. */}
                  <strong>
                    {/* Begins the nested block or object completed below. */}
                    {ta('progress', {
                      // Defines the current field in the surrounding object or type.
                      current: logicWeekProgress.current,
                      // Defines the target field in the surrounding object or type.
                      target: logicWeekProgress.target,
                      // Closes the expression, call, or declaration started above.
                    })}
                    {/* Closes the strong interface element. */}
                  </strong>
                  {/* Closes the div interface element. */}
                </div>
                {/* Renders the progress interface element or component. */}
                <progress
                  /* Begins the nested block or object completed below. */
                  aria-label={ta('progressLabel', {
                    // Defines the achievement field in the surrounding object or type.
                    achievement: ta('logicWeek'),
                    // Defines the current field in the surrounding object or type.
                    current: logicWeekProgress.current,
                    // Defines the target field in the surrounding object or type.
                    target: logicWeekProgress.target,
                    // Closes the expression, call, or declaration started above.
                  })}
                  /* Provides the max value to the surrounding call or element. */
                  max={logicWeekProgress.target}
                  /* Provides the value value to the surrounding call or element. */
                  value={logicWeekProgress.current}
                  /* Executes this line as the next step in the surrounding logic. */
                />
                {/* Renders the p interface element or component. */}
                <p>{ta('logicWeekBody')}</p>
                {/* Closes the div interface element. */}
              </div>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the Link interface element or component. */}
            <Link className="text-link" href="/achievements">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('viewAchievements')} →{/* Closes the Link interface element. */}
            </Link>
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="recent-games">
            {/* Renders the h2 interface element or component. */}
            <h2>{t('recentGames')}</h2>
            {/* Executes this line as the next step in the surrounding logic. */}
            {history.items.length ? (
              // Renders the ul interface element or component.
              <ul className="history-list">
                {/* Executes this line as the next step in the surrounding logic. */}
                {history.items.map((game) => (
                  // Renders the li interface element or component.
                  <li key={game.id}>
                    {/* Renders the Link interface element or component. */}
                    <Link href={`/play/${game.id}/result`}>
                      {/* Renders the span interface element or component. */}
                      <span>{difficultyLabel(game.difficulty, tp)}</span>
                      {/* Renders the span interface element or component. */}
                      <span className={`status ${game.status}`}>{tg(`status.${game.status}`)}</span>
                      {/* Renders the strong interface element or component. */}
                      <strong>
                        {/* Executes this line as the next step in the surrounding logic. */}
                        {game.score === null
                          ? // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            '—'
                          : // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            new Intl.NumberFormat(locale).format(game.score)}
                        {/* Closes the strong interface element. */}
                      </strong>
                      {/* Closes the Link interface element. */}
                    </Link>
                    {/* Closes the li interface element. */}
                  </li>
                  // Closes the expression, call, or declaration started above.
                ))}
                {/* Closes the ul interface element. */}
              </ul>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p>{t('historyEmpty')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Closes the div interface element. */}
        </div>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the AsyncState interface element. */}
    </AsyncState>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Computes and stores achievementDefinitions for subsequent operations.
const achievementDefinitions = [
  // Supplies this item to the surrounding call or collection.
  ['first_break', 'firstBreak'],
  // Supplies this item to the surrounding call or collection.
  ['one_shot', 'oneShot'],
  // Supplies this item to the surrounding call or collection.
  ['no_waste', 'noWaste'],
  // Supplies this item to the surrounding call or collection.
  ['daily_debut', 'dailyDebut'],
  // Supplies this item to the surrounding call or collection.
  ['logic_week', 'logicWeek'],
  // Supplies this item to the surrounding call or collection.
  ['hard_mode', 'hardMode'],
  // Supplies this item to the surrounding call or collection.
  ['expert_breaker', 'expertBreaker'],
  // Supplies this item to the surrounding call or collection.
  ['challenger', 'challenger'],
  // Supplies this item to the surrounding call or collection.
  ['duelist', 'duelist'],
  // Supplies this item to the surrounding call or collection.
  ['comeback', 'comeback'],
  // Executes this line as the next step in the surrounding logic.
] as const;

// Exports this declaration for use by other modules.
export function AchievementsPanel() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Achievements');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [stats, setStats] = useState<Stats | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Executes this line as the next step in the surrounding logic.
    api<Stats>('/v1/me/stats')
      // Begins the nested block or object completed below.
      .then((value) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setStats with the supplied values.
          setStats(value);
          // Calls setState with the supplied values.
          setState('ready');
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api]);
  // Computes and stores earned for subsequent operations.
  const earned = useMemo(() => new Set(stats?.achievements ?? []), [stats]);
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={tc('loadError')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={t('empty')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {stats ? (
        // Renders the ul interface element or component.
        <ul className="achievement-list">
          {/* Begins the nested block or object completed below. */}
          {achievementDefinitions.map(([id, key]) => {
            // Computes and stores progress for subsequent operations.
            const progress = stats.achievementProgress?.[id];
            // Returns this result to the caller and ends the current function.
            return (
              // Renders the li interface element or component.
              <li key={id} className={earned.has(id) ? 'earned' : 'locked'}>
                {/* Renders the span interface element or component. */}
                <span className="achievement-mark" aria-hidden="true">
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {earned.has(id) ? '●' : '○'}
                  {/* Closes the span interface element. */}
                </span>
                {/* Renders the div interface element or component. */}
                <div>
                  {/* Renders the h2 interface element or component. */}
                  <h2>{t(key)}</h2>
                  {/* Renders the p interface element or component. */}
                  <p>{t(`${key}Body`)}</p>
                  {/* Renders the small interface element or component. */}
                  <small>{earned.has(id) ? t('earnedStatus') : t('locked')}</small>
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {progress ? (
                    // Renders the div interface element or component.
                    <div className="achievement-progress-row">
                      {/* Renders the span interface element or component. */}
                      <span>
                        {/* Begins the nested block or object completed below. */}
                        {t('progress', {
                          // Defines the current field in the surrounding object or type.
                          current: progress.current,
                          // Defines the target field in the surrounding object or type.
                          target: progress.target,
                          // Closes the expression, call, or declaration started above.
                        })}
                        {/* Closes the span interface element. */}
                      </span>
                      {/* Renders the progress interface element or component. */}
                      <progress
                        /* Begins the nested block or object completed below. */
                        aria-label={t('progressLabel', {
                          // Defines the achievement field in the surrounding object or type.
                          achievement: t(key),
                          // Defines the current field in the surrounding object or type.
                          current: progress.current,
                          // Defines the target field in the surrounding object or type.
                          target: progress.target,
                          // Closes the expression, call, or declaration started above.
                        })}
                        /* Provides the max value to the surrounding call or element. */
                        max={progress.target}
                        /* Provides the value value to the surrounding call or element. */
                        value={progress.current}
                        /* Executes this line as the next step in the surrounding logic. */
                      />
                      {/* Closes the div interface element. */}
                    </div>
                  ) : // Continues the surrounding operation with this required value or expression.
                  // Executes this line as the next step in the surrounding logic.
                  null}
                  {/* Closes the div interface element. */}
                </div>
                {/* Closes the li interface element. */}
              </li>
              // Closes the expression, call, or declaration started above.
            );
            // Closes the expression, call, or declaration started above.
          })}
          {/* Closes the ul interface element. */}
        </ul>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the AsyncState interface element. */}
    </AsyncState>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the Stat function and its callable behavior.
function Stat({ label, value }: { label: string; value: string | number }) {
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div>
      {/* Renders the dt interface element or component. */}
      <dt>{label}</dt>
      {/* Renders the dd interface element or component. */}
      <dd>{value}</dd>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
// Defines the formatDuration function and its callable behavior.
function formatDuration(seconds: number) {
  // Returns this result to the caller and ends the current function.
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  // Closes the expression, call, or declaration started above.
}
// Defines the formatDailyChallengeDate function and its callable behavior.
function formatDailyChallengeDate(value: string, locale: string) {
  // Returns this result to the caller and ends the current function.
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: 'UTC' }).format(
    // Supplies this item to the surrounding call or collection.
    new Date(`${value}T00:00:00Z`),
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
// Defines the difficultyLabel function and its callable behavior.
function difficultyLabel(
  // Defines the value field in the surrounding object or type.
  value: string | null | undefined,
  // Defines the t field in the surrounding object or type.
  t: ReturnType<typeof useTranslations>,
  // Provides the fallback value to the surrounding call or element.
  fallback = '—',
  // Begins the nested block or object completed below.
) {
  // Returns this result to the caller and ends the current function.
  return value && ['easy', 'normal', 'hard', 'expert', 'custom'].includes(value)
    ? // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      t(value)
    : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      fallback;
  // Closes the expression, call, or declaration started above.
}
// Defines the modeLabel function and its callable behavior.
function modeLabel(
  // Defines the value field in the surrounding object or type.
  value: string | null,
  // Defines the tg field in the surrounding object or type.
  tg: ReturnType<typeof useTranslations>,
  // Defines the tc field in the surrounding object or type.
  tc: ReturnType<typeof useTranslations>,
  // Begins the nested block or object completed below.
) {
  // Returns this result to the caller and ends the current function.
  return value &&
    // Executes this line as the next step in the surrounding logic.
    ['solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel'].includes(value)
    ? // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      tg(`modes.${value}`)
    : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      tc('unavailable');
  // Closes the expression, call, or declaration started above.
}
