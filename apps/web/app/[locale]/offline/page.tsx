import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { Link } from '@/i18n/navigation';

export default async function OfflinePage() {
  const t = await getTranslations('Offline');
  return (
    <FeaturePage title={t('title')} intro={t('body')}>
      <div className="state-panel">
        <div className="button-row">
          <Link className="button primary" href="/play">
            {t('retry')}
          </Link>
          <Link className="button secondary" href="/guide">
            {t('practice')}
          </Link>
        </div>
      </div>
    </FeaturePage>
  );
}
