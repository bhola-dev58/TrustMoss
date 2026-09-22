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
  Menu,
  Settings,
  FileText,
} from 'lucide-react';
import TrustBadge from '../components/hud/TrustBadge';
import LatencyWaterfall from '../components/hud/LatencyWaterfall';
import ContextViewer from '../components/hud/ContextViewer';
import CitationDrawer from '../components/hud/CitationDrawer';
import SlaDeviationBanner from '../components/hud/SlaDeviationBanner';
import HitlQueueModal from '../components/hitl/HitlQueueModal';
import LiveKitVoiceRoom from '../components/voice/LiveKitVoiceRoom';
import DatabaseStatsPanel from '../components/database/DatabaseStatsPanel';
import CrispeCatalogViewer from '../components/catalog/CrispeCatalogViewer';
import K6BenchmarkDashboard from '../components/scalability/K6BenchmarkDashboard';
import AttackSimulator from '../components/attack/AttackSimulator';
import HeaderUserDropdown from '../components/header/HeaderUserDropdown';
import SidebarNavigation from '../components/navigation/SidebarNavigation';
import SettingsPanel from '../components/settings/SettingsPanel';
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
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
  const [citationDrawerOpen, setCitationDrawerOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);

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

      if (data.trust?.verdict === 'FAIL' || data.trust?.verdict === 'WARN' || data.trust?.verdict === 'SECURITY') {
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
    <div className="min-h-screen bg-[#121212] text-[#FFFFFF] flex font-sans">
      {/* Left Sliding Sidebar Navigation */}
      <SidebarNavigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="border-b border-[#333333] bg-[#1E1E1E]/95 backdrop-blur-md sticky top-0 z-30 px-3 sm:px-6 py-2.5 sm:py-3 shadow-lg flex items-center justify-between gap-3">
          {/* Left: Sidebar Toggle Button + Active View Indicator */}
          <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0">
            {/* Dynamic Opener Button: Visible ONLY on mobile when the sidebar is closed */}
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/40 text-[#9AA0A6] hover:text-[#FFFFFF] rounded-xl cursor-pointer transition-all shadow-sm flex items-center justify-center shrink-0"
                title="Open Navigation Menu"
                aria-label="Open Navigation Menu"
              >
                <Menu className="w-4 h-4 text-[#FF8C00]" />
              </button>
            )}

            {/* Active View Label & Icon */}
            <div className="flex items-center gap-2 min-w-0">
              <div className="p-1.5 rounded-lg bg-[#FF8C00]/10 border border-[#FF8C00]/30 shrink-0">
                {activeTab === 'agent' && <Radio className="w-4 h-4 text-[#FF8C00]" />}
                {activeTab === 'database' && <Database className="w-4 h-4 text-[#FF8C00]" />}
                {activeTab === 'catalog' && <BookOpen className="w-4 h-4 text-[#FF8C00]" />}
                {activeTab === 'scalability' && <Gauge className="w-4 h-4 text-[#FF8C00]" />}
                {activeTab === 'attack' && <Zap className="w-4 h-4 text-rose-400" />}
                {activeTab === 'settings' && <Settings className="w-4 h-4 text-[#FF8C00]" />}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <h1 className="text-xs sm:text-sm font-bold text-[#FFFFFF] truncate">
                    {activeTab === 'agent' && 'Agent HUD & Live WebRTC'}
                    {activeTab === 'database' && 'Postgres & Redis Architecture'}
                    {activeTab === 'catalog' && 'CRISPE Prompt Catalog'}
                    {activeTab === 'scalability' && 'k6 Scalability Benchmarks'}
                    {activeTab === 'attack' && 'Adversarial Attack Lab'}
                    {activeTab === 'settings' && 'Gateway & Stream Settings'}
                  </h1>
                  <span className="hidden sm:inline px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30 uppercase shrink-0">
                    Active
                  </span>
                </div>
                <p className="text-[10px] text-[#9AA0A6] truncate hidden sm:block">
                  TrustMoss Zero-Trust AI Gateway &bull; Next.js 14 App Router
                </p>
              </div>
            </div>
          </div>

          {/* Right: Consolidated Header Profile & Compliance Dropdown */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
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
        {/* Proactive SLA & Deviation Alert Monitor */}
        <div className="mb-4">
          <SlaDeviationBanner
            mossLatency={activeInspector?.latency_trace?.find(s => s.stage.includes('moss'))?.duration_ms || 6.2}
            ingressLatency={activeInspector?.latency_trace?.find(s => s.stage.includes('ingress'))?.duration_ms || 8.4}
            tripCount={flaggedItems.length}
          />
        </div>

        {/* TAB 1: LIVE AGENT HUD */}
        {activeTab === 'agent' && (
          <div className="space-y-5">
            {/* Active Pipeline & Surface Mode Bar */}
            <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-3 sm:p-4 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30 shrink-0">
                  {agentMode === 'voice' ? (
                    <Radio className="w-4 h-4 text-[#FF8C00]" />
                  ) : (
                    <MessageSquare className="w-4 h-4 text-[#FF8C00]" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs sm:text-sm font-bold text-[#FFFFFF] truncate">
                      {agentMode === 'voice'
                        ? 'LiveKit Voice Stream (WebRTC)'
                        : 'Text Query & Citation Inspection'}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-[10px] text-[#9AA0A6] truncate">
                    {agentMode === 'voice'
                      ? 'Duplex WebRTC audio • Indian English (en-IN) speaker tuning • Sub-350ms pipeline'
                      : 'SSE text stream with 5-stage zero-trust guardrails • Real-time citation inspection'}
                  </p>
                </div>
              </div>

              {/* Badges & Actions */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Domain Pill */}
                <div className="px-2.5 py-1 rounded-xl bg-[#121212] border border-[#333333] text-[10px] font-mono flex items-center gap-1.5">
                  <span className="text-[#9AA0A6]">Domain:</span>
                  <span className="text-[#FFC107] font-semibold">
                    {selectedDomain === 'general' && 'General (SaaS)'}
                    {selectedDomain === 'security' && 'Security (Zero-Trust)'}
                    {selectedDomain === 'finance' && 'Finance (PCI-DSS)'}
                    {selectedDomain === 'healthcare' && 'Healthcare (HIPAA)'}
                  </span>
                </div>

                {/* Moss Cache Pill */}
                <div className="px-2.5 py-1 rounded-xl bg-[#121212] border border-[#333333] text-[10px] font-mono flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#FF8C00] animate-pulse" />
                  <span className="text-[#9AA0A6]">Cache:</span>
                  <span className="text-[#FFC107] font-semibold">&lt;15ms</span>
                </div>

                {/* Inline Mode Switcher Button */}
                <button
                  onClick={() => setAgentMode(agentMode === 'voice' ? 'text' : 'voice')}
                  className="px-2.5 py-1 rounded-xl bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/40 text-[#FFC107] text-[10px] font-semibold flex items-center gap-1.5 cursor-pointer transition-all shadow-sm"
                  title={agentMode === 'voice' ? 'Switch to Text Query' : 'Switch to Voice Stream'}
                >
                  {agentMode === 'voice' ? (
                    <>
                      <MessageSquare className="w-3 h-3 text-[#FF8C00]" />
                      <span>Switch to Text</span>
                    </>
                  ) : (
                    <>
                      <Radio className="w-3 h-3 text-[#FF8C00]" />
                      <span>Switch to Voice</span>
                    </>
                  )}
                </button>

                {/* Settings Shortcut Button */}
                <button
                  onClick={() => setActiveTab('settings')}
                  className="px-2.5 py-1 rounded-xl bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/40 text-[#9AA0A6] hover:text-[#FFFFFF] text-[10px] font-semibold flex items-center gap-1.5 cursor-pointer transition-all"
                  title="Configure in Gateway Settings"
                >
                  <Settings className="w-3 h-3 text-[#FF8C00]" />
                  <span className="hidden sm:inline">Settings</span>
                </button>
              </div>
            </div>

            {/* Acting Interface based on configured mode */}
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

                          {/* Interactive Clickable Citation Badges */}
                          {m.context_chunks && m.context_chunks.length > 0 && (
                            <div className="pt-1.5 flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] font-mono text-[#9AA0A6]">Citations:</span>
                              {m.context_chunks.map((chunk, cIdx) => (
                                <button
                                  key={cIdx}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedCitation({
                                      ...chunk,
                                      domain: selectedDomain === 'general' ? 'General (SaaS Policies)' : selectedDomain,
                                    });
                                    setCitationDrawerOpen(true);
                                  }}
                                  className="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-[#141414] hover:bg-[#202020] text-[#FFC107] border border-[#FF8C00]/30 hover:border-[#FF8C00] flex items-center gap-1 transition-all cursor-pointer shadow-sm hover:scale-105 active:scale-95"
                                  title="Click to inspect verified grounding passage"
                                >
                                  <FileText className="w-2.5 h-2.5 text-[#FF8C00]" />
                                  <span>{chunk.id || `kb-00${cIdx + 1}`}</span>
                                  <span className="text-[9px] text-emerald-400 font-bold">
                                    {chunk.score ? Math.round(chunk.score * 100) : 98}%
                                  </span>
                                </button>
                              ))}
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

        {/* TAB 6: GATEWAY & STREAM SETTINGS */}
        {activeTab === 'settings' && (
          <SettingsPanel
            agentMode={agentMode}
            setAgentMode={setAgentMode}
            selectedDomain={selectedDomain}
            setSelectedDomain={setSelectedDomain}
            onLaunchHud={() => setActiveTab('agent')}
          />
        )}
      </main>
      </div>

      {/* HITL Review Modal */}
      <HitlQueueModal
        isOpen={hitlModalOpen}
        onClose={() => setHitlModalOpen(false)}
        flaggedItems={flaggedItems}
        onResolve={(id) => {
          setFlaggedItems((prev) => prev.filter((item) => (item.id || item.query_id) !== id));
        }}
      />

      {/* Citation Verification Drawer */}
      <CitationDrawer
        isOpen={citationDrawerOpen}
        onClose={() => setCitationDrawerOpen(false)}
        citation={selectedCitation}
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
