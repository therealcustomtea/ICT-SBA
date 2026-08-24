// Imports the dependency required by the module implementation below.
import { cleanup, render, screen, waitFor } from '@testing-library/react';
// Imports the dependency required by the module implementation below.
import userEvent from '@testing-library/user-event';
// Imports the dependency required by the module implementation below.
import { useEffect, useState } from 'react';
// Imports the dependency required by the module implementation below.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency required by the module implementation below.
import { SessionProvider, useSession } from './session-provider';

// Stores `guestPayload` because subsequent operations depend on this value.
const guestPayload = {
  // Defines this field so the surrounding object or type has an explicit contract.
  accessToken: 'guest-access-token',
  // Defines this field so the surrounding object or type has an explicit contract.
  expiresIn: 900,
  // Defines this field so the surrounding object or type has an explicit contract.
  user: { id: 'user-1', email: null, is_anonymous: true, mfa_enabled: false },
  // Closes the expression, call, or declaration opened above.
};

// Defines `response` as the callable responsible for this operation.
function response(status: number, body?: object): Response {
  // Returns the computed result and ends the current callable.
  return new Response(body ? JSON.stringify(body) : null, {
    // Continues the surrounding operation with this required value or expression.
    status,
    // Defines this field so the surrounding object or type has an explicit contract.
    headers: { 'Content-Type': 'application/json' },
    // Closes the expression, call, or declaration opened above.
  });
  // Closes the expression, call, or declaration opened above.
}

// Defines `Probe` as the callable responsible for this operation.
function Probe() {
  // Continues the surrounding operation with this required value or expression.
  const { getAccessToken, isGuest, sendMagicLink, session, signOut, status } = useSession();
  // Continues the surrounding operation with this required value or expression.
  const [token, setToken] = useState('pending');
  // Continues the surrounding operation with this required value or expression.
  useEffect(() => {
    // Runs this required asynchronous effect without leaving it implicit.
    void getAccessToken().then((value) => setToken(value ?? 'missing'));
    // Closes the expression, call, or declaration opened above.
  }, [getAccessToken]);
  // Returns the computed result and ends the current callable.
  return (
    // Groups these sibling interface elements without adding a wrapper node.
    <>
      {/* Renders the `output` element or component for this interface state. */}
      <output aria-label="session-state">
        {/* Continues the surrounding operation with this required value or expression. */}
        {`${status}:${isGuest ? 'guest' : 'registered'}:${session?.access_token ?? 'missing'}`}
        {/* Closes the interface element opened above. */}
      </output>
      {/* Renders the `output` element or component for this interface state. */}
      <output aria-label="eager-access-token">{token}</output>
      {/* Renders the `button` element or component for this interface state. */}
      <button type="button" onClick={() => void sendMagicLink('player@example.com')}>
        {/* Continues the surrounding operation with this required value or expression. */}
        Send magic link
        {/* Closes the interface element opened above. */}
      </button>
      {/* Renders the `button` element or component for this interface state. */}
      <button type="button" onClick={() => void signOut()}>
        {/* Continues the surrounding operation with this required value or expression. */}
        Sign out
        {/* Closes the interface element opened above. */}
      </button>
      {/* Closes the interface element opened above. */}
    </>
    // Closes the expression, call, or declaration opened above.
  );
  // Closes the expression, call, or declaration opened above.
}

// Continues the surrounding operation with this required value or expression.
describe('SessionProvider', () => {
  // Stores `fetchMock` because subsequent operations depend on this value.
  const fetchMock = vi.fn<typeof fetch>();

  // Continues the surrounding operation with this required value or expression.
  beforeEach(() => {
    // Continues the surrounding operation with this required value or expression.
    vi.stubGlobal('fetch', fetchMock);
    // Continues the surrounding operation with this required value or expression.
    fetchMock.mockReset();
    // Continues the surrounding operation with this required value or expression.
    sessionStorage.clear();
    // Continues the surrounding operation with this required value or expression.
    window.history.replaceState(null, '', '/en/profile');
    // Closes the expression, call, or declaration opened above.
  });

  // Continues the surrounding operation with this required value or expression.
  afterEach(() => {
    // Continues the surrounding operation with this required value or expression.
    cleanup();
    // Continues the surrounding operation with this required value or expression.
    vi.unstubAllGlobals();
    // Closes the expression, call, or declaration opened above.
  });

  // Continues the surrounding operation with this required value or expression.
  it('falls back from refresh to a new guest session', async () => {
    // Continues the surrounding operation with this required value or expression.
    fetchMock
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(401))
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(201, guestPayload));
    // Continues the surrounding operation with this required value or expression.
    render(
      // Renders the `SessionProvider` element or component for this interface state.
      <SessionProvider>
        {/* Renders the `Probe` element or component for this interface state. */}
        <Probe />
        {/* Closes the interface element opened above. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration opened above.
    );

    // Continues the surrounding operation with this required value or expression.
    expect(await screen.findByText('ready:guest:guest-access-token')).toBeInTheDocument();
    // Continues the surrounding operation with this required value or expression.
    expect(await screen.findByText('guest-access-token')).toBeInTheDocument();
    // Continues the surrounding operation with this required value or expression.
    expect(fetchMock).toHaveBeenNthCalledWith(
      // Continues the surrounding operation with this required value or expression.
      1,
      // Supplies this literal value to the surrounding declaration or call.
      'http://localhost:8000/v1/auth/refresh',
      // Continues the surrounding operation with this required value or expression.
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
      // Closes the expression, call, or declaration opened above.
    );
    // Continues the surrounding operation with this required value or expression.
    expect(fetchMock).toHaveBeenNthCalledWith(
      // Continues the surrounding operation with this required value or expression.
      2,
      // Supplies this literal value to the surrounding declaration or call.
      'http://localhost:8000/v1/auth/guest',
      // Continues the surrounding operation with this required value or expression.
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
      // Closes the expression, call, or declaration opened above.
    );
    // Closes the expression, call, or declaration opened above.
  });

  // Continues the surrounding operation with this required value or expression.
  it('sends an authenticated magic-link request through the API', async () => {
    // Continues the surrounding operation with this required value or expression.
    fetchMock
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(200, guestPayload))
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(202));
    // Stores `user` because subsequent operations depend on this value.
    const user = userEvent.setup();
    // Continues the surrounding operation with this required value or expression.
    render(
      // Renders the `SessionProvider` element or component for this interface state.
      <SessionProvider>
        {/* Renders the `Probe` element or component for this interface state. */}
        <Probe />
        {/* Closes the interface element opened above. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration opened above.
    );
    // Runs this required asynchronous effect without leaving it implicit.
    await screen.findByText('ready:guest:guest-access-token');

    // Runs this required asynchronous effect without leaving it implicit.
    await user.click(screen.getByRole('button', { name: 'Send magic link' }));

    // Runs this required asynchronous effect without leaving it implicit.
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    // Continues the surrounding operation with this required value or expression.
    expect(fetchMock).toHaveBeenLastCalledWith(
      // Supplies this literal value to the surrounding declaration or call.
      'http://localhost:8000/v1/auth/email',
      // Continues the surrounding operation with this required value or expression.
      expect.objectContaining({
        // Defines this field so the surrounding object or type has an explicit contract.
        method: 'POST',
        // Defines this field so the surrounding object or type has an explicit contract.
        credentials: 'include',
        // Defines this field so the surrounding object or type has an explicit contract.
        headers: expect.objectContaining({ Authorization: 'Bearer guest-access-token' }),
        // Defines this field so the surrounding object or type has an explicit contract.
        body: JSON.stringify({ email: 'player@example.com', next: '/en/profile' }),
        // Closes the expression, call, or declaration opened above.
      }),
      // Closes the expression, call, or declaration opened above.
    );
    // Continues the surrounding operation with this required value or expression.
    expect(sessionStorage.getItem('cipherboard:pending-account-upgrade')).toBe('true');
    // Closes the expression, call, or declaration opened above.
  });

  // Continues the surrounding operation with this required value or expression.
  it('revokes the session and establishes a replacement guest session', async () => {
    // Continues the surrounding operation with this required value or expression.
    fetchMock
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(200, guestPayload))
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(204))
      // Continues the surrounding operation with this required value or expression.
      .mockResolvedValueOnce(response(201, { ...guestPayload, accessToken: 'replacement-token' }));
    // Stores `user` because subsequent operations depend on this value.
    const user = userEvent.setup();
    // Continues the surrounding operation with this required value or expression.
    render(
      // Renders the `SessionProvider` element or component for this interface state.
      <SessionProvider>
        {/* Renders the `Probe` element or component for this interface state. */}
        <Probe />
        {/* Closes the interface element opened above. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration opened above.
    );
    // Runs this required asynchronous effect without leaving it implicit.
    await screen.findByText('ready:guest:guest-access-token');

    // Runs this required asynchronous effect without leaving it implicit.
    await user.click(screen.getByRole('button', { name: 'Sign out' }));

    // Continues the surrounding operation with this required value or expression.
    expect(await screen.findByText('ready:guest:replacement-token')).toBeInTheDocument();
    // Continues the surrounding operation with this required value or expression.
    expect(fetchMock).toHaveBeenNthCalledWith(
      // Continues the surrounding operation with this required value or expression.
      2,
      // Supplies this literal value to the surrounding declaration or call.
      'http://localhost:8000/v1/auth/logout',
      // Continues the surrounding operation with this required value or expression.
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
      // Closes the expression, call, or declaration opened above.
    );
    // Closes the expression, call, or declaration opened above.
  });
  // Closes the expression, call, or declaration opened above.
});
