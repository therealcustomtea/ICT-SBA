// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { AuthPanel } from '../_components/account-panels';
// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };
// Exports this declaration as the module default.
export default async function AuthPage({
  // Supplies this item to the surrounding call or collection.
  searchParams,
  // Begins the nested block or object completed below.
}: {
  // Defines the searchParams field in the surrounding object or type.
  searchParams: Promise<{ error?: string }>;
  // Begins the nested block or object completed below.
}) {
  // Executes this line as the next step in the surrounding logic.
  const [t, query] = await Promise.all([getTranslations('Auth'), searchParams]);
  // Computes and stores callbackError for subsequent operations.
  const callbackError =
    // Executes this line as the next step in the surrounding logic.
    query.error === 'configuration' ? 'configuration' : query.error ? 'invalid' : null;
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('title')} intro={t('intro')}>
      {/* Renders the AuthPanel interface element or component. */}
      <AuthPanel callbackError={callbackError} />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
