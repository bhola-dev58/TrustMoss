'use client';

import React from 'react';
import {
  Settings,
  Radio,
  MessageSquare,
  Zap,
  Shield,
  CheckCircle2,
  Cpu,
  Layers,
  Activity,
  Mic,
  Volume2,
  ArrowRight,
  Database,
  Sparkles,
} from 'lucide-react';

const DOMAIN_OPTIONS = [
  {
    id: 'general',
    name: 'General (SaaS Policies)',
    badge: 'Standard',
    description: 'General subscription plans, refund policy terms, enterprise SLAs, and user licensing.',
  },
  {
    id: 'security',
    name: 'Security (Zero-Trust)',
    badge: 'High Sec',
    description: 'RBAC identity controls, multi-tenant secrets protection, and intrusion detection parameters.',
  },
  {
    id: 'finance',
    name: 'Finance (PCI-DSS)',
    badge: 'Regulated',
    description: 'Cardholder data masking, SOX transaction auditing, and financial records segregation.',
  },
  {
    id: 'healthcare',
    name: 'Healthcare (HIPAA)',
    badge: 'PHI Guard',
    description: 'Patient health information (ePHI) de-identification, access logging, and HIPAA compliance.',
  },
];

export default function SettingsPanel({
  agentMode = 'voice',
  setAgentMode,
  selectedDomain = 'general',
  setSelectedDomain,
  onLaunchHud,
}) {
  return (
    <div data-testid="settings-panel" className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-4 sm:p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#FF8C00]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div className="flex items-start sm:items-center gap-3.5">
            <div className="p-3 rounded-xl bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 border border-[#FF8C00]/40 text-[#FF8C00] shadow-md shadow-[#FF8C00]/10 shrink-0">
              <Settings className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg sm:text-xl font-bold text-[#FFFFFF]">
                  Gateway &amp; Stream Settings
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30">
                  v2.4 READY
                </span>
              </div>
              <p className="text-xs text-[#9AA0A6] mt-0.5">
                Configure primary surface stream mode, zero-trust knowledge domain, cache latency SLA, and voice parameters.
              </p>
            </div>
          </div>

          {onLaunchHud && (
            <button
              onClick={onLaunchHud}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] font-bold text-xs flex items-center gap-2 shadow-lg shadow-[#FF8C00]/20 hover:opacity-95 transition-all cursor-pointer shrink-0 self-start sm:self-auto"
            >
              <span>Launch Agent HUD</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Active Pipeline Status Notice */}
      <div className="p-3.5 sm:p-4 bg-[#141414] border border-[#FF8C00]/30 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-inner">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30 shrink-0">
            <Sparkles className="w-4 h-4 text-[#FF8C00]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#FFFFFF]">
                Target Agent HUD Acting Mode:
              </span>
              <span className="text-xs font-mono font-bold text-[#FFC107]">
                {agentMode === 'voice' ? 'LiveKit Voice Stream (WebRTC)' : 'Text Query & Citation Inspection'}
              </span>
            </div>
            <p className="text-[10px] text-[#9AA0A6] mt-0.5">
              Configured for <strong className="text-[#FFFFFF]">{DOMAIN_OPTIONS.find((d) => d.id === selectedDomain)?.name || selectedDomain}</strong> with <strong className="text-[#FFC107]">Moss Cache &lt;15ms</strong>. Changes apply immediately to the Agent HUD interface.
            </p>
          </div>
        </div>

        {onLaunchHud && (
          <button
            onClick={onLaunchHud}
            className="px-3.5 py-1.5 rounded-xl bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/50 text-[#FFC107] text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shrink-0 self-start sm:self-auto"
          >
            <span>Open Acting Interface</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Main Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Surface Stream Mode Setting */}
        <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-[#333333] pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#FF8C00]" />
              <h3 className="text-sm font-bold text-[#FFFFFF]">Surface Stream Mode</h3>
            </div>
            <span className="text-[10px] font-mono text-[#9AA0A6]">Interactive Protocol</span>
          </div>

          <div className="space-y-3">
            {/* LiveKit Voice Stream Card */}
            <div
              onClick={() => setAgentMode && setAgentMode('voice')}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${
                agentMode === 'voice'
                  ? 'bg-[#FF8C00]/10 border-[#FF8C00] shadow-md shadow-[#FF8C00]/10 ring-1 ring-[#FF8C00]/30'
                  : 'bg-[#181818] border-[#333333] hover:border-[#FF8C00]/40 hover:bg-[#202020]'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                  agentMode === 'voice'
                    ? 'bg-[#FF8C00] text-[#121212]'
                    : 'bg-[#242424] text-[#9AA0A6]'
                }`}
              >
                <Radio className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs sm:text-sm font-bold text-[#FFFFFF]">
                    LiveKit Voice Stream (WebRTC)
                  </span>
                  {agentMode === 'voice' && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-[#FFC107] font-mono">
                      <CheckCircle2 className="w-3.5 h-3.5" /> ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#9AA0A6] mt-1 leading-relaxed">
                  Real-time ultra-low-latency duplex voice interaction powered by LiveKit WebRTC, neural VAD, and sub-350ms streaming pipeline.
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-2.5">
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Sub-350ms Latency
                  </span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    Duplex WebRTC
                  </span>
                </div>
              </div>
            </div>

            {/* Text Query & Citation Inspection Card */}
            <div
              onClick={() => setAgentMode && setAgentMode('text')}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${
                agentMode === 'text'
                  ? 'bg-[#FF8C00]/10 border-[#FF8C00] shadow-md shadow-[#FF8C00]/10 ring-1 ring-[#FF8C00]/30'
                  : 'bg-[#181818] border-[#333333] hover:border-[#FF8C00]/40 hover:bg-[#202020]'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                  agentMode === 'text'
                    ? 'bg-[#FF8C00] text-[#121212]'
                    : 'bg-[#242424] text-[#9AA0A6]'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs sm:text-sm font-bold text-[#FFFFFF]">
                    Text Query &amp; Citation Inspection
                  </span>
                  {agentMode === 'text' && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-[#FFC107] font-mono">
                      <CheckCircle2 className="w-3.5 h-3.5" /> ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#9AA0A6] mt-1 leading-relaxed">
                  High-throughput SSE text streaming with 5-stage zero-trust guardrail inspection, latency waterfall, and context tracing.
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-2.5">
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    SSE Token Stream
                  </span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    5-Stage Guardrails
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Knowledge Domain Selector Setting */}
        <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-[#333333] pb-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#FF8C00]" />
              <h3 className="text-sm font-bold text-[#FFFFFF]">Knowledge Domain:</h3>
            </div>
            <span className="text-[10px] font-mono text-[#FFC107] bg-[#FF8C00]/10 border border-[#FF8C00]/30 px-2 py-0.5 rounded">
              Active Context
            </span>
          </div>

          <div className="space-y-2.5">
            {DOMAIN_OPTIONS.map((domain) => {
              const isSelected = selectedDomain === domain.id;
              return (
                <div
                  key={domain.id}
                  onClick={() => setSelectedDomain && setSelectedDomain(domain.id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    isSelected
                      ? 'bg-[#FF8C00]/10 border-[#FF8C00]/60 shadow-sm'
                      : 'bg-[#181818] border-[#333333] hover:border-[#FF8C00]/30 hover:bg-[#202020]'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${isSelected ? 'text-[#FFC107]' : 'text-[#FFFFFF]'}`}>
                        {domain.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#242424] text-[#9AA0A6] border border-[#333333]">
                        {domain.badge}
                      </span>
                    </div>
                    <p className="text-[10px] text-[#9AA0A6] truncate mt-0.5">
                      {domain.description}
                    </p>
                  </div>
                  <div className="shrink-0">
                    <input
                      type="radio"
                      name="domainOption"
                      checked={isSelected}
                      onChange={() => setSelectedDomain && setSelectedDomain(domain.id)}
                      className="accent-[#FF8C00] cursor-pointer w-4 h-4"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Moss Cache & Latency Telemetry Setting */}
        <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-[#333333] pb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#FF8C00]" />
              <h3 className="text-sm font-bold text-[#FFFFFF]">Telemetry &amp; Cache Performance</h3>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              HEALTHY
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Cache Telemetry Card */}
            <div className="p-3.5 bg-[#141414] border border-[#333333] rounded-xl space-y-1">
              <div className="flex items-center gap-2 text-[11px] text-[#9AA0A6]">
                <span className="w-2 h-2 rounded-full bg-[#FF8C00] animate-pulse" />
                <span>Moss Cache:</span>
              </div>
              <div className="text-lg font-mono font-bold text-[#FFC107]">
                &lt;15ms
              </div>
              <div className="text-[9px] text-[#9AA0A6]/70">L1 Memory + L2 Redis</div>
            </div>

            {/* Ingress SLA Card */}
            <div className="p-3.5 bg-[#141414] border border-[#333333] rounded-xl space-y-1">
              <div className="flex items-center gap-2 text-[11px] text-[#9AA0A6]">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                <span>Target SLA:</span>
              </div>
              <div className="text-lg font-mono font-bold text-emerald-400">
                &lt;45ms
              </div>
              <div className="text-[9px] text-[#9AA0A6]/70">Gateway Edge Ingress</div>
            </div>

            {/* Guardrails Card */}
            <div className="p-3.5 bg-[#141414] border border-[#333333] rounded-xl space-y-1">
              <div className="flex items-center gap-2 text-[11px] text-[#9AA0A6]">
                <Shield className="w-3.5 h-3.5 text-sky-400" />
                <span>Guardrails:</span>
              </div>
              <div className="text-sm font-mono font-bold text-[#FFFFFF]">
                5-Stage Active
              </div>
              <div className="text-[9px] text-[#9AA0A6]/70">Regex + Sem + PII + Out</div>
            </div>

            {/* Simulated Hit Rate */}
            <div className="p-3.5 bg-[#141414] border border-[#333333] rounded-xl space-y-1">
              <div className="flex items-center gap-2 text-[11px] text-[#9AA0A6]">
                <Database className="w-3.5 h-3.5 text-amber-400" />
                <span>Hit Rate:</span>
              </div>
              <div className="text-sm font-mono font-bold text-[#FFC107]">
                99.4%
              </div>
              <div className="text-[9px] text-[#9AA0A6]/70">Sub-millisecond index</div>
            </div>
          </div>
        </div>

        {/* Voice Speaker Accent & Audio Tuning Setting */}
        <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-[#333333] pb-3">
            <div className="flex items-center gap-2">
              <Mic className="w-4 h-4 text-[#FF8C00]" />
              <h3 className="text-sm font-bold text-[#FFFFFF]">Voice &amp; Speaker Tuning</h3>
            </div>
            <span className="text-[10px] font-mono text-[#FFC107] bg-[#FF8C00]/10 border border-[#FF8C00]/30 px-2 py-0.5 rounded">
              WebRTC Audio
            </span>
          </div>

          <div className="space-y-3">
            <div className="p-3 bg-[#141414] border border-[#333333] rounded-xl flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-[#FF8C00]" />
                  <span className="text-xs font-semibold text-[#FFFFFF]">Native Accent Tuning</span>
                </div>
                <p className="text-[10px] text-[#9AA0A6] mt-0.5">
                  Indian English native speaker cadence &amp; prosody (en-IN)
                </p>
              </div>
              <span className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            <div className="p-3 bg-[#141414] border border-[#333333] rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-[#FFFFFF] block">Codec &amp; Bitrate</span>
                <p className="text-[10px] text-[#9AA0A6] mt-0.5">
                  Opus Fullband 48kHz Stereo &bull; 64 kbps VBR
                </p>
              </div>
              <span className="text-[10px] font-mono text-[#9AA0A6]">Default</span>
            </div>

            <div className="p-3 bg-[#141414] border border-[#333333] rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-[#FFFFFF] block">Noise Cancellation</span>
                <p className="text-[10px] text-[#9AA0A6] mt-0.5">
                  Client-side WebRTC Acoustic Echo Cancellation (AEC) + AGC
                </p>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">Enabled</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
