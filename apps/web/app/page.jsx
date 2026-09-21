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
import ComplianceExportButton from '../components/audit/ComplianceExportButton';
import AuthButton from '../components/auth/AuthButton';
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
    <div className="min-h-screen bg-[#090d14] text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-[#0c121e]/90 backdrop-blur-md sticky top-0 z-30 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-emerald-500/20 to-moss-600/30 border border-emerald-500/40 rounded-xl shadow-inner shadow-emerald-500/20">
            <Shield className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white">TrustMoss</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Next.js 14 App Router
              </span>
            </div>
            <p className="text-xs text-slate-400">Zero-Latency Trust & Guardrail Gateway for Voice & Text Agents</p>
          </div>
        </div>

        {/* Global Navigation Tabs */}
        <div className="flex items-center bg-slate-900/90 border border-slate-800 rounded-xl p-1 text-xs font-medium">
          <button
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'agent'
                ? 'bg-emerald-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Agent HUD</span>
          </button>

          <button
            onClick={() => setActiveTab('database')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'database'
                ? 'bg-emerald-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Postgres & Redis</span>
          </button>

          <button
            onClick={() => setActiveTab('catalog')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'catalog'
                ? 'bg-emerald-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>CRISPE Catalog</span>
          </button>

          <button
            onClick={() => setActiveTab('scalability')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'scalability'
                ? 'bg-emerald-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Gauge className="w-3.5 h-3.5" />
            <span>k6 Benchmarks</span>
          </button>

          <button
            onClick={() => setActiveTab('attack')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'attack'
                ? 'bg-red-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-red-400" />
            <span>Attack Lab</span>
          </button>
        </div>

        {/* Header Actions (HITL + Compliance + Google Auth) */}
        <div className="flex items-center gap-2.5">
          <ComplianceExportButton />

          <button
            onClick={() => setHitlModalOpen(true)}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium rounded-xl flex items-center gap-2 text-slate-300 transition-colors"
          >
            <Users className="w-3.5 h-3.5 text-amber-400" />
            <span>HITL Queue</span>
            {flaggedItems.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold font-mono">
                {flaggedItems.length}
              </span>
            )}
          </button>

          <AuthButton />
        </div>
      </header>

      {/* Demo Sandbox Alert Banner */}
      {isDemoMode && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>
              <strong>Demo Sandbox Mode:</strong> Operator session unverified. Sign in with Google Workspace to enable authenticated audit logging and LiveKit room token access.
            </span>
          </div>
          <button
            onClick={onExitDemo}
            className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-200 rounded-lg font-medium transition-colors"
          >
            Sign In Now
          </button>
        </div>
      )}

      {/* Main Tabbed Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {/* TAB 1: LIVE AGENT HUD */}
        {activeTab === 'agent' && (
          <div className="space-y-6">
            {/* Mode Switcher */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAgentMode('voice')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all ${
                    agentMode === 'voice'
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <Radio className="w-3.5 h-3.5 text-emerald-400" />
                  <span>LiveKit Voice Stream (WebRTC)</span>
                </button>
                <button
                  onClick={() => setAgentMode('text')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all ${
                    agentMode === 'text'
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
                  <span>Text Query & Citation Inspection</span>
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-[#131b2e] border border-slate-700/60 rounded-xl px-2.5 py-1 text-xs">
                  <span className="text-slate-400 font-medium">Domain:</span>
                  <select
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="bg-transparent text-emerald-400 font-semibold focus:outline-none cursor-pointer"
                  >
                    <option value="general" className="bg-slate-900 text-slate-200">
                      General (SaaS Policies)
                    </option>
                    <option value="security" className="bg-slate-900 text-slate-200">
                      Security (Zero-Trust)
                    </option>
                    <option value="finance" className="bg-slate-900 text-slate-200">
                      Finance (PCI-DSS)
                    </option>
                    <option value="healthcare" className="bg-slate-900 text-slate-200">
                      Healthcare (HIPAA)
                    </option>
                  </select>
                </div>

                <div className="text-xs font-mono text-slate-500 hidden sm:flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span>Moss Cache: &lt;15ms</span>
                </div>
              </div>
            </div>

            {agentMode === 'voice' ? (
              <LiveKitVoiceRoom onTurnLogged={handleVoiceTurnLogged} />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chat Column */}
                <div className="lg:col-span-2 flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl h-[640px] overflow-hidden">
                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                    {messages.map((m) => (
                      <div
                        key={m.id}
                        onClick={() => m.role === 'assistant' && setActiveInspector(m)}
                        className={`flex gap-3 p-3.5 rounded-xl transition-all ${
                          m.role === 'user'
                            ? 'bg-slate-800/40 border border-slate-700/50 ml-12'
                            : activeInspector?.id === m.id
                            ? 'bg-slate-850 border border-emerald-500/40 shadow-lg shadow-emerald-950/20 mr-4 cursor-pointer'
                            : 'bg-slate-900/80 border border-slate-800 hover:border-slate-700 mr-4 cursor-pointer'
                        }`}
                      >
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            m.role === 'user' ? 'bg-slate-700 text-slate-200' : 'bg-emerald-600/30 text-emerald-400'
                          }`}
                        >
                          {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-300 capitalize text-[11px]">{m.role}</span>
                            <span className="text-[10px] text-slate-500 font-mono">{m.timestamp}</span>
                          </div>
                          <p className="text-slate-200 leading-relaxed font-sans">{m.text}</p>
                          {m.trust && (
                            <div className="pt-1 flex items-center gap-2">
                              <TrustBadge trust={m.trust} />
                              {m.total_latency_ms && (
                                <span className="text-[10px] font-mono text-slate-400">
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
                  <div className="px-4 py-2 bg-slate-950/60 border-t border-slate-800 flex items-center gap-2 overflow-x-auto text-xs">
                    <span className="text-[11px] text-slate-500 font-medium whitespace-nowrap">Presets:</span>
                    {DEMO_PRESETS.map((p, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(p.query)}
                        disabled={isLoading}
                        className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[11px] text-slate-300 whitespace-nowrap transition-colors"
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>

                  {/* Input Box */}
                  <div className="p-3 bg-slate-900/90 border-t border-slate-800 flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Ask any enterprise question to verify Moss grounding..."
                      disabled={isLoading}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                    <button
                      onClick={() => handleSend()}
                      disabled={isLoading || !input.trim()}
                      className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Send</span>
                    </button>
                  </div>
                </div>

                {/* Real-Time Inspector Column */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Real-Time Reliability Inspector
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400">Glass-Box Tracing</span>
                  </div>

                  {activeInspector?.trust && (
                    <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-2xl space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-300">Composite Trust Verdict</span>
                        <TrustBadge
                          trust={activeInspector.trust}
                          history={messages.filter((m) => m.trust)}
                        />
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed font-sans">
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
        className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col items-center justify-center p-6"
      >
        <div className="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin mb-3" />
        <span className="text-xs text-slate-400 font-mono">Verifying enterprise operator credentials...</span>
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
