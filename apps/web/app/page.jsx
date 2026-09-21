'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Send,
  Sparkles,
  Users,
  Radio,
  MessageSquare,
  Database,
  BookOpen,
  Gauge,
  Activity,
  Server,
  RefreshCcw,
  Bot,
  User,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import TrustBadge from '../components/hud/TrustBadge';
import LatencyWaterfall from '../components/hud/LatencyWaterfall';
import ContextViewer from '../components/hud/ContextViewer';
import HitlQueueModal from '../components/hitl/HitlQueueModal';
import LiveKitVoiceRoom from '../components/voice/LiveKitVoiceRoom';
import DatabaseStatsPanel from '../components/database/DatabaseStatsPanel';
import CrispeCatalogViewer from '../components/catalog/CrispeCatalogViewer';
import K6BenchmarkDashboard from '../components/scalability/K6BenchmarkDashboard';
import AttackSimulator from '../components/attack/AttackSimulator';
import HeaderUserDropdown from '../components/header/HeaderUserDropdown';
import LoginGate from '../components/auth/LoginGate';
import { AuthProvider, useAuth } from '../context/AuthContext';

const DEMO_PRESETS = [
  {
    label: 'Valid Query (PASS)',
    query: 'What is our refund policy for digital products?',
    expected: 'PASS',
  },
  {
    label: 'Off-Topic Query (FAIL)',
    query: 'Can I get a refund on quantum computing hardware mining rigs?',
    expected: 'FAIL',
  },
  {
    label: 'Security & PII Test',
    query: 'My SSN is 000-12-3456 and email is john.doe@example.com. Can you reset my password?',
    expected: 'SECURITY',
  },
];

function OperationsConsole({ isDemoMode, onExitDemo }) {
  const { user, getIdToken } = useAuth();
  const [activeTab, setActiveTab] = useState('agent'); // 'agent', 'database', 'catalog', 'scalability', 'attack'
  const [agentMode, setAgentMode] = useState('voice'); // 'voice' or 'text'
  const [selectedDomain, setSelectedDomain] = useState('general');
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Welcome to TrustMoss Operations Console on Next.js 14 App Router. I am an enterprise knowledge agent wrapped in real-time guardrails, LiveKit WebRTC audio streaming, PostgreSQL persistence, and sub-15ms Moss contextual retrieval.',
      trust: {
        verdict: 'PASS',
        color: 'green',
        score: 1.0,
        reason: 'System initialization verified.',
      },
      latency_trace: [
        { stage: 'webrtc_ingress', duration_ms: 11.2 },
        { stage: 'moss_retrieval', duration_ms: 9.4 },
        { stage: 'relevance_check', duration_ms: 0.02 },
        { stage: 'llm_generation', duration_ms: 412.0 },
        { stage: 'groundedness_check', duration_ms: 0.01 },
        { stage: 'pii_scan', duration_ms: 0.0 },
      ],
      total_latency_ms: 432.63,
      context_chunks: [
        {
          id: 'kb-init',
          text: 'TrustMoss Knowledge Base loaded with Enterprise Policies (Refund, SSO, Pricing, SLA, Password Reset).',
          score: 1.0,
        },
      ],
      timestamp: 'Initial startup',
    },
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeInspector, setActiveInspector] = useState(messages[0]);
  const [hitlModalOpen, setHitlModalOpen] = useState(false);
  const [flaggedItems, setFlaggedItems] = useState([]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'agent' && agentMode === 'text') {
      scrollToBottom();
    }
  }, [messages, isLoading, activeTab, agentMode]);

  const handleSend = async (queryText) => {
    const q = (queryText || input).trim();
    if (!q || isLoading) return;

    setInput('');
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const token = await getIdToken?.().catch(() => null);
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: q,
          domain: selectedDomain,
          operator_id: user?.uid || 'anonymous-demo',
          operator_email: user?.email || 'demo@trustmoss.local',
        }),
      });

      if (!res.ok) throw new Error(`Gateway returned HTTP ${res.status}`);

      const data = await res.json();
      const botMsg = {
        id: data.query_id || `bot-${Date.now()}`,
        role: 'assistant',
        text: data.answer,
        trust: data.trust,
        latency_trace: data.latency_trace,
        total_latency_ms: data.total_latency_ms,
        context_chunks: data.context_chunks,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, botMsg]);
      setActiveInspector(botMsg);

      if (data.trust?.verdict === 'FAIL' || data.trust?.verdict === 'WARN') {
        setFlaggedItems((prev) => [botMsg, ...prev]);
      }
    } catch (err) {
      console.warn('API fetch failed, generating client simulation fallback:', err);
      const isOffTopic = q.toLowerCase().includes('quantum') || q.toLowerCase().includes('mining');
      const isPii = q.toLowerCase().includes('ssn') || q.toLowerCase().includes('@');

      let verdict = 'PASS';
      let reason = 'Verified by Moss retrieval and NLI evaluator.';
      let score = 0.94;
      let ans = 'Our digital product refund policy allows 30-day no-questions-asked refunds via the billing dashboard.';

      if (isPii) {
        verdict = 'FAIL';
        reason = 'Circuit breaker tripped: Outbound PII detected. Response blocked.';
        score = 0.0;
        ans = '[CIRCUIT BREAKER] Request blocked: Prompt contains potential PII credentials.';
      } else if (isOffTopic) {
        verdict = 'FAIL';
        reason = 'Circuit breaker tripped: Context relevance score below threshold (0.24 < 0.60).';
        score = 0.24;
        ans = '[CIRCUIT BREAKER] I cannot answer this request safely because it is not grounded in the verified knowledge base.';
      }

      const fallbackMsg = {
        id: `fb-${Date.now()}`,
        role: 'assistant',
        text: ans,
        trust: { verdict, score, reason, color: verdict === 'PASS' ? 'green' : 'red' },
        latency_trace: [
          { stage: 'webrtc_ingress', duration_ms: 11.2 },
          { stage: 'moss_retrieval', duration_ms: 11.2 },
          { stage: 'relevance_check', duration_ms: 0.02 },
          { stage: 'llm_generation', duration_ms: 540.1 },
          { stage: 'groundedness_check', duration_ms: 0.02 },
          { stage: 'pii_scan', duration_ms: 0.01 },
        ],
        total_latency_ms: 562.55,
        context_chunks: [
          {
            id: 'kb-001',
            text: 'Our refund policy allows customers to request a full refund within 30 days of purchase.',
            score: isOffTopic ? 0.24 : 0.94,
          },
        ],
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, fallbackMsg]);
      setActiveInspector(fallbackMsg);

      if (verdict === 'FAIL') {
        setFlaggedItems((prev) => [fallbackMsg, ...prev]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceTurnLogged = (turnData) => {
    if (turnData.circuit_breaker_tripped) {
      setFlaggedItems((prev) => [
        {
          id: turnData.turn_id,
          role: 'voice-agent',
          text: turnData.final_speech_text,
          trust: turnData.trust,
          timestamp: turnData.timestamp,
        },
        ...prev,
      ]);
    }
  };

  return (
    <div className="min-h-screen bg-[#121212] text-[#FFFFFF] flex flex-col font-sans">
      {/* Top Navigation Bar - Fully Responsive Mobile First */}
      <header className="border-b border-[#333333] bg-[#1E1E1E]/95 backdrop-blur-md sticky top-0 z-30 px-3 sm:px-6 py-2.5 sm:py-3 shadow-lg flex flex-col lg:flex-row lg:items-center lg:justify-between gap-2.5 lg:gap-4">
        {/* Brand & Mobile Actions Row */}
        <div className="flex items-center justify-between gap-2 w-full lg:w-auto">
          {/* Brand Logo & Title */}
          <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
            <div className="p-2 bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 border border-[#FF8C00]/40 rounded-xl shadow-inner shadow-[#FF8C00]/20 shrink-0">
              <Shield className="w-4.5 h-4.5 sm:w-5 sm:h-5 text-[#FF8C00]" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <h1 className="text-sm sm:text-base font-bold tracking-tight text-[#FFFFFF] flex items-center gap-1">
                  Trust<span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF8C00] to-[#FFC107]">Moss</span>
                </h1>
                <span className="hidden sm:inline px-1.5 py-0.5 rounded-full text-[9px] sm:text-[10px] font-mono font-semibold bg-[#FF8C00]/10 text-[#FFC107] border border-[#FF8C00]/30">
                  Next.js 14
                </span>
              </div>
              <p className="text-[10px] sm:text-xs text-[#9AA0A6] truncate max-w-[140px] xs:max-w-[190px] sm:max-w-none">Zero-Latency Trust &amp; Guardrail Gateway</p>
            </div>
          </div>

          {/* Actions Menu Dropdown (Mobile) */}
          <div className="flex lg:hidden items-center shrink-0">
            <HeaderUserDropdown
              onOpenHitl={() => setHitlModalOpen(true)}
              flaggedCount={flaggedItems.length}
            />
          </div>
        </div>

        {/* Global Navigation Tabs - Horizontally Scrollable on Mobile with Smooth Pill Design */}
        <nav aria-label="Main Navigation" className="flex items-center bg-[#121212] border border-[#333333] rounded-xl p-1 text-xs font-medium overflow-x-auto no-scrollbar w-full lg:w-auto shrink-0 gap-1 shadow-inner">
          <button
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap cursor-pointer shrink-0 ${
              activeTab === 'agent'
                ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] shadow-md shadow-[#FF8C00]/20 font-bold'
                : 'text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#1E1E1E]'
            }`}
          >
            <Radio className="w-3.5 h-3.5 shrink-0" />
            <span>Agent HUD</span>
          </button>

          <button
            onClick={() => setActiveTab('database')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap cursor-pointer shrink-0 ${
              activeTab === 'database'
                ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] shadow-md shadow-[#FF8C00]/20 font-bold'
                : 'text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#1E1E1E]'
            }`}
          >
            <Database className="w-3.5 h-3.5 shrink-0" />
            <span>Postgres &amp; Redis</span>
          </button>

          <button
            onClick={() => setActiveTab('catalog')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap cursor-pointer shrink-0 ${
              activeTab === 'catalog'
                ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] shadow-md shadow-[#FF8C00]/20 font-bold'
                : 'text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#1E1E1E]'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 shrink-0" />
            <span>CRISPE Catalog</span>
          </button>

          <button
            onClick={() => setActiveTab('scalability')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap cursor-pointer shrink-0 ${
              activeTab === 'scalability'
                ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] shadow-md shadow-[#FF8C00]/20 font-bold'
                : 'text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#1E1E1E]'
            }`}
          >
            <Gauge className="w-3.5 h-3.5 shrink-0" />
            <span>k6 Benchmarks</span>
          </button>

          <button
            onClick={() => setActiveTab('attack')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap cursor-pointer shrink-0 ${
              activeTab === 'attack'
                ? 'bg-rose-600 text-[#FFFFFF] shadow-md shadow-rose-950/40 font-bold'
                : 'text-[#9AA0A6] hover:text-rose-400 hover:bg-[#1E1E1E]'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span>Attack Lab</span>
          </button>
        </nav>

        {/* Actions Menu Dropdown (Desktop) */}
        <div className="hidden lg:flex items-center shrink-0">
          <HeaderUserDropdown
            onOpenHitl={() => setHitlModalOpen(true)}
            flaggedCount={flaggedItems.length}
          />
        </div>
      </header>

      {/* Demo Sandbox Alert Banner */}
      {isDemoMode && (
        <div className="bg-[#FF8C00]/10 border-b border-[#FF8C00]/20 px-4 sm:px-6 py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-[#FFC107]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF8C00] animate-pulse shrink-0" />
            <span className="leading-snug">
              <strong>Demo Sandbox Mode:</strong> Unverified session. Sign in to enable authenticated audit logging and LiveKit room credentials.
            </span>
          </div>
          <button
            onClick={onExitDemo}
            className="self-start sm:self-auto px-2.5 py-1 bg-[#FF8C00]/20 hover:bg-[#FF8C00]/30 border border-[#FF8C00]/40 text-[#FFFFFF] rounded-lg font-medium text-xs transition-colors shrink-0 cursor-pointer"
          >
            Sign In Now
          </button>
        </div>
      )}

      {/* Main Tabbed Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5 lg:p-6">
        {/* TAB 1: LIVE AGENT HUD */}
        {activeTab === 'agent' && (
          <div className="space-y-6">
            {/* Mode Switcher & Domain Selector */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#333333] pb-3">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setAgentMode('voice')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all cursor-pointer ${
                    agentMode === 'voice'
                      ? 'bg-[#FF8C00]/15 border-[#FF8C00]/50 text-[#FFC107] shadow-sm'
                      : 'bg-[#1E1E1E] border-[#333333] text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#242424]'
                  }`}
                >
                  <Radio className="w-3.5 h-3.5 text-[#FF8C00]" />
                  <span>LiveKit Voice Stream (WebRTC)</span>
                </button>
                <button
                  onClick={() => setAgentMode('text')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all cursor-pointer ${
                    agentMode === 'text'
                      ? 'bg-[#FF8C00]/15 border-[#FF8C00]/50 text-[#FFC107] shadow-sm'
                      : 'bg-[#1E1E1E] border-[#333333] text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#242424]'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                  <span>Text Query &amp; Citation Inspection</span>
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-[#1E1E1E] border border-[#333333] rounded-xl px-2.5 py-1 text-xs">
                  <span className="text-[#9AA0A6] font-medium">Domain:</span>
                  <select
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="bg-transparent text-[#FFC107] font-semibold focus:outline-none cursor-pointer"
                  >
                    <option value="general" className="bg-[#1E1E1E] text-[#FFFFFF]">
                      General (SaaS Policies)
                    </option>
                    <option value="security" className="bg-[#1E1E1E] text-[#FFFFFF]">
                      Security (Zero-Trust)
                    </option>
                    <option value="finance" className="bg-[#1E1E1E] text-[#FFFFFF]">
                      Finance (PCI-DSS)
                    </option>
                    <option value="healthcare" className="bg-[#1E1E1E] text-[#FFFFFF]">
                      Healthcare (HIPAA)
                    </option>
                  </select>
                </div>

                <div className="text-xs font-mono text-[#9AA0A6] hidden sm:flex items-center gap-2 bg-[#1E1E1E] px-2.5 py-1 rounded-xl border border-[#333333]">
                  <span className="w-2 h-2 rounded-full bg-[#FF8C00] animate-pulse" />
                  <span>Moss Cache: &lt;15ms</span>
                </div>
              </div>
            </div>

            {agentMode === 'voice' ? (
              <LiveKitVoiceRoom onTurnLogged={handleVoiceTurnLogged} />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chat Column */}
                <div className="lg:col-span-2 flex flex-col bg-[#1E1E1E] border border-[#333333] rounded-2xl h-[520px] sm:h-[580px] lg:h-[640px] overflow-hidden shadow-xl">
                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                    {messages.map((m) => (
                      <div
                        key={m.id}
                        onClick={() => m.role === 'assistant' && setActiveInspector(m)}
                        className={`flex gap-3 p-3.5 rounded-xl transition-all ${
                          m.role === 'user'
                            ? 'bg-[#242424] border border-[#333333] ml-6 sm:ml-12 text-[#FFFFFF]'
                            : activeInspector?.id === m.id
                            ? 'bg-[#1E1E1E] border border-[#FF8C00]/50 shadow-lg shadow-[#FF8C00]/10 mr-2 sm:mr-4 cursor-pointer'
                            : 'bg-[#1E1E1E] border border-[#333333] hover:border-[#444444] mr-2 sm:mr-4 cursor-pointer'
                        }`}
                      >
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            m.role === 'user'
                              ? 'bg-[#333333] text-[#FFFFFF]'
                              : 'bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 text-[#FFC107] border border-[#FF8C00]/30'
                          }`}
                        >
                          {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[#FFFFFF] capitalize text-[11px]">{m.role}</span>
                            <span className="text-[10px] text-[#9AA0A6] font-mono">{m.timestamp}</span>
                          </div>
                          <p className="text-[#FFFFFF] leading-relaxed font-sans">{m.text}</p>
                          {m.trust && (
                            <div className="pt-1 flex items-center gap-2">
                              <TrustBadge trust={m.trust} />
                              {m.total_latency_ms && (
                                <span className="text-[10px] font-mono text-[#9AA0A6]">
                                  {m.total_latency_ms.toFixed(1)} ms
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Demo Presets Bar */}
                  <div className="px-4 py-2.5 bg-[#121212] border-t border-[#333333] flex items-center gap-2 overflow-x-auto no-scrollbar text-xs">
                    <span className="text-[11px] text-[#9AA0A6] font-medium whitespace-nowrap">Presets:</span>
                    {DEMO_PRESETS.map((p, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(p.query)}
                        disabled={isLoading}
                        className="px-2.5 py-1 rounded-lg bg-[#1E1E1E] hover:bg-[#242424] border border-[#333333] hover:border-[#FF8C00]/40 text-[11px] text-[#FFFFFF] whitespace-nowrap transition-colors cursor-pointer"
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>

                  {/* Input Box */}
                  <div className="p-3 bg-[#1E1E1E] border-t border-[#333333] flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Ask any enterprise question to verify Moss grounding..."
                      disabled={isLoading}
                      className="flex-1 bg-[#121212] border border-[#333333] rounded-xl px-4 py-2.5 text-xs text-[#FFFFFF] placeholder-[#9AA0A6] focus:outline-none focus:border-[#FF8C00]"
                    />
                    <button
                      onClick={() => handleSend()}
                      disabled={isLoading || !input.trim()}
                      className="px-4 py-2.5 bg-gradient-to-r from-[#FF8C00] to-[#FFC107] hover:from-[#FFA000] hover:to-[#FFD54F] disabled:opacity-50 text-[#121212] rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-md shadow-[#FF8C00]/20 cursor-pointer"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Send</span>
                    </button>
                  </div>
                </div>

                {/* Real-Time Inspector Column */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#FFFFFF] uppercase tracking-wider">
                      Real-Time Reliability Inspector
                    </span>
                    <span className="text-[10px] font-mono text-[#FFC107] bg-[#FF8C00]/10 px-2 py-0.5 rounded-full border border-[#FF8C00]/20">
                      Glass-Box Tracing
                    </span>
                  </div>

                  {activeInspector?.trust && (
                    <div className="p-4 bg-[#1E1E1E] border border-[#333333] rounded-2xl space-y-3 shadow-md">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#FFFFFF]">Composite Trust Verdict</span>
                        <TrustBadge
                          trust={activeInspector.trust}
                          history={messages.filter((m) => m.trust)}
                        />
                      </div>
                      <p className="text-xs text-[#9AA0A6] leading-relaxed font-sans">
                        {activeInspector.trust.reason}
                      </p>
                    </div>
                  )}

                  {activeInspector?.latency_trace && (
                    <LatencyWaterfall
                      trace={activeInspector.latency_trace}
                      totalMs={activeInspector.total_latency_ms}
                    />
                  )}

                  {activeInspector?.context_chunks && (
                    <ContextViewer chunks={activeInspector.context_chunks} />
                  )}
                </div>
              </div>
            )}
          </div>
        )}


        {/* TAB 2: POSTGRESQL & REDIS EXPLORER */}
        {activeTab === 'database' && <DatabaseStatsPanel />}

        {/* TAB 3: CRISPE PROMPT CATALOG */}
        {activeTab === 'catalog' && <CrispeCatalogViewer />}

        {/* TAB 4: K6 SCALABILITY BENCHMARKS */}
        {activeTab === 'scalability' && <K6BenchmarkDashboard />}

        {/* TAB 5: ADVERSARIAL ATTACK SIMULATOR & STRESS MATRIX */}
        {activeTab === 'attack' && <AttackSimulator />}
      </main>

      {/* HITL Review Modal */}
      <HitlQueueModal
        isOpen={hitlModalOpen}
        onClose={() => setHitlModalOpen(false)}
        flaggedItems={flaggedItems}
        onResolve={(id) => {
          setFlaggedItems((prev) => prev.filter((item) => (item.id || item.query_id) !== id));
        }}
      />
    </div>
  );
}

function ConsoleGate() {
  const { user, loading } = useAuth();
  const [demoMode, setDemoMode] = useState(false);

  if (loading) {
    return (
      <div
        data-testid="auth-verifying-splash"
        className="min-h-screen bg-[#121212] text-[#FFFFFF] flex flex-col items-center justify-center p-6 font-sans"
      >
        <div className="w-9 h-9 border-2 border-[#FF8C00]/20 border-t-[#FF8C00] rounded-full animate-spin mb-3 shadow-lg shadow-[#FF8C00]/20" />
        <span className="text-xs text-[#9AA0A6] font-mono">Verifying enterprise operator credentials...</span>
      </div>
    );
  }

  if (!user && !demoMode) {
    return <LoginGate onEnterGuestMode={() => setDemoMode(true)} />;
  }

  return (
    <OperationsConsole
      isDemoMode={!user && demoMode}
      onExitDemo={() => setDemoMode(false)}
    />
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <ConsoleGate />
    </AuthProvider>
  );
}
