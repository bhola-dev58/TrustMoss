'use client';

import React, { useState } from 'react';
import { BookOpen, Sparkles, Code2, ShieldCheck, ChevronRight, Copy, Check } from 'lucide-react';

const CATALOG_TEMPLATES = [
  {
    name: 'ORCHESTRATOR_V1',
    category: 'orchestration',
    version: '1.0.0',
    surface: 'Text Agent & Primary LLM Inference',
    model: 'Groq / Llama-3.1-8B-Instant',
    crispe: {
      capacity: 'Zero-hallucination enterprise reliability orchestrator',
      role: 'Strict contextual answer synthesizer bound by retrieved Moss facts',
      insight: 'Prevent ungrounded claims with citation markers [kb-xxx]',
      statement: 'Synthesize verified answers solely from provided context chunks',
      personality: 'Concise, authoritative, professional, neutral',
      experiment: 'Sub-45ms latency with 100% citation precision',
    },
  },
  {
    name: 'VOICE_AGENT_V1',
    category: 'orchestration',
    version: '1.0.0',
    surface: 'LiveKit Real-Time WebRTC Worker',
    model: 'Groq / Llama-3.1-8B-Instant (Stream)',
    crispe: {
      capacity: 'Ultra-low-latency voice conversationalist',
      role: 'Spoken dialogue agent with strict 256-token turn length',
      insight: 'Natural conversational cadence with immediate circuit breaker trip on safety error',
      statement: 'Provide direct spoken response formatted for Cartesia TTS synthesis',
      personality: 'Natural, empathetic, concise, spoken-friendly',
      experiment: 'Under 350ms total turn turnaround time',
    },
  },
  {
    name: 'GROUNDEDNESS_JUDGE_V1',
    category: 'evaluation',
    version: '1.0.0',
    surface: 'Evaluation Microservice (NLI Evaluator)',
    model: 'NLI Entailment Classifier / Groq',
    crispe: {
      capacity: 'Mathematical groundedness evaluator',
      role: 'Natural Language Inference judge validating premise vs hypothesis',
      insight: 'Score between 0.0 and 1.0 against strict 0.85 pass threshold',
      statement: 'Return structured JSON with entailment probability and ungrounded statements',
      personality: 'Deterministic, analytical, rigorous',
      experiment: 'Zero hallucinated claims slip through to user',
    },
  },
  {
    name: 'HALLUCINATION_RISK_V1',
    category: 'evaluation',
    version: '1.0.0',
    surface: 'Evaluation Microservice (Risk Classifier)',
    model: 'Groq / Llama-3.1-8B-Instant',
    crispe: {
      capacity: 'Tri-state risk assessment engine',
      role: 'Classify response risk level: LOW, MEDIUM, HIGH, CRITICAL',
      insight: 'Identify statistical likelihood of unverified numerical/factual claims',
      statement: 'Evaluate answer text against golden knowledge base assertions',
      personality: 'Conservative risk auditor',
      experiment: '100% capture of fabricated dates, pricing, or SLAs',
    },
  },
  {
    name: 'JAILBREAK_ANALYST_V1',
    category: 'safety',
    version: '1.0.0',
    surface: 'Guardrails Microservice (Inbound Scanner)',
    model: 'Guardrails AI + Regex & Embedding Scanner',
    crispe: {
      capacity: 'Adversarial prompt injection detector',
      role: 'Intercept DAN, system override, base64 payload, and role-reversal attacks',
      insight: 'Sub-2ms heuristic scan with secondary LLM adversarial check if ambiguous',
      statement: 'Score injection probability 0.0-1.0; block immediately if > 0.70',
      personality: 'Zero-trust perimeter firewall',
      experiment: '100% intercept rate on OWASP LLM01 test vectors',
    },
  },
  {
    name: 'HITL_VERDICT_V1',
    category: 'governance',
    version: '1.0.0',
    surface: 'HITL Review & Knowledge Ingestion',
    model: 'Human Reviewer + Structured Prompt Formatter',
    crispe: {
      capacity: 'Audit and index version registry patcher',
      role: 'Generate cryptographically signed correction record for Moss re-indexing',
      insight: 'Ensure human supervisor corrections are formatted into golden KB chunks',
      statement: 'Produce immutable change audit log with operator identity and rationale',
      personality: 'Compliance-first auditor',
      experiment: 'Atomic index rollbacks in under 100ms',
    },
  },
  {
    name: 'HITL_SUMMARIZER_V1',
    category: 'governance',
    version: '1.0.0',
    surface: 'Operator Summary & Incident Management',
    model: 'Groq / Llama-3.1-8B-Instant',
    crispe: {
      capacity: 'Incident triage and summarization engine',
      role: 'Generate executive incident briefs for blocked prompts and security events',
      insight: 'Summarize root cause of circuit breaker trip for security officers',
      statement: 'Output concise markdown summary with violation timeline and impact',
      personality: 'Executive incident commander',
      experiment: 'Sub-2 second automated RCA report generation',
    },
  },
];

export default function CrispeCatalogViewer() {
  const [selectedTemplate, setSelectedTemplate] = useState(CATALOG_TEMPLATES[0]);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(selectedTemplate, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div data-testid="crispe-catalog-viewer" className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#333333] pb-4">
        <div>
          <h2 className="text-base font-bold text-[#FFFFFF] flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#FF8C00]" />
            CRISPE Prompt Catalog &amp; Governance Registry
          </h2>
          <p className="text-xs text-[#9AA0A6]">
            Version-controlled prompt architecture across all 7 LLM surfaces with zero drift
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 bg-[#FF8C00]/15 border border-[#FF8C00]/30 text-[#FFC107] font-mono text-xs font-semibold rounded-xl">
            7/7 Templates Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template List */}
        <div className="bg-[#1E1E1E] border border-[#333333] rounded-2xl p-4 space-y-2 shadow-xl">
          <span className="text-xs font-semibold text-[#9AA0A6] uppercase tracking-wider block px-2 mb-2">
            Registered Prompt Surfaces
          </span>
          {CATALOG_TEMPLATES.map((tpl) => {
            const isSelected = selectedTemplate.name === tpl.name;
            return (
              <button
                key={tpl.name}
                onClick={() => setSelectedTemplate(tpl)}
                className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between cursor-pointer ${
                  isSelected
                    ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] border-transparent shadow-md shadow-[#FF8C00]/20 font-bold'
                    : 'bg-[#242424] border-[#333333] hover:border-[#FF8C00]/40 text-[#9AA0A6] hover:text-[#FFFFFF]'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs">{tpl.name}</span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                        isSelected
                          ? 'bg-[#121212]/20 text-[#121212]'
                          : 'bg-[#121212] text-[#9AA0A6] border border-[#333333]'
                      }`}
                    >
                      v{tpl.version}
                    </span>
                  </div>
                  <span
                    className={`text-[11px] block mt-0.5 line-clamp-1 ${
                      isSelected ? 'text-[#121212]/85' : 'text-[#9AA0A6]'
                    }`}
                  >
                    {tpl.surface}
                  </span>
                </div>
                <ChevronRight
                  className={`w-4 h-4 ${isSelected ? 'text-[#121212]' : 'text-[#9AA0A6]'}`}
                />
              </button>
            );
          })}
        </div>

        {/* Selected Template Details */}
        <div className="lg:col-span-2 bg-[#1E1E1E] border border-[#333333] rounded-2xl p-6 space-y-5 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#333333] pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-5 h-5 text-[#FF8C00]" />
                <h3 className="text-base font-bold text-[#FFFFFF] font-mono">{selectedTemplate.name}</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30 uppercase">
                  {selectedTemplate.category}
                </span>
              </div>
              <p className="text-xs text-[#9AA0A6] mt-1">{selectedTemplate.surface}</p>
            </div>
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 bg-[#242424] hover:bg-[#333333] text-[#9AA0A6] hover:text-[#FFFFFF] text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-[#333333] hover:border-[#FF8C00]/40 transition-all cursor-pointer shadow-sm"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#FFC107]" /> : <Copy className="w-3.5 h-3.5 text-[#FF8C00]" />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
          </div>

          {/* Model info */}
          <div className="flex items-center gap-4 text-xs font-mono bg-[#121212] p-3.5 rounded-xl border border-[#333333]">
            <span className="text-[#9AA0A6]">Inference Target:</span>
            <span className="text-[#FFC107] font-semibold">{selectedTemplate.model}</span>
          </div>

          {/* CRISPE Framework Breakdown */}
          <div className="space-y-3 text-xs">
            <span className="font-semibold text-[#FFFFFF] uppercase tracking-wider text-[11px] block">
              CRISPE Prompt Specification
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FFC107]">Capacity [C]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.capacity}</p>
              </div>

              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FF8C00]">Role [R]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.role}</p>
              </div>

              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FFC107]">Insight [I]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.insight}</p>
              </div>

              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FF8C00]">Statement [S]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.statement}</p>
              </div>

              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FFC107]">Personality [P]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.personality}</p>
              </div>

              <div className="p-3.5 bg-[#121212] border border-[#333333] rounded-xl space-y-1 hover:border-[#FF8C00]/30 transition-colors">
                <span className="text-[10px] font-bold font-mono uppercase text-[#FF8C00]">Experiment [E]</span>
                <p className="text-[#FFFFFF] leading-relaxed">{selectedTemplate.crispe.experiment}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
