/** @type {import('next').NextConfig} */
const nextConfig = {
  // デバッグ用webpack設定
  webpack: (config, { dev, isServer }) => {
    // 開発環境でのソースマップ最適化
    if (dev && !isServer) {
      config.devtool = 'eval-source-map'
    }
    return config
  },

  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
  
  // デバッグ用CORS設定
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ]
  },

  // Minimal config to avoid WSL bus errors
  swcMinify: true,
  experimental: {
    forceSwcTransforms: true, // デバッグしやすくするためtrueに変更
  },
}

module.exports = nextConfig