'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Users,
  ShieldCheck,
  Download,
  LogOut,
  ChevronDown,
  User,
  Loader2,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function HeaderUserDropdown({ onOpenHitl, flaggedCount = 0 }) {
  const { user, loading, signInWithGoogle, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSignIn = async () => {
    try {
      setSigningIn(true);
      await signInWithGoogle();
      setIsOpen(false);
    } catch {
      // Handled in context
    } finally {
      setSigningIn(false);
    }
  };

  const handleExportAudit = async (e) => {
    e.stopPropagation();
    try {
      setExporting(true);
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

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to export compliance audit:', err);
    } finally {
      setExporting(false);
    }
  };

  const handleHitlClick = () => {
    setIsOpen(false);
    if (onOpenHitl) onOpenHitl();
  };

  const displayName = user?.displayName || user?.email?.split('@')[0] || 'Bhola Yadav';
  const userEmail = user?.email || (user ? 'Operator' : 'Guest Operator');

  if (loading) {
    return (
      <div className="h-8 w-28 bg-[#242424] border border-[#333333] rounded-xl animate-pulse" />
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Pill Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-2 bg-[#1E1E1E] hover:bg-[#242424] border border-[#333333] hover:border-[#FF8C00]/40 rounded-xl px-2.5 sm:px-3 py-1.5 text-xs transition-all shadow-sm cursor-pointer font-sans select-none"
        title="Account, Compliance & HITL Operations"
      >
        {/* Avatar */}
        {user?.photoURL ? (
          <img
            src={user.photoURL}
            alt={displayName}
            className="w-5 h-5 rounded-full border border-[#FF8C00]/50 object-cover shrink-0"
          />
        ) : (
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 text-[#FFC107] border border-[#FF8C00]/40 flex items-center justify-center font-bold text-[10px] shrink-0">
            {displayName.charAt(0).toUpperCase()}
          </div>
        )}

        {/* User Identity Info */}
        <div className="flex flex-col text-left">
          <span className="font-semibold text-[#FFFFFF] leading-tight max-w-[85px] sm:max-w-[120px] truncate text-[11px] sm:text-xs">
            {displayName}
          </span>
          <span className="text-[9px] sm:text-[10px] text-[#FFC107] flex items-center gap-1 font-mono leading-none mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF8C00] inline-block animate-pulse" />
            <span>Verified</span>
          </span>
        </div>

        {/* Notification Flag Dot (if HITL items pending) */}
        {flaggedCount > 0 && (
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
        )}

        {/* Dropdown Chevron */}
        <ChevronDown
          className={`w-3.5 h-3.5 text-[#9AA0A6] transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-[#FFC107]' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu Modal */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 sm:w-80 bg-[#1E1E1E] border border-[#333333] rounded-2xl shadow-2xl z-50 p-2 font-sans flex flex-col gap-1 backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Section 1: User Profile Header */}
          <div className="p-3 bg-[#121212] border border-[#333333] rounded-xl flex items-center gap-3">
            {user?.photoURL ? (
              <img
                src={user.photoURL}
                alt={displayName}
                className="w-9 h-9 rounded-full border border-[#FF8C00]/50 object-cover shrink-0 shadow-md"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 text-[#FFC107] border border-[#FF8C00]/40 flex items-center justify-center font-bold text-sm shrink-0">
                {displayName.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-xs text-[#FFFFFF] truncate">
                  {displayName}
                </span>
                <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono font-bold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30 shrink-0">
                  Verified
                </span>
              </div>
              <p className="text-[11px] text-[#9AA0A6] truncate mt-0.5 font-mono">
                {userEmail}
              </p>
            </div>
          </div>

          {/* Section 2: Operations Menu Items */}
          <div className="flex flex-col gap-0.5 pt-1">
            {/* Export Compliance Audit Option */}
            <button
              type="button"
              onClick={handleExportAudit}
              disabled={exporting}
              className="w-full px-3 py-2.5 rounded-xl text-left flex items-start gap-2.5 hover:bg-[#242424] text-[#FFFFFF] transition-colors cursor-pointer group disabled:opacity-50"
            >
              <div className="p-1.5 bg-[#242424] group-hover:bg-[#333333] border border-[#333333] group-hover:border-[#FF8C00]/40 rounded-lg text-[#FF8C00] shrink-0 transition-colors mt-0.5">
                {exporting ? (
                  <Loader2 className="w-4 h-4 animate-spin text-[#FF8C00]" />
                ) : exportSuccess ? (
                  <CheckCircle2 className="w-4 h-4 text-[#FFC107]" />
                ) : (
                  <Download className="w-4 h-4 text-[#FF8C00]" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#FFFFFF] group-hover:text-[#FFC107] transition-colors">
                    Export Compliance Audit
                  </span>
                  {exportSuccess && (
                    <span className="text-[10px] text-[#FFC107] font-mono font-bold">
                      Exported!
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#9AA0A6] line-clamp-1 mt-0.5">
                  Download certified GDPR, NIST AI RMF &amp; OWASP report
                </p>
              </div>
            </button>

            {/* HITL Queue Option */}
            <button
              type="button"
              onClick={handleHitlClick}
              className="w-full px-3 py-2.5 rounded-xl text-left flex items-start gap-2.5 hover:bg-[#242424] text-[#FFFFFF] transition-colors cursor-pointer group"
            >
              <div className="p-1.5 bg-[#242424] group-hover:bg-[#333333] border border-[#333333] group-hover:border-[#FFC107]/40 rounded-lg text-[#FFC107] shrink-0 transition-colors mt-0.5">
                <Users className="w-4 h-4 text-[#FFC107]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#FFFFFF] group-hover:text-[#FFC107] transition-colors">
                    HITL Review Queue
                  </span>
                  {flaggedCount > 0 ? (
                    <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold font-mono">
                      {flaggedCount} Pending
                    </span>
                  ) : (
                    <span className="text-[10px] text-[#9AA0A6] font-mono">
                      All Clear
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#9AA0A6] line-clamp-1 mt-0.5">
                  Inspect flagged model turns &amp; apply human override
                </p>
              </div>
            </button>
          </div>

          {/* Section 3: Auth Controls (Sign In / Sign Out) */}
          <div className="pt-1 mt-1 border-t border-[#333333]">
            {user ? (
              <button
                type="button"
                onClick={() => {
                  logout();
                  setIsOpen(false);
                }}
                className="w-full px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-950/25 flex items-center gap-2 transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSignIn}
                disabled={signingIn}
                className="w-full px-3 py-2 bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm disabled:opacity-50"
              >
                <User className="w-4 h-4" />
                <span>{signingIn ? 'Connecting...' : 'Sign in with Google'}</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
