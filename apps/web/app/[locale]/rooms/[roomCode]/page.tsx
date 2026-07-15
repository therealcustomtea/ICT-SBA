import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { RoomLobby } from '../../_components/room-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function RoomLobbyPage({ params }: { params: Promise<{ roomCode: string }> }) {
  const { roomCode } = await params;
  const t = await getTranslations('Rooms');
  return (
    <FeaturePage title={t('lobbyTitle')}>
      <RoomLobby roomId={roomCode} />
    </FeaturePage>
  );
}
