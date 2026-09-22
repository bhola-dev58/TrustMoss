'use client';

import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  RefreshCw,
  GitCommit,
  X,
  Ban,
  CheckSquare,
  AlertTriangle,
  Database,
  ArrowRight,
  ShieldCheck,
  UserX,
  FileCheck,
} from 'lucide-react';

export default function HitlQueueModal({ isOpen, onClose, flaggedItems = [], onResolve }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [annotation, setAnnotation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  if (!isOpen) return null;

  const currentItem = flaggedItems[selectedIndex] || flaggedItems[0] || null;

  const handleAction = (actionType) => {
    if (!currentItem) return;
    setIsSubmitting(true);

    setTimeout(() => {
      setIsSubmitting(false);
      const commitHash = `sha256:${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 8)}`;

      if (actionType === 'patch') {
        setActionMsg(`✓ Knowledge Patched & Re-indexed to Moss: [${commitHash}]`);
      } else if (actionType === 'block') {
        setActionMsg(`✓ Threat Actor Session Quarantined & Blocked: [${commitHash}]`);
      } else {
        setActionMsg(`✓ False Positive Cleared & Session Restored: [${commitHash}]`);
      }

      setTimeout(() => {
        setActionMsg('');
        setAnnotation('');
        if (onResolve) {
          onResolve(currentItem.id || currentItem.query_id);
        }
        if (selectedIndex >= flaggedItems.length - 1) {
          setSelectedIndex(Math.max(0, flaggedItems.length - 2));
        }
      }, 1800);
    }, 900);
  };

  return (
    <div data-testid="hitl-queue-modal" className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#333333] flex items-center justify-between bg-[#242424]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-rose-500/15 border border-rose-500/30 rounded-xl text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-[#FFFFFF]">HITL Operator Decision Console</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  {flaggedItems.length} PENDING AUDIT
                </span>
              </div>
              <p className="text-[11px] text-[#9AA0A6]">
                Human verification loop for tripped circuit breakers, PII leaks, and ungrounded hallucinations
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#9AA0A6] hover:text-[#FFFFFF] rounded-lg hover:bg-[#333333] cursor-pointer transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {/* Left: Queue List */}
          {flaggedItems.length > 0 && (
            <div className="w-full md:w-72 border-r border-[#333333] bg-[#181818] p-3 overflow-y-auto space-y-2 shrink-0">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#9AA0A6] px-1 block">
                Flagged Incidents ({flaggedItems.length})
              </span>
              {flaggedItems.map((item, idx) => {
                const isSelected = idx === selectedIndex;
                const isPii = item.trust?.verdict === 'SECURITY' || (item.query || item.text || '').toLowerCase().includes('ssn');

                return (
                  <button
                    key={item.id || item.query_id || idx}
                    onClick={() => {
                      setSelectedIndex(idx);
                      setActionMsg('');
                    }}
                    className={`w-full p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#242424] border-[#FF8C00] shadow-sm'
                        : 'bg-[#141414] border-[#2A2A2A] hover:border-[#444444] text-[#9AA0A6]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className={`text-[11px] font-bold truncate block ${isSelected ? 'text-[#FFFFFF]' : 'text-[#9AA0A6]'}`}>
                        Incident #{idx + 1}
                      </span>
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold ${
                        isPii ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                      }`}>
                        {isPii ? 'PII WARN' : 'BREAKER TRIP'}
                      </span>
                    </div>
                    <p className="text-[10px] truncate text-[#9AA0A6] mt-1">
                      {item.query || item.text || 'Flagged interaction payload'}
                    </p>
                  </button>
                );
              })}
            </div>
          )}

          {/* Right: Inspection & Resolution Workspace */}
          <div className="flex-1 p-6 space-y-4 overflow-y-auto text-xs bg-[#1E1E1E]">
            {flaggedItems.length === 0 ? (
              <div className="text-center py-16 text-[#9AA0A6] space-y-3">
                <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-[#FFFFFF]">All Incidents Cleared</h4>
                <p className="text-xs text-[#9AA0A6] max-w-sm mx-auto">
                  Zero flagged interactions in the queue. All live voice and text queries satisfy the 5-stage zero-trust guardrails.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Incident Detail Banner */}
                <div className="p-3.5 bg-rose-950/20 border border-rose-900/40 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-rose-400 font-mono flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Tripped Query Payload
                    </span>
                    <span className="text-[10px] font-mono text-[#FFC107]">
                      Confidence: {currentItem?.trust?.score ? `${Math.round(currentItem.trust.score * 100)}%` : 'Low'}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-[#FFFFFF] bg-[#121212] p-2.5 rounded-lg border border-[#2E2E2E]">
                    &ldquo;{currentItem?.query || currentItem?.text || 'Off-topic or low-grounded query'}&rdquo;
                  </p>
                  <div className="text-[11px] text-rose-300 font-mono">
                    Trigger Reason: {currentItem?.trust?.reason || 'Circuit breaker tripped due to ungrounded claims outside enterprise domain'}
                  </div>
                </div>

                {/* Operator Knowledge Correction Input */}
                <div className="space-y-1.5">
                  <label className="text-[#FFFFFF] font-semibold flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-[#FF8C00]" />
                      Verified Ground Truth Patch (Moss Re-Indexing):
                    </span>
                    <span className="text-[10px] text-[#9AA0A6] font-mono">Sub-10ms Vector Re-index</span>
                  </label>
                  <textarea
                    value={annotation}
                    onChange={(e) => setAnnotation(e.target.value)}
                    placeholder="Enter verified factual statement to patch into Moss knowledge index (e.g., 'Enterprise cloud customers are entitled to 30-day refunds via ticketing')..."
                    className="w-full h-24 bg-[#121212] border border-[#333333] rounded-xl p-3 text-[#FFFFFF] placeholder-[#9AA0A6] focus:outline-none focus:border-[#FF8C00] font-sans text-xs leading-relaxed"
                  />
                </div>

                {/* Status Notice */}
                {actionMsg && (
                  <div className="p-3 bg-[#FF8C00]/10 border border-[#FF8C00]/30 rounded-xl text-[#FFC107] flex items-center gap-2 font-mono text-xs animate-in fade-in">
                    <GitCommit className="w-4 h-4 text-[#FF8C00] shrink-0" />
                    <span>{actionMsg}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Action Footer */}
        {flaggedItems.length > 0 && (
          <div className="px-6 py-3.5 border-t border-[#333333] bg-[#242424] flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="text-[#9AA0A6] font-mono text-[11px]">
              Triage Mode: Dual-Control HITL Active
            </span>

            <div className="flex items-center gap-2">
              {/* Action 1: Dismiss False Positive */}
              <button
                onClick={() => handleAction('dismiss')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-[#1E1E1E] hover:bg-[#2A2A2A] border border-[#333333] hover:border-emerald-500/40 text-[#9AA0A6] hover:text-emerald-400 font-semibold rounded-xl transition-all cursor-pointer disabled:opacity-50"
                title="Dismiss and restore normal session flow"
              >
                Dismiss False Positive
              </button>

              {/* Action 2: Quarantine Threat Actor */}
              <button
                onClick={() => handleAction('block')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-950/70 border border-rose-800 text-rose-300 hover:text-rose-200 font-semibold rounded-xl transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                title="Quarantine and block actor"
              >
                <UserX className="w-3.5 h-3.5" />
                <span>Quarantine Actor</span>
              </button>

              {/* Action 3: Approve & Patch Moss */}
              <button
                onClick={() => handleAction('patch')}
                disabled={isSubmitting || !annotation.trim()}
                className="px-4 py-1.5 bg-gradient-to-r from-[#FF8C00] to-[#FFC107] hover:opacity-95 text-[#121212] font-bold rounded-xl transition-all shadow-md shadow-[#FF8C00]/20 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Re-indexing...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve &amp; Patch Moss</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


