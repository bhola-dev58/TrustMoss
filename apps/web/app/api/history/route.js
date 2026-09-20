import { NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.TRUSTMOSS_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_BASE_URL}/history`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return NextResponse.json({ count: 0, queries: [] });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({
      count: 0,
      queries: [],
      connected: false,
    });
  }
}
