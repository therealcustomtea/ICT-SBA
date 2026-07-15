import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { SupportForm } from '../_components/account-panels';
export const metadata = { robots: { index: false, follow: false } };
export default async function SupportPage() {
  const t = await getTranslations('Support');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <SupportForm />
    </FeaturePage>
  );
}
