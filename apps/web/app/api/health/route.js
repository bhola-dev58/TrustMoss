import { NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.TRUSTMOSS_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export async function GET() {
  let upstreamHealth = null;
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (res.ok) {
      upstreamHealth = await res.json();
    }
  } catch (err) {
    upstreamHealth = { error: err.message, reachable: false };
  }

  return NextResponse.json({
    framework: 'Next.js 14+ App Router',
    status: 'ok',
    timestamp: new Date().toISOString(),
    upstream_gateway: upstreamHealth,
  });
}
