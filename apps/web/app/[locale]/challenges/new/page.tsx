import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { ChallengeCreator } from '../../_components/challenge-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function NewChallengePage() {
  const t = await getTranslations('Challenges');
  return (
    <FeaturePage title={t('createTitle')} intro={t('createIntro')}>
      <ChallengeCreator />
    </FeaturePage>
  );
}
