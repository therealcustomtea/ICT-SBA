import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const origin = process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000';
  const paths = [
    '',
    '/play',
    '/daily',
    '/leaderboards',
    '/guide',
    '/privacy',
    '/terms',
    '/accessibility',
    '/support',
  ];
  return ['en', 'zh-Hant'].flatMap((locale) =>
    paths.map((path) => ({
      url: `${origin}/${locale}${path}`,
      changeFrequency: path === '/daily' ? ('daily' as const) : ('weekly' as const),
    })),
  );
}
