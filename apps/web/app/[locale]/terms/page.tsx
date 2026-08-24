// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { productConfig } from '@mastermind/shared-config';

// Exports this declaration as the module default.
export default async function TermsPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Terms');
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
          <h2>{t('eligibilityTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('eligibilityBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('conductTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('conductBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('serviceTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('serviceBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('contentTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('contentBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('disclaimerTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('disclaimerBody')}</p>
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
