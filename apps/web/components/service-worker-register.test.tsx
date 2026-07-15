import { NextIntlClientProvider } from 'next-intl';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/en.json';
import { ServiceWorkerRegister } from './service-worker-register';

describe('ServiceWorkerRegister', () => {
  afterEach(cleanup);

  it('offers the browser install prompt and respects dismissal', async () => {
    const prompt = vi.fn().mockResolvedValue(undefined);
    const installEvent = new Event('beforeinstallprompt', { cancelable: true });
    Object.assign(installEvent, { prompt, userChoice: Promise.resolve({ outcome: 'accepted' }) });
    const user = userEvent.setup();
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <ServiceWorkerRegister />
      </NextIntlClientProvider>,
    );

    fireEvent(window, installEvent);
    expect(await screen.findByText('Install Cipherboard')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Install' }));
    await waitFor(() => expect(prompt).toHaveBeenCalledOnce());
    expect(screen.queryByText('Install Cipherboard')).not.toBeInTheDocument();

    fireEvent(window, installEvent);
    await user.click(await screen.findByRole('button', { name: 'Dismiss' }));
    expect(screen.queryByText('Install Cipherboard')).not.toBeInTheDocument();
  });
});
