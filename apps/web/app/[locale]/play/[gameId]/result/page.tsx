import { getTranslations } from 'next-intl/server';
import { GameBoard } from '@/components/game-board';

export const metadata = { robots: { index: false, follow: false } };

export default async function GameResultPage({ params }: { params: Promise<{ gameId: string }> }) {
  const { gameId } = await params;
  const t = await getTranslations('Result');
  return (
    <div className="page-shell">
      <GameBoard title={t('summary')} initialGameId={gameId} />
    </div>
  );
}
