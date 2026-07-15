'use client';

import type { Session, User } from '@supabase/supabase-js';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { createSupabaseBrowserClient, isSupabaseConfigured } from '@/lib/supabase';
import { deliverProductEvent } from '@/lib/analytics-delivery';

const pendingUpgradeKey = 'cipherboard:pending-account-upgrade';

function reportPendingUpgrade(nextSession: Session) {
  if (nextSession.user.is_anonymous || sessionStorage.getItem(pendingUpgradeKey) !== 'true') return;
  sessionStorage.removeItem(pendingUpgradeKey);
  const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
  void deliverProductEvent(nextSession.access_token, locale, 'account_upgraded', {
    previousAnonymous: true,
  });
}

type SessionState = {
  status: 'loading' | 'ready' | 'error';
  session: Session | null;
  user: User | null;
  error: string | null;
  isGuest: boolean;
  getAccessToken: () => Promise<string | null>;
  sendMagicLink: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionState | null>(null);

function createSessionGate() {
  let resolve!: (session: Session | null) => void;
  const promise = new Promise<Session | null>((settle) => {
    resolve = settle;
  });
  return { promise, resolve, settled: false };
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const supabase = useMemo(() => createSupabaseBrowserClient(), []);
  const [status, setStatus] = useState<SessionState['status']>(
    isSupabaseConfigured ? 'loading' : 'error',
  );
  const [session, setSession] = useState<Session | null>(null);
  const sessionRef = useRef<Session | null>(null);
  const sessionGateRef = useRef<ReturnType<typeof createSessionGate> | null>(null);
  sessionGateRef.current ??= createSessionGate();
  const [error, setError] = useState<string | null>(
    isSupabaseConfigured ? null : 'AUTH_NOT_CONFIGURED',
  );

  const applySession = useCallback((nextSession: Session | null, settle = true) => {
    sessionRef.current = nextSession;
    setSession(nextSession);
    const gate = sessionGateRef.current!;
    if (settle && !gate.settled) {
      gate.settled = true;
      gate.resolve(nextSession);
    }
  }, []);

  useEffect(() => {
    if (!supabase || !isSupabaseConfigured) {
      return;
    }
    let active = true;
    const initialize = async () => {
      const { data, error: sessionError } = await supabase.auth.getSession();
      if (!active) return;
      if (sessionError) {
        setError(sessionError.code ?? 'AUTH_UNAVAILABLE');
        setStatus('error');
        applySession(null);
        return;
      }
      if (data.session) {
        reportPendingUpgrade(data.session);
        setError(null);
        applySession(data.session);
        setStatus('ready');
        return;
      }
      const { data: guestData, error: guestError } = await supabase.auth.signInAnonymously();
      if (!active) return;
      if (guestError) {
        setError(guestError.code ?? 'GUEST_SIGN_IN_FAILED');
        setStatus('error');
        applySession(null);
        return;
      }
      setError(null);
      applySession(guestData.session);
      setStatus('ready');
    };
    void initialize();
    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) return;
      if (nextSession) reportPendingUpgrade(nextSession);
      applySession(nextSession, nextSession !== null);
      setStatus(nextSession ? 'ready' : 'loading');
    });
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [applySession, supabase]);

  const getAccessToken = useCallback(async () => {
    if (!supabase) return null;
    if (sessionRef.current) return sessionRef.current.access_token;
    await sessionGateRef.current!.promise;
    const initializedSession = sessionRef.current as Session | null;
    if (initializedSession) return initializedSession.access_token;
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, [supabase]);

  const sendMagicLink = useCallback(
    async (email: string) => {
      if (!supabase) throw new Error('AUTH_NOT_CONFIGURED');
      const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
      const redirectTo = `${window.location.origin}/auth/callback?next=/${locale}/profile`;
      if (session?.user.is_anonymous) {
        const { error: upgradeError } = await supabase.auth.updateUser(
          { email },
          { emailRedirectTo: redirectTo },
        );
        if (!upgradeError) {
          sessionStorage.setItem(pendingUpgradeKey, 'true');
          return;
        }
        const accountAlreadyExists = [
          'email_exists',
          'user_already_exists',
          'identity_already_exists',
        ].includes(upgradeError.code ?? '');
        if (!accountAlreadyExists && upgradeError.status !== 422) throw upgradeError;
      }
      const { error: otpError } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: redirectTo, shouldCreateUser: false },
      });
      if (otpError) throw otpError;
    },
    [session, supabase],
  );

  const signOut = useCallback(async () => {
    if (!supabase) return;
    const { error: signOutError } = await supabase.auth.signOut({ scope: 'local' });
    if (signOutError) throw signOutError;
    const { data, error: guestError } = await supabase.auth.signInAnonymously();
    if (guestError) {
      setError(guestError.code ?? 'GUEST_SIGN_IN_FAILED');
      setStatus('error');
      throw guestError;
    }
    setError(null);
    applySession(data.session);
    setStatus('ready');
  }, [applySession, supabase]);

  const value = useMemo<SessionState>(
    () => ({
      status,
      session,
      user: session?.user ?? null,
      error,
      isGuest: Boolean(session?.user?.is_anonymous),
      getAccessToken,
      sendMagicLink,
      signOut,
    }),
    [status, session, error, getAccessToken, sendMagicLink, signOut],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionState {
  const value = useContext(SessionContext);
  if (!value) throw new Error('useSession must be used inside SessionProvider');
  return value;
}
