// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { ChallengeCreator } from '../../_components/challenge-panels';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function NewChallengePage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Challenges');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('createTitle')} intro={t('createIntro')}>
      {/* Renders the ChallengeCreator interface element or component. */}
      <ChallengeCreator />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
