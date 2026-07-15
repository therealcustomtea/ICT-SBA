import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { DuelPanel } from '../../../_components/room-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function DuelPage({ params }: { params: Promise<{ roomCode: string }> }) {
  const { roomCode } = await params;
  const t = await getTranslations('Rooms');
  return (
    <FeaturePage title={t('duelTitle')}>
      <DuelPanel roomId={roomCode} />
    </FeaturePage>
  );
}
