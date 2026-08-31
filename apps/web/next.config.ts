// Imports the dependency used by this module.
import createNextIntlPlugin from 'next-intl/plugin';
// Imports the dependency used by this module.
import type { NextConfig } from 'next';

// Computes and stores nextConfig for subsequent operations.
const nextConfig: NextConfig = {
  // Defines the poweredByHeader field in the surrounding object or type.
  poweredByHeader: false,
  // Defines the productionBrowserSourceMaps field in the surrounding object or type.
  productionBrowserSourceMaps: false,
  // Defines the transpilePackages field in the surrounding object or type.
  transpilePackages: ['@mastermind/api-client', '@mastermind/shared-config'],
  // Begins the nested block or object completed below.
  async headers() {
    // Returns this result to the caller and ends the current function.
    return [
      // Begins the nested block or object completed below.
      {
        // Defines the source field in the surrounding object or type.
        source: '/:path*',
        // Defines the headers field in the surrounding object or type.
        headers: [
          // Supplies this item to the surrounding call or collection.
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          // Supplies this item to the surrounding call or collection.
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          // Supplies this item to the surrounding call or collection.
          { key: 'X-Frame-Options', value: 'DENY' },
          // Begins the nested block or object completed below.
          {
            // Defines the key field in the surrounding object or type.
            key: 'Permissions-Policy',
            // Defines the value field in the surrounding object or type.
            value: 'camera=(), microphone=(), geolocation=(), payment=()',
            // Closes the expression, call, or declaration started above.
          },
          // Supplies this item to the surrounding call or collection.
          { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
          // Executes this line as the next step in the surrounding logic.
          ...(process.env.NODE_ENV === 'production'
            ? // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              [{ key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' }]
            : // Continues the surrounding operation with this required value or expression.
              // Supplies this item to the surrounding call or collection.
              []),
          // Closes the expression, call, or declaration started above.
        ],
        // Closes the expression, call, or declaration started above.
      },
      // Closes the expression, call, or declaration started above.
    ];
    // Closes the expression, call, or declaration started above.
  },
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration as the module default.
export default createNextIntlPlugin('./i18n/request.ts')(nextConfig);
