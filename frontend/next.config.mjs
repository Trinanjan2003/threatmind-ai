/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    return [
      // Proxy API calls in dev to avoid CORS friction.
      { source: "/api/:path*", destination: `${api}/api/:path*` },
    ];
  },
};

export default nextConfig;
