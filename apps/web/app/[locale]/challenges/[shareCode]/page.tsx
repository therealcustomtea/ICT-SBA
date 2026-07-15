import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { ChallengePlayer } from '../../_components/challenge-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function FriendChallengePage({
  params,
}: {
  params: Promise<{ shareCode: string }>;
}) {
  const { shareCode } = await params;
  const t = await getTranslations('Challenges');
  return (
    <FeaturePage title={t('playTitle')}>
      <ChallengePlayer shareCode={shareCode} />
    </FeaturePage>
  );
}
