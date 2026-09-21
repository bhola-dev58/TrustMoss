'use client';

import React, { useState } from 'react';
import {
  Shield,
  Lock,
  CheckCircle2,
  Server,
  Zap,
  Radio,
  Eye,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function LoginGate({ onEnterGuestMode }) {
  const { signInWithGoogle } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSignIn = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      await signInWithGoogle();
    } catch (err) {
      if (err.code !== 'auth/popup-closed-by-user') {
        if (err.code === 'auth/unauthorized-domain') {
          const currentHost = typeof window !== 'undefined' ? window.location.hostname : 'this domain';
          setErrorMsg(
            `Firebase Domain Unauthorized: "${currentHost}" needs to be added to Firebase Console > Authentication > Settings > Authorized Domains. In the meantime, use Guest Demo Mode below.`
          );
        } else if (err.code === 'auth/popup-blocked') {
          setErrorMsg('Popup Blocked: Please allow popups for this site in your browser URL bar.');
        } else {
          setErrorMsg(err.message || 'Sign-in failed. Please verify popup permissions and try again.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      data-testid="login-gate"
      className="min-h-screen bg-[#121212] text-[#FFFFFF] flex flex-col items-center justify-center p-4 sm:p-6 relative overflow-hidden font-sans"
    >
      {/* Ambient Ember Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[#FF8C00]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-[#FFC107]/5 rounded-full blur-2xl pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 max-w-md w-full bg-[#1E1E1E] border border-[#333333] rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
        {/* Header Icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="p-3.5 bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/30 border border-[#FF8C00]/50 rounded-2xl shadow-lg shadow-[#FF8C00]/20">
              <Shield className="w-8 h-8 text-[#FF8C00]" />
            </div>
            <div className="absolute -bottom-1 -right-1 p-1 bg-[#121212] border border-[#333333] rounded-full">
              <Lock className="w-3.5 h-3.5 text-[#FFC107]" />
            </div>
          </div>
        </div>

        {/* Title & Description */}
        <div className="text-center space-y-2 mb-6">
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-[#FFFFFF] flex items-center gap-1.5">
              Trust<span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF8C00] to-[#FFC107]">Moss</span>
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-[#FF8C00]/10 text-[#FFC107] border border-[#FF8C00]/30">
              Zero-Trust AI
            </span>
          </div>
          <p className="text-xs text-[#9AA0A6] leading-relaxed">
            Enterprise Trust &amp; Guardrail Gateway for Voice &amp; Text Agents
          </p>
        </div>

        {/* Security Notice Box */}
        <div className="bg-[#242424] border border-[#333333] rounded-xl p-3 mb-6 text-xs text-[#9AA0A6] flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-[#FF8C00] mt-0.5 shrink-0" />
          <div>
            <span className="font-semibold text-[#FFFFFF]">Operator Authentication Required:</span>
            <p className="text-[#9AA0A6] text-[11px] mt-0.5 leading-relaxed">
              Access to agent telemetry, LiveKit WebRTC audio, database records, and HITL overrides is restricted to verified operators.
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-400 space-y-2">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{errorMsg}</span>
            </div>
            {onEnterGuestMode && (
              <button
                onClick={onEnterGuestMode}
                className="w-full py-1.5 px-3 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-200 font-medium text-[11px] rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Bypass and Enter in Demo Mode</span>
              </button>
            )}
          </div>
        )}

        {/* Action Button: Google Sign-In */}
        <button
          onClick={handleSignIn}
          disabled={loading}
          data-testid="google-signin-button"
          className="w-full py-2.5 px-4 bg-white hover:bg-slate-100 text-slate-900 font-semibold text-xs rounded-xl flex items-center justify-center gap-3 transition-all shadow-md shadow-slate-900/50 disabled:opacity-60 cursor-pointer"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-slate-400 border-t-slate-900 rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.665-5.17 3.665-9.12z"
              />
              <path
                fill="#34A853"
                d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.27 21.43 7.34 24 12 24z"
              />
              <path
                fill="#FBBC05"
                d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.13z"
              />
              <path
                fill="#EA4335"
                d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.27 2.57 1.25 6.58l4.03 3.13c.95-2.83 3.6-4.96 6.72-4.96z"
              />
            </svg>
          )}
          <span>{loading ? 'Authenticating...' : 'Sign in with Google'}</span>
        </button>

        {/* Read-Only Demo Option */}
        {onEnterGuestMode && (
          <div className="mt-3">
            <button
              onClick={onEnterGuestMode}
              className="w-full py-2.5 px-4 bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/50 text-[#FFFFFF] font-semibold text-xs rounded-xl flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm"
            >
              <Eye className="w-3.5 h-3.5 text-[#FFC107]" />
              <span>Continue in Guest Demo Mode</span>
            </button>
          </div>
        )}

        {/* Enterprise Security Features Checklist */}
        <div className="mt-6 pt-5 border-t border-[#333333] space-y-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9AA0A6] block mb-2">
            Enterprise Security Standards
          </span>
          <div className="grid grid-cols-2 gap-2 text-[11px] text-[#9AA0A6]">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#FFC107] shrink-0" />
              <span>Zero-Trust RBAC</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#FFC107] shrink-0" />
              <span>Token Verification</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#FFC107] shrink-0" />
              <span>Audit Logging</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#FFC107] shrink-0" />
              <span>GDPR Compliance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 mt-8 text-center text-xs text-[#9AA0A6]">
        TrustMoss Security Gateway &bull; Protected by Firebase Enterprise Identity
      </footer>
    </div>
  );
}

