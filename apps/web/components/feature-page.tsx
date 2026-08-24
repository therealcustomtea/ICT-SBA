// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { AlertCircle, LoaderCircle } from 'lucide-react';

// Exports this declaration for use by other modules.
export function FeaturePage({
  // Supplies this item to the surrounding call or collection.
  title,
  // Supplies this item to the surrounding call or collection.
  intro,
  // Supplies this item to the surrounding call or collection.
  actions,
  // Supplies this item to the surrounding call or collection.
  children,
  // Begins the nested block or object completed below.
}: {
  // Defines the title field in the surrounding object or type.
  title: string;
  // Executes this line as the next step in the surrounding logic.
  intro?: string;
  // Executes this line as the next step in the surrounding logic.
  actions?: React.ReactNode;
  // Defines the children field in the surrounding object or type.
  children: React.ReactNode;
  // Begins the nested block or object completed below.
}) {
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="page-shell">
      {/* Renders the header interface element or component. */}
      <header className="page-heading">
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the h1 interface element or component. */}
          <h1>{title}</h1>
          {/* Executes this line as the next step in the surrounding logic. */}
          {intro ? <p>{intro}</p> : null}
          {/* Closes the div interface element. */}
        </div>
        {/* Executes this line as the next step in the surrounding logic. */}
        {actions}
        {/* Closes the header interface element. */}
      </header>
      {/* Executes this line as the next step in the surrounding logic. */}
      {children}
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function AsyncState({
  // Supplies this item to the surrounding call or collection.
  state,
  // Supplies this item to the surrounding call or collection.
  loadingLabel,
  // Supplies this item to the surrounding call or collection.
  errorLabel,
  // Supplies this item to the surrounding call or collection.
  emptyLabel,
  // Supplies this item to the surrounding call or collection.
  children,
  // Begins the nested block or object completed below.
}: {
  // Defines the state field in the surrounding object or type.
  state: 'loading' | 'error' | 'empty' | 'ready';
  // Defines the loadingLabel field in the surrounding object or type.
  loadingLabel: string;
  // Defines the errorLabel field in the surrounding object or type.
  errorLabel: string;
  // Defines the emptyLabel field in the surrounding object or type.
  emptyLabel: string;
  // Executes this line as the next step in the surrounding logic.
  children?: React.ReactNode;
  // Begins the nested block or object completed below.
}) {
  // Continues the surrounding operation with this required value or expression.
  {
    /* Checks this condition before running the nested branch. */
  }
  // Guards the nested operation so it runs only when this condition is satisfied.
  if (state === 'ready') return <>{children}</>;
  // Checks this condition before running the nested branch.
  if (state === 'loading')
    // Returns this result to the caller and ends the current function.
    return (
      // Renders the div interface element or component.
      <div className="state-panel" role="status">
        {/* Renders the LoaderCircle interface element or component. */}
        <LoaderCircle className="spin" aria-hidden="true" />
        {/* Renders the p interface element or component. */}
        <p>{loadingLabel}</p>
        {/* Closes the div interface element. */}
      </div>
      // Closes the expression, call, or declaration started above.
    );
  // Checks this condition before running the nested branch.
  if (state === 'error')
    // Returns this result to the caller and ends the current function.
    return (
      // Renders the div interface element or component.
      <div className="state-panel error-panel" role="alert">
        {/* Renders the AlertCircle interface element or component. */}
        <AlertCircle aria-hidden="true" />
        {/* Renders the p interface element or component. */}
        <p>{errorLabel}</p>
        {/* Closes the div interface element. */}
      </div>
      // Closes the expression, call, or declaration started above.
    );
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="state-panel">
      {/* Renders the p interface element or component. */}
      <p>{emptyLabel}</p>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
