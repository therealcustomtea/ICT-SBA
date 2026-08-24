// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { LeaderboardPanel } from '../_components/data-panels';

// Exports this declaration as the module default.
export default async function LeaderboardsPage({
  // Supplies this item to the surrounding call or collection.
  searchParams,
  // Begins the nested block or object completed below.
}: {
  // Defines the searchParams field in the surrounding object or type.
  searchParams: Promise<{ period?: string }>;
  // Begins the nested block or object completed below.
}) {
  // Executes this line as the next step in the surrounding logic.
  const [t, query] = await Promise.all([getTranslations('Leaderboards'), searchParams]);
  // Computes and stores initialPeriod for subsequent operations.
  const initialPeriod =
    // Executes this line as the next step in the surrounding logic.
    query.period === 'daily' || query.period === 'all-time' ? query.period : 'weekly';
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('title')} intro={t('intro')}>
      {/* Renders the LeaderboardPanel interface element or component. */}
      <LeaderboardPanel initialPeriod={initialPeriod} />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
