// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { ChallengePlayer } from '../../_components/challenge-panels';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function FriendChallengePage({
  // Supplies this item to the surrounding call or collection.
  params,
  // Begins the nested block or object completed below.
}: {
  // Defines the params field in the surrounding object or type.
  params: Promise<{ shareCode: string }>;
  // Begins the nested block or object completed below.
}) {
  // Executes this line as the next step in the surrounding logic.
  const { shareCode } = await params;
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Challenges');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('playTitle')}>
      {/* Renders the ChallengePlayer interface element or component. */}
      <ChallengePlayer shareCode={shareCode} />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
