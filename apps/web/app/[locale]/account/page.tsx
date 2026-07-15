import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { AccountPanel } from '../_components/account-panels';
export const metadata = { robots: { index: false, follow: false } };
export default async function AccountPage() {
  const t = await getTranslations('Account');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <AccountPanel />
    </FeaturePage>
  );
}
