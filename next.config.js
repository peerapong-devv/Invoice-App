/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://peepong.pythonanywhere.com/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig