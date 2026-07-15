import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { AuthPanel } from '../_components/account-panels';
export const metadata = { robots: { index: false, follow: false } };
export default async function AuthPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const [t, query] = await Promise.all([getTranslations('Auth'), searchParams]);
  const callbackError =
    query.error === 'configuration' ? 'configuration' : query.error ? 'invalid' : null;
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <AuthPanel callbackError={callbackError} />
    </FeaturePage>
  );
}
