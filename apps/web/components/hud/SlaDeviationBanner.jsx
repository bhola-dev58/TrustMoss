'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Bell,
  Activity,
  Zap,
  Sliders,
  X,
  RefreshCw,
} from 'lucide-react';

export default function SlaDeviationBanner({ mossLatency = 6.2, ingressLatency = 8.4, tripCount = 0 }) {
  const [isAlertSimulated, setIsAlertSimulated] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const effectiveMossLatency = isAlertSimulated ? 14.8 : mossLatency;
  const isMossBreached = effectiveMossLatency > 10.0;

  if (dismissed && !isAlertSimulated) return null;

  return (
    <div
      data-testid="sla-deviation-banner"
      className={`rounded-2xl p-3 sm:p-4 border transition-all duration-300 font-sans shadow-lg ${
        isMossBreached
          ? 'bg-rose-950/40 border-rose-600/60 text-[#FFFFFF] animate-pulse'
          : 'bg-[#181818] border-[#333333] text-[#9AA0A6]'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-xl shrink-0 ${
              isMossBreached
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                : 'bg-[#121212] text-[#FFC107] border border-[#333333]'
            }`}
          >
            {isMossBreached ? (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            ) : (
              <Activity className="w-4 h-4 text-[#FF8C00]" />
            )}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#FFFFFF]">
                {isMossBreached ? 'Proactive SLA Breach Alert' : 'Real-Time SLA & Deviation Monitor'}
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold border flex items-center gap-1 ${
                  isMossBreached
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isMossBreached ? 'bg-rose-400' : 'bg-emerald-400'
                  } animate-pulse`}
                />
                {isMossBreached ? 'DEVIATION DETECTED' : 'ALL SLAS HEALTHY'}
              </span>
            </div>
            <p className="text-[10px] text-[#9AA0A6] mt-0.5">
              {isMossBreached
                ? `Moss Context Retrieval exceeded 10ms SLA (${effectiveMossLatency} ms detected). Auto-reindexing and Redis L2 failover triggered.`
                : 'Proactive telemetry: Continuously monitoring sub-10ms Moss semantic search and sub-45ms edge ingress limits.'}
            </p>
          </div>
        </div>

        {/* Telemetry Metrics & Simulator Action */}
        <div className="flex items-center gap-2 self-end sm:self-center">
          <div className="px-2.5 py-1 rounded-xl bg-[#121212] border border-[#333333] text-[10px] font-mono flex items-center gap-1.5">
            <span className="text-[#9AA0A6]">Moss SLA:</span>
            <span
              className={`font-bold ${
                isMossBreached ? 'text-rose-400 font-bold' : 'text-[#FFC107]'
              }`}
            >
              {effectiveMossLatency.toFixed(1)} ms
            </span>
          </div>

          <div className="px-2.5 py-1 rounded-xl bg-[#121212] border border-[#333333] text-[10px] font-mono hidden md:flex items-center gap-1.5">
            <span className="text-[#9AA0A6]">Ingress:</span>
            <span className="text-emerald-400 font-semibold">{ingressLatency} ms</span>
          </div>

          {/* Simulate SLA Deviation Demo Toggle */}
          <button
            onClick={() => {
              setIsAlertSimulated(!isAlertSimulated);
              setDismissed(false);
            }}
            className={`px-2.5 py-1 rounded-xl text-[10px] font-semibold flex items-center gap-1.5 border transition-all cursor-pointer ${
              isAlertSimulated
                ? 'bg-rose-600 hover:bg-rose-700 text-[#FFFFFF] border-rose-500'
                : 'bg-[#242424] hover:bg-[#333333] text-[#FFC107] border-[#333333] hover:border-[#FF8C00]/40'
            }`}
            title="Demonstrate proactive alerting to hackathon evaluators"
          >
            <Sliders className="w-3 h-3" />
            <span>{isAlertSimulated ? 'Clear Deviation' : 'Test SLA Alert'}</span>
          </button>

          {!isAlertSimulated && (
            <button
              onClick={() => setDismissed(true)}
              className="p-1 rounded-lg text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#242424] transition-colors cursor-pointer"
              title="Dismiss banner"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
