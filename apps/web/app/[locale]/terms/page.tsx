import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { productConfig } from '@mastermind/shared-config';

export default async function TermsPage() {
  const t = await getTranslations('Terms');
  const date = productConfig.policyDate || '—';
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <article className="legal-document">
        <p className="quiet-note">{t('updated', { date })}</p>
        <section>
          <h2>{t('eligibilityTitle')}</h2>
          <p>{t('eligibilityBody')}</p>
        </section>
        <section>
          <h2>{t('conductTitle')}</h2>
          <p>{t('conductBody')}</p>
        </section>
        <section>
          <h2>{t('serviceTitle')}</h2>
          <p>{t('serviceBody')}</p>
        </section>
        <section>
          <h2>{t('contentTitle')}</h2>
          <p>{t('contentBody')}</p>
        </section>
        <section>
          <h2>{t('disclaimerTitle')}</h2>
          <p>{t('disclaimerBody')}</p>
        </section>
        <section>
          <h2>{t('contactTitle')}</h2>
          <p>{t('contactBody')}</p>
        </section>
      </article>
    </FeaturePage>
  );
}
