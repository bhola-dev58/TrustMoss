import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function TrustBadge({ trust }) {
  if (!trust) return null;

  const { verdict, score, color, reason } = trust;

  const config = {
    PASS: {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      icon: ShieldCheck,
      label: 'TRUST VERIFIED',
      dot: 'bg-emerald-400 animate-pulse',
    },
    WARN: {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      icon: AlertTriangle,
      label: 'TRUST WARNING',
      dot: 'bg-amber-400',
    },
    FAIL: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      icon: ShieldAlert,
      label: 'CIRCUIT BREAKER TRIPPED',
      dot: 'bg-rose-400 animate-ping',
    },
  }[verdict] || {
    bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400',
    icon: ShieldCheck,
    label: verdict,
    dot: 'bg-slate-400',
  };

  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${config.bg}`}>
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      <Icon className="w-3.5 h-3.5" />
      <span>{config.label}</span>
      <span className="font-mono opacity-80">({(score * 100).toFixed(0)}%)</span>
    </div>
  );
}
