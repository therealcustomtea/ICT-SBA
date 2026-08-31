// Selects the execution mode required by this module.
'use client';

// Imports the dependency required by the module implementation below.
import {
  // Continues the surrounding operation with this required value or expression.
  createContext,
  // Continues the surrounding operation with this required value or expression.
  useCallback,
  // Continues the surrounding operation with this required value or expression.
  useContext,
  // Continues the surrounding operation with this required value or expression.
  useEffect,
  // Continues the surrounding operation with this required value or expression.
  useMemo,
  // Continues the surrounding operation with this required value or expression.
  useRef,
  // Continues the surrounding operation with this required value or expression.
  useState,
  // Closes the expression, call, or declaration opened above.
} from 'react';
// Imports the dependency required by the module implementation below.
import { deliverProductEvent } from '@/lib/analytics-delivery';

// Stores `apiOrigin` because subsequent operations depend on this value.
const apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8000';
// Stores `pendingUpgradeKey` because subsequent operations depend on this value.
const pendingUpgradeKey = 'cipherboard:pending-account-upgrade';

// Exports this declaration because other modules rely on its contract.
export type AuthUser = {
  // Defines this field so the surrounding object or type has an explicit contract.
  id: string;
  // Defines this field so the surrounding object or type has an explicit contract.
  email: string | null;
  // Defines this field so the surrounding object or type has an explicit contract.
  is_anonymous: boolean;
  // Defines this field so the surrounding object or type has an explicit contract.
  mfa_enabled: boolean;
  // Closes the expression, call, or declaration opened above.
};

// Exports this declaration because other modules rely on its contract.
export type Session = {
  // Defines this field so the surrounding object or type has an explicit contract.
  access_token: string;
  // Defines this field so the surrounding object or type has an explicit contract.
  expires_at: number;
  // Defines this field so the surrounding object or type has an explicit contract.
  user: AuthUser;
  // Closes the expression, call, or declaration opened above.
};

// Continues the surrounding operation with this required value or expression.
type AuthSessionResponse = {
  // Defines this field so the surrounding object or type has an explicit contract.
  accessToken: string;
  // Defines this field so the surrounding object or type has an explicit contract.
  expiresIn: number;
  // Defines this field so the surrounding object or type has an explicit contract.
  user: AuthUser;
  // Closes the expression, call, or declaration opened above.
};

// Continues the surrounding operation with this required value or expression.
type SessionState = {
  // Defines this field so the surrounding object or type has an explicit contract.
  status: 'loading' | 'ready' | 'error';
  // Defines this field so the surrounding object or type has an explicit contract.
  session: Session | null;
  // Defines this field so the surrounding object or type has an explicit contract.
  user: AuthUser | null;
  // Defines this field so the surrounding object or type has an explicit contract.
  error: string | null;
  // Defines this field so the surrounding object or type has an explicit contract.
  isGuest: boolean;
  // Defines this field so the surrounding object or type has an explicit contract.
  getAccessToken: () => Promise<string | null>;
  // Defines this field so the surrounding object or type has an explicit contract.
  sendMagicLink: (email: string) => Promise<void>;
  // Defines this field so the surrounding object or type has an explicit contract.
  signOut: () => Promise<void>;
  // Closes the expression, call, or declaration opened above.
};

// Stores `SessionContext` because subsequent operations depend on this value.
const SessionContext = createContext<SessionState | null>(null);

// Defines `toSession` as the callable responsible for this operation.
function toSession(payload: AuthSessionResponse): Session {
  // Returns the computed result and ends the current callable.
  return {
    // Defines this field so the surrounding object or type has an explicit contract.
    access_token: payload.accessToken,
    // Defines this field so the surrounding object or type has an explicit contract.
    expires_at: Date.now() + payload.expiresIn * 1000,
    // Defines this field so the surrounding object or type has an explicit contract.
    user: payload.user,
    // Closes the expression, call, or declaration opened above.
  };
  // Closes the expression, call, or declaration opened above.
}

// Defines `authRequest` as the callable responsible for this operation.
async function authRequest(path: string, init: RequestInit = {}): Promise<Response> {
  // Returns the computed result and ends the current callable.
  return fetch(`${apiOrigin}${path}`, {
    // Continues the surrounding operation with this required value or expression.
    ...init,
    // Defines this field so the surrounding object or type has an explicit contract.
    credentials: 'include',
    // Defines this field so the surrounding object or type has an explicit contract.
    headers: { 'Content-Type': 'application/json', ...init.headers },
    // Closes the expression, call, or declaration opened above.
  });
  // Closes the expression, call, or declaration opened above.
}

// Defines `sessionRequest` as the callable responsible for this operation.
async function sessionRequest(path: '/v1/auth/guest' | '/v1/auth/refresh'): Promise<Session> {
  // Stores `response` because subsequent operations depend on this value.
  const response = await authRequest(path, { method: 'POST' });
  // Guards the nested operation so it runs only when this condition is satisfied.
  if (!response.ok)
    // Throws this error so invalid state cannot continue silently.
    throw new Error(response.status === 401 ? 'SESSION_EXPIRED' : 'AUTH_UNAVAILABLE');
  // Returns the computed result and ends the current callable.
  return toSession((await response.json()) as AuthSessionResponse);
  // Closes the expression, call, or declaration opened above.
}

// Defines `reportPendingUpgrade` as the callable responsible for this operation.
function reportPendingUpgrade(nextSession: Session) {
  // Guards the nested operation so it runs only when this condition is satisfied.
  if (nextSession.user.is_anonymous || sessionStorage.getItem(pendingUpgradeKey) !== 'true') return;
  // Continues the surrounding operation with this required value or expression.
  sessionStorage.removeItem(pendingUpgradeKey);
  // Stores `locale` because subsequent operations depend on this value.
  const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
  // Runs this required asynchronous effect without leaving it implicit.
  void deliverProductEvent(nextSession.access_token, locale, 'account_upgraded', {
    // Defines this field so the surrounding object or type has an explicit contract.
    previousAnonymous: true,
    // Closes the expression, call, or declaration opened above.
  });
  // Closes the expression, call, or declaration opened above.
}

// Exports this declaration because other modules rely on its contract.
export function SessionProvider({ children }: { children: React.ReactNode }) {
  // Continues the surrounding operation with this required value or expression.
  const [status, setStatus] = useState<SessionState['status']>('loading');
  // Continues the surrounding operation with this required value or expression.
  const [session, setSession] = useState<Session | null>(null);
  // Continues the surrounding operation with this required value or expression.
  const [error, setError] = useState<string | null>(null);
  // Stores `sessionRef` because subsequent operations depend on this value.
  const sessionRef = useRef<Session | null>(null);
  // Stores `initializationRef` because subsequent operations depend on this value.
  const initializationRef = useRef<Promise<Session | null> | null>(null);
  // Stores `refreshRef` because subsequent operations depend on this value.
  const refreshRef = useRef<Promise<Session> | null>(null);

  // Stores `applySession` because subsequent operations depend on this value.
  const applySession = useCallback((nextSession: Session | null) => {
    // Continues the surrounding operation with this required value or expression.
    sessionRef.current = nextSession;
    // Continues the surrounding operation with this required value or expression.
    setSession(nextSession);
    // Closes the expression, call, or declaration opened above.
  }, []);

  // Stores `refresh` because subsequent operations depend on this value.
  const refresh = useCallback(async () => {
    // Continues the surrounding operation with this required value or expression.
    refreshRef.current ??= sessionRequest('/v1/auth/refresh').finally(() => {
      // Continues the surrounding operation with this required value or expression.
      refreshRef.current = null;
      // Closes the expression, call, or declaration opened above.
    });
    // Stores `nextSession` because subsequent operations depend on this value.
    const nextSession = await refreshRef.current;
    // Continues the surrounding operation with this required value or expression.
    reportPendingUpgrade(nextSession);
    // Continues the surrounding operation with this required value or expression.
    applySession(nextSession);
    // Returns the computed result and ends the current callable.
    return nextSession;
    // Closes the expression, call, or declaration opened above.
  }, [applySession]);

  // Continues the surrounding operation with this required value or expression.
  useEffect(() => {
    // Stores `active` because subsequent operations depend on this value.
    let active = true;
    // Stores `initialize` because subsequent operations depend on this value.
    const initialize = async () => {
      // Starts an operation whose expected failures are handled below.
      try {
        // Stores `nextSession` because subsequent operations depend on this value.
        let nextSession: Session;
        // Starts an operation whose expected failures are handled below.
        try {
          // Continues the surrounding operation with this required value or expression.
          nextSession = await refresh();
          // Closes the expression, call, or declaration opened above.
        } catch {
          // Continues the surrounding operation with this required value or expression.
          nextSession = await sessionRequest('/v1/auth/guest');
          // Closes the expression, call, or declaration opened above.
        }
        // Guards the nested operation so it runs only when this condition is satisfied.
        if (active) {
          // Continues the surrounding operation with this required value or expression.
          applySession(nextSession);
          // Continues the surrounding operation with this required value or expression.
          setError(null);
          // Continues the surrounding operation with this required value or expression.
          setStatus('ready');
          // Closes the expression, call, or declaration opened above.
        }
        // Returns the computed result and ends the current callable.
        return nextSession;
        // Closes the expression, call, or declaration opened above.
      } catch (cause) {
        // Guards the nested operation so it runs only when this condition is satisfied.
        if (active) {
          // Continues the surrounding operation with this required value or expression.
          applySession(null);
          // Continues the surrounding operation with this required value or expression.
          setError(cause instanceof Error ? cause.message : 'AUTH_UNAVAILABLE');
          // Continues the surrounding operation with this required value or expression.
          setStatus('error');
          // Closes the expression, call, or declaration opened above.
        }
        // Returns the computed result and ends the current callable.
        return null;
        // Closes the expression, call, or declaration opened above.
      }
      // Closes the expression, call, or declaration opened above.
    };
    // Continues the surrounding operation with this required value or expression.
    initializationRef.current = initialize();
    // Returns the computed result and ends the current callable.
    return () => {
      // Continues the surrounding operation with this required value or expression.
      active = false;
      // Closes the expression, call, or declaration opened above.
    };
    // Closes the expression, call, or declaration opened above.
  }, [applySession, refresh]);

  // Continues the surrounding operation with this required value or expression.
  useEffect(() => {
    // Guards the nested operation so it runs only when this condition is satisfied.
    if (!session) return;
    // Stores `delay` because subsequent operations depend on this value.
    const delay = Math.max(1_000, session.expires_at - Date.now() - 60_000);
    // Stores `timer` because subsequent operations depend on this value.
    const timer = window.setTimeout(() => {
      // Runs this required asynchronous effect without leaving it implicit.
      void refresh().catch(() => {
        // Continues the surrounding operation with this required value or expression.
        setError('SESSION_EXPIRED');
        // Continues the surrounding operation with this required value or expression.
        setStatus('error');
        // Closes the expression, call, or declaration opened above.
      });
      // Closes the expression, call, or declaration opened above.
    }, delay);
    // Returns the computed result and ends the current callable.
    return () => window.clearTimeout(timer);
    // Closes the expression, call, or declaration opened above.
  }, [refresh, session]);

  // Stores `getAccessToken` because subsequent operations depend on this value.
  const getAccessToken = useCallback(async () => {
    // Stores `current` because subsequent operations depend on this value.
    let current = sessionRef.current;
    // Guards the nested operation so it runs only when this condition is satisfied.
    if (!current && !initializationRef.current) await Promise.resolve();
    // Guards the nested operation so it runs only when this condition is satisfied.
    if (!current && initializationRef.current) current = await initializationRef.current;
    // Guards the nested operation so it runs only when this condition is satisfied.
    if (!current) return null;
    // Guards the nested operation so it runs only when this condition is satisfied.
    if (current.expires_at - Date.now() <= 60_000) {
      // Starts an operation whose expected failures are handled below.
      try {
        // Continues the surrounding operation with this required value or expression.
        current = await refresh();
        // Closes the expression, call, or declaration opened above.
      } catch {
        // Returns the computed result and ends the current callable.
        return null;
        // Closes the expression, call, or declaration opened above.
      }
      // Closes the expression, call, or declaration opened above.
    }
    // Returns the computed result and ends the current callable.
    return current.access_token;
    // Closes the expression, call, or declaration opened above.
  }, [refresh]);

  // Stores `sendMagicLink` because subsequent operations depend on this value.
  const sendMagicLink = useCallback(
    // Continues the surrounding operation with this required value or expression.
    async (email: string) => {
      // Stores `accessToken` because subsequent operations depend on this value.
      const accessToken = await getAccessToken();
      // Guards the nested operation so it runs only when this condition is satisfied.
      if (!accessToken) throw new Error('AUTH_UNAVAILABLE');
      // Stores `locale` because subsequent operations depend on this value.
      const locale = window.location.pathname.split('/')[1] === 'zh-Hant' ? 'zh-Hant' : 'en';
      // Stores `response` because subsequent operations depend on this value.
      const response = await authRequest('/v1/auth/email', {
        // Defines this field so the surrounding object or type has an explicit contract.
        method: 'POST',
        // Defines this field so the surrounding object or type has an explicit contract.
        headers: { Authorization: `Bearer ${accessToken}` },
        // Defines this field so the surrounding object or type has an explicit contract.
        body: JSON.stringify({ email, next: `/${locale}/profile` }),
        // Closes the expression, call, or declaration opened above.
      });
      // Guards the nested operation so it runs only when this condition is satisfied.
      if (!response.ok) {
        // Stores `body` because subsequent operations depend on this value.
        const body = (await response.json().catch(() => null)) as { code?: string } | null;
        // Throws this error so invalid state cannot continue silently.
        throw new Error(body?.code ?? 'MAGIC_LINK_FAILED');
        // Closes the expression, call, or declaration opened above.
      }
      // Guards the nested operation so it runs only when this condition is satisfied.
      if (sessionRef.current?.user.is_anonymous) sessionStorage.setItem(pendingUpgradeKey, 'true');
      // Closes the expression, call, or declaration opened above.
    },
    // Continues the surrounding operation with this required value or expression.
    [getAccessToken],
    // Closes the expression, call, or declaration opened above.
  );

  // Stores `signOut` because subsequent operations depend on this value.
  const signOut = useCallback(async () => {
    // Runs this required asynchronous effect without leaving it implicit.
    await authRequest('/v1/auth/logout', { method: 'POST' });
    // Starts an operation whose expected failures are handled below.
    try {
      // Stores `guestSession` because subsequent operations depend on this value.
      const guestSession = await sessionRequest('/v1/auth/guest');
      // Continues the surrounding operation with this required value or expression.
      applySession(guestSession);
      // Continues the surrounding operation with this required value or expression.
      setError(null);
      // Continues the surrounding operation with this required value or expression.
      setStatus('ready');
      // Closes the expression, call, or declaration opened above.
    } catch (cause) {
      // Continues the surrounding operation with this required value or expression.
      applySession(null);
      // Continues the surrounding operation with this required value or expression.
      setError(cause instanceof Error ? cause.message : 'GUEST_SIGN_IN_FAILED');
      // Continues the surrounding operation with this required value or expression.
      setStatus('error');
      // Throws this error so invalid state cannot continue silently.
      throw cause;
      // Closes the expression, call, or declaration opened above.
    }
    // Closes the expression, call, or declaration opened above.
  }, [applySession]);

  // Stores `value` because subsequent operations depend on this value.
  const value = useMemo<SessionState>(
    // Continues the surrounding operation with this required value or expression.
    () => ({
      // Continues the surrounding operation with this required value or expression.
      status,
      // Continues the surrounding operation with this required value or expression.
      session,
      // Defines this field so the surrounding object or type has an explicit contract.
      user: session?.user ?? null,
      // Continues the surrounding operation with this required value or expression.
      error,
      // Defines this field so the surrounding object or type has an explicit contract.
      isGuest: Boolean(session?.user.is_anonymous),
      // Continues the surrounding operation with this required value or expression.
      getAccessToken,
      // Continues the surrounding operation with this required value or expression.
      sendMagicLink,
      // Continues the surrounding operation with this required value or expression.
      signOut,
      // Closes the expression, call, or declaration opened above.
    }),
    // Continues the surrounding operation with this required value or expression.
    [status, session, error, getAccessToken, sendMagicLink, signOut],
    // Closes the expression, call, or declaration opened above.
  );

  // Returns the computed result and ends the current callable.
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
  // Closes the expression, call, or declaration opened above.
}

// Exports this declaration because other modules rely on its contract.
export function useSession(): SessionState {
  // Stores `value` because subsequent operations depend on this value.
  const value = useContext(SessionContext);
  // Guards the nested operation so it runs only when this condition is satisfied.
  if (!value) throw new Error('useSession must be used inside SessionProvider');
  // Returns the computed result and ends the current callable.
  return value;
  // Closes the expression, call, or declaration opened above.
}
