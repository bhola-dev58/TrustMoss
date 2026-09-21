import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function ContextViewer({ chunks = [] }) {
  const [expanded, setExpanded] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div data-testid="context-viewer" className="bg-[#1E1E1E] border border-[#333333] rounded-xl overflow-hidden shadow-sm font-sans">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-xs font-semibold text-[#FFFFFF] hover:bg-[#242424] transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-[#FF8C00]" />
          <span>Moss Context Grounding ({chunks.length} chunks retrieved)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[#9AA0A6] font-mono">
            Top Score: {chunks[0]?.score ? (chunks[0].score * 100).toFixed(1) + '%' : 'N/A'}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4 text-[#FFC107]" /> : <ChevronDown className="w-4 h-4 text-[#9AA0A6]" />}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 space-y-2 border-t border-[#333333]">
          {chunks.map((chunk, idx) => (
            <div key={idx} className="p-3 bg-[#121212] border border-[#333333] rounded-lg text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 font-mono text-[11px] text-[#FFC107] font-semibold">
                  <FileText className="w-3 h-3 text-[#9AA0A6]" />
                  Chunk {chunk.id || idx + 1}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30">
                  Sim: {chunk.score ? (chunk.score * 100).toFixed(1) + '%' : '100%'}
                </span>
              </div>
              <p className="text-[#FFFFFF] leading-relaxed font-sans">{chunk.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

}
