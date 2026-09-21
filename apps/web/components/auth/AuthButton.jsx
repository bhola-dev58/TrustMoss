'use client';

import React, { useState } from 'react';
import { LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AuthButton() {
  const { user, loading, signInWithGoogle, logout } = useAuth();
  const [signingIn, setSigningIn] = useState(false);

  const handleSignIn = async () => {
    try {
      setSigningIn(true);
      await signInWithGoogle();
    } catch {
      // User cancelled or closed popup
    } finally {
      setSigningIn(false);
    }
  };

  if (loading) {
    return (
      <div
        data-testid="auth-loading"
        className="h-8 w-24 bg-slate-800/60 rounded-xl animate-pulse border border-slate-800"
      />
    );
  }

  if (user) {
    const displayName = user.displayName || user.email?.split('@')[0] || 'User';
    return (
      <div
        data-testid="auth-user-badge"
        className="flex items-center gap-2 bg-[#242424] border border-[#333333] rounded-xl px-2.5 py-1 text-xs shadow-sm font-sans"
      >
        {user.photoURL ? (
          <img
            src={user.photoURL}
            alt={displayName}
            className="w-5 h-5 rounded-full border border-[#FF8C00]/40 object-cover"
          />
        ) : (
          <div className="w-5 h-5 rounded-full bg-[#FF8C00]/20 text-[#FFC107] border border-[#FF8C00]/40 flex items-center justify-center font-bold text-[10px]">
            {displayName.charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex flex-col text-left">
          <span className="font-semibold text-[#FFFFFF] leading-tight max-w-[110px] truncate">
            {displayName}
          </span>
          <span className="text-[10px] text-[#FFC107] flex items-center gap-1 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF8C00] inline-block animate-pulse" />
            Verified
          </span>
        </div>
        <button
          onClick={logout}
          title="Sign Out"
          className="ml-1 p-1 text-[#9AA0A6] hover:text-rose-400 hover:bg-[#333333] rounded-lg transition-colors cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleSignIn}
      disabled={signingIn}
      data-testid="auth-login-button"
      className="px-3 py-1.5 bg-[#242424] hover:bg-[#333333] border border-[#333333] hover:border-[#FF8C00]/40 text-xs font-semibold rounded-xl flex items-center gap-2 text-[#FFFFFF] transition-all shadow-sm disabled:opacity-50 cursor-pointer font-sans"
    >
      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
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
      <span>{signingIn ? 'Connecting...' : 'Sign in with Google'}</span>
    </button>
  );

}
