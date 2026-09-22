import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = __dirname.startsWith('/app') ? __dirname : path.resolve(__dirname, '../..');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  outputFileTracingRoot: projectRoot,
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_APP_NAME: 'TrustMoss',
    NEXT_PUBLIC_APP_VERSION: '0.2.0-next',
  },
  turbopack: {
    root: projectRoot,
  },
};

export default nextConfig;
