import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const origin = process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000';
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: [
        '/*/challenges/',
        '/*/rooms/',
        '/*/play/*',
        '/*/admin',
        '/*/account',
        '/*/profile',
      ],
    },
    sitemap: `${origin}/sitemap.xml`,
  };
}
