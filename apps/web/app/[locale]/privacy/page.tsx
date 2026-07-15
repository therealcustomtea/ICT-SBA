import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { productConfig } from '@mastermind/shared-config';

export default async function PrivacyPage() {
  const t = await getTranslations('Privacy');
  const date = productConfig.policyDate || '—';
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <article className="legal-document">
        <p className="quiet-note">{t('updated', { date })}</p>
        <section>
          <h2>{t('collectTitle')}</h2>
          <p>{t('collectBody')}</p>
        </section>
        <section>
          <h2>{t('notCollectTitle')}</h2>
          <p>{t('notCollectBody')}</p>
        </section>
        <section>
          <h2>{t('useTitle')}</h2>
          <p>{t('useBody')}</p>
        </section>
        <section>
          <h2>{t('retentionTitle')}</h2>
          <p>{t('retentionBody')}</p>
        </section>
        <section>
          <h2>{t('childrenTitle')}</h2>
          <p>{t('childrenBody')}</p>
        </section>
        <section>
          <h2>{t('contactTitle')}</h2>
          <p>{t('contactBody')}</p>
        </section>
      </article>
    </FeaturePage>
  );
}
