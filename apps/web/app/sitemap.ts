// Imports the dependency used by this module.
import type { MetadataRoute } from 'next';

// Exports this declaration as the module default.
export default function sitemap(): MetadataRoute.Sitemap {
  // Computes and stores origin for subsequent operations.
  const origin = process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000';
  // Computes and stores paths for subsequent operations.
  const paths = [
    // Supplies this item to the surrounding call or collection.
    '',
    // Supplies this item to the surrounding call or collection.
    '/play',
    // Supplies this item to the surrounding call or collection.
    '/daily',
    // Supplies this item to the surrounding call or collection.
    '/leaderboards',
    // Supplies this item to the surrounding call or collection.
    '/guide',
    // Supplies this item to the surrounding call or collection.
    '/privacy',
    // Supplies this item to the surrounding call or collection.
    '/terms',
    // Supplies this item to the surrounding call or collection.
    '/accessibility',
    // Supplies this item to the surrounding call or collection.
    '/support',
    // Closes the expression, call, or declaration started above.
  ];
  // Returns this result to the caller and ends the current function.
  return ['en', 'zh-Hant'].flatMap(
    (locale) =>
      // Calls paths.map with the supplied values.
      paths.map((path) => ({
        // Defines the url field in the surrounding object or type.
        url: `${origin}/${locale}${path}`,
        // Defines the changeFrequency field in the surrounding object or type.
        changeFrequency: path === '/daily' ? ('daily' as const) : ('weekly' as const),
        // Closes the expression, call, or declaration started above.
      })),
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
