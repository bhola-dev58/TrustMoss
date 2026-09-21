import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function TrustBadge({ trust, history = [] }) {
  if (!trust) return null;

  const { verdict = 'PASS', score = 1.0, reason } = trust;

  const config = {
    PASS: {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      icon: ShieldCheck,
      label: 'TRUST VERIFIED',
      dot: 'bg-emerald-400 animate-pulse',
      stroke: '#34d399',
    },
    WARN: {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      icon: AlertTriangle,
      label: 'TRUST WARNING',
      dot: 'bg-amber-400',
      stroke: '#fbbf24',
    },
    FAIL: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      icon: ShieldAlert,
      label: 'CIRCUIT BREAKER TRIPPED',
      dot: 'bg-rose-400 animate-ping',
      stroke: '#f43f5e',
    },
  }[verdict] || {
    bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400',
    icon: ShieldCheck,
    label: verdict,
    dot: 'bg-slate-400',
    stroke: '#94a3b8',
  };

  const Icon = config.icon;

  // Build sparkline points if history is provided
  let sparklinePoints = '';
  if (Array.isArray(history) && history.length > 1) {
    const rawScores = history.map((item) => {
      if (typeof item === 'number') return item;
      return item.trust?.score ?? item.score ?? 1.0;
    });
    const maxIdx = rawScores.length - 1;
    const width = 48;
    const height = 14;
    sparklinePoints = rawScores
      .map((s, idx) => {
        const x = (idx / maxIdx) * width;
        const y = height - s * height + 1;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }

  return (
    <div
      data-testid="trust-badge"
      title={reason || config.label}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${config.bg}`}
    >
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      <Icon className="w-3.5 h-3.5" />
      <span>{config.label}</span>
      <span className="font-mono opacity-80">({(score * 100).toFixed(0)}%)</span>

      {sparklinePoints && (
        <div className="flex items-center pl-1 border-l border-current/20">
          <svg
            width="48"
            height="16"
            className="overflow-visible"
            aria-label="Trust timeline sparkline"
          >
            <polyline
              fill="none"
              stroke={config.stroke}
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={sparklinePoints}
            />
          </svg>
        </div>
      )}
    </div>
  );
}
