// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { ProfilePanel } from '../_components/data-panels';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function ProfilePage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Profile');
  // Computes and stores ta for subsequent operations.
  const ta = await getTranslations('Nav');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage
      /* Provides the title value to the surrounding call or element. */
      title={t('title')}
      /* Provides the actions value to the surrounding call or element. */
      actions={
        // Renders the div interface element or component.
        <div className="button-row">
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/achievements">
            {/* Executes this line as the next step in the surrounding logic. */}
            {ta('achievements')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/settings">
            {/* Executes this line as the next step in the surrounding logic. */}
            {ta('settings')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/account">
            {/* Executes this line as the next step in the surrounding logic. */}
            {ta('account')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Closes the div interface element. */}
        </div>
        // Closes the expression, call, or declaration started above.
      }
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Renders the ProfilePanel interface element or component. */}
      <ProfilePanel />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
