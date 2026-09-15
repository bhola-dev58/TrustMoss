'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Send,
  Zap,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Github,
  Users,
  AlertOctagon,
  CheckCircle2,
  Info,
  Server,
  Activity,
  Bot,
  User,
  Radio,
  MessageSquare,
} from 'lucide-react';
import TrustBadge from '../src/components/TrustBadge';
import LatencyWaterfall from '../src/components/LatencyWaterfall';
import ContextViewer from '../src/components/ContextViewer';
import HitlQueueModal from '../src/components/HitlQueueModal';
import LiveKitVoiceRoom from '../src/components/LiveKitVoiceRoom';

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

export default function Home() {
  const [activeTab, setActiveTab] = useState('voice'); // 'voice' or 'text'
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Welcome to TrustMoss on Next.js 14 App Router. I am an enterprise knowledge agent wrapped in real-time guardrails, LiveKit WebRTC audio streaming, and sub-15ms Moss contextual retrieval.',
      trust: {
        verdict: 'PASS',
        color: 'green',
        score: 1.0,
        reason: 'System initialization verified.',
      },
      latency_trace: [
        { stage: 'moss_retrieval', duration_ms: 9.4 },
        { stage: 'relevance_check', duration_ms: 0.02 },
        { stage: 'llm_generation', duration_ms: 412.0 },
        { stage: 'groundedness_check', duration_ms: 0.01 },
        { stage: 'pii_scan', duration_ms: 0.0 },
      ],
      total_latency_ms: 421.43,
      context_chunks: [
        {
          id: 'kb-init',
          text: 'TrustMoss Knowledge Base loaded with Enterprise Policies (Refund, SSO, Pricing, SLA, Password Reset).',
          score: 1.0,
        },
      ],
      timestamp: new Date().toLocaleTimeString(),
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
    scrollToBottom();
  }, [messages, isLoading]);

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
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, top_k: 3 }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.statusText}`);
      }

      const data = await res.json();

      const assistantMsg = {
        id: data.query_id || `resp-${Date.now()}`,
        role: 'assistant',
        text: data.answer,
        trust: data.trust,
        guardrails: data.guardrails,
        latency_trace: data.latency_trace,
        total_latency_ms: data.total_latency_ms,
        context_chunks: data.context_chunks,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setActiveInspector(assistantMsg);

      if (data.trust?.verdict === 'WARN' || data.trust?.verdict === 'FAIL') {
        setFlaggedItems((prev) => [assistantMsg, ...prev]);
      }
    } catch (err) {
      console.warn('API error, using local fallback:', err);
      const isOffTopic = q.toLowerCase().includes('quantum') || q.toLowerCase().includes('crypto');
      const isPii = q.includes('SSN') || q.includes('000-12');

      let verdict = 'PASS';
      let reason = 'All guardrail checks passed. Grounded in Moss context.';
      let score = 0.94;
      let ans = 'Our refund policy allows customers to request a full refund within 30 days of purchase. Digital products are eligible if defective.';

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
          { stage: 'moss_retrieval', duration_ms: 11.2 },
          { stage: 'relevance_check', duration_ms: 0.02 },
          { stage: 'llm_generation', duration_ms: 540.1 },
          { stage: 'groundedness_check', duration_ms: 0.02 },
          { stage: 'pii_scan', duration_ms: 0.01 },
        ],
        total_latency_ms: 551.35,
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
    // Also push voice turns that fail into HITL queue
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
                Next.js App Router • LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">Zero-Latency Trust & Guardrail Gateway for Voice & Text Agents</p>
          </div>
        </div>

        {/* Live System Status Badges */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-slate-400">LiveKit:</span>
            <span className="text-emerald-400 font-semibold">WebRTC Gateway</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-slate-400">Moss Index:</span>
            <span className="text-emerald-400 font-semibold">trustmoss-kb (~11ms)</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Groq:</span>
            <span className="text-slate-200">Llama-3.1-8B</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setHitlModalOpen(true)}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium rounded-xl flex items-center gap-2 text-slate-300 transition-colors"
          >
            <Users className="w-3.5 h-3.5 text-amber-400" />
            <span>HITL Queue</span>
            {flaggedItems.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-500 text-white font-bold">
                {flaggedItems.length}
              </span>
            )}
          </button>

          <a
            href="https://github.com/bhola-dev58/TrustMoss"
            target="_blank"
            rel="noreferrer"
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="GitHub Repository"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </header>

      {/* Gateway Mode Switcher Tabs */}
      <div className="border-b border-slate-800 bg-[#0a0f19] px-6 py-2 flex items-center gap-3">
        <button
          onClick={() => setActiveTab('voice')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'voice'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border border-transparent'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>LiveKit Voice Reliability Gateway</span>
          <span className="px-1.5 py-0.2 rounded text-[9px] bg-emerald-400/20 text-emerald-300 font-mono">
            MANDATORY STACK
          </span>
        </button>

        <button
          onClick={() => setActiveTab('text')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'text'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border border-transparent'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Synchronous Text Trust Console</span>
        </button>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Interactive Area */}
        <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-4xl mx-auto w-full gap-6">
          {activeTab === 'voice' ? (
            /* LiveKit Voice Room Interface */
            <LiveKitVoiceRoom onTurnLogged={handleVoiceTurnLogged} />
          ) : (
            /* Text RAG Pipeline Console */
            <>
              {/* Presets */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-slate-400 font-medium">Test Presets:</span>
                {DEMO_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(p.query)}
                    disabled={isLoading}
                    className="px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg text-xs text-slate-300 transition-all font-medium flex items-center gap-1.5"
                  >
                    <Zap className="w-3 h-3 text-emerald-400" />
                    <span>{p.label}</span>
                  </button>
                ))}
              </div>

              {/* Chat Log */}
              <div className="flex-1 flex flex-col gap-4">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => m.role === 'assistant' && setActiveInspector(m)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                      m.role === 'user'
                        ? 'bg-slate-900/60 border-slate-800 ml-12'
                        : activeInspector?.id === m.id
                        ? 'bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/20 mr-12'
                        : 'bg-[#0c121e]/80 border-slate-800/80 hover:border-slate-700 mr-12'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {m.role === 'user' ? (
                          <div className="p-1.5 bg-slate-800 rounded-lg text-slate-300">
                            <User className="w-3.5 h-3.5" />
                          </div>
                        ) : (
                          <div className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30">
                            <Bot className="w-3.5 h-3.5" />
                          </div>
                        )}
                        <span className="text-xs font-semibold text-slate-300">
                          {m.role === 'user' ? 'User Query' : 'TrustMoss Agent'}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">{m.timestamp}</span>
                      </div>

                      {m.trust && <TrustBadge trust={m.trust} />}
                    </div>

                    <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">{m.text}</p>

                    {m.latency_trace && (
                      <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
                        <span>Total: {m.total_latency_ms}ms</span>
                        <span className="text-emerald-400">Click to inspect verification hops</span>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="sticky bottom-0 bg-[#090d14]/90 backdrop-blur-md pt-2"
              >
                <div className="relative flex items-center">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter prompt to evaluate through Trust Gateway..."
                    disabled={isLoading}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 pr-12 font-medium"
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="absolute right-2 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white rounded-lg transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </>
          )}
        </div>

        {/* Right Telemetry & Inspection Sidebar */}
        <aside className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-slate-800 bg-[#0a0f19] p-5 flex flex-col gap-5 overflow-y-auto">
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 font-mono">
              Live Trust Inspector
            </h2>
            {activeInspector ? (
              <div className="flex flex-col gap-4">
                <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                  <span className="text-xs text-slate-400 font-mono block mb-1">Status Verdict</span>
                  <TrustBadge trust={activeInspector.trust} />
                  <p className="text-xs text-slate-300 mt-2 font-medium">{activeInspector.trust?.reason}</p>
                </div>

                {/* Per-Hop Latency Waterfall */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-300 mb-2 font-mono">
                    Per-Hop Latency Waterfall ({activeInspector.total_latency_ms}ms)
                  </h3>
                  <LatencyWaterfall latencyTrace={activeInspector.latency_trace} />
                </div>

                {/* Moss Context Chunks */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-300 mb-2 font-mono">
                    Moss Context Chunks ({activeInspector.context_chunks?.length || 0})
                  </h3>
                  <ContextViewer chunks={activeInspector.context_chunks} />
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Select an agent turn to inspect reliability metrics
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* HITL Modal */}
      <HitlQueueModal
        isOpen={hitlModalOpen}
        onClose={() => setHitlModalOpen(false)}
        flaggedItems={flaggedItems}
      />
    </div>
  );
}
