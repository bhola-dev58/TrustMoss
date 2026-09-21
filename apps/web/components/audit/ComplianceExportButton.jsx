'use client';

import React, { useState } from 'react';
import { Download, ShieldCheck, Loader2 } from 'lucide-react';

export default function ComplianceExportButton({ className = '' }) {
  const [loading, setLoading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/compliance/audit-report');
      const data = await res.json();

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trustmoss-compliance-audit-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 3000);
    } catch (err) {
      console.error('Failed to export compliance audit:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={loading}
      className={`flex items-center gap-2 px-3 py-1.5 bg-[#242424] hover:bg-[#333333] text-[#9AA0A6] hover:text-[#FFFFFF] text-xs font-semibold rounded-xl border border-[#333333] hover:border-[#FF8C00]/40 transition-all shadow-sm cursor-pointer disabled:opacity-50 font-sans ${className}`}
      title="Download certified GDPR, NIST AI RMF, and OWASP audit report"
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin text-[#FF8C00]" />
      ) : downloaded ? (
        <ShieldCheck className="w-3.5 h-3.5 text-[#FFC107]" />
      ) : (
        <Download className="w-3.5 h-3.5 text-[#FF8C00]" />
      )}
      <span>{downloaded ? 'Audit Exported!' : 'Export Compliance Audit'}</span>
    </button>
  );
}

