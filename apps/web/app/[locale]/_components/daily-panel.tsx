// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useState } from 'react';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { GameBoard } from '@/components/game-board';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { type DailyDefinition, useApi } from '@/lib/api';

// Exports this declaration for use by other modules.
export function DailyPanel() {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Daily');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [daily, setDaily] = useState<DailyDefinition | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [streak, setStreak] = useState(0);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Calls Promise.all with the supplied values.
    Promise.all([api<DailyDefinition>('/v1/daily'), api<{ dailyStreak: number }>('/v1/me/stats')])
      // Begins the nested block or object completed below.
      .then(([value, stats]) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setDaily with the supplied values.
          setDaily(value);
          // Calls setStreak with the supplied values.
          setStreak(stats.dailyStreak);
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

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={t('unavailable')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={tc('empty')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {daily ? (
        // Renders the div interface element or component.
        <div className="daily-layout">
          {/* Renders the section interface element or component. */}
          <section className="daily-brief panel">
            {/* Renders the div interface element or component. */}
            <div>
              {/* Renders the p interface element or component. */}
              <p className="mode-label">{t('official')}</p>
              {/* Renders the h2 interface element or component. */}
              <h2>
                {/* Begins the nested block or object completed below. */}
                {t('today', {
                  // Defines the date field in the surrounding object or type.
                  date: new Intl.DateTimeFormat(locale, {
                    // Defines the dateStyle field in the surrounding object or type.
                    dateStyle: 'long',
                    // Defines the timeZone field in the surrounding object or type.
                    timeZone: 'UTC',
                    // Supplies this item to the surrounding call or collection.
                  }).format(new Date(`${daily.date}T00:00:00Z`)),
                  // Closes the expression, call, or declaration started above.
                })}
                {/* Closes the h2 interface element. */}
              </h2>
              {/* Closes the div interface element. */}
            </div>
            {/* Renders the dl interface element or component. */}
            <dl className="rules-summary">
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the dt interface element or component. */}
                <dt>{tc('ranked')}</dt>
                {/* Renders the dd interface element or component. */}
                <dd>
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {daily.config.codeLength} × {daily.config.colours.length}
                  {/* Closes the dd interface element. */}
                </dd>
                {/* Closes the div interface element. */}
              </div>
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the dt interface element or component. */}
                <dt>{t('rollover')}</dt>
                {/* Renders the dd interface element or component. */}
                <dd>
                  {/* Begins the nested block or object completed below. */}
                  {new Intl.DateTimeFormat(locale, {
                    // Defines the dateStyle field in the surrounding object or type.
                    dateStyle: 'medium',
                    // Defines the timeStyle field in the surrounding object or type.
                    timeStyle: 'short',
                    // Defines the timeZone field in the surrounding object or type.
                    timeZone: 'UTC',
                    // Executes this line as the next step in the surrounding logic.
                  }).format(new Date(daily.rolloverAt))}
                  {/* Closes the dd interface element. */}
                </dd>
                {/* Closes the div interface element. */}
              </div>
              {/* Closes the dl interface element. */}
            </dl>
            {/* Renders the p interface element or component. */}
            <p>{t('notStarted')}</p>
            {/* Renders the p interface element or component. */}
            <p>{t('streak', { count: streak })}</p>
            {/* Renders the p interface element or component. */}
            <p className="quiet-note">{t('rollover')}</p>
            {/* Renders the Link interface element or component. */}
            <Link href="/leaderboards?period=daily" className="text-link">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('leaderboard')} →{/* Closes the Link interface element. */}
            </Link>
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the GameBoard interface element or component. */}
          <GameBoard
            /* Provides the key value to the surrounding call or element. */
            key={daily.id}
            /* Provides the title value to the surrounding call or element. */
            title={t('title')}
            /* Provides the intro value to the surrounding call or element. */
            intro={t('intro')}
            /* Provides the startEndpoint value to the surrounding call or element. */
            startEndpoint="/v1/daily/start"
            /* Provides the startBody value to the surrounding call or element. */
            startBody={{ practice: false }}
            /* Provides the replayBody value to the surrounding call or element. */
            replayBody={{ practice: true }}
            /* Provides the replayLabel value to the surrounding call or element. */
            replayLabel={t('replay')}
            /* Provides the dailyChallengeId value to the surrounding call or element. */
            dailyChallengeId={daily.id}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Closes the div interface element. */}
        </div>
      ) : // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the AsyncState interface element. */}
    </AsyncState>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
