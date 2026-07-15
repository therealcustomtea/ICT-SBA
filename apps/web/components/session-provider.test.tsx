import type { Session } from '@supabase/supabase-js';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useEffect, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SessionProvider, useSession } from './session-provider';

const auth = vi.hoisted(() => ({
  getSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  signInAnonymously: vi.fn(),
  signInWithOtp: vi.fn(),
  signOut: vi.fn(),
  updateUser: vi.fn(),
}));

vi.mock('@/lib/supabase', () => ({
  createSupabaseBrowserClient: () => ({ auth }),
  isSupabaseConfigured: true,
}));

const session = (anonymous: boolean) =>
  ({
    access_token: 'access-token',
    user: { id: 'user-1', is_anonymous: anonymous },
  }) as unknown as Session;

function MagicLinkProbe() {
  const { sendMagicLink, status } = useSession();
  return (
    <button
      type="button"
      disabled={status !== 'ready'}
      onClick={() => void sendMagicLink('player@example.com')}
    >
      Send
    </button>
  );
}

function TokenProbe() {
  const { getAccessToken } = useSession();
  const [token, setToken] = useState('pending');
  useEffect(() => {
    void getAccessToken().then((value) => setToken(value ?? 'missing'));
  }, [getAccessToken]);
  return (
    <>
      <output>{token}</output>
      <button
        type="button"
        onClick={() => void getAccessToken().then((value) => setToken(value ?? 'missing'))}
      >
        Refresh token
      </button>
    </>
  );
}

describe('SessionProvider magic links', () => {
  beforeEach(() => {
    auth.getSession.mockReset();
    auth.onAuthStateChange.mockReset();
    auth.signInAnonymously.mockReset();
    auth.signInWithOtp.mockReset();
    auth.signOut.mockReset();
    auth.updateUser.mockReset();
    auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
    auth.signInWithOtp.mockResolvedValue({ error: null });
    auth.updateUser.mockResolvedValue({ error: null });
    sessionStorage.clear();
    window.history.replaceState(null, '', '/en/auth');
  });

  afterEach(cleanup);

  it('upgrades a guest in place when the email is new', async () => {
    auth.getSession.mockResolvedValue({ data: { session: session(true) }, error: null });
    render(
      <SessionProvider>
        <MagicLinkProbe />
      </SessionProvider>,
    );
    const user = userEvent.setup();

    await user.click(await screen.findByRole('button', { name: 'Send' }));

    await waitFor(() =>
      expect(auth.updateUser).toHaveBeenCalledWith(
        { email: 'player@example.com' },
        { emailRedirectTo: `${window.location.origin}/auth/callback?next=/en/profile` },
      ),
    );
    expect(auth.signInWithOtp).not.toHaveBeenCalled();
  });

  it('falls back to an existing-account OTP when a guest email is already registered', async () => {
    auth.getSession.mockResolvedValue({ data: { session: session(true) }, error: null });
    auth.updateUser.mockResolvedValue({ error: { code: 'email_exists', status: 422 } });
    render(
      <SessionProvider>
        <MagicLinkProbe />
      </SessionProvider>,
    );
    const user = userEvent.setup();

    await user.click(await screen.findByRole('button', { name: 'Send' }));

    await waitFor(() =>
      expect(auth.signInWithOtp).toHaveBeenCalledWith({
        email: 'player@example.com',
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?next=/en/profile`,
          shouldCreateUser: false,
        },
      }),
    );
  });

  it('uses OTP directly for a registered session', async () => {
    auth.getSession.mockResolvedValue({ data: { session: session(false) }, error: null });
    render(
      <SessionProvider>
        <MagicLinkProbe />
      </SessionProvider>,
    );
    const user = userEvent.setup();

    await user.click(await screen.findByRole('button', { name: 'Send' }));

    expect(auth.updateUser).not.toHaveBeenCalled();
    await waitFor(() => expect(auth.signInWithOtp).toHaveBeenCalledOnce());
  });

  it('waits for anonymous initialization before an eager child requests a token', async () => {
    let resolveGuest!: (value: { data: { session: Session }; error: null }) => void;
    auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    auth.signInAnonymously.mockReturnValue(
      new Promise((resolve) => {
        resolveGuest = resolve;
      }),
    );
    render(
      <SessionProvider>
        <TokenProbe />
      </SessionProvider>,
    );

    expect(screen.getByText('pending')).toBeInTheDocument();
    resolveGuest({ data: { session: session(true) }, error: null });

    expect(await screen.findByText('access-token')).toBeInTheDocument();
    expect(auth.getSession).toHaveBeenCalledOnce();
  });

  it('does not return the initialized token after a later signed-out event', async () => {
    auth.getSession.mockResolvedValue({ data: { session: session(false) }, error: null });
    render(
      <SessionProvider>
        <TokenProbe />
      </SessionProvider>,
    );
    const user = userEvent.setup();
    expect(await screen.findByText('access-token')).toBeInTheDocument();
    const onAuthChange = auth.onAuthStateChange.mock.calls[0]![0] as (
      event: string,
      nextSession: Session | null,
    ) => void;
    auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    act(() => onAuthChange('SIGNED_OUT', null));

    await user.click(screen.getByRole('button', { name: 'Refresh token' }));

    expect(await screen.findByText('missing')).toBeInTheDocument();
  });
});
