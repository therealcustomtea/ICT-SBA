// Exports this declaration for use by other modules.
export function Logo({ compact = false }: { compact?: boolean }) {
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the span interface element or component.
    <span className="logo-lockup" role="img" aria-label="Cipherboard" translate="no">
      {/* Renders the svg interface element or component. */}
      <svg aria-hidden="true" viewBox="0 0 40 40" className="logo-mark">
        {/* Renders the rect interface element or component. */}
        <rect width="40" height="40" rx="9" className="logo-ground" />
        {/* Renders the circle interface element or component. */}
        <circle cx="13" cy="13" r="5" className="logo-one" />
        {/* Renders the path interface element or component. */}
        <path d="M23 8h9v10h-9z" className="logo-two" />
        {/* Renders the path interface element or component. */}
        <path d="m8 28 5-5 5 5-5 5z" className="logo-three" />
        {/* Renders the circle interface element or component. */}
        <circle cx="28" cy="28" r="5" className="logo-four" />
        {/* Closes the svg interface element. */}
      </svg>
      {/* Executes this line as the next step in the surrounding logic. */}
      {compact ? null : <span>Cipherboard</span>}
      {/* Closes the span interface element. */}
    </span>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
