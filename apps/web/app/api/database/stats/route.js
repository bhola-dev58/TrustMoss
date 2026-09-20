import { NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.TRUSTMOSS_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_BASE_URL}/database/stats`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return NextResponse.json({
        postgresql: {
          status: 'standby',
          pool_size: 10,
          active_connections: 0,
          idle_connections: 10,
          tables: { trust_events: 0, audit_logs: 0, hitl_records: 0, load_test_runs: 0 },
        },
        redis: {
          status: 'standby',
          active_sessions: 0,
          memory_used_kb: 0,
          key_count: 0,
          ttl_policy: 'allkeys-lru',
        },
      });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      postgresql: {
        status: 'simulated',
        pool_size: 10,
        active_connections: 2,
        idle_connections: 8,
        tables: { trust_events: 142, audit_logs: 184, hitl_records: 6, load_test_runs: 12 },
      },
      redis: {
        status: 'simulated',
        active_sessions: 4,
        memory_used_kb: 148,
        key_count: 28,
        ttl_policy: 'allkeys-lru (256MB)',
      },
    });
  }
}
