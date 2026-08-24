// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { Download, RefreshCw, X } from 'lucide-react';
// Imports the dependency used by this module.
import { useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useRef, useState } from 'react';

// Declares the BeforeInstallPromptEvent data shape or implementation.
interface BeforeInstallPromptEvent extends Event {
  // Defines the prompt field in the surrounding object or type.
  prompt: () => Promise<void>;
  // Defines the userChoice field in the surrounding object or type.
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function ServiceWorkerRegister() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Pwa');
  // Executes this line as the next step in the surrounding logic.
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [dismissed, setDismissed] = useState(false);
  // Computes and stores updateRequestedRef for subsequent operations.
  const updateRequestedRef = useRef(false);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores handleInstallPrompt for subsequent operations.
    const handleInstallPrompt = (event: Event) => {
      // Calls event.preventDefault with the supplied values.
      event.preventDefault();
      // Checks this condition before running the nested branch.
      if (active) {
        // Calls setDismissed with the supplied values.
        setDismissed(false);
        // Calls setInstallPrompt with the supplied values.
        setInstallPrompt(event as BeforeInstallPromptEvent);
        // Closes the expression, call, or declaration started above.
      }
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores handleInstalled for subsequent operations.
    const handleInstalled = () => setInstallPrompt(null);
    // Computes and stores handleControllerChange for subsequent operations.
    const handleControllerChange = () => {
      // Checks this condition before running the nested branch.
      if (updateRequestedRef.current) location.reload();
      // Closes the expression, call, or declaration started above.
    };
    // Calls addEventListener with the supplied values.
    addEventListener('beforeinstallprompt', handleInstallPrompt);
    // Calls addEventListener with the supplied values.
    addEventListener('appinstalled', handleInstalled);
    // Checks this condition before running the nested branch.
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      // Calls navigator.serviceWorker.addEventListener with the supplied values.
      navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);
      // Executes this line as the next step in the surrounding logic.
      void navigator.serviceWorker
        // Executes this line as the next step in the surrounding logic.
        .register('/sw.js', { updateViaCache: 'none' })
        // Begins the nested block or object completed below.
        .then((registration) => {
          // Checks this condition before running the nested branch.
          if (!active) return;
          // Checks this condition before running the nested branch.
          if (registration.waiting) {
            // Calls setDismissed with the supplied values.
            setDismissed(false);
            // Calls setWaitingWorker with the supplied values.
            setWaitingWorker(registration.waiting);
            // Closes the expression, call, or declaration started above.
          }
          // Calls registration.addEventListener with the supplied values.
          registration.addEventListener('updatefound', () => {
            // Computes and stores installing for subsequent operations.
            const installing = registration.installing;
            // Begins the nested block or object completed below.
            installing?.addEventListener('statechange', () => {
              // Checks this condition before running the nested branch.
              if (
                // Executes this line as the next step in the surrounding logic.
                active &&
                // Executes this line as the next step in the surrounding logic.
                installing.state === 'installed' &&
                // Executes this line as the next step in the surrounding logic.
                navigator.serviceWorker.controller
                // Begins the nested block or object completed below.
              ) {
                // Calls setDismissed with the supplied values.
                setDismissed(false);
                // Calls setWaitingWorker with the supplied values.
                setWaitingWorker(installing);
                // Closes the expression, call, or declaration started above.
              }
              // Closes the expression, call, or declaration started above.
            });
            // Closes the expression, call, or declaration started above.
          });
          // Executes this line as the next step in the surrounding logic.
          void registration.update();
          // Closes the expression, call, or declaration started above.
        })
        // Executes this line as the next step in the surrounding logic.
        .catch(() => undefined);
      // Closes the expression, call, or declaration started above.
    }
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Calls removeEventListener with the supplied values.
      removeEventListener('beforeinstallprompt', handleInstallPrompt);
      // Calls removeEventListener with the supplied values.
      removeEventListener('appinstalled', handleInstalled);
      // Executes this line as the next step in the surrounding logic.
      navigator.serviceWorker?.removeEventListener('controllerchange', handleControllerChange);
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, []);

  // Checks this condition before running the nested branch.
  if (dismissed || (!waitingWorker && !installPrompt)) return null;
  // Computes and stores updateAvailable for subsequent operations.
  const updateAvailable = Boolean(waitingWorker);
  // Computes and stores act for subsequent operations.
  const act = async () => {
    // Checks this condition before running the nested branch.
    if (waitingWorker) {
      // Executes this line as the next step in the surrounding logic.
      updateRequestedRef.current = true;
      // Calls waitingWorker.postMessage with the supplied values.
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
      // Returns this result to the caller and ends the current function.
      return;
      // Closes the expression, call, or declaration started above.
    }
    // Checks this condition before running the nested branch.
    if (installPrompt) {
      // Waits for this asynchronous operation to complete.
      await installPrompt.prompt();
      // Waits for this asynchronous operation to complete.
      await installPrompt.userChoice;
      // Calls setInstallPrompt with the supplied values.
      setInstallPrompt(null);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the aside interface element or component.
    <aside
      /* Provides the className value to the surrounding call or element. */
      className="pwa-prompt"
      /* Executes this line as the next step in the surrounding logic. */
      aria-labelledby="pwa-prompt-title"
      /* Executes this line as the next step in the surrounding logic. */
      aria-live="polite"
      /* Provides the role value to the surrounding call or element. */
      role="region"
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Renders the div interface element or component. */}
      <div>
        {/* Renders the strong interface element or component. */}
        <strong id="pwa-prompt-title">{t(updateAvailable ? 'updateTitle' : 'installTitle')}</strong>
        {/* Renders the p interface element or component. */}
        <p>{t(updateAvailable ? 'updateBody' : 'installBody')}</p>
        {/* Closes the div interface element. */}
      </div>
      {/* Renders the button interface element or component. */}
      <button className="button primary" type="button" onClick={() => void act()}>
        {/* Executes this line as the next step in the surrounding logic. */}
        {updateAvailable ? <RefreshCw aria-hidden="true" /> : <Download aria-hidden="true" />}
        {/* Executes this line as the next step in the surrounding logic. */}
        {t(updateAvailable ? 'updateAction' : 'installAction')}
        {/* Closes the button interface element. */}
      </button>
      {/* Renders the button interface element or component. */}
      <button
        /* Provides the className value to the surrounding call or element. */
        className="icon-button"
        /* Provides the type value to the surrounding call or element. */
        type="button"
        /* Executes this line as the next step in the surrounding logic. */
        aria-label={t('dismiss')}
        /* Provides the onClick value to the surrounding call or element. */
        onClick={() => setDismissed(true)}
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Renders the X interface element or component. */}
        <X aria-hidden="true" />
        {/* Closes the button interface element. */}
      </button>
      {/* Closes the aside interface element. */}
    </aside>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
