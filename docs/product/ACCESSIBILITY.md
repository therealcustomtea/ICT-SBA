# Accessibility

Cipherboard targets WCAG 2.2 AA in English and Traditional Chinese.

## Interaction contract

- Every peg is a real button with a localized colour name and stable symbol; hue never carries meaning alone.
- Colour shortcuts 1–10, arrow keys, Backspace/Delete, Enter, and ordinary Tab navigation support a complete game without a pointer.
- Controls have at least 44×44 CSS-pixel targets, visible focus, logical order, and no drag-only action.
- Submitted feedback is announced once through a polite live region: attempt, exact matches, misplaced matches, and attempts remaining.
- The elapsed timer has an accessible label but is not live-announced every second.
- Errors are associated with their control, preserve input, and move focus only when needed to make recovery clear.
- Dialogs use semantic modal behavior, Escape, focus containment, and focus restoration.
- Offline, reconnecting, loading, empty, success, and degraded states are textual as well as visual.
- Reduced-motion preferences remove nonessential transitions. Sound is off unless the player enables it.

## Visual contract

- Normal text contrast is at least 4.5:1; large text and essential graphics at least 3:1.
- Focus indication has at least 3:1 adjacent contrast.
- Browser zoom is not disabled.
- Peg symbols/patterns remain legible in common colour-vision deficiencies and high-contrast modes.
- Tables use captions and scoped headers; pagination identifies the current page.

## Manual release checklist

At 375, 390, 768, 1024, and 1280 CSS pixels:

1. Use only keyboard controls to start, play, abandon, and replay a game.
2. Verify focus never disappears behind a sticky control or dialog.
3. Inspect English and Traditional Chinese headings, labels, errors, and accessible names.
4. Run VoiceOver or NVDA through setup, one invalid row, one valid row, result, profile, leaderboard, and account deletion.
5. Confirm a screen reader does not announce the timer every second.
6. Enable reduced motion and confirm gameplay loses no information.
7. Simulate offline and reconnect; ensure the unsubmitted row remains while submission is blocked.
8. Check 200% and 400% zoom and portrait/landscape orientation.
9. Verify light and dark theme contrast with an automated checker and visual review.
10. Run axe on every primary route and terminal state; resolve all serious or critical findings before release.

Automated checks supplement, not replace, the keyboard and screen-reader review.
