/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
  // Minimal config to avoid WSL bus errors
  swcMinify: true,
  experimental: {
    forceSwcTransforms: false,
  },
}

module.exports = nextConfig