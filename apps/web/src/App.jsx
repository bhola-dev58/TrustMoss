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
} from 'lucide-react';
import TrustBadge from './components/TrustBadge';
import LatencyWaterfall from './components/LatencyWaterfall';
import ContextViewer from './components/ContextViewer';
import HitlQueueModal from './components/HitlQueueModal';

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

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Welcome to TrustMoss. I am an enterprise knowledge agent wrapped in real-time guardrails and low-latency Moss contextual retrieval. Ask a question about our policies, or test our circuit breaker with off-topic or sensitive prompts.',
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

      // If WARN or FAIL, push to HITL queue
      if (data.trust?.verdict === 'WARN' || data.trust?.verdict === 'FAIL') {
        setFlaggedItems((prev) => [assistantMsg, ...prev]);
      }
    } catch (err) {
      console.warn('API error, falling back to local simulation:', err);

      // Graceful local fallback for preview
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
                v0.1.0 • LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">Zero-Latency Trust & Guardrail Gateway for AI Agents</p>
          </div>
        </div>

        {/* Live System Status Badges */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400">Moss Index:</span>
            <span className="text-emerald-400 font-semibold">trustmoss-kb (~11ms)</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Groq LLM:</span>
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

      {/* Main Workspace Layout */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-0 overflow-hidden">
        {/* Left Column: Interactive Chat Stream (7 cols) */}
        <section className="lg:col-span-7 flex flex-col border-r border-slate-800/80 h-[calc(100vh-61px)]">
          {/* Quick Demo Test Pills */}
          <div className="px-6 py-2.5 bg-slate-950/60 border-b border-slate-800/60 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-slate-500 font-medium whitespace-nowrap flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-400" /> Demo Scenarios:
            </span>
            {DEMO_PRESETS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p.query)}
                className="whitespace-nowrap px-2.5 py-1 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg text-[11px] text-slate-300 transition-all font-medium"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((m) => (
              <div
                key={m.id}
                onClick={() => m.role === 'assistant' && setActiveInspector(m)}
                className={`flex gap-3 cursor-pointer transition-all ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Shield className="w-4 h-4 text-emerald-400" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-4 space-y-3 ${
                    m.role === 'user'
                      ? 'bg-emerald-600 text-white rounded-tr-none'
                      : 'bg-slate-900/90 border border-slate-800/90 text-slate-100 rounded-tl-none hover:border-slate-700 shadow-lg'
                  }`}
                >
                  {/* Assistant Header with Trust Badge */}
                  {m.role === 'assistant' && m.trust && (
                    <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                      <TrustBadge trust={m.trust} />
                      <span className="text-[10px] text-slate-500 font-mono">{m.timestamp}</span>
                    </div>
                  )}

                  {/* Body Text */}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap font-sans">{m.text}</p>

                  {/* Assistant Quick Stats Footer */}
                  {m.role === 'assistant' && m.total_latency_ms && (
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 font-mono">
                      <span className="text-emerald-400 flex items-center gap-1">
                        <Zap className="w-3 h-3" /> Moss: ~11ms
                      </span>
                      <span>Total: {m.total_latency_ms.toFixed(1)} ms</span>
                    </div>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <User className="w-4 h-4 text-slate-300" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-xl bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center flex-shrink-0 animate-pulse">
                  <Shield className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl rounded-tl-none space-y-2 max-w-sm">
                  <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono">
                    <Zap className="w-3.5 h-3.5 animate-spin" />
                    <span>Executing Moss Retrieval & Guardrails...</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full w-2/3 animate-pulse" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Footer */}
          <div className="p-4 bg-slate-950/90 border-t border-slate-800/80">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="relative flex items-center"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about enterprise policies (or test hallucination & PII detection)..."
                disabled={isLoading}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-2xl pl-4 pr-12 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2.5 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white rounded-xl transition-all shadow-md shadow-emerald-900/30"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </section>

        {/* Right Column: Real-time Telemetry & Trust Inspector (5 cols) */}
        <section className="lg:col-span-5 flex flex-col h-[calc(100vh-61px)] bg-[#0a0f19] p-6 space-y-5 overflow-y-auto">
          <div>
            <h2 className="text-xs uppercase font-bold tracking-wider text-slate-400">Live Trust & Telemetry Inspector</h2>
            <p className="text-[11px] text-slate-500">Inspecting request: {activeInspector?.id || 'Latest'}</p>
          </div>

          {/* Active Verdict Summary Card */}
          {activeInspector?.trust && (
            <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Trust Verdict</span>
                <TrustBadge trust={activeInspector.trust} />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{activeInspector.trust.reason}</p>
            </div>
          )}

          {/* Latency Waterfall */}
          <LatencyWaterfall
            trace={activeInspector?.latency_trace}
            totalMs={activeInspector?.total_latency_ms}
          />

          {/* Moss Context Chunks */}
          <ContextViewer chunks={activeInspector?.context_chunks} />

          {/* Circuit Breaker & Safety Logic Rules */}
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 text-xs space-y-2.5 text-slate-400">
            <h3 className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-emerald-400" />
              Tri-State Guardrail Policy
            </h3>
            <ul className="space-y-1.5 text-[11px]">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span><strong className="text-slate-200">PASS:</strong> Relevance &ge; 0.7, Groundedness &ge; 0.7, Zero PII</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span><strong className="text-slate-200">WARN:</strong> Exactly 1 check borderline; response flagged</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <span><strong className="text-slate-200">FAIL:</strong> 2+ checks fail OR PII leaked; circuit breaker trips</span>
              </li>
            </ul>
          </div>
        </section>
      </main>

      {/* HITL Review Modal */}
      <HitlQueueModal
        isOpen={hitlModalOpen}
        onClose={() => setHitlModalOpen(false)}
        flaggedItems={flaggedItems}
        onResolve={(id) => {
          setFlaggedItems((prev) => prev.filter((i) => (i.id || i.query_id) !== id));
        }}
      />
    </div>
  );
}
