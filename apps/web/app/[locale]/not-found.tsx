import { getTranslations } from 'next-intl/server';
import { Link } from '@/i18n/navigation';

export default async function NotFoundPage() {
  const t = await getTranslations('Errors');
  return (
    <div className="page-shell">
      <section className="state-panel">
        <h1>{t('notFoundTitle')}</h1>
        <p>{t('notFoundBody')}</p>
        <div className="button-row">
          <Link className="button primary" href="/">
            {t('home')}
          </Link>
          <Link className="button secondary" href="/play">
            {t('newGame')}
          </Link>
        </div>
      </section>
    </div>
  );
}
