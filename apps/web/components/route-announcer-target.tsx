// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLayoutEffect } from 'react';

// Computes and stores announcerName for subsequent operations.
const announcerName = 'next-route-announcer';

// Exports this declaration for use by other modules.
export function RouteAnnouncerTarget() {
  // Calls useLayoutEffect with the supplied values.
  useLayoutEffect(() => {
    // Checks this condition before running the nested branch.
    if (document.getElementsByName(announcerName)[0]?.shadowRoot?.childNodes[0]) return;
    // Computes and stores host for subsequent operations.
    const host = document.createElement(announcerName);
    // Calls host.setAttribute with the supplied values.
    host.setAttribute('name', announcerName);
    // Computes and stores shadow for subsequent operations.
    const shadow = host.attachShadow({ mode: 'open' });
    // Computes and stores announcement for subsequent operations.
    const announcement = document.createElement('div');
    // Calls announcement.setAttribute with the supplied values.
    announcement.setAttribute('aria-live', 'assertive');
    // Calls announcement.setAttribute with the supplied values.
    announcement.setAttribute('role', 'alert');
    // Calls shadow.appendChild with the supplied values.
    shadow.appendChild(announcement);
    // Calls document.body.appendChild with the supplied values.
    document.body.appendChild(host);
    // Executes this line as the next step in the surrounding logic.
  }, []);

  // Returns this result to the caller and ends the current function.
  return null;
  // Closes the expression, call, or declaration started above.
}
