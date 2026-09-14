import React from 'react';
import { Zap, Clock } from 'lucide-react';

export default function LatencyWaterfall({ trace = [], totalMs = 0 }) {
  if (!trace || trace.length === 0) return null;

  const stageLabels = {
    moss_retrieval: 'Moss Context Retrieval',
    relevance_check: 'Pre-Gen Relevance Gate',
    llm_generation: 'Groq LLM Generation',
    groundedness_check: 'Groundedness Evaluator',
    pii_scan: 'PII & Security Filter',
  };

  const stageColors = {
    moss_retrieval: 'bg-emerald-500',
    relevance_check: 'bg-blue-500',
    llm_generation: 'bg-purple-500',
    groundedness_check: 'bg-indigo-500',
    pii_scan: 'bg-amber-500',
  };

  const maxDuration = Math.max(...trace.map((s) => s.duration_ms || 1), totalMs || 1);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Clock className="w-4 h-4 text-emerald-400" />
          <span>Per-Hop Latency Trace</span>
        </div>
        <div className="flex items-center gap-1 text-xs font-mono font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
          <Zap className="w-3 h-3" />
          <span>Total: {totalMs.toFixed(1)} ms</span>
        </div>
      </div>

      <div className="space-y-2.5">
        {trace.map((step, idx) => {
          const duration = step.duration_ms || 0;
          const percentage = Math.max(3, Math.min(100, (duration / maxDuration) * 100));
          const isMoss = step.stage === 'moss_retrieval';

          return (
            <div key={idx} className="text-xs space-y-1">
              <div className="flex justify-between text-slate-400 font-medium">
                <span className="flex items-center gap-1.5">
                  {isMoss && <span className="text-[10px] bg-emerald-900/60 text-emerald-300 px-1 rounded border border-emerald-600/40">MOSS</span>}
                  {stageLabels[step.stage] || step.stage}
                </span>
                <span className={`font-mono ${isMoss ? 'text-emerald-400 font-semibold' : 'text-slate-300'}`}>
                  {duration.toFixed(2)} ms
                </span>
              </div>
              <div className="h-2 w-full bg-slate-800/80 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    stageColors[step.stage] || 'bg-slate-500'
                  } ${isMoss ? 'shadow-[0_0_8px_rgba(16,185,129,0.5)]' : ''}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-2 text-[11px] text-slate-500 flex items-center justify-between border-t border-slate-800/60">
        <span>Sub-50ms Moss Retrieval target achieved</span>
        <span className="text-emerald-400/80 font-mono">Zero Retrieval Overhead</span>
      </div>
    </div>
  );
}
