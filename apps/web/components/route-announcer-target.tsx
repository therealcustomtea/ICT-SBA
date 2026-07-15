'use client';

import { useLayoutEffect } from 'react';

const announcerName = 'next-route-announcer';

export function RouteAnnouncerTarget() {
  useLayoutEffect(() => {
    if (document.getElementsByName(announcerName)[0]?.shadowRoot?.childNodes[0]) return;
    const host = document.createElement(announcerName);
    host.setAttribute('name', announcerName);
    const shadow = host.attachShadow({ mode: 'open' });
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.setAttribute('role', 'alert');
    shadow.appendChild(announcement);
    document.body.appendChild(host);
  }, []);

  return null;
}
