/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'https://peepong.pythonanywhere.com/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig