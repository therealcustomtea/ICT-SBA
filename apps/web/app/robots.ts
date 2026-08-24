// Imports the dependency used by this module.
import type { MetadataRoute } from 'next';

// Exports this declaration as the module default.
export default function robots(): MetadataRoute.Robots {
  // Computes and stores origin for subsequent operations.
  const origin = process.env.NEXT_PUBLIC_PRODUCT_ORIGIN ?? 'http://localhost:3000';
  // Returns this result to the caller and ends the current function.
  return {
    // Defines the rules field in the surrounding object or type.
    rules: {
      // Defines the userAgent field in the surrounding object or type.
      userAgent: '*',
      // Defines the allow field in the surrounding object or type.
      allow: '/',
      // Defines the disallow field in the surrounding object or type.
      disallow: [
        // Supplies this item to the surrounding call or collection.
        '/*/challenges/',
        // Supplies this item to the surrounding call or collection.
        '/*/rooms/',
        // Supplies this item to the surrounding call or collection.
        '/*/play/*',
        // Supplies this item to the surrounding call or collection.
        '/*/admin',
        // Supplies this item to the surrounding call or collection.
        '/*/account',
        // Supplies this item to the surrounding call or collection.
        '/*/profile',
        // Closes the expression, call, or declaration started above.
      ],
      // Closes the expression, call, or declaration started above.
    },
    // Defines the sitemap field in the surrounding object or type.
    sitemap: `${origin}/sitemap.xml`,
    // Closes the expression, call, or declaration started above.
  };
  // Closes the expression, call, or declaration started above.
}
