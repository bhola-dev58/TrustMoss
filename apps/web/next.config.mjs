/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_APP_NAME: 'TrustMoss',
    NEXT_PUBLIC_APP_VERSION: '0.2.0-next',
  },
};

export default nextConfig;
