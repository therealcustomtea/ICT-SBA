import { getTranslations } from 'next-intl/server';
import { GameBoard } from '@/components/game-board';

export const metadata = { robots: { index: false, follow: false } };

export default async function ActiveGamePage({ params }: { params: Promise<{ gameId: string }> }) {
  const { gameId } = await params;
  const t = await getTranslations('Game');
  return (
    <div className="page-shell">
      <GameBoard title={t('title')} initialGameId={gameId} />
    </div>
  );
}
