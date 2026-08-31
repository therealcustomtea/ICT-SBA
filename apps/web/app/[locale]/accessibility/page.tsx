// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function AccessibilityPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Accessibility');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('title')} intro={t('intro')}>
      {/* Renders the article interface element or component. */}
      <article className="legal-document">
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('featuresTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('featuresBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('knownTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('knownBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('compatibilityTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('compatibilityBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('feedbackTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('feedbackBody')}</p>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/support">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('feedbackTitle')}
            {/* Closes the Link interface element. */}
          </Link>
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
