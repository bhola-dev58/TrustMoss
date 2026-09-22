import { describe, it, expect } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';

// Components under test
import TrustBadge from '../components/hud/TrustBadge.jsx';
import LatencyWaterfall from '../components/hud/LatencyWaterfall.jsx';
import ContextViewer from '../components/hud/ContextViewer.jsx';
import DatabaseStatsPanel from '../components/database/DatabaseStatsPanel.jsx';
import CrispeCatalogViewer from '../components/catalog/CrispeCatalogViewer.jsx';
import K6BenchmarkDashboard from '../components/scalability/K6BenchmarkDashboard.jsx';
import SettingsPanel from '../components/settings/SettingsPanel.jsx';

// Backward compatibility re-exports
import LegacyTrustBadge from '../src/components/TrustBadge.jsx';
import LegacyLatencyWaterfall from '../src/components/LatencyWaterfall.jsx';

// Helper to strip React 18 SSR comments like <!-- -->
const renderClean = (component) => renderToString(component).replace(/<!--.*?-->/g, '');

describe('HUD & UI Component Suite', () => {
  describe('TrustBadge Component', () => {
    it('renders TRUST VERIFIED badge for PASS verdict', () => {
      const html = renderClean(
        React.createElement(TrustBadge, { trust: { verdict: 'PASS', score: 0.96 } })
      );
      expect(html).toContain('data-testid="trust-badge"');
      expect(html).toContain('TRUST VERIFIED');
      expect(html).toContain('(96%)');
      expect(html).toContain('text-emerald-400');
    });

    it('renders TRUST WARNING badge for WARN verdict', () => {
      const html = renderClean(
        React.createElement(TrustBadge, { trust: { verdict: 'WARN', score: 0.74, reason: 'Low semantic grounding' } })
      );
      expect(html).toContain('TRUST WARNING');
      expect(html).toContain('(74%)');
      expect(html).toContain('text-amber-400');
    });

    it('renders CIRCUIT BREAKER TRIPPED badge for FAIL verdict', () => {
      const html = renderClean(
        React.createElement(TrustBadge, { trust: { verdict: 'FAIL', score: 0.42, reason: 'Hallucination detected' } })
      );
      expect(html).toContain('CIRCUIT BREAKER TRIPPED');
      expect(html).toContain('(42%)');
      expect(html).toContain('text-rose-400');
    });

    it('supports backward compatibility via src/components/TrustBadge re-export', () => {
      const html = renderClean(
        React.createElement(LegacyTrustBadge, { trust: { verdict: 'PASS', score: 0.98 } })
      );
      expect(html).toContain('TRUST VERIFIED');
      expect(html).toContain('(98%)');
    });
  });

  describe('LatencyWaterfall Component', () => {
    const mockTrace = [
      { stage: 'webrtc_ingress', duration_ms: 2.1 },
      { stage: 'stt_transcription', duration_ms: 3.4 },
      { stage: 'inbound_guardrail', duration_ms: 1.8 },
      { stage: 'moss_retrieval', duration_ms: 10.5 },
      { stage: 'relevance_gate', duration_ms: 2.3 },
      { stage: 'llm_reasoning', duration_ms: 12.1 },
      { stage: 'groundedness_eval', duration_ms: 3.2 },
      { stage: 'outbound_pii_check', duration_ms: 1.4 },
      { stage: 'tts_synthesis', duration_ms: 3.0 },
    ];

    it('renders 8-hop microsecond latency trace with SLA gate', () => {
      const html = renderClean(React.createElement(LatencyWaterfall, { trace: mockTrace }));
      expect(html).toContain('data-testid="latency-waterfall"');
      expect(html).toContain('8-Hop Microsecond Latency Trace');
      expect(html).toContain('Total: 39.8 ms');
      expect(html).toContain('WebRTC Signaling Ingress');
      expect(html).toContain('Moss Context Retrieval');
      expect(html).toContain('NLI Groundedness Evaluator');
    });

    it('supports backward compatibility via src/components/LatencyWaterfall re-export', () => {
      const html = renderClean(React.createElement(LegacyLatencyWaterfall, { trace: mockTrace }));
      expect(html).toContain('Total: 39.8 ms');
    });
  });

  describe('ContextViewer Component', () => {
    it('renders grounding chunks with count and top score header', () => {
      const mockChunks = [
        {
          id: 'chunk-1',
          score: 0.942,
          text: 'TrustMoss enforces strict sub-45ms latency SLAs.',
        },
        {
          id: 'chunk-2',
          score: 0.887,
          text: 'Moss vector similarity search operates under 15ms.',
        },
      ];
      const html = renderClean(React.createElement(ContextViewer, { chunks: mockChunks }));
      expect(html).toContain('data-testid="context-viewer"');
      expect(html).toContain('Moss Context Grounding (2 chunks retrieved)');
      expect(html).toContain('Top Score: 94.2%');
    });
  });

  describe('CRISPE Prompt Catalog Component', () => {
    it('renders all 7 system surfaces with roles and principles', () => {
      const html = renderClean(React.createElement(CrispeCatalogViewer));
      expect(html).toContain('data-testid="crispe-catalog-viewer"');
      expect(html).toContain('CRISPE Prompt Catalog &amp; Governance Registry');
      expect(html).toContain('ORCHESTRATOR_V1');
      expect(html).toContain('VOICE_AGENT_V1');
    });
  });

  describe('k6 Scalability Benchmark Component', () => {
    it('renders load profile options and k6 OSS engine header', () => {
      const html = renderClean(React.createElement(K6BenchmarkDashboard));
      expect(html).toContain('data-testid="k6-benchmark-dashboard"');
      expect(html).toContain('k6 OSS Scalability Testing &amp; Concurrency Benchmarks');
      expect(html).toContain('Grafana k6 OSS Engine');
      expect(html).toContain('Virtual Users (VUs)');
      expect(html).toContain('Load Test');
      expect(html).toContain('Stress Test');
    });
  });

  describe('Database Stats Panel Component', () => {
    it('renders PostgreSQL connection pool and Redis session metrics', () => {
      const html = renderClean(React.createElement(DatabaseStatsPanel));
      expect(html).toContain('data-testid="database-stats-panel"');
      expect(html).toContain('PostgreSQL Persistence &amp; Redis Session Cache Layer');
      expect(html).toContain('PostgreSQL Pool');
      expect(html).toContain('Redis Cache');
      expect(html).toContain('Trust Events');
      expect(html).toContain('Audit Logs');
    });
  });

  describe('SettingsPanel Component', () => {
    it('renders dynamic Voice & Speaker Tuning controls with active Indian English accent', () => {
      const html = renderClean(React.createElement(SettingsPanel));
      expect(html).toContain('data-testid="settings-panel"');
      expect(html).toContain('Voice &amp; Speaker Tuning');
      expect(html).toContain('Native Accent Tuning');
      expect(html).toContain('Indian English native speaker cadence &amp; prosody (en-IN)');
      expect(html).toContain('ACTIVE');
      expect(html).toContain('Codec &amp; Bitrate');
      expect(html).toContain('Opus Fullband 48kHz Stereo • 64 kbps VBR');
      expect(html).toContain('Default');
      expect(html).toContain('Noise Cancellation');
      expect(html).toContain('Client-side WebRTC Acoustic Echo Cancellation (AEC) + AGC');
      expect(html).toContain('Enabled');
    });
  });
});
