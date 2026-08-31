// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { productConfig } from '@mastermind/shared-config';

// Exports this declaration as the module default.
export default async function PrivacyPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Privacy');
  // Computes and stores date for subsequent operations.
  const date = productConfig.policyDate || '—';
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('title')} intro={t('intro')}>
      {/* Renders the article interface element or component. */}
      <article className="legal-document">
        {/* Renders the p interface element or component. */}
        <p className="quiet-note">{t('updated', { date })}</p>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('collectTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('collectBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('notCollectTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('notCollectBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('useTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('useBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('retentionTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('retentionBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('childrenTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('childrenBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('contactTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('contactBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Closes the article interface element. */}
      </article>
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
