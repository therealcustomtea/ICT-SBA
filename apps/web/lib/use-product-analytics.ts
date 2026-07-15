'use client';

import { useLocale } from 'next-intl';
import { useCallback } from 'react';
import { useSession } from '@/components/session-provider';
import { type AnalyticsEventMap, deliverProductEvent } from './analytics-delivery';

export function useProductAnalytics() {
  const locale = useLocale();
  const { getAccessToken } = useSession();
  return useCallback(
    <K extends keyof AnalyticsEventMap>(eventName: K, fields: AnalyticsEventMap[K]) => {
      void getAccessToken().then((token) =>
        deliverProductEvent(token, locale === 'zh-Hant' ? 'zh-Hant' : 'en', eventName, fields),
      );
    },
    [getAccessToken, locale],
  );
}
