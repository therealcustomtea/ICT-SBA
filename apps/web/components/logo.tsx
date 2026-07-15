export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="logo-lockup" role="img" aria-label="Cipherboard" translate="no">
      <svg aria-hidden="true" viewBox="0 0 40 40" className="logo-mark">
        <rect width="40" height="40" rx="9" className="logo-ground" />
        <circle cx="13" cy="13" r="5" className="logo-one" />
        <path d="M23 8h9v10h-9z" className="logo-two" />
        <path d="m8 28 5-5 5 5-5 5z" className="logo-three" />
        <circle cx="28" cy="28" r="5" className="logo-four" />
      </svg>
      {compact ? null : <span>Cipherboard</span>}
    </span>
  );
}
