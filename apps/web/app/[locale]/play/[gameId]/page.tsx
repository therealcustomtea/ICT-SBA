// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { GameBoard } from '@/components/game-board';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function ActiveGamePage({ params }: { params: Promise<{ gameId: string }> }) {
  // Executes this line as the next step in the surrounding logic.
  const { gameId } = await params;
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Game');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="page-shell">
      {/* Renders the GameBoard interface element or component. */}
      <GameBoard title={t('title')} initialGameId={gameId} />
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
