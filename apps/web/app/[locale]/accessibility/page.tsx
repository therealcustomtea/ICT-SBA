import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { Link } from '@/i18n/navigation';

export default async function AccessibilityPage() {
  const t = await getTranslations('Accessibility');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <article className="legal-document">
        <section>
          <h2>{t('featuresTitle')}</h2>
          <p>{t('featuresBody')}</p>
        </section>
        <section>
          <h2>{t('knownTitle')}</h2>
          <p>{t('knownBody')}</p>
        </section>
        <section>
          <h2>{t('compatibilityTitle')}</h2>
          <p>{t('compatibilityBody')}</p>
        </section>
        <section>
          <h2>{t('feedbackTitle')}</h2>
          <p>{t('feedbackBody')}</p>
          <Link className="button secondary" href="/support">
            {t('feedbackTitle')}
          </Link>
        </section>
      </article>
    </FeaturePage>
  );
}
