/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    proxyTimeout: 120000, // 120 seconds, to give buffer for 120s API calls
  },
  rewrites: async () => {
    return [
      // Special case: Keep download-image handled by Next.js API route
      {
        source: "/api/download-image",
        destination: "/api/download-image",
      },
      // All other API routes go to the FastAPI backend
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "/api/",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/docs"
            : "/api/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/openapi.json"
            : "/api/openapi.json",
      },
    ];
  },
  webpack: (config, { isServer }) => {
    // Suppress EXIFR warnings and provide fallbacks for browser environment
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        zlib: false,
        util: false,
      };
    }
    
    // Comprehensive warning suppression
    config.ignoreWarnings = [
      // Function-based suppression for EXIFR
      (warning) => {
        if (warning.module?.resource?.includes('exifr')) {
          return true;
        }
        if (warning.message?.includes('exifr')) {
          return true;
        }
        if (warning.message?.includes('Critical dependency: the request of a dependency is an expression')) {
          return true;
        }
        return false;
      },
      // Regex patterns for additional coverage
      /Critical dependency.*exifr/i,
      /Critical dependency: the request of a dependency is an expression/,
      /Can't resolve 'fs'/,
      /Can't resolve 'zlib'/,
      /Can't resolve 'util'/,
    ];
    
    return config;
  },
};

module.exports = nextConfig;
