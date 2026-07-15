'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { AsyncState } from '@/components/feature-page';
import { GameBoard } from '@/components/game-board';
import { Link } from '@/i18n/navigation';
import { type DailyDefinition, useApi } from '@/lib/api';

export function DailyPanel() {
  const locale = useLocale();
  const t = useTranslations('Daily');
  const tc = useTranslations('Common');
  const api = useApi();
  const [daily, setDaily] = useState<DailyDefinition | null>(null);
  const [streak, setStreak] = useState(0);
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');

  useEffect(() => {
    let active = true;
    Promise.all([api<DailyDefinition>('/v1/daily'), api<{ dailyStreak: number }>('/v1/me/stats')])
      .then(([value, stats]) => {
        if (active) {
          setDaily(value);
          setStreak(stats.dailyStreak);
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

  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={t('unavailable')}
      emptyLabel={tc('empty')}
    >
      {daily ? (
        <div className="daily-layout">
          <section className="daily-brief panel">
            <div>
              <p className="mode-label">{t('official')}</p>
              <h2>
                {t('today', {
                  date: new Intl.DateTimeFormat(locale, {
                    dateStyle: 'long',
                    timeZone: 'UTC',
                  }).format(new Date(`${daily.date}T00:00:00Z`)),
                })}
              </h2>
            </div>
            <dl className="rules-summary">
              <div>
                <dt>{tc('ranked')}</dt>
                <dd>
                  {daily.config.codeLength} × {daily.config.colours.length}
                </dd>
              </div>
              <div>
                <dt>{t('rollover')}</dt>
                <dd>
                  {new Intl.DateTimeFormat(locale, {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                    timeZone: 'UTC',
                  }).format(new Date(daily.rolloverAt))}
                </dd>
              </div>
            </dl>
            <p>{t('notStarted')}</p>
            <p>{t('streak', { count: streak })}</p>
            <p className="quiet-note">{t('rollover')}</p>
            <Link href="/leaderboards?period=daily" className="text-link">
              {t('leaderboard')} →
            </Link>
          </section>
          <GameBoard
            key={daily.id}
            title={t('title')}
            intro={t('intro')}
            startEndpoint="/v1/daily/start"
            startBody={{ practice: false }}
            replayBody={{ practice: true }}
            replayLabel={t('replay')}
            dailyChallengeId={daily.id}
          />
        </div>
      ) : null}
    </AsyncState>
  );
}
