import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { LeaderboardPanel } from '../_components/data-panels';

export default async function LeaderboardsPage({
  searchParams,
}: {
  searchParams: Promise<{ period?: string }>;
}) {
  const [t, query] = await Promise.all([getTranslations('Leaderboards'), searchParams]);
  const initialPeriod =
    query.period === 'daily' || query.period === 'all-time' ? query.period : 'weekly';
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <LeaderboardPanel initialPeriod={initialPeriod} />
    </FeaturePage>
  );
}
