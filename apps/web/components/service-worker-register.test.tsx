// Imports the dependency used by this module.
import { NextIntlClientProvider } from 'next-intl';
// Imports the dependency used by this module.
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
// Imports the dependency used by this module.
import userEvent from '@testing-library/user-event';
// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import messages from '@/messages/en.json';
// Imports the dependency used by this module.
import { ServiceWorkerRegister } from './service-worker-register';

// Calls describe with the supplied values.
describe('ServiceWorkerRegister', () => {
  // Calls afterEach with the supplied values.
  afterEach(cleanup);

  // Calls it with the supplied values.
  it('offers the browser install prompt and respects dismissal', async () => {
    // Computes and stores prompt for subsequent operations.
    const prompt = vi.fn().mockResolvedValue(undefined);
    // Computes and stores installEvent for subsequent operations.
    const installEvent = new Event('beforeinstallprompt', { cancelable: true });
    // Calls Object.assign with the supplied values.
    Object.assign(installEvent, { prompt, userChoice: Promise.resolve({ outcome: 'accepted' }) });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls render with the supplied values.
    render(
      // Renders the NextIntlClientProvider interface element or component.
      <NextIntlClientProvider locale="en" messages={messages}>
        {/* Renders the ServiceWorkerRegister interface element or component. */}
        <ServiceWorkerRegister />
        {/* Closes the NextIntlClientProvider interface element. */}
      </NextIntlClientProvider>,
      // Closes the expression, call, or declaration started above.
    );

    // Calls fireEvent with the supplied values.
    fireEvent(window, installEvent);
    // Calls expect with the supplied values.
    expect(await screen.findByText('Install Cipherboard')).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Install' }));
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(prompt).toHaveBeenCalledOnce());
    // Calls expect with the supplied values.
    expect(screen.queryByText('Install Cipherboard')).not.toBeInTheDocument();

    // Calls fireEvent with the supplied values.
    fireEvent(window, installEvent);
    // Waits for this asynchronous operation to complete.
    await user.click(await screen.findByRole('button', { name: 'Dismiss' }));
    // Calls expect with the supplied values.
    expect(screen.queryByText('Install Cipherboard')).not.toBeInTheDocument();
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
