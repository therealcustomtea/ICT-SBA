'use client';

import { useTranslations } from 'next-intl';
import { useEffect } from 'react';
import { Link } from '@/i18n/navigation';

export default function LocaleError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations('Errors');
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <div className="page-shell">
      <section className="state-panel error-panel" role="alert">
        <h1>{t('errorTitle')}</h1>
        <p>{t('errorBody')}</p>
        <div className="button-row">
          <button className="button primary" type="button" onClick={reset}>
            {t('newGame')}
          </button>
          <Link className="button secondary" href="/">
            {t('home')}
          </Link>
        </div>
      </section>
    </div>
  );
}
