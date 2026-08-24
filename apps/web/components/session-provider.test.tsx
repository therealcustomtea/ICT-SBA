// Imports the dependency used by this module.
import type { Session } from '@supabase/supabase-js';
// Imports the dependency used by this module.
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
// Imports the dependency used by this module.
import userEvent from '@testing-library/user-event';
// Imports the dependency used by this module.
import { useEffect, useState } from 'react';
// Imports the dependency used by this module.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import { SessionProvider, useSession } from './session-provider';

// Computes and stores auth for subsequent operations.
const auth = vi.hoisted(() => ({
  // Defines the getSession field in the surrounding object or type.
  getSession: vi.fn(),
  // Defines the onAuthStateChange field in the surrounding object or type.
  onAuthStateChange: vi.fn(),
  // Defines the signInAnonymously field in the surrounding object or type.
  signInAnonymously: vi.fn(),
  // Defines the signInWithOtp field in the surrounding object or type.
  signInWithOtp: vi.fn(),
  // Defines the signOut field in the surrounding object or type.
  signOut: vi.fn(),
  // Defines the updateUser field in the surrounding object or type.
  updateUser: vi.fn(),
  // Closes the expression, call, or declaration started above.
}));

// Calls vi.mock with the supplied values.
vi.mock('@/lib/supabase', () => ({
  // Defines the createSupabaseBrowserClient field in the surrounding object or type.
  createSupabaseBrowserClient: () => ({ auth }),
  // Defines the isSupabaseConfigured field in the surrounding object or type.
  isSupabaseConfigured: true,
  // Closes the expression, call, or declaration started above.
}));

// Computes and stores session for subsequent operations.
const session = (anonymous: boolean) =>
  // Begins the nested block or object completed below.
  ({
    // Defines the access_token field in the surrounding object or type.
    access_token: 'access-token',
    // Defines the user field in the surrounding object or type.
    user: { id: 'user-1', is_anonymous: anonymous },
    // Executes this line as the next step in the surrounding logic.
  }) as unknown as Session;

// Defines the MagicLinkProbe function and its callable behavior.
function MagicLinkProbe() {
  // Executes this line as the next step in the surrounding logic.
  const { sendMagicLink, status } = useSession();
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the button interface element or component.
    <button
      /* Provides the type value to the surrounding call or element. */
      type="button"
      /* Provides the disabled value to the surrounding call or element. */
      disabled={status !== 'ready'}
      /* Provides the onClick value to the surrounding call or element. */
      onClick={() => void sendMagicLink('player@example.com')}
      /* Closes the expression, call, or declaration started above. */
    >
      Send
      {/* Closes the button interface element. */}
    </button>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the TokenProbe function and its callable behavior.
function TokenProbe() {
  // Executes this line as the next step in the surrounding logic.
  const { getAccessToken } = useSession();
  // Executes this line as the next step in the surrounding logic.
  const [token, setToken] = useState('pending');
  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Executes this line as the next step in the surrounding logic.
    void getAccessToken().then((value) => setToken(value ?? 'missing'));
    // Executes this line as the next step in the surrounding logic.
  }, [getAccessToken]);
  // Returns this result to the caller and ends the current function.
  return (
    // Starts a JSX fragment that groups the following interface elements.
    <>
      {/* Renders the output interface element or component. */}
      <output>{token}</output>
      {/* Renders the button interface element or component. */}
      <button
        /* Provides the type value to the surrounding call or element. */
        type="button"
        /* Provides the onClick value to the surrounding call or element. */
        onClick={() => void getAccessToken().then((value) => setToken(value ?? 'missing'))}
        /* Closes the expression, call, or declaration started above. */
      >
        Refresh token
        {/* Closes the button interface element. */}
      </button>
      {/* Closes the JSX fragment started above. */}
    </>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Calls describe with the supplied values.
describe('SessionProvider magic links', () => {
  // Calls beforeEach with the supplied values.
  beforeEach(() => {
    // Calls auth.getSession.mockReset with the supplied values.
    auth.getSession.mockReset();
    // Calls auth.onAuthStateChange.mockReset with the supplied values.
    auth.onAuthStateChange.mockReset();
    // Calls auth.signInAnonymously.mockReset with the supplied values.
    auth.signInAnonymously.mockReset();
    // Calls auth.signInWithOtp.mockReset with the supplied values.
    auth.signInWithOtp.mockReset();
    // Calls auth.signOut.mockReset with the supplied values.
    auth.signOut.mockReset();
    // Calls auth.updateUser.mockReset with the supplied values.
    auth.updateUser.mockReset();
    // Calls auth.onAuthStateChange.mockReturnValue with the supplied values.
    auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
    // Calls auth.signInWithOtp.mockResolvedValue with the supplied values.
    auth.signInWithOtp.mockResolvedValue({ error: null });
    // Calls auth.updateUser.mockResolvedValue with the supplied values.
    auth.updateUser.mockResolvedValue({ error: null });
    // Calls sessionStorage.clear with the supplied values.
    sessionStorage.clear();
    // Calls window.history.replaceState with the supplied values.
    window.history.replaceState(null, '', '/en/auth');
    // Closes the expression, call, or declaration started above.
  });

  // Calls afterEach with the supplied values.
  afterEach(cleanup);

  // Calls it with the supplied values.
  it('upgrades a guest in place when the email is new', async () => {
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: session(true) }, error: null });
    // Calls render with the supplied values.
    render(
      // Renders the SessionProvider interface element or component.
      <SessionProvider>
        {/* Renders the MagicLinkProbe interface element or component. */}
        <MagicLinkProbe />
        {/* Closes the SessionProvider interface element. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();

    // Waits for this asynchronous operation to complete.
    await user.click(await screen.findByRole('button', { name: 'Send' }));

    // Waits for this asynchronous operation to complete.
    await waitFor(
      () =>
        // Calls expect with the supplied values.
        expect(auth.updateUser).toHaveBeenCalledWith(
          // Supplies this item to the surrounding call or collection.
          { email: 'player@example.com' },
          // Supplies this item to the surrounding call or collection.
          { emailRedirectTo: `${window.location.origin}/auth/callback?next=/en/profile` },
          // Closes the expression, call, or declaration started above.
        ),
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(auth.signInWithOtp).not.toHaveBeenCalled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('falls back to an existing-account OTP when a guest email is already registered', async () => {
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: session(true) }, error: null });
    // Calls auth.updateUser.mockResolvedValue with the supplied values.
    auth.updateUser.mockResolvedValue({ error: { code: 'email_exists', status: 422 } });
    // Calls render with the supplied values.
    render(
      // Renders the SessionProvider interface element or component.
      <SessionProvider>
        {/* Renders the MagicLinkProbe interface element or component. */}
        <MagicLinkProbe />
        {/* Closes the SessionProvider interface element. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();

    // Waits for this asynchronous operation to complete.
    await user.click(await screen.findByRole('button', { name: 'Send' }));

    // Waits for this asynchronous operation to complete.
    await waitFor(
      () =>
        // Calls expect with the supplied values.
        expect(auth.signInWithOtp).toHaveBeenCalledWith({
          // Defines the email field in the surrounding object or type.
          email: 'player@example.com',
          // Defines the options field in the surrounding object or type.
          options: {
            // Defines the emailRedirectTo field in the surrounding object or type.
            emailRedirectTo: `${window.location.origin}/auth/callback?next=/en/profile`,
            // Defines the shouldCreateUser field in the surrounding object or type.
            shouldCreateUser: false,
            // Closes the expression, call, or declaration started above.
          },
          // Closes the expression, call, or declaration started above.
        }),
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('uses OTP directly for a registered session', async () => {
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: session(false) }, error: null });
    // Calls render with the supplied values.
    render(
      // Renders the SessionProvider interface element or component.
      <SessionProvider>
        {/* Renders the MagicLinkProbe interface element or component. */}
        <MagicLinkProbe />
        {/* Closes the SessionProvider interface element. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();

    // Waits for this asynchronous operation to complete.
    await user.click(await screen.findByRole('button', { name: 'Send' }));

    // Calls expect with the supplied values.
    expect(auth.updateUser).not.toHaveBeenCalled();
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(auth.signInWithOtp).toHaveBeenCalledOnce());
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('waits for anonymous initialization before an eager child requests a token', async () => {
    // Computes and stores resolveGuest for subsequent operations.
    let resolveGuest!: (value: { data: { session: Session }; error: null }) => void;
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    // Calls auth.signInAnonymously.mockReturnValue with the supplied values.
    auth.signInAnonymously.mockReturnValue(
      // Begins the nested block or object completed below.
      new Promise((resolve) => {
        // Provides the resolveGuest value to the surrounding call or element.
        resolveGuest = resolve;
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Calls render with the supplied values.
    render(
      // Renders the SessionProvider interface element or component.
      <SessionProvider>
        {/* Renders the TokenProbe interface element or component. */}
        <TokenProbe />
        {/* Closes the SessionProvider interface element. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration started above.
    );

    // Calls expect with the supplied values.
    expect(screen.getByText('pending')).toBeInTheDocument();
    // Calls resolveGuest with the supplied values.
    resolveGuest({ data: { session: session(true) }, error: null });

    // Calls expect with the supplied values.
    expect(await screen.findByText('access-token')).toBeInTheDocument();
    // Calls expect with the supplied values.
    expect(auth.getSession).toHaveBeenCalledOnce();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('does not return the initialized token after a later signed-out event', async () => {
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: session(false) }, error: null });
    // Calls render with the supplied values.
    render(
      // Renders the SessionProvider interface element or component.
      <SessionProvider>
        {/* Renders the TokenProbe interface element or component. */}
        <TokenProbe />
        {/* Closes the SessionProvider interface element. */}
      </SessionProvider>,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls expect with the supplied values.
    expect(await screen.findByText('access-token')).toBeInTheDocument();
    // Computes and stores onAuthChange for subsequent operations.
    const onAuthChange = auth.onAuthStateChange.mock.calls[0]![0] as (
      // Defines the event field in the surrounding object or type.
      event: string,
      // Defines the nextSession field in the surrounding object or type.
      nextSession: Session | null,
      // Executes this line as the next step in the surrounding logic.
    ) => void;
    // Calls auth.getSession.mockResolvedValue with the supplied values.
    auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    // Calls act with the supplied values.
    act(() => onAuthChange('SIGNED_OUT', null));

    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Refresh token' }));

    // Calls expect with the supplied values.
    expect(await screen.findByText('missing')).toBeInTheDocument();
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
