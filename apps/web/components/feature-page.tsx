'use client';

import { AlertCircle, LoaderCircle } from 'lucide-react';

export function FeaturePage({
  title,
  intro,
  actions,
  children,
}: {
  title: string;
  intro?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="page-shell">
      <header className="page-heading">
        <div>
          <h1>{title}</h1>
          {intro ? <p>{intro}</p> : null}
        </div>
        {actions}
      </header>
      {children}
    </div>
  );
}

export function AsyncState({
  state,
  loadingLabel,
  errorLabel,
  emptyLabel,
  children,
}: {
  state: 'loading' | 'error' | 'empty' | 'ready';
  loadingLabel: string;
  errorLabel: string;
  emptyLabel: string;
  children?: React.ReactNode;
}) {
  if (state === 'ready') return <>{children}</>;
  if (state === 'loading')
    return (
      <div className="state-panel" role="status">
        <LoaderCircle className="spin" aria-hidden="true" />
        <p>{loadingLabel}</p>
      </div>
    );
  if (state === 'error')
    return (
      <div className="state-panel error-panel" role="alert">
        <AlertCircle aria-hidden="true" />
        <p>{errorLabel}</p>
      </div>
    );
  return (
    <div className="state-panel">
      <p>{emptyLabel}</p>
    </div>
  );
}
