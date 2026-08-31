// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { DuelPanel } from '../../../_components/room-panels';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function DuelPage({ params }: { params: Promise<{ roomCode: string }> }) {
  // Executes this line as the next step in the surrounding logic.
  const { roomCode } = await params;
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Rooms');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('duelTitle')}>
      {/* Renders the DuelPanel interface element or component. */}
      <DuelPanel roomId={roomCode} />
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
