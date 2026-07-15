import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { DailyPanel } from '../_components/daily-panel';

export default async function DailyPage() {
  const t = await getTranslations('Daily');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <DailyPanel />
    </FeaturePage>
  );
}
