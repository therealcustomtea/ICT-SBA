'use client';

import { Download, RefreshCw, X } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function ServiceWorkerRegister() {
  const t = useTranslations('Pwa');
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const updateRequestedRef = useRef(false);

  useEffect(() => {
    let active = true;
    const handleInstallPrompt = (event: Event) => {
      event.preventDefault();
      if (active) {
        setDismissed(false);
        setInstallPrompt(event as BeforeInstallPromptEvent);
      }
    };
    const handleInstalled = () => setInstallPrompt(null);
    const handleControllerChange = () => {
      if (updateRequestedRef.current) location.reload();
    };
    addEventListener('beforeinstallprompt', handleInstallPrompt);
    addEventListener('appinstalled', handleInstalled);
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);
      void navigator.serviceWorker
        .register('/sw.js', { updateViaCache: 'none' })
        .then((registration) => {
          if (!active) return;
          if (registration.waiting) {
            setDismissed(false);
            setWaitingWorker(registration.waiting);
          }
          registration.addEventListener('updatefound', () => {
            const installing = registration.installing;
            installing?.addEventListener('statechange', () => {
              if (
                active &&
                installing.state === 'installed' &&
                navigator.serviceWorker.controller
              ) {
                setDismissed(false);
                setWaitingWorker(installing);
              }
            });
          });
          void registration.update();
        })
        .catch(() => undefined);
    }
    return () => {
      active = false;
      removeEventListener('beforeinstallprompt', handleInstallPrompt);
      removeEventListener('appinstalled', handleInstalled);
      navigator.serviceWorker?.removeEventListener('controllerchange', handleControllerChange);
    };
  }, []);

  if (dismissed || (!waitingWorker && !installPrompt)) return null;
  const updateAvailable = Boolean(waitingWorker);
  const act = async () => {
    if (waitingWorker) {
      updateRequestedRef.current = true;
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
      return;
    }
    if (installPrompt) {
      await installPrompt.prompt();
      await installPrompt.userChoice;
      setInstallPrompt(null);
    }
  };

  return (
    <aside
      className="pwa-prompt"
      aria-labelledby="pwa-prompt-title"
      aria-live="polite"
      role="region"
    >
      <div>
        <strong id="pwa-prompt-title">{t(updateAvailable ? 'updateTitle' : 'installTitle')}</strong>
        <p>{t(updateAvailable ? 'updateBody' : 'installBody')}</p>
      </div>
      <button className="button primary" type="button" onClick={() => void act()}>
        {updateAvailable ? <RefreshCw aria-hidden="true" /> : <Download aria-hidden="true" />}
        {t(updateAvailable ? 'updateAction' : 'installAction')}
      </button>
      <button
        className="icon-button"
        type="button"
        aria-label={t('dismiss')}
        onClick={() => setDismissed(true)}
      >
        <X aria-hidden="true" />
      </button>
    </aside>
  );
}
