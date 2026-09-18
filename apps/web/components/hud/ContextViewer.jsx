import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function ContextViewer({ chunks = [] }) {
  const [expanded, setExpanded] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div data-testid="context-viewer" className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-xs font-semibold text-slate-300 hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <span>Moss Context Grounding ({chunks.length} chunks retrieved)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-500 font-mono">
            Top Score: {chunks[0]?.score ? (chunks[0].score * 100).toFixed(1) + '%' : 'N/A'}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 space-y-2 border-t border-slate-800/60">
          {chunks.map((chunk, idx) => (
            <div key={idx} className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400 font-medium">
                  <FileText className="w-3 h-3 text-slate-400" />
                  Chunk {chunk.id || idx + 1}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  Sim: {chunk.score ? (chunk.score * 100).toFixed(1) + '%' : '100%'}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed font-sans">{chunk.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
