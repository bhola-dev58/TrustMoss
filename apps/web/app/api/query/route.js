import { NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.TRUSTMOSS_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export async function POST(request) {
  try {
    const body = await request.json();
    const res = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json(
        { error: `Trust Gateway returned ${res.status}: ${errorText}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: `Gateway Proxy Error: ${err.message}` },
      { status: 502 }
    );
  }
}
