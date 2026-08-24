// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import type { Session, User } from '@supabase/supabase-js';
// Imports the dependency used by this module.
import {
  // Supplies this item to the surrounding call or collection.
  createContext,
  // Supplies this item to the surrounding call or collection.
  useCallback,
  // Supplies this item to the surrounding call or collection.
  useContext,
  // Supplies this item to the surrounding call or collection.
  useEffect,
  // Supplies this item to the surrounding call or collection.
  useMemo,
  // Supplies this item to the surrounding call or collection.
  useRef,
  // Supplies this item to the surrounding call or collection.
  useState,
  // Executes this line as the next step in the surrounding logic.
} from 'react';
// Imports the dependency used by this module.
import { createSupabaseBrowserClient, isSupabaseConfigured } from '@/lib/supabase';
// Imports the dependency used by this module.
import { deliverProductEvent } from '@/lib/analytics-delivery';

// Computes and stores pendingUpgradeKey for subsequent operations.
const pendingUpgradeKey = 'cipherboard:pending-account-upgrade';

// Defines the reportPendingUpgrade function and its callable behavior.
function reportPendingUpgrade(nextSession: Session) {
  // Checks this condition before running the nested branch.
  if (nextSession.user.is_anonymous || sessionStorage.getItem(pendingUpgradeKey) !== 'true') return;
  // Calls sessionStorage.removeItem with the supplied values.
  sessionStorage.removeItem(pendingUpgradeKey);
  // Computes and stores locale for subsequent operations.
  const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
  // Begins the nested block or object completed below.
  void deliverProductEvent(nextSession.access_token, locale, 'account_upgraded', {
    // Defines the previousAnonymous field in the surrounding object or type.
    previousAnonymous: true,
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
}

// Declares the SessionState data shape or implementation.
type SessionState = {
  // Defines the status field in the surrounding object or type.
  status: 'loading' | 'ready' | 'error';
  // Defines the session field in the surrounding object or type.
  session: Session | null;
  // Defines the user field in the surrounding object or type.
  user: User | null;
  // Defines the error field in the surrounding object or type.
  error: string | null;
  // Defines the isGuest field in the surrounding object or type.
  isGuest: boolean;
  // Defines the getAccessToken field in the surrounding object or type.
  getAccessToken: () => Promise<string | null>;
  // Defines the sendMagicLink field in the surrounding object or type.
  sendMagicLink: (email: string) => Promise<void>;
  // Defines the signOut field in the surrounding object or type.
  signOut: () => Promise<void>;
  // Closes the expression, call, or declaration started above.
};

// Computes and stores SessionContext for subsequent operations.
const SessionContext = createContext<SessionState | null>(null);

// Defines the createSessionGate function and its callable behavior.
function createSessionGate() {
  // Computes and stores resolve for subsequent operations.
  let resolve!: (session: Session | null) => void;
  // Computes and stores promise for subsequent operations.
  const promise = new Promise<Session | null>((settle) => {
    // Provides the resolve value to the surrounding call or element.
    resolve = settle;
    // Closes the expression, call, or declaration started above.
  });
  // Returns this result to the caller and ends the current function.
  return { promise, resolve, settled: false };
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function SessionProvider({ children }: { children: React.ReactNode }) {
  // Computes and stores supabase for subsequent operations.
  const supabase = useMemo(() => createSupabaseBrowserClient(), []);
  // Executes this line as the next step in the surrounding logic.
  const [status, setStatus] = useState<SessionState['status']>(
    // Supplies this item to the surrounding call or collection.
    isSupabaseConfigured ? 'loading' : 'error',
    // Closes the expression, call, or declaration started above.
  );
  // Executes this line as the next step in the surrounding logic.
  const [session, setSession] = useState<Session | null>(null);
  // Computes and stores sessionRef for subsequent operations.
  const sessionRef = useRef<Session | null>(null);
  // Computes and stores sessionGateRef for subsequent operations.
  const sessionGateRef = useRef<ReturnType<typeof createSessionGate> | null>(null);
  // Executes this line as the next step in the surrounding logic.
  sessionGateRef.current ??= createSessionGate();
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(
    // Supplies this item to the surrounding call or collection.
    isSupabaseConfigured ? null : 'AUTH_NOT_CONFIGURED',
    // Closes the expression, call, or declaration started above.
  );

  // Computes and stores applySession for subsequent operations.
  const applySession = useCallback((nextSession: Session | null, settle = true) => {
    // Executes this line as the next step in the surrounding logic.
    sessionRef.current = nextSession;
    // Calls setSession with the supplied values.
    setSession(nextSession);
    // Computes and stores gate for subsequent operations.
    const gate = sessionGateRef.current!;
    // Checks this condition before running the nested branch.
    if (settle && !gate.settled) {
      // Executes this line as the next step in the surrounding logic.
      gate.settled = true;
      // Calls gate.resolve with the supplied values.
      gate.resolve(nextSession);
      // Closes the expression, call, or declaration started above.
    }
    // Executes this line as the next step in the surrounding logic.
  }, []);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!supabase || !isSupabaseConfigured) {
      // Returns this result to the caller and ends the current function.
      return;
      // Closes the expression, call, or declaration started above.
    }
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores initialize for subsequent operations.
    const initialize = async () => {
      // Executes this line as the next step in the surrounding logic.
      const { data, error: sessionError } = await supabase.auth.getSession();
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Checks this condition before running the nested branch.
      if (sessionError) {
        // Calls setError with the supplied values.
        setError(sessionError.code ?? 'AUTH_UNAVAILABLE');
        // Calls setStatus with the supplied values.
        setStatus('error');
        // Calls applySession with the supplied values.
        applySession(null);
        // Returns this result to the caller and ends the current function.
        return;
        // Closes the expression, call, or declaration started above.
      }
      // Checks this condition before running the nested branch.
      if (data.session) {
        // Calls reportPendingUpgrade with the supplied values.
        reportPendingUpgrade(data.session);
        // Calls setError with the supplied values.
        setError(null);
        // Calls applySession with the supplied values.
        applySession(data.session);
        // Calls setStatus with the supplied values.
        setStatus('ready');
        // Returns this result to the caller and ends the current function.
        return;
        // Closes the expression, call, or declaration started above.
      }
      // Executes this line as the next step in the surrounding logic.
      const { data: guestData, error: guestError } = await supabase.auth.signInAnonymously();
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Checks this condition before running the nested branch.
      if (guestError) {
        // Calls setError with the supplied values.
        setError(guestError.code ?? 'GUEST_SIGN_IN_FAILED');
        // Calls setStatus with the supplied values.
        setStatus('error');
        // Calls applySession with the supplied values.
        applySession(null);
        // Returns this result to the caller and ends the current function.
        return;
        // Closes the expression, call, or declaration started above.
      }
      // Calls setError with the supplied values.
      setError(null);
      // Calls applySession with the supplied values.
      applySession(guestData.session);
      // Calls setStatus with the supplied values.
      setStatus('ready');
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
    void initialize();
    // Begins the nested block or object completed below.
    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Checks this condition before running the nested branch.
      if (nextSession) reportPendingUpgrade(nextSession);
      // Calls applySession with the supplied values.
      applySession(nextSession, nextSession !== null);
      // Calls setStatus with the supplied values.
      setStatus(nextSession ? 'ready' : 'loading');
      // Closes the expression, call, or declaration started above.
    });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Calls listener.subscription.unsubscribe with the supplied values.
      listener.subscription.unsubscribe();
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [applySession, supabase]);

  // Computes and stores getAccessToken for subsequent operations.
  const getAccessToken = useCallback(async () => {
    // Checks this condition before running the nested branch.
    if (!supabase) return null;
    // Checks this condition before running the nested branch.
    if (sessionRef.current) return sessionRef.current.access_token;
    // Waits for this asynchronous operation to complete.
    await sessionGateRef.current!.promise;
    // Computes and stores initializedSession for subsequent operations.
    const initializedSession = sessionRef.current as Session | null;
    // Checks this condition before running the nested branch.
    if (initializedSession) return initializedSession.access_token;
    // Executes this line as the next step in the surrounding logic.
    const { data } = await supabase.auth.getSession();
    // Returns this result to the caller and ends the current function.
    return data.session?.access_token ?? null;
    // Executes this line as the next step in the surrounding logic.
  }, [supabase]);

  // Computes and stores sendMagicLink for subsequent operations.
  const sendMagicLink = useCallback(
    // Begins the nested block or object completed below.
    async (email: string) => {
      // Checks this condition before running the nested branch.
      if (!supabase) throw new Error('AUTH_NOT_CONFIGURED');
      // Computes and stores locale for subsequent operations.
      const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
      // Computes and stores redirectTo for subsequent operations.
      const redirectTo = `${window.location.origin}/auth/callback?next=/${locale}/profile`;
      // Checks this condition before running the nested branch.
      if (session?.user.is_anonymous) {
        // Executes this line as the next step in the surrounding logic.
        const { error: upgradeError } = await supabase.auth.updateUser(
          // Supplies this item to the surrounding call or collection.
          { email },
          // Supplies this item to the surrounding call or collection.
          { emailRedirectTo: redirectTo },
          // Closes the expression, call, or declaration started above.
        );
        // Checks this condition before running the nested branch.
        if (!upgradeError) {
          // Calls sessionStorage.setItem with the supplied values.
          sessionStorage.setItem(pendingUpgradeKey, 'true');
          // Returns this result to the caller and ends the current function.
          return;
          // Closes the expression, call, or declaration started above.
        }
        // Computes and stores accountAlreadyExists for subsequent operations.
        const accountAlreadyExists = [
          // Supplies this item to the surrounding call or collection.
          'email_exists',
          // Supplies this item to the surrounding call or collection.
          'user_already_exists',
          // Supplies this item to the surrounding call or collection.
          'identity_already_exists',
          // Executes this line as the next step in the surrounding logic.
        ].includes(upgradeError.code ?? '');
        // Checks this condition before running the nested branch.
        if (!accountAlreadyExists && upgradeError.status !== 422) throw upgradeError;
        // Closes the expression, call, or declaration started above.
      }
      // Begins the nested block or object completed below.
      const { error: otpError } = await supabase.auth.signInWithOtp({
        // Supplies this item to the surrounding call or collection.
        email,
        // Defines the options field in the surrounding object or type.
        options: { emailRedirectTo: redirectTo, shouldCreateUser: false },
        // Closes the expression, call, or declaration started above.
      });
      // Checks this condition before running the nested branch.
      if (otpError) throw otpError;
      // Closes the expression, call, or declaration started above.
    },
    // Supplies this item to the surrounding call or collection.
    [session, supabase],
    // Closes the expression, call, or declaration started above.
  );

  // Computes and stores signOut for subsequent operations.
  const signOut = useCallback(async () => {
    // Checks this condition before running the nested branch.
    if (!supabase) return;
    // Executes this line as the next step in the surrounding logic.
    const { error: signOutError } = await supabase.auth.signOut({ scope: 'local' });
    // Checks this condition before running the nested branch.
    if (signOutError) throw signOutError;
    // Executes this line as the next step in the surrounding logic.
    const { data, error: guestError } = await supabase.auth.signInAnonymously();
    // Checks this condition before running the nested branch.
    if (guestError) {
      // Calls setError with the supplied values.
      setError(guestError.code ?? 'GUEST_SIGN_IN_FAILED');
      // Calls setStatus with the supplied values.
      setStatus('error');
      // Throws this error to report an invalid or failed operation.
      throw guestError;
      // Closes the expression, call, or declaration started above.
    }
    // Calls setError with the supplied values.
    setError(null);
    // Calls applySession with the supplied values.
    applySession(data.session);
    // Calls setStatus with the supplied values.
    setStatus('ready');
    // Executes this line as the next step in the surrounding logic.
  }, [applySession, supabase]);

  // Computes and stores value for subsequent operations.
  const value = useMemo<SessionState>(
    // Begins the nested block or object completed below.
    () => ({
      // Supplies this item to the surrounding call or collection.
      status,
      // Supplies this item to the surrounding call or collection.
      session,
      // Defines the user field in the surrounding object or type.
      user: session?.user ?? null,
      // Supplies this item to the surrounding call or collection.
      error,
      // Defines the isGuest field in the surrounding object or type.
      isGuest: Boolean(session?.user?.is_anonymous),
      // Supplies this item to the surrounding call or collection.
      getAccessToken,
      // Supplies this item to the surrounding call or collection.
      sendMagicLink,
      // Supplies this item to the surrounding call or collection.
      signOut,
      // Closes the expression, call, or declaration started above.
    }),
    // Supplies this item to the surrounding call or collection.
    [status, session, error, getAccessToken, sendMagicLink, signOut],
    // Closes the expression, call, or declaration started above.
  );

  {
    /* Returns this result to the caller and ends the current function. */
  }
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function useSession(): SessionState {
  // Computes and stores value for subsequent operations.
  const value = useContext(SessionContext);
  // Checks this condition before running the nested branch.
  if (!value) throw new Error('useSession must be used inside SessionProvider');
  // Returns this result to the caller and ends the current function.
  return value;
  // Closes the expression, call, or declaration started above.
}
