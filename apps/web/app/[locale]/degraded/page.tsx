// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function DegradedPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Offline');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('degradedTitle')} intro={t('degradedBody')}>
      {/* Renders the section interface element or component. */}
      <section className="panel">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('status')}</h2>
        {/* Renders the div interface element or component. */}
        <div className="button-row">
          {/* Renders the Link interface element or component. */}
          <Link className="button primary" href="/play">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('soloAvailable')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/support">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('support')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the section interface element. */}
      </section>
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
