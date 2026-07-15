import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { Link } from '@/i18n/navigation';

export default async function DegradedPage() {
  const t = await getTranslations('Offline');
  return (
    <FeaturePage title={t('degradedTitle')} intro={t('degradedBody')}>
      <section className="panel">
        <h2>{t('status')}</h2>
        <div className="button-row">
          <Link className="button primary" href="/play">
            {t('soloAvailable')}
          </Link>
          <Link className="button secondary" href="/support">
            {t('support')}
          </Link>
        </div>
      </section>
    </FeaturePage>
  );
}
