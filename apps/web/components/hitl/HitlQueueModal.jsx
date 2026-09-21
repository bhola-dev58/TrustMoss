import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, RefreshCw, GitCommit, X } from 'lucide-react';

export default function HitlQueueModal({ isOpen, onClose, flaggedItems = [], onResolve }) {
  const [selectedItem, setSelectedItem] = useState(flaggedItems[0] || null);
  const [annotation, setAnnotation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen) return null;

  const handleApprove = () => {
    if (!selectedItem) return;
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSuccessMsg(`Committed to Moss Index Registry under hash: #commit-${Math.random().toString(36).substring(2, 9)}`);
      setTimeout(() => {
        setSuccessMsg('');
        if (onResolve) onResolve(selectedItem.id || selectedItem.query_id);
      }, 2000);
    }, 1000);
  };

  return (
    <div data-testid="hitl-queue-modal" className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 font-sans">

      <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#333333] flex items-center justify-between bg-[#242424]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#FF8C00]/15 border border-[#FF8C00]/30 rounded-lg">
              <ShieldAlert className="w-5 h-5 text-[#FF8C00]" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#FFFFFF]">HITL Review Queue &amp; Knowledge Ingestion</h3>
              <p className="text-xs text-[#9AA0A6]">Human verification loop for flagged WARN / FAIL interactions</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-[#9AA0A6] hover:text-[#FFFFFF] rounded-lg hover:bg-[#333333] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1 text-xs">
          {flaggedItems.length === 0 ? (
            <div className="text-center py-12 text-[#9AA0A6] space-y-2">
              <CheckCircle2 className="w-10 h-10 text-[#FFC107] mx-auto" />
              <p className="text-sm font-medium text-[#FFFFFF]">Zero Flagged Issues in Queue</p>
              <p className="text-xs text-[#9AA0A6]">All queries currently satisfy the Groundedness and Security thresholds.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-3 bg-rose-950/30 border border-rose-900/40 rounded-xl space-y-1.5">
                <span className="text-[10px] uppercase font-bold tracking-wider text-rose-400">Flagged Query:</span>
                <p className="text-sm font-medium text-[#FFFFFF]">{selectedItem?.query || selectedItem?.text || 'Off-topic or low-grounded query'}</p>
                <div className="flex items-center gap-2 pt-1 text-[11px] text-rose-300">
                  <span>Reason: {selectedItem?.trust?.reason || 'Circuit breaker tripped due to low context relevance / groundedness'}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[#FFFFFF] font-semibold flex items-center justify-between">
                  <span>Operator Verified Ground Truth / Context Correction:</span>
                  <span className="text-[#9AA0A6] font-normal">Will be re-indexed into Moss</span>
                </label>
                <textarea
                  value={annotation}
                  onChange={(e) => setAnnotation(e.target.value)}
                  placeholder="Enter corrected knowledge chunk or verified policy statement to patch the knowledge base..."
                  className="w-full h-28 bg-[#121212] border border-[#333333] rounded-xl p-3 text-[#FFFFFF] placeholder-[#9AA0A6] focus:outline-none focus:border-[#FF8C00] font-sans"
                />
              </div>

              {successMsg && (
                <div className="p-3 bg-[#FF8C00]/10 border border-[#FF8C00]/30 rounded-xl text-[#FFC107] flex items-center gap-2">
                  <GitCommit className="w-4 h-4 text-[#FF8C00]" />
                  <span>{successMsg}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {flaggedItems.length > 0 && (
          <div className="px-6 py-3 border-t border-[#333333] bg-[#242424] flex items-center justify-between text-xs">
            <span className="text-[#9AA0A6] font-mono">Status: Pending Operator Verification</span>
            <button
              onClick={handleApprove}
              disabled={isSubmitting || !annotation.trim()}
              className="px-4 py-2 bg-gradient-to-r from-[#FF8C00] to-[#FFC107] hover:from-[#FFA000] hover:to-[#FFD54F] disabled:opacity-50 text-[#121212] font-bold rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-[#FF8C00]/25 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Re-indexing into Moss...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve &amp; Update Index Version</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

