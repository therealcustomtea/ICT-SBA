// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function OfflinePage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Offline');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('title')} intro={t('body')}>
      {/* Renders the div interface element or component. */}
      <div className="state-panel">
        {/* Renders the div interface element or component. */}
        <div className="button-row">
          {/* Renders the Link interface element or component. */}
          <Link className="button primary" href="/play">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('retry')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/guide">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('practice')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the div interface element. */}
      </div>
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
