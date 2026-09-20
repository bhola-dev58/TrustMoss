/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone mode is only for Docker builds; Vercel uses its native serverless output
  ...(process.env.DOCKER_BUILD ? { output: 'standalone' } : {}),
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_APP_NAME: 'TrustMoss',
    NEXT_PUBLIC_APP_VERSION: '0.2.0-next',
  },
};

export default nextConfig;
